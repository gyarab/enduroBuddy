(function () {
  window.EB = window.EB || {};

  function getCookie(name) {
    const cookieValue = document.cookie
      .split(";")
      .map((c) => c.trim())
      .find((c) => c.startsWith(`${name}=`));
    if (!cookieValue) return null;
    return decodeURIComponent(cookieValue.substring(name.length + 1));
  }

  function getCsrfToken() {
    return (
      getCookie("endurobuddy_csrftoken") ||
      getCookie("csrftoken") ||
      (document.querySelector("input[name='csrfmiddlewaretoken']") || {}).value ||
      ""
    );
  }

  function getWidgetState(widget) {
    if (!widget) return {};
    if (!widget.__ebState) {
      widget.__ebState = {
        monthRevisions: {},
        monthLayoutCache: {},
        eqTimer: null,
        eqRaf: null,
        resizeBound: false,
        resizeObserver: null,
      };
    }
    return widget.__ebState;
  }

  window.EB.core = {
    getCookie,
    getCsrfToken,
    getWidgetState,
  };
})();
