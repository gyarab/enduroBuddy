(function () {
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
    const getNotifications = () => (window.EB && window.EB.notifications) || null;
    const dashboardApp = (window.EB && window.EB.dashboardApp) || {};
    const getCsrfToken = dashboardApp.getCsrfToken || (() => "");
    const refreshDashboardMonthCards = dashboardApp.refreshDashboardMonthCards || (async () => {});
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

          const notifications = getNotifications();
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
              refreshDashboardMonthCards().catch(() => {});
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
        const notifications = getNotifications();
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
        const notifications = getNotifications();
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

  function initGarminWeekSync() {
    if (document.body.dataset.ebGarminWeekSyncInit === "1") return;
    document.body.dataset.ebGarminWeekSyncInit = "1";

    const getNotifications = () => (window.EB && window.EB.notifications) || null;
    const dashboardApp = (window.EB && window.EB.dashboardApp) || {};
    const getCsrfToken = dashboardApp.getCsrfToken || (() => "");
    const refreshDashboardMonthCards = dashboardApp.refreshDashboardMonthCards || (async () => {});
    const formatWeekSyncText = (job) => {
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

    document.addEventListener("click", async (event) => {
      const button = event.target && event.target.closest
        ? event.target.closest(".eb-garmin-week-sync-btn")
        : null;
      if (!button) return;

      event.preventDefault();
      if (button.disabled || button.dataset.loading === "1") return;

      const widget = button.closest(".eb-month-widget");
      const startUrl = widget ? widget.getAttribute("data-garmin-week-sync-url") || "" : "";
      const weekStart = button.getAttribute("data-week-start") || "";
      if (!startUrl || !weekStart) return;

      const spinner = button.querySelector(".eb-garmin-week-sync-spinner");
      const icon = button.querySelector(".eb-garmin-week-sync-icon");
      const wasDisabled = button.disabled;
      const activeNotificationId = `garmin-week-sync-${weekStart}-${Date.now()}`;
      button.dataset.loading = "1";
      button.disabled = true;
      if (spinner) spinner.classList.remove("d-none");
      if (icon) icon.classList.add("d-none");

      const formData = new FormData();
      formData.append("week_start", weekStart);

      const notifications = getNotifications();
      if (notifications) {
        notifications.addNotification({
          id: activeNotificationId,
          text: formatWeekSyncText({
            status: "RUNNING",
            status_label: "Running",
            progress_percent: 10,
            message: "Garmin sync is running.",
          }),
          tone: "warning",
          unread: true,
          persistent: true,
          statusLabel: "Running",
          progressPercent: 10,
        });
      }

      try {
        const response = await fetch(startUrl, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCsrfToken() || "",
          },
          body: formData,
          credentials: "same-origin",
        });
        const payload = await response.json();
        if (!response.ok || !payload || !payload.ok) {
          throw new Error((payload && payload.error) || "Tydenni Garmin import selhal.");
        }

        const notifications = getNotifications();
        if (notifications) {
          notifications.updateNotification({
            id: activeNotificationId,
            text: formatWeekSyncText(payload),
            tone: "success",
            unread: true,
            persistent: false,
            statusLabel: payload.status_label || payload.status || "Done",
            progressPercent: Number(payload.progress_percent || 100),
          });
        }
        await refreshDashboardMonthCards();
      } catch (error) {
        const notifications = getNotifications();
        if (notifications) {
          notifications.updateNotification({
            id: activeNotificationId,
            text: formatWeekSyncText({
              status: "ERROR",
              status_label: "Error",
              progress_percent: 0,
              message: (error && error.message) || "Garmin sync failed.",
            }),
            tone: "danger",
            unread: true,
            persistent: false,
            statusLabel: "Error",
            progressPercent: 0,
          });
        }
      } finally {
        delete button.dataset.loading;
        if (spinner) spinner.classList.add("d-none");
        if (icon) icon.classList.remove("d-none");
        button.disabled = wasDisabled;
      }
    });
  }

  window.EB = window.EB || {};
  window.EB.dashboardApp = Object.assign(window.EB.dashboardApp || {}, {
    initGarminBackgroundSync,
    initGarminWeekSync,
  });
})();
