// The menu on small screens, the Console tour's tabs and views, and copy buttons.
(function () {
  "use strict";

  // Menu on small screens
  var toggle = document.querySelector(".nav-toggle");
  var links = document.getElementById("nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    links.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        links.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Tour tabs: who is looking
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tour-tabs [role="tab"]'));
  function selectTab(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(t.getAttribute("aria-controls"));
      if (panel) panel.hidden = !on;
    });
    if (focus) tab.focus();
  }
  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { selectTab(tab, false); });
    tab.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
      else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
      else if (e.key === "Home") next = tabs[0];
      else if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) { e.preventDefault(); selectTab(next, true); }
    });
  });

  // Tour views: show the picked screenshot and say what it is
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll(".tour-panel").forEach(function (panel) {
    var link = panel.querySelector(".tour-stage .frame");
    var img = panel.querySelector(".tour-img");
    var caption = panel.querySelector(".tour-caption");
    var views = panel.querySelectorAll(".tour-view");
    views.forEach(function (view) {
      view.addEventListener("click", function () {
        views.forEach(function (v) { v.setAttribute("aria-pressed", v === view ? "true" : "false"); });
        var src = view.getAttribute("data-src");
        var show = function () {
          img.src = src;
          img.alt = view.getAttribute("data-alt");
          link.href = src;
          caption.textContent = view.getAttribute("data-text");
        };
        if (still) { show(); return; }
        img.classList.add("swapping");
        var pre = new Image();
        pre.onload = pre.onerror = function () { show(); img.classList.remove("swapping"); };
        pre.src = src;
      });
    });
  });

  // The latest release, from PyPI, so the page never shows an old version.
  // hugo.toml's version stays if PyPI can't be reached.
  var versions = document.querySelectorAll("[data-version]");
  if (versions.length && window.fetch) {
    fetch("https://pypi.org/pypi/nomad-hpc/json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.info || !/^\d+(\.\d+)+$/.test(j.info.version)) return;
        var v = j.info.version;
        var files = (j.releases && j.releases[v]) || [];
        var when = files.length ? new Date(files[0].upload_time_iso_8601) : null;
        var said = when && !isNaN(when) ? when.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" }) : null;
        versions.forEach(function (el) { el.textContent = v; });
        if (said) document.querySelectorAll("[data-released]").forEach(function (el) { el.textContent = "released " + said; });
      })
      .catch(function () {});
  }

  // Copy buttons
  document.querySelectorAll(".copy[data-copy]").forEach(function (btn) {
    var label = btn.textContent;
    btn.addEventListener("click", function () {
      var src = document.querySelector(btn.getAttribute("data-copy"));
      if (!src || !navigator.clipboard) return;
      navigator.clipboard.writeText(src.textContent.trim()).then(function () {
        btn.textContent = "Copied";
        btn.classList.add("done");
        setTimeout(function () { btn.textContent = label; btn.classList.remove("done"); }, 1600);
      });
    });
  });
})();
