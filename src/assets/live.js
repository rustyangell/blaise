// Swaps the home page hero photo for the YouTube stream while the church is live.
// Asks /api/live (see netlify/functions/live.mjs) on load and once a minute after that, so the
// player appears when the stream starts and the photo returns when it ends — no reload needed.
// Anything unexpected (no network, no API key, an error) leaves the photo exactly as it is.
(function () {
  var hero = document.querySelector("[data-live-hero]");
  if (!hero) return;

  var POLL_MS = 60000;
  var watchUrl = hero.getAttribute("data-youtube") || "https://www.youtube.com/";
  var photo = hero.innerHTML; // the not-live state, restored when the stream ends
  var showing = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function show(id) {
    if (showing === id) return;
    showing = id;
    if (!id) {
      hero.innerHTML = photo;
      hero.classList.remove("hero-live");
      return;
    }
    hero.classList.add("hero-live");
    // Muted autoplay: browsers allow it, and nobody gets ambushed by sound.
    hero.innerHTML =
      '<div class="hero-live-inner">' +
      '<p class="live-badge"><span class="live-dot"></span>Live Now</p>' +
      '<iframe src="https://www.youtube.com/embed/' + esc(id) + '?autoplay=1&mute=1&playsinline=1" ' +
      'title="Blaise Baptist Church live stream" allow="autoplay; encrypted-media; picture-in-picture" ' +
      'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>' +
      '<p class="hero-live-actions"><a class="btn btn-outline" href="' + esc(watchUrl) + '" target="_blank" rel="noopener">Watch on YouTube</a></p>' +
      "</div>";
  }

  // ?live=<videoId> forces the live layout, for checking the design without a real stream.
  var forced = (location.search.match(/[?&]live=([\w-]{6,})/) || [])[1];
  if (forced) return show(forced);

  function check() {
    fetch("/api/live", { headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data) show(data.live && data.video_id ? data.video_id : null); })
      .catch(function () { /* keep whatever is on screen */ });
  }

  check();
  setInterval(function () {
    if (!document.hidden) check();
  }, POLL_MS);
})();
