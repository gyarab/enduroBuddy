(function () {
  function showMonth(monthId) {
    document.querySelectorAll(".month-container").forEach((el) => {
      el.classList.remove("is-active");
    });

    const target = document.querySelector(`.month-container[data-month-id="${monthId}"]`);
    if (target) target.classList.add("is-active");

    document.querySelectorAll(".month-btn").forEach((btn) => {
      const isActive = btn.getAttribute("data-month-id") === String(monthId);
      btn.classList.toggle("is-active", isActive);
      btn.classList.toggle("btn-outline-dark", !isActive);
      btn.classList.toggle("btn-dark", isActive);
    });
  }

  function init() {
    const buttons = Array.from(document.querySelectorAll(".month-btn"));
    const months = Array.from(document.querySelectorAll(".month-container"));
    if (!months.length) return;

    const firstId = buttons.length
      ? buttons[0].getAttribute("data-month-id")
      : months[0].getAttribute("data-month-id");

    showMonth(firstId);

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        showMonth(btn.getAttribute("data-month-id"));
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
