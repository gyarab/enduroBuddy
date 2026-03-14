(function () {
  window.EB = window.EB || {};
  window.EB.ui = window.EB.ui || {};

  window.EB.ui.setButtonBusy = function setButtonBusy(button, isBusy, options) {
    if (!(button instanceof HTMLElement)) return;

    const opts = options || {};
    const busyLabel = Object.prototype.hasOwnProperty.call(opts, "label")
      ? String(opts.label || "")
      : String(
          button.getAttribute("data-loading-label")
          || button.getAttribute("aria-label")
          || button.getAttribute("title")
          || "Probíhá..."
        );

    if (isBusy) {
      if (button.dataset.ebBusy === "1") return;
      button.dataset.ebBusy = "1";
      button.dataset.ebBusyDisabled = button.disabled ? "1" : "0";
      button.dataset.ebBusyHtml = button.innerHTML;
      button.dataset.ebBusyMinWidth = button.style.minWidth || "";
      button.style.minWidth = `${Math.ceil(button.getBoundingClientRect().width)}px`;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.classList.add("eb-btn-busy");

      const spinnerMarkup = '<span class="spinner-border spinner-border-sm eb-btn-busy-spinner" role="status" aria-hidden="true"></span>';
      button.innerHTML = busyLabel
        ? `${spinnerMarkup}<span>${busyLabel}</span>`
        : spinnerMarkup;
      return;
    }

    if (button.dataset.ebBusy !== "1") return;
    button.innerHTML = button.dataset.ebBusyHtml || button.innerHTML;
    button.style.minWidth = button.dataset.ebBusyMinWidth || "";
    button.disabled = button.dataset.ebBusyDisabled === "1";
    button.removeAttribute("aria-busy");
    button.classList.remove("eb-btn-busy");
    delete button.dataset.ebBusy;
    delete button.dataset.ebBusyDisabled;
    delete button.dataset.ebBusyHtml;
    delete button.dataset.ebBusyMinWidth;
  };

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.dataset.ebSkipSubmitLoading === "1") return;

    if (form.dataset.ebSubmitting === "1") {
      event.preventDefault();
      return;
    }

    const submitter = event.submitter instanceof HTMLElement
      ? event.submitter
      : form.querySelector("button[type='submit'], input[type='submit']");

    if (!(submitter instanceof HTMLElement) || submitter.getAttribute("data-eb-no-loading") === "1") {
      form.dataset.ebSubmitting = "1";
      return;
    }

    form.dataset.ebSubmitting = "1";
    window.EB.ui.setButtonBusy(submitter, true);
  });

  if (window.location.hash === "#profileModal") {
    const profileModalEl = document.getElementById("profileModal");
    if (profileModalEl && window.bootstrap && window.bootstrap.Modal) {
      window.bootstrap.Modal.getOrCreateInstance(profileModalEl).show();
      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(null, "", window.location.pathname + window.location.search);
      }
    }
  }

  (function () {
    const bellBtn = document.getElementById("notificationBellButton");
    const dropdownRoot = document.getElementById("notificationDropdownRoot");
    if (!bellBtn || !dropdownRoot) return;

    const unreadItems = Array.from(dropdownRoot.querySelectorAll("[data-notification-item].is-unread"));
    const badge = bellBtn.querySelector(".eb-notification-badge");
    const toastTimers = new Map();
    const activeToasts = new Map();
    let markReadTimerId = null;

    const ensureBadge = () => {
      if (badge) return badge;
      const created = document.createElement("span");
      created.className = "eb-notification-badge";
      bellBtn.appendChild(created);
      return created;
    };

    const syncUnreadCount = () => {
      const count = dropdownRoot.querySelectorAll("[data-notification-item].is-unread").length;
      const targetBadge = ensureBadge();
      targetBadge.textContent = String(count);
      targetBadge.style.display = count > 0 ? "inline-block" : "none";
    };

    const ensureNotificationList = () => {
      let list = dropdownRoot.querySelector(".eb-notification-list");
      if (list) return list;
      const menu = dropdownRoot.querySelector(".eb-notification-dropdown");
      if (!menu) return null;
      list = document.createElement("div");
      list.className = "eb-notification-list";
      menu.appendChild(list);
      return list;
    };

    const upsertNotificationDetails = (item, { statusLabel = "", progressPercent = null } = {}) => {
      let meta = item.querySelector(".eb-notification-meta");
      if (!meta) {
        meta = document.createElement("div");
        meta.className = "eb-notification-meta";
        item.appendChild(meta);
      }
      const normalizedStatus = (statusLabel || "").trim();
      meta.textContent = normalizedStatus;
      meta.style.display = normalizedStatus ? "block" : "none";

      let progress = item.querySelector(".eb-notification-progress");
      if (!progress) {
        progress = document.createElement("div");
        progress.className = "eb-notification-progress";
        progress.innerHTML = '<div class="eb-notification-progress-bar"></div>';
        item.appendChild(progress);
      }
      const bar = progress.querySelector(".eb-notification-progress-bar");
      const hasProgress = Number.isFinite(Number(progressPercent));
      if (hasProgress) {
        const pct = Math.max(0, Math.min(100, Number(progressPercent)));
        progress.style.display = "block";
        if (bar) bar.style.width = `${pct}%`;
      } else {
        progress.style.display = "none";
        if (bar) bar.style.width = "0%";
      }
    };

    const buildNotificationItem = ({
      text,
      tone = "success",
      unread = true,
      spinner = false,
      statusLabel = "",
      progressPercent = null,
    }) => {
      const item = document.createElement("div");
      item.className = `eb-notification-item eb-notification-item--${tone}`;
      item.setAttribute("data-notification-item", "1");
      if (unread) item.classList.add("is-unread");

      if (spinner) {
        const spinnerEl = document.createElement("span");
        spinnerEl.className = "spinner-border spinner-border-sm text-primary eb-notification-spinner";
        spinnerEl.setAttribute("aria-hidden", "true");
        item.appendChild(spinnerEl);
      } else {
        const dot = document.createElement("span");
        dot.className = "eb-notification-dot";
        dot.setAttribute("aria-hidden", "true");
        item.appendChild(dot);
      }

      const content = document.createElement("div");
      content.className = "eb-notification-content";

      const textEl = document.createElement("span");
      textEl.className = "eb-notification-text";
      textEl.textContent = text || "";
      content.appendChild(textEl);
      item.appendChild(content);
      upsertNotificationDetails(content, { statusLabel, progressPercent });
      return item;
    };

    const ensureToastStack = () => {
      const existing = document.getElementById("notificationBellToastStack");
      if (existing) return existing;
      const stack = document.createElement("div");
      stack.id = "notificationBellToastStack";
      stack.className = "eb-bell-toast-stack";
      document.body.appendChild(stack);
      return stack;
    };

    const positionToastStack = () => {
      const stack = document.getElementById("notificationBellToastStack");
      if (!stack) return;
      const rect = bellBtn.getBoundingClientRect();
      const stackWidth = Math.min(320, window.innerWidth - 24);
      const bellCenterX = rect.left + (rect.width / 2);
      let left = bellCenterX - stackWidth + 18;
      left = Math.max(12, Math.min(window.innerWidth - stackWidth - 12, left));
      const pointerRight = Math.max(12, Math.min(stackWidth - 12, stackWidth - (bellCenterX - left)));
      stack.style.setProperty("--eb-stack-pointer-right", `${pointerRight}px`);
      stack.style.width = `${stackWidth}px`;
      stack.style.top = `${rect.bottom + 10}px`;
      stack.style.left = `${left}px`;
    };

    const clearBellToastsImmediately = () => {
      const stack = document.getElementById("notificationBellToastStack");
      if (!stack) return;
      toastTimers.forEach((timerId) => window.clearTimeout(timerId));
      toastTimers.clear();
      activeToasts.clear();
      stack.remove();
    };

    const hideToastElement = (toast) => {
      if (!toast) return;
      const timerId = toastTimers.get(toast);
      if (timerId) {
        window.clearTimeout(timerId);
        toastTimers.delete(toast);
      }
      toast.classList.remove("show");
      toast.classList.add("hide");
      window.setTimeout(() => {
        if (toast.dataset.toastId && activeToasts.get(toast.dataset.toastId) === toast) {
          activeToasts.delete(toast.dataset.toastId);
        }
        toast.remove();
        const stack = document.getElementById("notificationBellToastStack");
        if (stack && !stack.children.length) stack.remove();
      }, 280);
    };

    const showToastWithText = (text, { tone = "success", persistent = false, toastId = "" } = {}) => {
      if (!text) return null;
      const stack = ensureToastStack();
      positionToastStack();

      const existing = toastId ? activeToasts.get(toastId) : null;
      if (existing) {
        const textEl = existing.querySelector(".eb-notification-text");
        if (textEl) textEl.textContent = text;
        const hasSpinner = Boolean(existing.querySelector(".eb-notification-spinner"));
        if (persistent && !hasSpinner) {
          const dot = existing.querySelector(".eb-notification-dot");
          if (dot) dot.remove();
          const spinnerEl = document.createElement("span");
          spinnerEl.className = "spinner-border spinner-border-sm text-primary eb-notification-spinner";
          spinnerEl.setAttribute("aria-hidden", "true");
          existing.insertBefore(spinnerEl, existing.firstChild);
        }
        if (!persistent && hasSpinner) {
          const spinnerEl = existing.querySelector(".eb-notification-spinner");
          if (spinnerEl) spinnerEl.remove();
          const dot = document.createElement("span");
          dot.className = "eb-notification-dot";
          dot.setAttribute("aria-hidden", "true");
          existing.insertBefore(dot, existing.firstChild);
        }
        if (!persistent) {
          const hideTimerId = window.setTimeout(() => hideToastElement(existing), 5000);
          toastTimers.set(existing, hideTimerId);
        }
        return existing;
      }

      const toast = document.createElement("div");
      toast.className = "eb-bell-toast";
      const iconHtml = persistent
        ? '<span class="spinner-border spinner-border-sm text-primary eb-notification-spinner" aria-hidden="true"></span>'
        : '<span class="eb-notification-dot" aria-hidden="true"></span>';
      toast.innerHTML = `${iconHtml}<span class="eb-notification-text"></span>`;
      toast.querySelector(".eb-notification-text").textContent = text;
      if (toastId) {
        toast.dataset.toastId = toastId;
        activeToasts.set(toastId, toast);
      }
      stack.appendChild(toast);
      window.requestAnimationFrame(() => toast.classList.add("show"));

      if (!persistent) {
        const hideTimerId = window.setTimeout(() => hideToastElement(toast), 5000);
        toastTimers.set(toast, hideTimerId);
      }
      return toast;
    };

    const showBellToast = (item, delayMs) => {
      window.setTimeout(() => {
        const textEl = item.querySelector(".eb-notification-text");
        const text = textEl ? textEl.textContent.trim() : item.textContent.trim();
        showToastWithText(text, { tone: "success", persistent: false });
      }, delayMs);
    };

    const addNotification = ({
      id,
      text,
      tone = "success",
      unread = true,
      persistent = false,
      statusLabel = "",
      progressPercent = null,
    }) => {
      const list = ensureNotificationList();
      if (!list) return { item: null, toast: null };

      const itemId = id || `n-${Date.now()}`;
      const existingItem = list.querySelector(`[data-eb-notification-id="${itemId}"]`);
      if (existingItem) {
        const textEl = existingItem.querySelector(".eb-notification-text");
        if (textEl) textEl.textContent = text;
        const content = existingItem.querySelector(".eb-notification-content");
        if (content) upsertNotificationDetails(content, { statusLabel, progressPercent });
        return { item: existingItem, toast: activeToasts.get(itemId) || null };
      }

      const item = buildNotificationItem({
        text,
        tone,
        unread,
        spinner: persistent,
        statusLabel,
        progressPercent,
      });
      item.dataset.ebNotificationId = itemId;
      list.prepend(item);
      syncUnreadCount();

      const toast = showToastWithText(text, { tone, persistent, toastId: itemId });
      return { item, toast };
    };

    const updateNotification = ({
      id,
      text,
      tone = "success",
      persistent = false,
      statusLabel = "",
      progressPercent = null,
    }) => {
      if (!id) return;
      const list = ensureNotificationList();
      const item = list ? list.querySelector(`[data-eb-notification-id="${id}"]`) : null;
      if (item) {
        item.classList.remove("eb-notification-item--success", "eb-notification-item--danger", "eb-notification-item--warning", "eb-notification-item--secondary");
        item.classList.add(`eb-notification-item--${tone}`);
        const textEl = item.querySelector(".eb-notification-text");
        if (textEl) textEl.textContent = text;
        const content = item.querySelector(".eb-notification-content");
        if (content) upsertNotificationDetails(content, { statusLabel, progressPercent });

        const currentSpinner = item.querySelector(".eb-notification-spinner");
        const currentDot = item.querySelector(".eb-notification-dot");
        if (persistent && !currentSpinner) {
          if (currentDot) currentDot.remove();
          const spinnerEl = document.createElement("span");
          spinnerEl.className = "spinner-border spinner-border-sm text-primary eb-notification-spinner";
          spinnerEl.setAttribute("aria-hidden", "true");
          item.insertBefore(spinnerEl, item.firstChild);
        }
        if (!persistent && !currentDot) {
          if (currentSpinner) currentSpinner.remove();
          const dot = document.createElement("span");
          dot.className = "eb-notification-dot";
          dot.setAttribute("aria-hidden", "true");
          item.insertBefore(dot, item.firstChild);
        }
      }
      showToastWithText(text, { tone, persistent, toastId: id });
      if (!persistent) {
        const toast = activeToasts.get(id);
        if (toast) {
          window.setTimeout(() => {
            if (toast && toast.isConnected) hideToastElement(toast);
          }, 1200);
        }
      }
    };

    unreadItems.forEach((item, index) => {
      showBellToast(item, index * 260);
    });

    dropdownRoot.addEventListener("shown.bs.dropdown", () => {
      clearBellToastsImmediately();
      if (markReadTimerId) window.clearTimeout(markReadTimerId);
      markReadTimerId = window.setTimeout(() => {
        dropdownRoot.querySelectorAll("[data-notification-item].is-unread").forEach((item) => {
          item.classList.remove("is-unread");
        });
        syncUnreadCount();
        markReadTimerId = null;
      }, 400);
    });

    dropdownRoot.addEventListener("hidden.bs.dropdown", () => {
      if (markReadTimerId) {
        window.clearTimeout(markReadTimerId);
        markReadTimerId = null;
      }
    });

    window.addEventListener("resize", positionToastStack);
    window.addEventListener("scroll", positionToastStack, { passive: true });

    syncUnreadCount();

    window.EB = window.EB || {};
    window.EB.notifications = {
      addNotification,
      updateNotification,
    };
  })();
})();
