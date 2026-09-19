// Campus map on the About page. Hover or focus a building for its name; select it (click, tap, Enter/Space)
// to open its panel. A building can have more than one shape (the Underground entrance and its inset).
// Deep link: /about?building=<id>#campus-map selects that building on load.
(function () {
  var root = document.getElementById("campus-map");
  var dataEl = document.getElementById("campus-data");
  if (!root || !dataEl) return;

  var data = JSON.parse(dataEl.textContent);
  var canvas = root.querySelector(".campus-canvas");
  var tip = root.querySelector(".campus-tip");
  var panel = document.getElementById("campus-panel");
  var number = panel.querySelector(".campus-panel-number");
  var title = panel.querySelector("h3");
  var desc = panel.querySelector(".campus-panel-desc");
  var list = panel.querySelector(".campus-panel-list");
  var shapes = root.querySelectorAll(".campus-building");
  var inset = document.getElementById("campus-inset");
  var UNDERGROUND = "youth-underground";
  var selectedId = null;
  var insetTimer = null;
  var lastFocused = null;

  // On phones the whole site is too small to read, so crop in on the buildings (data-mobile-viewbox).
  var svg = root.querySelector(".campus-svg");
  var fullView = svg.getAttribute("viewBox");
  var mobileView = svg.dataset.mobileViewbox;
  var phone = window.matchMedia("(max-width: 760px)");
  function fitView() { svg.setAttribute("viewBox", phone.matches && mobileView ? mobileView : fullView); }
  fitView();
  if (phone.addEventListener) phone.addEventListener("change", fitView);

  function setUrl(id) {
    var url = new URL(window.location.href);
    if (id) url.searchParams.set("building", id);
    else url.searchParams.delete("building");
    history.replaceState(null, "", url.pathname + url.search + "#campus-map");
  }

  function showTip(el) {
    var b = data[el.dataset.building];
    var box = el.getBoundingClientRect();
    var host = canvas.getBoundingClientRect();
    tip.innerHTML = "";
    var strong = document.createElement("strong");
    strong.textContent = b.number + " · " + b.name;
    var p = document.createElement("span");
    p.textContent = b.hover;
    tip.append(strong, p);
    tip.hidden = false;
    var left = box.left - host.left + box.width / 2 - tip.offsetWidth / 2;
    left = Math.max(8, Math.min(left, host.width - tip.offsetWidth - 8));
    var top = box.top - host.top - tip.offsetHeight - 10;
    if (top < 8) top = box.bottom - host.top + 10;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }

  function hideTip() { tip.hidden = true; }

  // The Underground inset pops up only while its entrance is hovered/focused, or while it is selected.
  function showInset() {
    clearTimeout(insetTimer);
    if (!inset.hidden) return;
    inset.hidden = false;
    var marker = canvas.querySelector(".campus-entrance").getBoundingClientRect();
    var host = canvas.getBoundingClientRect();
    var left = marker.left - host.left + marker.width / 2 - inset.offsetWidth / 2;
    left = Math.max(8, Math.min(left, host.width - inset.offsetWidth - 8));
    var top = marker.bottom - host.top + 8;
    if (top + inset.offsetHeight > host.height) top = Math.max(8, marker.top - host.top - inset.offsetHeight - 8);
    inset.style.left = left + "px";
    inset.style.top = top + "px";
  }

  function hideInsetSoon() {
    clearTimeout(insetTimer);
    insetTimer = setTimeout(function () {
      if (selectedId !== UNDERGROUND && !inset.contains(document.activeElement)) inset.hidden = true;
    }, 250);
  }

  inset.addEventListener("pointerenter", function () { clearTimeout(insetTimer); });
  inset.addEventListener("pointerleave", hideInsetSoon);

  function select(id) {
    var b = data[id];
    if (!b) return false;
    shapes.forEach(function (node) {
      var on = node.dataset.building === id;
      node.classList.toggle("is-selected", on);
      node.setAttribute("aria-pressed", on ? "true" : "false");
    });
    selectedId = id;
    if (id === UNDERGROUND) showInset();
    else inset.hidden = true;
    number.textContent = "Building " + b.number;
    title.textContent = b.name;
    desc.textContent = b.description;
    list.textContent = "";
    if (b.ministries.length) {
      b.ministries.forEach(function (m) {
        var li = document.createElement("li");
        var a = document.createElement(m.url ? "a" : "strong");
        if (m.url) a.href = m.url;
        a.textContent = m.name;
        li.appendChild(a);
        if (m.when) {
          var when = document.createElement("span");
          when.className = "campus-when";
          when.textContent = m.when;
          li.appendChild(when);
        }
        list.appendChild(li);
      });
    } else {
      var li = document.createElement("li");
      li.className = "campus-none";
      li.textContent = "No regular ministries listed yet.";
      list.appendChild(li);
    }
    panel.hidden = false;
    root.classList.add("has-selection");
    return true;
  }

  function close() {
    panel.hidden = true;
    root.classList.remove("has-selection");
    shapes.forEach(function (node) {
      node.classList.remove("is-selected");
      node.setAttribute("aria-pressed", "false");
    });
    inset.hidden = true;
    if (lastFocused) lastFocused.focus({ preventScroll: true });
    selectedId = null;
    setUrl(null);
  }

  shapes.forEach(function (el) {
    var id = el.dataset.building;
    el.addEventListener("click", function () {
      lastFocused = el;
      hideTip();
      if (select(id)) setUrl(id);
    });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        lastFocused = el;
        if (select(id)) setUrl(id);
      }
    });
    var isUnderground = id === UNDERGROUND;
    el.addEventListener("pointerenter", function (e) {
      if (e.pointerType !== "mouse") return;
      if (isUnderground) showInset();
      else showTip(el);
    });
    el.addEventListener("pointerleave", function () {
      hideTip();
      if (isUnderground) hideInsetSoon();
    });
    el.addEventListener("focus", function () {
      if (isUnderground) showInset();
      else showTip(el);
    });
    el.addEventListener("blur", function () {
      hideTip();
      if (isUnderground) hideInsetSoon();
    });
  });
  panel.querySelector(".campus-panel-close").addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      hideTip();
      if (!panel.hidden) close();
    }
  });

  var initial = new URLSearchParams(window.location.search).get("building");
  if (initial && select(initial)) {
    // The hash already scrolls here on load; repeat once layout settles (fonts, images above).
    requestAnimationFrame(function () { root.scrollIntoView({ block: "start" }); });
  }
})();
