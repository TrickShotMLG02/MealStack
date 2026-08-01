from __future__ import annotations

import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management.color import color_style
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.test.runner import DiscoverRunner


APP_SOURCE = ["apps"]
APP_OMIT = [
    "*/tests/*",
    "*/migrations/*",
    "*/test_runner.py",
    "*/management/commands/test_coverage.py",
]


@dataclass(frozen=True)
class CoverageResult:
    label: str
    status: str
    scope: str
    statements: int
    missing: int
    covered: int
    percent: float
    executed: int
    succeeded: int
    failed: int
    errors: int
    skipped: int


@dataclass(frozen=True)
class TestSummary:
    discovered: int
    executed: int
    succeeded: int
    failed: int
    errors: int
    skipped: int


class ProgressDiscoverRunner(DiscoverRunner):
    def __init__(self, *args, progress_bar=None, **kwargs):
        self.progress_bar = progress_bar
        super().__init__(*args, **kwargs)

    def get_resultclass(self):
        base_result_class = super().get_resultclass() or unittest.TextTestResult
        progress_bar = self.progress_bar

        class ProgressTextTestResult(base_result_class):
            def stopTest(self, test):
                super().stopTest(test)
                if progress_bar is not None:
                    progress_bar.update(1)

        return ProgressTextTestResult


class Command(BaseCommand):
    help = (
        "Run the Django test suite and report app-only coverage overall and "
        "for each discovered test."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "test_labels",
            nargs="*",
            help="Optional test labels. Defaults to all discovered tests.",
        )
        parser.add_argument(
            "--pattern",
            default="test*.py",
            help="Test discovery pattern. Defaults to test*.py.",
        )
        parser.add_argument(
            "--keepdb",
            action="store_true",
            help="Preserve the test database between runs.",
        )
        parser.add_argument(
            "--per-test",
            action="store_true",
            help="Also run each discovered test individually for touched-file coverage.",
        )
        parser.add_argument(
            "--configured-database",
            action="store_true",
            help=(
                "Use the database configured by the active settings instead "
                "of the default temporary SQLite test database."
            ),
        )
        parser.add_argument(
            "--no-progress",
            action="store_true",
            help="Disable progress bars and print line-based progress instead.",
        )

    def handle(self, *args, **options):
        self.no_color_output = options["no_color"]
        if not options["no_color"]:
            self.style = color_style(force_color=True)

        try:
            import coverage
        except ImportError as exc:
            raise CommandError(
                "The coverage package is required. Install dev dependencies "
                "or run `uv sync --dev`."
            ) from exc

        labels = options["test_labels"]
        pattern = options["pattern"]
        keepdb = options["keepdb"]
        include_per_test = options["per_test"]
        use_progress = not options["no_progress"]
        tqdm = self._get_tqdm(use_progress)

        if not options["configured_database"]:
            self._use_sqlite_test_database()

        discovered_tests = self._discover_test_ids(labels, pattern)
        if not discovered_tests:
            raise CommandError("No tests were discovered.")

        self.stdout.write(f"Discovered {len(discovered_tests)} test(s).")

        with TemporaryDirectory(prefix="mealstack-coverage-") as coverage_dir:
            overall_progress = self._progress_bar(
                tqdm,
                total=len(discovered_tests),
                desc="Overall coverage",
                use_progress=use_progress,
            )
            overall = self._run_with_coverage(
                coverage,
                labels,
                "overall",
                coverage_dir,
                coverage_scope="app",
                pattern=pattern,
                keepdb=keepdb,
                progress_bar=overall_progress,
            )
            if overall_progress is not None:
                overall_progress.close()

            per_test_results = []
            if include_per_test:
                per_test_progress = self._progress_bar(
                    tqdm,
                    total=len(discovered_tests),
                    desc="Per-test coverage",
                    use_progress=use_progress,
                )
                for index, test_label in enumerate(discovered_tests, start=1):
                    if not use_progress:
                        self.stdout.write(
                            f"[{index}/{len(discovered_tests)}] Measuring {test_label}"
                        )
                    result = self._run_with_coverage(
                        coverage,
                        [test_label],
                        test_label,
                        coverage_dir,
                        coverage_scope="touched-files",
                        pattern=pattern,
                        keepdb=keepdb,
                        progress_bar=None,
                    )
                    per_test_results.append(result)
                    if per_test_progress is not None:
                        per_test_progress.update(1)
                if per_test_progress is not None:
                    per_test_progress.close()

        if include_per_test:
            self._print_results("Per-test touched-file coverage", per_test_results)
            self.stdout.write("")

        self._print_results("Overall app coverage", [overall])
        self.stdout.write("")
        if include_per_test:
            self._print_summary(
                "Per-test execution summary",
                self._summarize_results(discovered_tests, per_test_results),
            )
        else:
            self._print_summary(
                "Execution summary",
                self._summarize_results(discovered_tests, [overall]),
            )

    def _discover_test_ids(self, labels, pattern):
        runner = DiscoverRunner(
            verbosity=0,
            interactive=False,
            pattern=pattern,
        )
        suite = runner.build_suite(test_labels=labels)
        return sorted(test.id() for test in self._iter_test_cases(suite))

    def _use_sqlite_test_database(self):
        databases = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        }
        settings.DATABASES = connections.configure_settings(databases)
        connections.close_all()
        connections.settings = settings.DATABASES
        connections._settings = settings.DATABASES
        if hasattr(connections._connections, "default"):
            delattr(connections._connections, "default")

    def _iter_test_cases(self, suite):
        for item in suite:
            if isinstance(item, unittest.TestSuite):
                yield from self._iter_test_cases(item)
            else:
                yield item

    def _get_tqdm(self, use_progress):
        if not use_progress:
            return None
        try:
            from tqdm import tqdm
        except ImportError as exc:
            raise CommandError(
                "The tqdm package is required for progress bars. Install dev "
                "dependencies with `uv sync --dev`, or pass `--no-progress`."
            ) from exc
        return tqdm

    def _progress_bar(self, tqdm, *, total, desc, use_progress):
        if not use_progress:
            return None
        return tqdm(
            total=total,
            desc=desc,
            unit="test",
            file=sys.stderr,
            leave=False,
            ncols=100,
            colour=None if self.no_color_output else "cyan",
        )

    def _run_with_coverage(
        self,
        coverage_module,
        test_labels,
        result_label,
        coverage_dir,
        *,
        coverage_scope,
        pattern,
        keepdb,
        progress_bar,
    ):
        data_file = os.path.join(coverage_dir, ".coverage")
        cov = coverage_module.Coverage(
            data_file=data_file,
            config_file=False,
            source=APP_SOURCE,
            omit=APP_OMIT,
        )
        cov.set_option("run:disable_warnings", ["no-data-collected"])

        runner = ProgressDiscoverRunner(
            verbosity=0,
            interactive=False,
            pattern=pattern,
            keepdb=keepdb,
            progress_bar=progress_bar,
        )

        captured_stdout = StringIO()
        captured_stderr = StringIO()
        coverage_started = False
        result = None
        try:
            cov.start()
            coverage_started = True
            with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
                result = self._run_suite(runner, test_labels)
            cov.stop()
            coverage_started = False
        except SystemExit as exc:
            self._write_captured_output(captured_stdout, captured_stderr)
            raise CommandError(
                f"{result_label} exited during test setup or execution "
                f"with code {exc.code}."
            ) from exc
        finally:
            if coverage_started:
                cov.stop()
        cov.save()

        statements, missing = self._coverage_counts(cov, coverage_scope)

        errors = len(result.errors)
        failed = len(result.failures) + len(result.unexpectedSuccesses)
        skipped = len(result.skipped)
        succeeded = (
            result.testsRun
            - failed
            - errors
            - skipped
            - len(result.expectedFailures)
        )
        status = "passed"
        if errors:
            status = "error"
        elif failed:
            status = "failed"
        elif skipped == result.testsRun:
            status = "skipped"

        covered = statements - missing
        percent = (covered / statements * 100) if statements else 100.0
        return CoverageResult(
            result_label,
            status,
            coverage_scope,
            statements,
            missing,
            covered,
            percent,
            result.testsRun,
            max(succeeded, 0),
            failed,
            errors,
            skipped,
        )

    def _coverage_counts(self, cov, coverage_scope):
        statements = 0
        missing = 0
        for filename in cov.get_data().measured_files():
            analysis = cov.analysis2(filename)
            executable_statements = analysis[1]
            missing_statements = analysis[3]
            executed_statements = set(executable_statements) - set(missing_statements)
            if coverage_scope == "touched-files" and not executed_statements:
                continue
            statements += len(executable_statements)
            missing += len(missing_statements)
        return statements, missing

    def _run_suite(self, runner, test_labels):
        runner.setup_test_environment()
        suite = runner.build_suite(test_labels)
        databases = runner.get_databases(suite)
        suite.serialized_aliases = {
            alias for alias, serialize in databases.items() if serialize
        }
        suite.used_aliases = set(databases)
        old_config = runner.setup_databases(
            aliases=databases,
            serialized_aliases=suite.serialized_aliases,
        )
        run_failed = False
        try:
            runner.run_checks(databases)
            return runner.run_suite(suite)
        except Exception:
            run_failed = True
            raise
        finally:
            try:
                runner.teardown_databases(old_config)
                runner.teardown_test_environment()
            except Exception:
                if not run_failed:
                    raise

    def _write_captured_output(self, captured_stdout, captured_stderr):
        output = captured_stdout.getvalue() + captured_stderr.getvalue()
        if output:
            self.stderr.write(output)

    def _print_results(self, title, results):
        label_width = max(len("Test"), *(len(result.label) for result in results))
        status_width = max(len("Status"), *(len(result.status) for result in results))
        self.stdout.write(self.style.MIGRATE_HEADING(title))
        self.stdout.write(
            f"{'Test'.ljust(label_width)}  "
            f"{'Status'.ljust(status_width)}  "
            f"Scope          Executed/Statements  Coverage"
        )
        self.stdout.write(
            f"{'-' * label_width}  "
            f"{'-' * status_width}  "
            f"-------------  -------------------  --------"
        )
        for result in results:
            executed_statements = (
                f"{result.covered}/{result.statements}"
                if result.status == "passed" and result.statements
                else "n/a"
            )
            coverage = (
                f"{result.percent:.1f}%"
                if result.status == "passed" and result.statements
                else "n/a"
            )
            self.stdout.write(
                f"{result.label.ljust(label_width)}  "
                f"{self._style_status(result.status.ljust(status_width))}  "
                f"{result.scope.ljust(13)}  "
                f"{executed_statements.ljust(19)}  "
                f"{self._style_coverage(coverage, result.percent)}"
            )

    def _summarize_results(self, discovered_tests, results):
        return TestSummary(
            discovered=len(discovered_tests),
            executed=sum(result.executed for result in results),
            succeeded=sum(result.succeeded for result in results),
            failed=sum(result.failed for result in results),
            errors=sum(result.errors for result in results),
            skipped=sum(result.skipped for result in results),
        )

    def _print_summary(self, title, summary):
        self.stdout.write(self.style.MIGRATE_HEADING(title))
        self.stdout.write(f"Discovered: {summary.discovered}")
        self.stdout.write(f"Executed:   {summary.executed}")
        self.stdout.write(f"Succeeded:  {self.style.SUCCESS(str(summary.succeeded))}")
        self.stdout.write(f"Failed:     {self._style_count(summary.failed, bad=True)}")
        self.stdout.write(f"Errors:     {self._style_count(summary.errors, bad=True)}")
        self.stdout.write(f"Skipped:    {self._style_count(summary.skipped, warning=True)}")

    def _style_status(self, status):
        stripped_status = status.strip()
        if stripped_status == "passed":
            return self.style.SUCCESS(status)
        if stripped_status == "skipped":
            return self.style.WARNING(status)
        if stripped_status in {"failed", "error"}:
            return self.style.ERROR(status)
        return status

    def _style_coverage(self, coverage, percent):
        if coverage == "n/a":
            return self.style.WARNING(coverage)
        if percent >= 80:
            return self.style.SUCCESS(coverage)
        if percent >= 50:
            return self.style.WARNING(coverage)
        return self.style.ERROR(coverage)

    def _style_count(self, count, *, bad=False, warning=False):
        count_text = str(count)
        if count == 0:
            return self.style.SUCCESS(count_text)
        if bad:
            return self.style.ERROR(count_text)
        if warning:
            return self.style.WARNING(count_text)
        return count_text
