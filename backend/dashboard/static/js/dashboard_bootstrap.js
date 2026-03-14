(function () {
  function requiredFn(name) {
    return () => {
      throw new Error(`EB module dependency is missing: ${name}`);
    };
  }

  const core = (window.EB && window.EB.core) || {};
  const api = (window.EB && window.EB.api) || {};
  const inlineShared = (window.EB && window.EB.inlineShared) || {};
  const monthModule = (window.EB && window.EB.month) || {};
  const plannedModule = (window.EB && window.EB.editorPlanned) || {};
  const completedModule = (window.EB && window.EB.editorCompleted) || {};
  const coachModule = (window.EB && window.EB.coach) || {};

  const getCsrfToken = core.getCsrfToken || requiredFn("core.getCsrfToken");
  const getWidgetState = core.getWidgetState || requiredFn("core.getWidgetState");
  const getHtml = api.getHtml || requiredFn("api.getHtml");
  const postJson = api.postJson || requiredFn("api.postJson");
  const postForm = api.postForm || requiredFn("api.postForm");
  const placeCaretToEnd = inlineShared.placeCaretToEnd || requiredFn("inlineShared.placeCaretToEnd");
  const setClipboardText = inlineShared.setClipboardText || requiredFn("inlineShared.setClipboardText");
  const parsePasteMatrix = inlineShared.parsePasteMatrix || requiredFn("inlineShared.parsePasteMatrix");
  const createHistoryManager = inlineShared.createHistoryManager || requiredFn("inlineShared.createHistoryManager");

  const createMonthController = monthModule.createMonthController || null;
  const createPlannedEditor = plannedModule.createPlannedEditor || null;
  const createCompletedEditor = completedModule.createCompletedEditor || null;
  const createCoachController = coachModule.createCoachController || null;

  const monthController = createMonthController
    ? createMonthController({
        getWidgetState,
        postForm,
      })
    : null;

  const plannedEditor = createPlannedEditor
    ? createPlannedEditor({
        getCsrfToken,
        postJson,
        placeCaretToEnd,
        setClipboardText,
        parsePasteMatrix,
        createHistoryManager,
      })
    : null;

  const completedEditor = createCompletedEditor
    ? createCompletedEditor({
        getCsrfToken,
        postJson,
        placeCaretToEnd,
        setClipboardText,
        parsePasteMatrix,
        createHistoryManager,
      })
    : null;

  function initSingleMonthWidget(widget) {
    if (!monthController) return;
    monthController.initMonthWidget(widget);
    monthController.initMonthSwitcherScroll(widget);
    if (plannedEditor && widget.getAttribute("data-inline-editable") === "1") {
      plannedEditor.initCoachInlineEditing(widget, monthController.scheduleEqualize);
    }
    if (completedEditor && widget.getAttribute("data-completed-inline-editable") === "1") {
      completedEditor.initCompletedInlineEditing(widget, monthController.scheduleEqualize);
    }
  }

  function initCoachMainContent(root) {
    const scope = root || document;
    const widgets = Array.from(scope.querySelectorAll(".eb-month-widget"));
    widgets.forEach((widget) => {
      initSingleMonthWidget(widget);
      if (monthController) {
        monthController.enhanceAddMonthForms(widget, initSingleMonthWidget);
      }
    });
  }

  let coachController = null;
  function getCoachController() {
    if (!createCoachController) return null;
    if (!coachController) {
      coachController = createCoachController({
        getCsrfToken,
        postJson,
        postForm,
        getHtml,
        initCoachMainContent,
      });
    }
    return coachController;
  }

  async function refreshDashboardMonthCards() {
    const root = document.getElementById("dashboardMonthCardsRoot");
    if (!root) return;
    const html = await getHtml(window.location.pathname + window.location.search);
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const nextRoot = doc.getElementById("dashboardMonthCardsRoot");
    if (!nextRoot) return;
    root.innerHTML = nextRoot.innerHTML;
    initCoachMainContent(root);
    if (window.EB && window.EB.dashboardApp && typeof window.EB.dashboardApp.initGarminWeekSync === "function") {
      window.EB.dashboardApp.initGarminWeekSync();
    }
  }

  window.EB = window.EB || {};
  window.EB.dashboardApp = Object.assign(window.EB.dashboardApp || {}, {
    getCsrfToken,
    getCoachController,
    initCoachMainContent,
    refreshDashboardMonthCards,
  });
})();
