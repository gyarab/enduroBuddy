(function () {
  function showMonth(widget, monthId) {
    widget.querySelectorAll(".month-container").forEach((el) => {
      el.classList.remove("is-active");
    });

    const target = widget.querySelector(`.month-container[data-month-id="${monthId}"]`);
    if (target) target.classList.add("is-active");

    widget.querySelectorAll(".month-btn").forEach((btn) => {
      const isActive = btn.getAttribute("data-month-id") === String(monthId);
      btn.classList.toggle("is-active", isActive);
      btn.classList.toggle("btn-outline-dark", !isActive);
      btn.classList.toggle("btn-dark", isActive);
    });
  }

  function initMonthWidget(widget) {
    const buttons = Array.from(widget.querySelectorAll(".month-btn"));
    const months = Array.from(widget.querySelectorAll(".month-container"));
    if (!months.length) return;

    const stateKeyRaw = widget.getAttribute("data-month-state-key");
    const storageKey = stateKeyRaw ? `eb_month_${stateKeyRaw}` : null;
    const savedMonthId = storageKey ? window.localStorage.getItem(storageKey) : null;

    const firstId = buttons.length
      ? buttons[0].getAttribute("data-month-id")
      : months[0].getAttribute("data-month-id");

    const useSaved = savedMonthId && months.some((m) => m.getAttribute("data-month-id") === savedMonthId);
    const activeMonthId = useSaved ? savedMonthId : firstId;

    showMonth(widget, activeMonthId);

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const monthId = btn.getAttribute("data-month-id");
        showMonth(widget, monthId);
        if (storageKey) {
          window.localStorage.setItem(storageKey, monthId);
        }
      });
    });
  }

  function init() {
    const widgets = Array.from(document.querySelectorAll(".eb-month-widget"));
    widgets.forEach((widget) => initMonthWidget(widget));

    const importLink = document.getElementById("fitImportLink");
    const fileInput = document.getElementById("fitFileInput");
    const form = document.getElementById("fitImportForm");
    const importSourceInput = document.getElementById("importSourceInput");

    if (importLink && fileInput && form && importSourceInput) {
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
