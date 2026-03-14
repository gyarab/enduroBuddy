(function () {
  function init() {
    const dashboardApp = (window.EB && window.EB.dashboardApp) || {};
    const getCoachController = dashboardApp.getCoachController || (() => null);
    const initCoachMainContent = dashboardApp.initCoachMainContent || (() => {});
    const initLegendKeyboardShortcut = dashboardApp.initLegendKeyboardShortcut || (() => {});
    const initFitImportQuickAction = dashboardApp.initFitImportQuickAction || (() => {});
    const initGarminBackgroundSync = dashboardApp.initGarminBackgroundSync || (() => {});
    const initGarminWeekSync = dashboardApp.initGarminWeekSync || (() => {});

    const controller = getCoachController();
    if (controller && typeof controller.initCoachShellContent === "function") {
      controller.initCoachShellContent();
    } else {
      initCoachMainContent(document);
    }
    if (controller && typeof controller.initCoachAthleteKeyboardSwitch === "function") {
      controller.initCoachAthleteKeyboardSwitch();
    }
    initLegendKeyboardShortcut();
    initFitImportQuickAction();
    initGarminBackgroundSync();
    initGarminWeekSync();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
