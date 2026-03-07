from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase


BACKEND_DIR = Path(__file__).resolve().parents[2]
JS_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard.js"
CSS_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard.css"
DASHBOARD_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "dashboard.html"
COACH_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "coach_training_plans.html"
MONTH_CARDS_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_month_cards.html"


class DashboardFrontendRegressionTests(SimpleTestCase):
    def test_js_contains_keyboard_navigation_and_selection_handlers(self):
        js = JS_PATH.read_text(encoding="utf-8")

        self.assertIn('event.key === "Enter"', js)
        self.assertIn('event.key === "Tab"', js)
        self.assertIn('event.key === "Delete"', js)
        self.assertIn('event.key === "Backspace"', js)
        self.assertIn('event.key === "ArrowDown"', js)
        self.assertIn('event.key === "ArrowUp"', js)
        self.assertIn('event.key === "ArrowLeft"', js)
        self.assertIn('event.key === "ArrowRight"', js)
        self.assertIn('event.key === "z" || event.key === "Z"', js)
        self.assertIn('event.key === "y" || event.key === "Y"', js)
        self.assertIn("clearSelectedCellsIfAny()", js)

    def test_js_contains_column_width_equalization_for_month(self):
        js = JS_PATH.read_text(encoding="utf-8")

        self.assertIn('--eb-planned-training-col-width', js)
        self.assertIn('--eb-planned-notes-col-width', js)
        self.assertIn("measureNodesMaxWidth", js)
        self.assertIn('month.style.setProperty("--eb-planned-training-col-width"', js)
        self.assertIn('month.style.setProperty("--eb-planned-notes-col-width"', js)
        self.assertIn('querySelectorAll(".eb-week-row")', js)
        self.assertIn('querySelectorAll(".eb-col-planned tbody tr")', js)
        self.assertIn('querySelectorAll(".eb-col-completed tbody tr")', js)

    def test_css_contains_selection_states_and_column_width_variables(self):
        css = CSS_PATH.read_text(encoding="utf-8")

        self.assertIn("--eb-planned-training-col-width", css)
        self.assertIn("--eb-planned-notes-col-width", css)
        self.assertIn(".eb-inline-edit.is-selected", css)
        self.assertIn(".eb-inline-edit.is-selection-anchor", css)
        self.assertIn("width: var(--eb-planned-training-col-width);", css)
        self.assertIn("width: var(--eb-planned-notes-col-width);", css)

    def test_dashboard_and_coach_templates_use_same_asset_versions(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_html = COACH_TEMPLATE_PATH.read_text(encoding="utf-8")

        js_pattern = re.compile(r"js/dashboard\.js' %}\?v=(\d+)")
        css_pattern = re.compile(r"css/dashboard\.css' %}\?v=(\d+)")

        dashboard_js_match = js_pattern.search(dashboard_html)
        coach_js_match = js_pattern.search(coach_html)
        dashboard_css_match = css_pattern.search(dashboard_html)
        coach_css_match = css_pattern.search(coach_html)

        self.assertIsNotNone(dashboard_js_match)
        self.assertIsNotNone(coach_js_match)
        self.assertIsNotNone(dashboard_css_match)
        self.assertIsNotNone(coach_css_match)

        dashboard_js_version = int(dashboard_js_match.group(1))
        coach_js_version = int(coach_js_match.group(1))
        dashboard_css_version = int(dashboard_css_match.group(1))
        coach_css_version = int(coach_css_match.group(1))

        self.assertEqual(dashboard_js_version, coach_js_version)
        self.assertEqual(dashboard_css_version, coach_css_version)

    def test_month_cards_template_contains_planned_footer_row_for_alignment(self):
        month_cards_html = MONTH_CARDS_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn('tfoot class="table-light eb-planned-week-footer"', month_cards_html)
