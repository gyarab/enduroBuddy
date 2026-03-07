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

  function initFitImportQuickAction() {
    const importLink = document.getElementById("fitImportLink");
    const fileInput = document.getElementById("fitFileInput");
    const form = document.getElementById("fitImportForm");
    const importSourceInput = document.getElementById("importSourceInput");
    if (!importLink || !fileInput || !form || !importSourceInput) return;

    importLink.addEventListener("click", (event) => {
      event.preventDefault();
      importSourceInput.value = "fit_upload";
      fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        importSourceInput.value = "fit_upload";
        form.submit();
      }
    });
  }

  function init() {
    const controller = getCoachController();
    if (controller && typeof controller.initCoachShellContent === "function") {
      controller.initCoachShellContent();
    } else {
      initCoachMainContent(document);
    }
    if (controller && typeof controller.initCoachAthleteKeyboardSwitch === "function") {
      controller.initCoachAthleteKeyboardSwitch();
    }
    initFitImportQuickAction();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
