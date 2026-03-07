(function () {
  window.EB = window.EB || {};

  function withDefaultHeaders(headers) {
    return Object.assign({ "X-Requested-With": "XMLHttpRequest" }, headers || {});
  }

  async function getHtml(url) {
    const response = await fetch(url, {
      method: "GET",
      headers: withDefaultHeaders(),
      credentials: "same-origin",
    });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    return response.text();
  }

  async function postJson(url, payload, csrfToken) {
    const response = await fetch(url, {
      method: "POST",
      headers: withDefaultHeaders({
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken || "",
      }),
      body: JSON.stringify(payload || {}),
      credentials: "same-origin",
    });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    return response.json();
  }

  async function postForm(url, formData, csrfToken) {
    const response = await fetch(url, {
      method: "POST",
      headers: withDefaultHeaders({
        "X-CSRFToken": csrfToken || "",
      }),
      body: formData,
      credentials: "same-origin",
    });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    return response;
  }

  window.EB.api = {
    getHtml,
    postJson,
    postForm,
  };
})();
