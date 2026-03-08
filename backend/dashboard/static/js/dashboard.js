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

  function initGarminBackgroundSync() {
    const form = document.getElementById("garminSyncForm");
    const submitButton = document.getElementById("garminSyncSubmitButton");
    const spinner = document.getElementById("garminSyncSpinner");
    const label = document.getElementById("garminSyncButtonLabel");
    if (!form || !submitButton || !spinner || !label) return;

    const startUrl = form.getAttribute("data-garmin-sync-start-url") || "";
    const statusUrlTemplate = form.getAttribute("data-garmin-job-status-url-template") || "";
    if (!startUrl || !statusUrlTemplate) return;

    const defaultLabel = label.textContent || "Sync Garmin";
    const notifications = (window.EB && window.EB.notifications) || null;
    let pollingTimerId = null;
    let activeNotificationId = "";

    const setLoading = (isLoading) => {
      submitButton.disabled = isLoading;
      spinner.classList.toggle("d-none", !isLoading);
      label.textContent = isLoading ? "Synchronizuji..." : defaultLabel;
    };

    const stopPolling = () => {
      if (!pollingTimerId) return;
      window.clearInterval(pollingTimerId);
      pollingTimerId = null;
    };

    const statusUrlForJob = (jobId) => {
      if (statusUrlTemplate.includes("/0/status/")) {
        return statusUrlTemplate.replace("/0/status/", `/${jobId}/status/`);
      }
      return statusUrlTemplate.replace("0", String(jobId));
    };

    const refreshMonthCards = async () => {
      const root = document.getElementById("dashboardMonthCardsRoot");
      if (!root) return;
      const html = await getHtml(window.location.pathname + window.location.search);
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const nextRoot = doc.getElementById("dashboardMonthCardsRoot");
      if (!nextRoot) return;
      root.innerHTML = nextRoot.innerHTML;
      initCoachMainContent(root);
    };

    const formatSyncText = (job) => {
      const status = (job && (job.status_label || job.status)) || "RUNNING";
      const progress = Number.isFinite(Number(job && job.progress_percent))
        ? Math.max(0, Math.min(100, Number(job.progress_percent)))
        : 0;
      if (job && job.status === "SUCCESS") {
        return `${status} (${progress}%): imported ${job.imported_count || 0}, duplicates ${job.skipped_count || 0}.`;
      }
      if (job && job.status === "ERROR") {
        return `${status} (${progress}%): ${job.message || "Garmin sync failed."}`;
      }
      return `${status} (${progress}%): ${job && job.message ? job.message : "Garmin sync is running."}`;
    };

    const startPolling = (jobId) => {
      stopPolling();
      pollingTimerId = window.setInterval(async () => {
        try {
          const response = await fetch(statusUrlForJob(jobId), {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
          });
          if (!response.ok) return;
          const payload = await response.json();
          if (!payload || !payload.ok || !payload.job) return;
          const job = payload.job;
          const isSuccess = job.status === "SUCCESS";

          if (notifications && activeNotificationId) {
            if (job.status === "RUNNING" || job.status === "QUEUED") {
              notifications.updateNotification({
                id: activeNotificationId,
                text: formatSyncText(job),
                tone: "warning",
                persistent: true,
                statusLabel: job.status_label || job.status,
                progressPercent: job.progress_percent,
              });
            } else if (job.status === "SUCCESS") {
              notifications.updateNotification({
                id: activeNotificationId,
                text: formatSyncText(job),
                tone: "success",
                persistent: false,
                statusLabel: job.status_label || job.status,
                progressPercent: 100,
              });
            } else if (job.status === "ERROR") {
              notifications.updateNotification({
                id: activeNotificationId,
                text: formatSyncText(job),
                tone: "danger",
                persistent: false,
                statusLabel: job.status_label || job.status,
                progressPercent: job.progress_percent,
              });
            }
          }

          if (job.done) {
            stopPolling();
            setLoading(false);
            if (isSuccess) {
              refreshMonthCards().catch(() => {});
            }
          }
        } catch (_error) {
          // Keep polling; transient fetch errors should not terminate the sync UX.
        }
      }, 1800);
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (submitButton.disabled) return;

      const formData = new FormData(form);
      const csrfToken = getCsrfToken();

      setLoading(true);
      try {
        const response = await fetch(startUrl, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfToken || "",
          },
          body: formData,
          credentials: "same-origin",
        });
        const payload = await response.json();
        if (!response.ok || !payload || !payload.ok) {
          throw new Error((payload && payload.error) || "Synchronizaci se nepodařilo spustit.");
        }

        const jobId = payload.job_id;
        activeNotificationId = `garmin-sync-job-${jobId}`;
        if (notifications) {
          notifications.addNotification({
            id: activeNotificationId,
            text: `${payload.status_label || payload.status || "QUEUED"} (${Number(payload.progress_percent || 0)}%): ${payload.message || "Garmin sync queued."}`,
            tone: "warning",
            unread: true,
            persistent: true,
            statusLabel: payload.status_label || payload.status,
            progressPercent: payload.progress_percent,
          });
        }
        startPolling(jobId);
      } catch (error) {
        setLoading(false);
        if (notifications) {
          notifications.addNotification({
            id: `garmin-sync-error-${Date.now()}`,
            text: (error && error.message) || "Synchronizace Garmin selhala.",
            tone: "danger",
            unread: true,
            persistent: false,
          });
        }
      }
    });
  }

  function initLegendKeyboardShortcut() {
    if (document.body.dataset.ebLegendShortcutInit === "1") return;
    document.body.dataset.ebLegendShortcutInit = "1";

    document.addEventListener("keydown", (event) => {
      if (!event.altKey || event.ctrlKey || event.metaKey) return;
      if ((event.key || "").toLowerCase() !== "l") return;

      const legendModal = document.getElementById("coachLegendModal");
      if (!legendModal || !(window.bootstrap && window.bootstrap.Modal)) return;
      event.preventDefault();

      const childModalIds = ["coachLegendZonesModal", "coachLegendThresholdModal", "coachLegendPrModal"];
      childModalIds.forEach((id) => {
        const child = document.getElementById(id);
        if (!child || !child.classList.contains("show")) return;
        const childInstance = window.bootstrap.Modal.getInstance(child);
        if (childInstance) childInstance.hide();
      });

      const instance = window.bootstrap.Modal.getOrCreateInstance(legendModal);
      if (legendModal.classList.contains("show")) {
        instance.hide();
      } else {
        instance.show();
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
    initLegendKeyboardShortcut();
    initFitImportQuickAction();
    initGarminBackgroundSync();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
