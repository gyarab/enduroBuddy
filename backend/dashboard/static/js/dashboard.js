// backend/static/js/dashboard.js
(function () {
  let syncing = false;

  function showMonth(monthId) {
    const months = Array.from(document.querySelectorAll(".month-container"));
    const buttons = Array.from(document.querySelectorAll(".month-btn"));

    // 1) vždy schovej všechny měsíce (nezávisle na CSS)
    months.forEach((el) => {
      el.style.display = "none";
      el.classList.remove("is-active");
    });

    // 2) ukaž vybraný měsíc
    const target = document.querySelector(
      `.month-container[data-month-id="${monthId}"]`
    );
    if (target) {
      target.style.display = "block";
      target.classList.add("is-active");
    }

    // 3) zvýrazni button
    buttons.forEach((btn) => {
      const isActive = btn.dataset.monthId === String(monthId);
      btn.classList.toggle("is-active", isActive);
      btn.classList.toggle("btn-dark", isActive);
      btn.classList.toggle("btn-outline-dark", !isActive);
    });

    // 4) reset scrollů při přepnutí
    const x = document.getElementById("monthXScroll");
    const track = document.getElementById("monthSwitcherTrack");
    if (x) x.scrollLeft = 0;
    if (track) track.scrollLeft = 0;
  }

  function initScrollSync() {
    const x = document.getElementById("monthXScroll");
    const track = document.getElementById("monthSwitcherTrack");
    if (!x || !track) return;

    x.addEventListener("scroll", () => {
      if (syncing) return;
      syncing = true;
      track.scrollLeft = x.scrollLeft;
      syncing = false;
    });

    track.addEventListener("scroll", () => {
      if (syncing) return;
      syncing = true;
      x.scrollLeft = track.scrollLeft;
      syncing = false;
    });
  }

  function init() {
    const buttons = Array.from(document.querySelectorAll(".month-btn"));
    const months = Array.from(document.querySelectorAll(".month-container"));

    if (!months.length) return;

    // vyber první month id z buttonů nebo prvního měsíce
    const firstId =
      (buttons[0] && buttons[0].dataset.monthId) || months[0].dataset.monthId;

    showMonth(firstId);

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => showMonth(btn.dataset.monthId));
    });

    initScrollSync();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
