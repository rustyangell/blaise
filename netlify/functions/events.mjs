// Serves upcoming public events + open signups from Planning Center as JSON.
// Credentials come from Netlify env vars PCO_APP_ID / PCO_SECRET (a Personal Access Token);
// they never reach the browser. The CDN caches the response, so Planning Center is hit
// at most every few minutes regardless of traffic.

const API = "https://api.planningcenteronline.com";
const CC = "https://blaisebaptist.churchcenter.com";
const HORIZON_DAYS = 90;
const MAX_PAGES = 5;
// Calendar events carrying a ministry-area tag are shown further out than ordinary events, since
// trips and retreats are planned and promoted months ahead. Each ministry page filters this list
// by its own tag. Walking that far costs more pages, so it has a time cap.
const MINISTRY_TAGS = ["missions", "special friends", "youth ministry", "men's ministry", "women's ministry"];
const MINISTRY_HORIZON_DAYS = 365;
const MINISTRY_MAX_PAGES = 20;
const MINISTRY_TIME_BUDGET_MS = 7000;

const normTag = (name) => name.toLowerCase().replace(/[\u2018\u2019]/g, "'").trim();

async function pco(path) {
  const auth = Buffer.from(`${process.env.PCO_APP_ID}:${process.env.PCO_SECRET}`).toString("base64");
  const res = await fetch(path.startsWith("http") ? path : API + path, {
    headers: { Authorization: `Basic ${auth}` },
  });
  if (!res.ok) throw new Error(`PCO ${res.status} for ${path}`);
  return res.json();
}

function indexIncluded(included = []) {
  const map = new Map();
  for (const r of included) map.set(`${r.type}:${r.id}`, r);
  return map;
}

async function calendarEvents() {
  const started = Date.now();
  const horizon = started + HORIZON_DAYS * 864e5;
  const ministryHorizon = started + MINISTRY_HORIZON_DAYS * 864e5;
  const byEvent = new Map(); // one card per parent event: its next occurrence
  const ministry = new Map(); // same, for events with a ministry-area tag (longer horizon)
  let url = "/calendar/v2/event_instances?filter=future&order=starts_at&include=event,tags&per_page=100";
  for (let page = 0; url && page < MINISTRY_MAX_PAGES; page++) {
    const body = await pco(url);
    const included = indexIncluded(body.included);
    let pastHorizon = false;
    for (const inst of body.data) {
      const a = inst.attributes;
      const start = Date.parse(a.starts_at);
      if (start > ministryHorizon) { pastHorizon = true; break; }
      const eventRef = inst.relationships?.event?.data;
      const event = eventRef && included.get(`Event:${eventRef.id}`);
      if (!event) continue;
      const e = event.attributes;
      if (!e.visible_in_church_center || e.link_only) continue;
      const categories = (inst.relationships?.tags?.data || [])
        .map((t) => included.get(`Tag:${t.id}`)?.attributes?.name)
        .filter(Boolean);
      const isMinistry = categories.some((c) => MINISTRY_TAGS.includes(normTag(c)));
      const card = {
        id: event.id,
        name: a.name || e.name,
        summary: e.summary || null,
        categories,
        starts_at: a.starts_at,
        ends_at: a.ends_at,
        all_day: !!a.all_day_event,
        location: a.location || null,
        recurrence: a.recurrence && a.recurrence !== "None" ? a.compact_recurrence_description : null,
        featured: !!e.featured,
        image: e.image_url || null,
        url: a.church_center_url || `${CC}/calendar/event/${inst.id}`,
        register_url: e.registration_url || null,
      };
      if (start <= horizon && !byEvent.has(event.id)) byEvent.set(event.id, card);
      if (isMinistry && !ministry.has(event.id)) ministry.set(event.id, card);
    }
    if (pastHorizon) break;
    // Past the ordinary horizon we are only looking for ministry-tagged events: stop when out of time or pages.
    const pastOrdinary = body.data.length && Date.parse(body.data[body.data.length - 1].attributes.starts_at) > horizon;
    if (pastOrdinary && (page + 1 >= MINISTRY_MAX_PAGES || Date.now() - started > MINISTRY_TIME_BUDGET_MS)) break;
    url = body.links?.next;
  }
  return { events: [...byEvent.values()], categorized: [...ministry.values()] };
}

// Registrations descriptions are HTML; cards want a short plain-text blurb.
function plainText(html, max = 200) {
  if (!html) return null;
  const text = html
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&#39;|&rsquo;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, " ")
    .trim();
  if (!text) return null;
  return text.length > max ? text.slice(0, max).replace(/\s+\S*$/, "") + "…" : text;
}

async function signups() {
  const body = await pco("/registrations/v2/signups?filter=unarchived&include=next_signup_time,categories&per_page=100");
  const included = indexIncluded(body.included);
  return body.data
    .filter((s) => s.attributes.open && !s.attributes.archived)
    .map((s) => {
      const ref = s.relationships?.next_signup_time?.data;
      const t = ref && included.get(`SignupTime:${ref.id}`)?.attributes;
      const categories = (s.relationships?.categories?.data || [])
        .map((c) => included.get(`Category:${c.id}`)?.attributes?.name)
        .filter(Boolean);
      return {
        id: s.id,
        name: s.attributes.name,
        categories,
        summary: plainText(s.attributes.description),
        starts_at: t?.starts_at || null,
        ends_at: t?.ends_at || null,
        all_day: !!t?.all_day,
        close_at: s.attributes.close_at || null,
        // Public URL that redirects to a freshly signed image.
        image: s.attributes.logo_url || null,
        // Info page, not /reservations/new: loads without sign-in and shows details first.
        url: `${CC}/registrations/events/${s.id}`,
      };
    })
    .sort((a, b) => (a.starts_at || "9999").localeCompare(b.starts_at || "9999"));
}

export default async () => {
  if (!process.env.PCO_APP_ID || !process.env.PCO_SECRET) {
    return Response.json({ error: "Planning Center credentials not configured" }, { status: 500 });
  }
  try {
    const [{ events, categorized }, open] = await Promise.all([calendarEvents(), signups()]);
    // Fall back to the linked calendar event's image for signups without a logo.
    const imageByUrl = new Map([...events, ...categorized].filter((e) => e.register_url).map((e) => [e.register_url, e.image]));
    for (const s of open) s.image = s.image || imageByUrl.get(s.url) || null;
    return Response.json(
      { updated: new Date().toISOString(), signups: open, events, categorized },
      {
        headers: {
          "Cache-Control": "public, max-age=60",
          // Fresh for 15 min; if Planning Center is down, keep serving the last good copy for a day.
          "Netlify-CDN-Cache-Control": "public, durable, s-maxage=900, stale-while-revalidate=86400, stale-if-error=86400",
        },
      },
    );
  } catch (err) {
    console.error(err);
    return Response.json({ error: "Could not reach Planning Center" }, { status: 502, headers: { "Cache-Control": "no-store" } });
  }
};

export const config = { path: "/api/events" };
