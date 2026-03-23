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
JS_BOOTSTRAP_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_bootstrap.js"
JS_FIT_IMPORT_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_fit_import.js"
JS_GARMIN_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_garmin.js"
JS_LEGEND_SHORTCUTS_PATH = BACKEND_DIR / "dashboard" / "static" / "js" / "dashboard_legend_shortcuts.js"
CSS_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard.css"
CSS_MONTH_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard_month.css"
CSS_IMPORT_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard_import.css"
CSS_COACH_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard_coach.css"
CSS_LEGEND_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard_legend.css"
CSS_EDITOR_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard_editor.css"
CSS_RESPONSIVE_PATH = BACKEND_DIR / "dashboard" / "static" / "css" / "dashboard_responsive.css"
BASE_CSS_PATH = BACKEND_DIR / "static" / "css" / "base.css"
BASE_JS_PATH = BACKEND_DIR / "static" / "js" / "base_ui.js"
DASHBOARD_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "dashboard.html"
COACH_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "coach_training_plans.html"
MONTH_CARDS_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_month_cards.html"
ASSETS_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_assets.html"
BASE_TEMPLATE_PATH = BACKEND_DIR / "templates" / "base.html"
TOP_NAV_TEMPLATE_PATH = BACKEND_DIR / "templates" / "includes" / "_top_nav.html"
NOTIFICATIONS_TEMPLATE_PATH = BACKEND_DIR / "templates" / "includes" / "_notifications_dropdown.html"
PROFILE_MODAL_TEMPLATE_PATH = BACKEND_DIR / "templates" / "includes" / "_profile_modal.html"
LEGEND_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_legend_modals.html"
PLANNED_WEEK_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_planned_week_table.html"
COMPLETED_WEEK_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_completed_week_table.html"
MONTH_SWITCHER_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_month_switcher.html"
KM_RULES_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_planned_km_rules_modal.html"
DASHBOARD_HEADER_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_dashboard_header.html"
IMPORT_MODAL_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_import_modal.html"
COACH_SIDEBAR_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_coach_sidebar.html"
COACH_MAIN_TOOLBAR_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_coach_main_toolbar.html"
COACH_MANAGE_MODAL_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_coach_manage_modal.html"
COACH_REMOVE_ATHLETE_MODAL_TEMPLATE_PATH = BACKEND_DIR / "templates" / "dashboard" / "_coach_remove_athlete_modal.html"


class DashboardFrontendRegressionTests(SimpleTestCase):
    def _combined_js(self) -> str:
        parts = [
            JS_CORE_PATH.read_text(encoding="utf-8"),
            JS_METRICS_PATH.read_text(encoding="utf-8"),
            JS_API_PATH.read_text(encoding="utf-8"),
            JS_INLINE_SHARED_PATH.read_text(encoding="utf-8"),
            JS_MONTH_PATH.read_text(encoding="utf-8"),
            JS_PLANNED_PATH.read_text(encoding="utf-8"),
            JS_COMPLETED_PATH.read_text(encoding="utf-8"),
            JS_COACH_PATH.read_text(encoding="utf-8"),
            JS_BOOTSTRAP_PATH.read_text(encoding="utf-8"),
            JS_FIT_IMPORT_PATH.read_text(encoding="utf-8"),
            JS_GARMIN_PATH.read_text(encoding="utf-8"),
            JS_LEGEND_SHORTCUTS_PATH.read_text(encoding="utf-8"),
            JS_PATH.read_text(encoding="utf-8"),
        ]
        return "\n".join(parts)

    def _combined_css(self) -> str:
        parts = [
            CSS_MONTH_PATH.read_text(encoding="utf-8"),
            CSS_IMPORT_PATH.read_text(encoding="utf-8"),
            CSS_COACH_PATH.read_text(encoding="utf-8"),
            CSS_LEGEND_PATH.read_text(encoding="utf-8"),
            CSS_EDITOR_PATH.read_text(encoding="utf-8"),
            CSS_RESPONSIVE_PATH.read_text(encoding="utf-8"),
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
        css = self._combined_css()

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
        self.assertIn(f"css/dashboard_month.css' %}}{expected_suffix}", assets_html)
        self.assertIn(f"css/dashboard_editor.css' %}}{expected_suffix}", assets_html)
        self.assertIn(f"js/dashboard.js' %}}{expected_suffix}", assets_html)

    def test_dashboard_and_coach_templates_include_module_chain(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_html = COACH_TEMPLATE_PATH.read_text(encoding="utf-8")
        assets_html = ASSETS_TEMPLATE_PATH.read_text(encoding="utf-8")

        required_assets = [
            "css/dashboard_month.css",
            "css/dashboard_import.css",
            "css/dashboard_coach.css",
            "css/dashboard_legend.css",
            "css/dashboard_editor.css",
            "css/dashboard_responsive.css",
            "js/dashboard_core.js",
            "js/dashboard_metrics.js",
            "js/dashboard_api.js",
            "js/dashboard_inline_shared.js",
            "js/dashboard_month.js",
            "js/dashboard_editor_planned.js",
            "js/dashboard_editor_completed.js",
            "js/dashboard_coach.js",
            "js/dashboard_bootstrap.js",
            "js/dashboard_fit_import.js",
            "js/dashboard_garmin.js",
            "js/dashboard_legend_shortcuts.js",
            "js/dashboard.js",
        ]

        for asset in required_assets:
            self.assertIn(asset, assets_html)
            self.assertIn(f"{asset}' %}}?v={{{{ dashboard_asset_version }}}}", assets_html)
        self.assertIn('{% include "dashboard/_assets.html" %}', dashboard_html)
        self.assertIn('{% include "dashboard/_assets.html" %}', coach_html)

    def test_dashboard_bootstrap_uses_fail_fast_dependency_guards(self):
        js = JS_BOOTSTRAP_PATH.read_text(encoding="utf-8")
        self.assertIn("requiredFn(", js)
        self.assertIn("EB module dependency is missing", js)

    def test_month_cards_template_contains_planned_footer_row_for_alignment(self):
        month_cards_html = MONTH_CARDS_TEMPLATE_PATH.read_text(encoding="utf-8")
        planned_week_html = PLANNED_WEEK_TEMPLATE_PATH.read_text(encoding="utf-8")
        completed_week_html = COMPLETED_WEEK_TEMPLATE_PATH.read_text(encoding="utf-8")
        switcher_html = MONTH_SWITCHER_TEMPLATE_PATH.read_text(encoding="utf-8")
        km_rules_html = KM_RULES_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('{% include "dashboard/_planned_week_table.html" %}', month_cards_html)
        self.assertIn('{% include "dashboard/_completed_week_table.html" %}', month_cards_html)
        self.assertIn('{% include "dashboard/_month_switcher.html" %}', month_cards_html)
        self.assertIn('{% include "dashboard/_planned_km_rules_modal.html" %}', month_cards_html)
        self.assertIn('tfoot class="table-light eb-planned-week-footer"', planned_week_html)
        self.assertIn("eb-planned-week-total-km", planned_week_html)
        self.assertIn('data-bs-target="#ebPlannedKmRulesModal"', planned_week_html)
        self.assertIn('id="ebPlannedKmRulesModal"', km_rules_html)
        self.assertNotIn("eb-plan-rules-onboarding", month_cards_html)
        self.assertNotIn("eb-plan-rules-dismiss", month_cards_html)
        self.assertIn('data-completed-inline-editable="1"', month_cards_html)
        self.assertIn('data-add-phase-url="{{ add_phase_url }}"', month_cards_html)
        self.assertIn('data-remove-phase-url="{{ remove_phase_url }}"', month_cards_html)
        self.assertIn("eb-completed-inline-edit", completed_week_html)
        self.assertIn("eb-add-month-btn", switcher_html)

    def test_month_cards_templates_use_css_classes_instead_of_inline_width_styles(self):
        month_cards_html = MONTH_CARDS_TEMPLATE_PATH.read_text(encoding="utf-8")
        planned_week_html = PLANNED_WEEK_TEMPLATE_PATH.read_text(encoding="utf-8")
        completed_week_html = COMPLETED_WEEK_TEMPLATE_PATH.read_text(encoding="utf-8")
        legend_html = LEGEND_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertNotIn('style="width:', month_cards_html)
        self.assertNotIn('style="width:', planned_week_html)
        self.assertNotIn('style="width:', completed_week_html)
        self.assertNotIn('style="width:', legend_html)
        self.assertIn("eb-plan-rules-help-btn", planned_week_html)
        self.assertIn("eb-garmin-week-sync-btn", completed_week_html)
        self.assertIn("eb-legend-zone-col", legend_html)

    def test_garmin_week_sync_hook_is_present_in_template_and_js(self):
        month_cards_html = MONTH_CARDS_TEMPLATE_PATH.read_text(encoding="utf-8")
        completed_week_html = COMPLETED_WEEK_TEMPLATE_PATH.read_text(encoding="utf-8")
        js = self._combined_js()

        self.assertIn('data-garmin-week-sync-url="{{ garmin_week_sync_url }}"', month_cards_html)
        self.assertIn("eb-garmin-week-sync-btn", completed_week_html)
        self.assertIn("data-week-start", completed_week_html)
        self.assertIn('closest(".eb-garmin-week-sync-btn")', js)
        self.assertIn('formData.append("week_start", weekStart)', js)
        self.assertIn("notifications.updateNotification({", js)
        self.assertIn('imported ${job.imported_count || 0}, duplicates ${job.skipped_count || 0}.', js)
        self.assertIn("Garmin sync is running.", js)

    def test_dashboard_and_coach_templates_share_legend_partial(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_html = COACH_TEMPLATE_PATH.read_text(encoding="utf-8")
        legend_html = LEGEND_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('{% include "dashboard/_legend_modals.html"', dashboard_html)
        self.assertIn('{% include "dashboard/_legend_modals.html"', coach_html)
        self.assertIn('id="coachLegendModal"', legend_html)
        self.assertIn('id="coachLegendZonesModal"', legend_html)
        self.assertIn('id="coachLegendThresholdModal"', legend_html)
        self.assertIn('id="coachLegendPrModal"', legend_html)

    def test_base_template_keeps_top_nav_sticky(self):
        base_html = BASE_TEMPLATE_PATH.read_text(encoding="utf-8")
        base_css = BASE_CSS_PATH.read_text(encoding="utf-8")
        top_nav_html = TOP_NAV_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("css/base.css", base_html)
        self.assertIn(".eb-top-nav {", base_css)
        self.assertIn("position: sticky;", base_css)
        self.assertIn("top: 0;", base_css)
        self.assertIn('class="navbar navbar-expand-lg navbar-light bg-white border-bottom eb-top-nav"', top_nav_html)

    def test_base_template_uses_shared_partials_and_static_ui_assets(self):
        base_html = BASE_TEMPLATE_PATH.read_text(encoding="utf-8")
        top_nav_html = TOP_NAV_TEMPLATE_PATH.read_text(encoding="utf-8")
        notifications_html = NOTIFICATIONS_TEMPLATE_PATH.read_text(encoding="utf-8")
        profile_modal_html = PROFILE_MODAL_TEMPLATE_PATH.read_text(encoding="utf-8")
        base_js = BASE_JS_PATH.read_text(encoding="utf-8")

        self.assertIn('{% include "includes/_top_nav.html" %}', base_html)
        self.assertIn('{% include "includes/_profile_modal.html" %}', base_html)
        self.assertIn("js/base_ui.js", base_html)
        self.assertIn('{% include "includes/_notifications_dropdown.html" %}', top_nav_html)
        self.assertIn('id="notificationDropdownRoot"', notifications_html)
        self.assertIn('id="profileModal"', profile_modal_html)
        self.assertIn("window.EB.ui.setButtonBusy", base_js)
        self.assertIn("window.EB.notifications", base_js)

    def test_dashboard_toolbar_is_sticky_below_top_nav(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        css = self._combined_css()

        dashboard_header_html = DASHBOARD_HEADER_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn('{% include "dashboard/_dashboard_header.html" %}', dashboard_html)
        self.assertIn("eb-dashboard-toolbar", dashboard_header_html)
        self.assertIn(".eb-dashboard-toolbar {", css)
        self.assertIn("position: sticky;", css)
        self.assertIn("top: 57px;", css)

    def test_dashboard_css_legacy_entrypoint_reexports_split_files(self):
        css = CSS_PATH.read_text(encoding="utf-8")

        self.assertIn('@import url("./dashboard_month.css");', css)
        self.assertIn('@import url("./dashboard_import.css");', css)
        self.assertIn('@import url("./dashboard_coach.css");', css)
        self.assertIn('@import url("./dashboard_legend.css");', css)
        self.assertIn('@import url("./dashboard_editor.css");', css)
        self.assertIn('@import url("./dashboard_responsive.css");', css)

    def test_dashboard_template_uses_split_header_and_import_modal_partials(self):
        dashboard_html = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
        dashboard_header_html = DASHBOARD_HEADER_TEMPLATE_PATH.read_text(encoding="utf-8")
        import_modal_html = IMPORT_MODAL_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('{% include "dashboard/_dashboard_header.html" %}', dashboard_html)
        self.assertIn('{% include "dashboard/_import_modal.html" %}', dashboard_html)
        self.assertIn('data-bs-target="#importActivitiesModal"', dashboard_header_html)
        self.assertIn('id="importActivitiesModal"', import_modal_html)
        self.assertIn('id="fitImportLink"', import_modal_html)
        self.assertIn('id="garminSyncForm"', import_modal_html)

    def test_import_modal_supports_garmin_feature_flags(self):
        import_modal_html = IMPORT_MODAL_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("{% elif garmin_connect_enabled %}", import_modal_html)
        self.assertIn("{% if garmin_sync_enabled %}", import_modal_html)
        self.assertIn("Garmin propojení je teď v produkci dočasně vypnuté.", import_modal_html)
        self.assertIn("Garmin synchronizace je teď v produkci dočasně vypnutá.", import_modal_html)

    def test_coach_template_uses_split_sidebar_toolbar_and_modals(self):
        coach_html = COACH_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_sidebar_html = COACH_SIDEBAR_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_toolbar_html = COACH_MAIN_TOOLBAR_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_manage_modal_html = COACH_MANAGE_MODAL_TEMPLATE_PATH.read_text(encoding="utf-8")
        coach_remove_modal_html = COACH_REMOVE_ATHLETE_MODAL_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('{% include "dashboard/_coach_sidebar.html" %}', coach_html)
        self.assertIn('{% include "dashboard/_coach_main_toolbar.html" %}', coach_html)
        self.assertIn('{% include "dashboard/_coach_manage_modal.html" %}', coach_html)
        self.assertIn('{% include "dashboard/_coach_remove_athlete_modal.html" %}', coach_html)
        self.assertIn('id="coachAthleteList"', coach_sidebar_html)
        self.assertIn('id="coachAthletesToggleBtnSidebar"', coach_sidebar_html)
        self.assertIn('id="coachAthletesToggleBtnMain"', coach_toolbar_html)
        self.assertIn('id="coachManageModal"', coach_manage_modal_html)
        self.assertIn('data-athlete-visibility-form="1"', coach_manage_modal_html)
        self.assertIn('data-remove-athlete-id="{{ athlete.id }}"', coach_manage_modal_html)
        self.assertIn('id="coachRemoveAthleteModal"', coach_remove_modal_html)
        self.assertIn('id="coachRemoveAthleteIdInput"', coach_remove_modal_html)
        self.assertIn('id="coachRemoveAthleteConfirmInput"', coach_remove_modal_html)
        self.assertIn('id="coachRemoveAthleteSubmitBtn"', coach_remove_modal_html)
