from __future__ import annotations

import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from django.core.management.color import color_style, no_style
from django.test.runner import DiscoverRunner


class StyledProgressTestRunner(DiscoverRunner):
    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--no-progress",
            action="store_true",
            help="Disable the test progress bar.",
        )

    def __init__(self, *args, no_progress=False, no_color=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.no_progress = no_progress
        self.no_color = no_color
        self.style = no_style() if no_color else color_style(force_color=True)
        self.progress_bar = None

    def get_resultclass(self):
        base_result_class = super().get_resultclass() or unittest.TextTestResult
        progress_bar = self.progress_bar

        class ProgressTextTestResult(base_result_class):
            def stopTest(self, test):
                super().stopTest(test)
                if progress_bar is not None:
                    progress_bar.update(1)

        return ProgressTextTestResult

    def get_test_runner_kwargs(self):
        kwargs = super().get_test_runner_kwargs()
        if self._use_progress_bar():
            kwargs["verbosity"] = 0
        return kwargs

    def run_tests(self, test_labels, **kwargs):
        self.setup_test_environment()
        suite = self.build_suite(test_labels)
        databases = self.get_databases(suite)
        suite.serialized_aliases = {
            alias for alias, serialize in databases.items() if serialize
        }
        suite.used_aliases = set(databases)

        with self.time_keeper.timed("Total database setup"):
            old_config = self.setup_databases(
                aliases=databases,
                serialized_aliases=suite.serialized_aliases,
            )

        run_failed = False
        result = None
        captured_stdout = StringIO()
        captured_stderr = StringIO()
        try:
            self.run_checks(databases)
            self.progress_bar = self._create_progress_bar(suite)
            if self.progress_bar is None:
                result = self.run_suite(suite)
            else:
                with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
                    result = self.run_suite(suite)
            if self.progress_bar is not None:
                self.progress_bar.close()
        except Exception:
            run_failed = True
            raise
        finally:
            if self.progress_bar is not None:
                self.progress_bar.close()
                self.progress_bar = None
            try:
                with self.time_keeper.timed("Total database teardown"):
                    self.teardown_databases(old_config)
                self.teardown_test_environment()
            except Exception:
                if not run_failed:
                    raise

        self.time_keeper.print_results()
        if result is not None and self.suite_result(suite, result):
            self._write_captured_output(captured_stdout, captured_stderr)
        self._print_summary(suite, result)
        return self.suite_result(suite, result)

    def _use_progress_bar(self):
        return not self.no_progress and self.parallel == 0

    def _create_progress_bar(self, suite):
        if not self._use_progress_bar():
            return None

        try:
            from tqdm import tqdm
        except ImportError:
            return None

        return tqdm(
            total=suite.countTestCases(),
            desc="Running tests",
            unit="test",
            file=sys.stderr,
            leave=False,
            ncols=100,
            colour=None if self.no_color else "cyan",
        )

    def _print_summary(self, suite, result):
        tests_run = result.testsRun
        failed = len(result.failures) + len(result.unexpectedSuccesses)
        errors = len(result.errors)
        skipped = len(result.skipped)
        succeeded = max(
            tests_run - failed - errors - skipped - len(result.expectedFailures),
            0,
        )

        print(self.style.MIGRATE_HEADING("Test summary"), file=sys.stderr)
        print(f"Discovered: {suite.countTestCases()}", file=sys.stderr)
        print(f"Executed:   {tests_run}", file=sys.stderr)
        print(f"Succeeded:  {self.style.SUCCESS(str(succeeded))}", file=sys.stderr)
        print(f"Failed:     {self._style_count(failed, bad=True)}", file=sys.stderr)
        print(f"Errors:     {self._style_count(errors, bad=True)}", file=sys.stderr)
        print(f"Skipped:    {self._style_count(skipped, warning=True)}", file=sys.stderr)

    def _write_captured_output(self, captured_stdout, captured_stderr):
        output = captured_stdout.getvalue() + captured_stderr.getvalue()
        if output:
            print(output, file=sys.stderr, end="")

    def _style_count(self, count, *, bad=False, warning=False):
        count_text = str(count)
        if count == 0:
            return self.style.SUCCESS(count_text)
        if bad:
            return self.style.ERROR(count_text)
        if warning:
            return self.style.WARNING(count_text)
        return count_text
