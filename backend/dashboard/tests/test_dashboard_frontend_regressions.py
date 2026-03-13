from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase


BACKEND_DIR = Path(__file__).resolve().parents[2]
JS_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard.js"
JS_CORE_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_core.js"
JS_METRICS_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_metrics.js"
JS_API_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_api.js"
JS_INLINE_SHARED_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_inline_shared.js"
JS_MONTH_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_month.js"
JS_PLANNED_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_editor_planned.js"
JS_COMPLETED_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_editor_completed.js"
JS_COACH_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_coach.js"
CSS_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard.css"
DASHBOARD_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "dashboard.html"
COACH_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "coach_training_plans.html"
MONTH_CARDS_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_month_cards.html"
ASSETS_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_assets.html"
BASE_TEMPLATE_PATH = BACKEND_DIR / "templates" / "base.html"


class DashboardFrontendRegressionTests(SimpleTestCase):
    def _combined_js(self) -> str:
        parts = [
            JS_PATH.read_text(encoding="utf-8"),
            JS_CORE_PATH.read_text(encoding="utf-8"),
            JS_METRICS_PATH.read_text(encoding="utf-8"),
            JS_API_PATH.read_text(encoding="utf-8"),
            JS_INLINE_SHARED_PATH.read_text(encoding="utf-8"),
            JS_MONTH_PATH.read_text(encoding="utf-8"),
            JS_PLANNED_PATH.read_text(encoding="utf-8"),
            JS_COMPLETED_PATH.read_text(encoding="utf-8"),
            JS_COACH_PATH.read_text(encoding="utf-8"),
        ]
        return "\n".join(parts)

    def test_js_contains_keyboard_navigation_and_selection_handlers(self):
        js = self._combined_js()

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
        self.assertIn('isCtrlOrMeta && event.key === "Enter"', js)
        self.assertIn('isCtrlOrMeta && event.shiftKey && event.key === "Enter"', js)
        self.assertIn("clearSelectedCellsIfAny()", js)

    def test_js_contains_column_width_equalization_for_month(self):
        js = self._combined_js()

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

    def test_dashboard_and_coach_templates_use_shared_asset_version_token(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_html = COACH_TEMPLATE_PATH.read_text(encoding="utf-8")
        assets_html = ASSETS_TEMPLATE_PATH.read_text(encoding="utf-8")

        expected_suffix = "?v={{ dashboard_asset_version }}"
        self.assertIn('{% include "dashboard/_assets.html" %}', dashboard_html)
        self.assertIn('{% include "dashboard/_assets.html" %}', coach_html)
        self.assertIn(f"css/dashboard.css' %}}{expected_suffix}", assets_html)
        self.assertIn(f"js/dashboard.js' %}}{expected_suffix}", assets_html)

    def test_dashboard_and_coach_templates_include_module_chain(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_html = COACH_TEMPLATE_PATH.read_text(encoding="utf-8")
        assets_html = ASSETS_TEMPLATE_PATH.read_text(encoding="utf-8")

        required_assets = [
            "js/dashboard_core.js",
            "js/dashboard_metrics.js",
            "js/dashboard_api.js",
            "js/dashboard_inline_shared.js",
            "js/dashboard_month.js",
            "js/dashboard_editor_planned.js",
            "js/dashboard_editor_completed.js",
            "js/dashboard_coach.js",
            "js/dashboard.js",
        ]

        for asset in required_assets:
            self.assertIn(asset, assets_html)
            self.assertIn(f"{asset}' %}}?v={{{{ dashboard_asset_version }}}}", assets_html)
        self.assertIn('{% include "dashboard/_assets.html" %}', dashboard_html)
        self.assertIn('{% include "dashboard/_assets.html" %}', coach_html)

    def test_dashboard_bootstrap_uses_fail_fast_dependency_guards(self):
        js = JS_PATH.read_text(encoding="utf-8")
        self.assertIn("requiredFn(", js)
        self.assertIn("EB module dependency is missing", js)

    def test_month_cards_template_contains_planned_footer_row_for_alignment(self):
        month_cards_html = MONTH_CARDS_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn('tfoot class="table-light eb-planned-week-footer"', month_cards_html)
        self.assertIn("eb-planned-week-total-km", month_cards_html)
        self.assertIn('data-bs-target="#ebPlannedKmRulesModal"', month_cards_html)
        self.assertIn('id="ebPlannedKmRulesModal"', month_cards_html)
        self.assertIn("eb-plan-rules-onboarding", month_cards_html)
        self.assertIn("eb-plan-rules-dismiss", month_cards_html)
        self.assertIn('data-completed-inline-editable="1"', month_cards_html)
        self.assertIn('data-add-phase-url="{{ add_phase_url }}"', month_cards_html)
        self.assertIn('data-remove-phase-url="{{ remove_phase_url }}"', month_cards_html)
        self.assertIn("eb-completed-inline-edit", month_cards_html)

    def test_garmin_week_sync_hook_is_present_in_template_and_js(self):
        month_cards_html = MONTH_CARDS_TEMPLATE_PATH.read_text(encoding="utf-8")
        js = JS_PATH.read_text(encoding="utf-8")

        self.assertIn('data-garmin-week-sync-url="{{ garmin_week_sync_url }}"', month_cards_html)
        self.assertIn("eb-garmin-week-sync-btn", month_cards_html)
        self.assertIn("data-week-start", month_cards_html)
        self.assertIn('closest(".eb-garmin-week-sync-btn")', js)
        self.assertIn('formData.append("week_start", weekStart)', js)
        self.assertIn("notifications.updateNotification({", js)
        self.assertIn('imported ${job.imported_count || 0}, duplicates ${job.skipped_count || 0}.', js)
        self.assertIn("Garmin sync is running.", js)

    def test_base_template_keeps_top_nav_sticky(self):
        base_html = BASE_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn(".eb-top-nav {", base_html)
        self.assertIn("position: sticky;", base_html)
        self.assertIn("top: 0;", base_html)
        self.assertIn('class="navbar navbar-expand-lg navbar-light bg-white border-bottom eb-top-nav"', base_html)

    def test_dashboard_toolbar_is_sticky_below_top_nav(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        css = CSS_PATH.read_text(encoding="utf-8")

        self.assertIn("eb-dashboard-toolbar", dashboard_html)
        self.assertIn(".eb-dashboard-toolbar {", css)
        self.assertIn("position: sticky;", css)
        self.assertIn("top: 57px;", css)
