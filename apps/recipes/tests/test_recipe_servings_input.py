import json
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent
from unittest import skipUnless

from django.test import SimpleTestCase


RECIPE_DETAIL_SCRIPT = Path(__file__).resolve().parents[3] / "MealStack" / "static" / "recipes" / "js" / "recipe_detail.js"
NODE_BINARY = shutil.which("node")


@skipUnless(NODE_BINARY, "Node.js is required for the recipe detail JavaScript tests")
class RecipeServingsInputJavaScriptTests(SimpleTestCase):
    def run_browser_simulation(self):
        script_path = json.dumps(str(RECIPE_DETAIL_SCRIPT))
        browser_simulation = dedent(
            f"""
            const fs = require('fs');
            const vm = require('vm');
            const recipeDetailScript = fs.readFileSync({script_path}, 'utf8');

            class Element {{
                constructor(value = '') {{
                    this.value = value;
                    this.dataset = {{}};
                    this.listeners = {{}};
                    this.textContent = '';
                    this.classList = {{
                        enabled: false,
                        toggle: (name, enabled) => {{ this.classList.enabled = enabled; }},
                        contains: () => this.classList.enabled,
                    }};
                }}

                addEventListener(name, handler) {{ this.listeners[name] = handler; }}
                setAttribute() {{}}
                dispatch(name, event = {{}}) {{
                    if (this.listeners[name]) this.listeners[name](event);
                }}
            }}

            const article = new Element();
            article.dataset.baseServings = '4';
            const toggle = new Element();
            toggle.dataset.labelOn = 'Exit cook mode';
            toggle.dataset.labelOff = 'Cook mode';
            const input = new Element('4');
            const servingsControl = new Element();
            const servingsDisplay = new Element();
            const selectedSummary = new Element();
            const selectedNote = new Element();
            const elements = {{
                '.recipe-detail': article,
                '[data-cook-toggle]': toggle,
                '[data-servings-control]': servingsControl,
                '[data-servings-input]': input,
                '[data-servings-decrease]': new Element(),
                '[data-servings-increase]': new Element(),
                '[data-selected-servings-summary]': selectedSummary,
                '[data-selected-servings-note]': selectedNote,
            }};
            let lastUrl = null;
            const context = {{
                document: {{
                    documentElement: {{ lang: 'de' }},
                    querySelector: (selector) => elements[selector] || null,
                    querySelectorAll: (selector) => selector === '[data-servings-display]' ? [servingsDisplay] : [],
                    addEventListener: (name, handler) => {{
                        if (name === 'DOMContentLoaded') handler();
                    }},
                }},
                navigator: {{ language: 'de-DE' }},
                localStorage: {{ getItem: () => null, setItem: () => {{}} }},
                window: {{ location: {{ href: 'https://example.test/recipes/pizza/' }} }},
                history: {{ replaceState: (_state, _title, url) => {{ lastUrl = url; }} }},
                URL,
                Intl,
                console,
            }};

            vm.runInNewContext(recipeDetailScript, context);

            function assertEqual(actual, expected, message) {{
                if (actual !== expected) {{
                    throw new Error(`${{message}}: expected ${{JSON.stringify(expected)}}, got ${{JSON.stringify(actual)}}`);
                }}
            }}

            function enter(value) {{
                input.value = value;
                input.dispatch('input');
            }}

            assertEqual(input.value, '4', 'initial serving value');

            enter('3');
            assertEqual(input.value, '3', 'integer input');
            enter('3,');
            assertEqual(input.value, '3,', 'trailing comma remains editable');
            enter('3,5');
            assertEqual(input.value, '3,5', 'completed comma decimal');
            enter('3.');
            assertEqual(input.value, '3.', 'trailing dot remains editable');
            enter('3.5');
            assertEqual(input.value, '3,5', 'completed dot decimal is localized');

            enter('3,');
            input.dispatch('change');
            assertEqual(input.value, '3', 'unfinished decimal is normalized on change');
            enter('3,');
            servingsControl.dispatch('keydown', {{ key: 'Enter' }});
            assertEqual(input.value, '3', 'unfinished decimal is normalized on Enter');

            enter('3,');
            elements['[data-servings-increase]'].dispatch('click');
            assertEqual(input.value, '4', 'increase button handles an unfinished decimal');

            enter('7 ');
            assertEqual(input.value, '7 ', 'space before a mixed fraction remains editable');
            enter('7 3');
            assertEqual(input.value, '7 3', 'mixed fraction numerator remains editable');
            enter('7 3/');
            assertEqual(input.value, '7 3/', 'mixed fraction slash remains editable');
            enter('7 3/4');
            assertEqual(input.value, '7 3/4', 'completed mixed fraction remains visible while editing');
            assertEqual(servingsDisplay.textContent, '7,75', 'display follows mixed fraction value');
            assertEqual(selectedSummary.textContent, '7,75', 'summary follows mixed fraction value');
            assertEqual(selectedNote.textContent, '7,75', 'note follows mixed fraction value');
            if (!String(lastUrl).includes('servings=7.75')) throw new Error('URL was not updated for mixed fraction');
            input.dispatch('change');
            assertEqual(input.value, '7,75', 'mixed fraction is normalized on change');
            enter('7 3/4');
            servingsControl.dispatch('keydown', {{ key: 'Enter' }});
            assertEqual(input.value, '7,75', 'mixed fraction is normalized on Enter');

            enter('31/4');
            assertEqual(input.value, '7,75', 'simple fraction remains supported');

            enter('not a number');
            assertEqual(input.value, 'not a number', 'invalid input is not destroyed while typing');
            input.dispatch('change');
            assertEqual(input.value, '4', 'invalid input falls back on change');
            console.log('recipe serving browser simulation passed');
            """
        )
        result = subprocess.run(
            [NODE_BINARY, "-e", browser_simulation],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_serving_input_supports_decimals_and_mixed_fractions(self):
        self.run_browser_simulation()
