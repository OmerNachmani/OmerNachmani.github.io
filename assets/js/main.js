/* Optional writeup filters. Reading and navigation do not depend on JavaScript. */
(function () {
  "use strict";

  function initializeWriteupFilters() {
    const list = document.getElementById("writeup-list");
    const search = document.getElementById("writeup-search");
    const controls = document.querySelector(".writing-controls");
    if (!list || !search || !controls) return;

    const entries = Array.from(list.querySelectorAll("[data-entry]"));
    if (!entries.length) return;

    const buttons = Array.from(controls.querySelectorAll("button[data-filter]"));
    const categories = new Set(buttons.map(function (button) { return button.dataset.filter; }));
    const count = document.getElementById("filter-count");
    const empty = document.getElementById("no-results");
    const parameters = new URL(window.location.href).searchParams;
    const requestedCategory = parameters.get("category");
    let category = categories.has(requestedCategory) ? requestedCategory : "all";
    search.value = parameters.get("q") || "";

    function normalize(value) {
      return value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    }

    const records = entries.map(function (entry) {
      return {
        element: entry,
        categories: (entry.dataset.categories || "").split(/[\s,|]+/).filter(Boolean),
        text: normalize((entry.dataset.search || "") + " " + entry.textContent)
      };
    });

    function syncURL() {
      if (!/^https?:$/.test(window.location.protocol)) return;
      const url = new URL(window.location.href);
      if (category === "all") url.searchParams.delete("category");
      else url.searchParams.set("category", category);
      const query = search.value.trim();
      if (query) url.searchParams.set("q", query);
      else url.searchParams.delete("q");
      window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
    }

    function applyFilters() {
      const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      let visible = 0;

      records.forEach(function (record) {
        const categoryMatches = category === "all" || record.categories.includes(category);
        const queryMatches = words.every(function (word) { return record.text.includes(word); });
        record.element.hidden = !(categoryMatches && queryMatches);
        if (!record.element.hidden) visible += 1;
      });

      buttons.forEach(function (button) {
        button.setAttribute("aria-pressed", String(button.dataset.filter === category));
      });
      if (count) count.textContent = visible + " of " + records.length + " entries";
      if (empty) empty.hidden = visible !== 0;
      syncURL();
    }

    buttons.forEach(function (button) {
      button.type = "button";
      button.addEventListener("click", function () {
        category = button.dataset.filter;
        applyFilters();
      });
    });

    search.addEventListener("input", applyFilters);
    search.addEventListener("search", applyFilters);

    document.querySelectorAll("[data-reset]").forEach(function (button) {
      button.type = "button";
      button.addEventListener("click", function () {
        category = "all";
        search.value = "";
        applyFilters();
        search.focus();
      });
    });

    if (count) count.setAttribute("aria-live", "polite");
    controls.hidden = false;
    applyFilters();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeWriteupFilters, { once: true });
  } else {
    initializeWriteupFilters();
  }
})();
