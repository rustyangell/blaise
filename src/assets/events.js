// Renders live Planning Center events into any [data-pco] container.
//   data-pco="signups" : open registrations
//   data-pco="events"  : upcoming public calendar events
//   data-pco="home"    : a short mix for the home page (data-limit, default 3)
// Containers hold fallback markup (a link to Church Center) until data arrives.
(function () {
  var TZ = "America/New_York";
  var nodes = document.querySelectorAll("[data-pco]");
  if (!nodes.length) return;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fmt(iso, opts) {
    return new Date(iso).toLocaleString("en-US", Object.assign({ timeZone: TZ }, opts));
  }

  function when(item) {
    if (!item.starts_at) return "Ongoing";
    var day = { month: "short", day: "numeric" };
    var start = fmt(item.starts_at, day);
    var end = item.ends_at ? fmt(item.ends_at, day) : start;
    if (item.recurrence) return item.recurrence + " &middot; next " + esc(start);
    if (start !== end) {
      // "Nov 12–14" within a month, "Oct 30–Nov 2" across months
      var sameMonth = start.split(" ")[0] === end.split(" ")[0];
      return esc(start) + "&ndash;" + esc(sameMonth ? end.split(" ")[1] : end);
    }
    if (item.all_day) return esc(fmt(item.starts_at, { weekday: "short", month: "short", day: "numeric" }));
    return esc(fmt(item.starts_at, { weekday: "short", month: "short", day: "numeric" }) + ", " +
      fmt(item.starts_at, { hour: "numeric", minute: "2-digit" }));
  }

  function card(item, isSignup) {
    var href = isSignup ? item.url : item.register_url || item.url;
    var label = isSignup || item.register_url ? "Get Info &amp; Register" : "Details";
    var sub = isSignup
      ? item.close_at ? "Registration closes " + esc(fmt(item.close_at, { month: "short", day: "numeric" })) : ""
      : esc(item.summary || item.location || "");
    return '<div class="event-card">' +
      (item.image ? '<img class="event-img" src="' + esc(item.image) + '" alt="" loading="lazy">' : "") +
      '<span class="date">' + when(item) + "</span>" +
      "<h3>" + esc(item.name) + "</h3>" +
      (sub ? "<p>" + sub + "</p>" : "") +
      '<a class="btn btn-primary" href="' + esc(href) + '" target="_blank" rel="noopener">' + label + "</a>" +
      "</div>";
  }

  fetch("/api/events")
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      var signupIds = {};
      data.signups.forEach(function (s) { signupIds[s.url] = true; });
      // Calendar events that are just a mirror of an open signup would show twice.
      var events = data.events.filter(function (e) { return !(e.register_url && signupIds[e.register_url]); });

      nodes.forEach(function (node) {
        var kind = node.getAttribute("data-pco");
        var html = "";
        if (kind === "signups") {
          html = data.signups.map(function (s) { return card(s, true); }).join("");
        } else if (kind === "events") {
          html = events.map(function (e) { return card(e, false); }).join("");
        } else if (kind === "home") {
          var limit = parseInt(node.getAttribute("data-limit") || "3", 10);
          var mix = data.signups.map(function (s) { return card(s, true); })
            .concat(events.filter(function (e) { return e.featured || !e.recurrence; }).map(function (e) { return card(e, false); }))
            .concat(events.filter(function (e) { return !e.featured && e.recurrence; }).map(function (e) { return card(e, false); }));
          html = mix.slice(0, limit).join("");
        }
        if (html) node.innerHTML = html;
        else if (node.hasAttribute("data-empty")) node.innerHTML = '<p>' + esc(node.getAttribute("data-empty")) + "</p>";
      });
    })
    .catch(function () { /* keep the fallback markup */ });
})();
