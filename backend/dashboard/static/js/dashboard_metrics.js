(function () {
  window.EB = window.EB || {};

  function isEnabled() {
    return window.EB_DEBUG_METRICS === 1 || window.EB_DEBUG_METRICS === true;
  }

  function now() {
    if (window.performance && typeof window.performance.now === "function") {
      return window.performance.now();
    }
    return Date.now();
  }

  function start(name) {
    if (!isEnabled()) return null;
    return { name: String(name || "metric"), t0: now() };
  }

  function end(token, meta) {
    if (!token || !isEnabled()) return null;
    const durationMs = Math.round((now() - token.t0) * 100) / 100;
    const payload = Object.assign({ metric: token.name, duration_ms: durationMs }, meta || {});
    try {
      console.debug("[EB_METRIC]", payload);
    } catch (_) {}
    return payload;
  }

  async function measureAsync(name, fn, meta) {
    const token = start(name);
    try {
      return await fn();
    } finally {
      end(token, meta);
    }
  }

  window.EB.metrics = {
    isEnabled,
    start,
    end,
    measureAsync,
  };
})();
