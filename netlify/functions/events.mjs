// Serves upcoming public events + open signups from Planning Center as JSON.
// Credentials come from Netlify env vars PCO_APP_ID / PCO_SECRET (a Personal Access Token);
// they never reach the browser. The CDN caches the response, so Planning Center is hit
// at most every few minutes regardless of traffic.

const API = "https://api.planningcenteronline.com";
const CC = "https://blaisebaptist.churchcenter.com";
const HORIZON_DAYS = 90;
const MAX_PAGES = 5;

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
  const horizon = Date.now() + HORIZON_DAYS * 864e5;
  const byEvent = new Map(); // one card per parent event: its next occurrence
  let url = "/calendar/v2/event_instances?filter=future&order=starts_at&include=event&per_page=100";
  for (let page = 0; url && page < MAX_PAGES; page++) {
    const body = await pco(url);
    const included = indexIncluded(body.included);
    let pastHorizon = false;
    for (const inst of body.data) {
      const a = inst.attributes;
      if (Date.parse(a.starts_at) > horizon) { pastHorizon = true; break; }
      const eventRef = inst.relationships?.event?.data;
      const event = eventRef && included.get(`Event:${eventRef.id}`);
      if (!event) continue;
      const e = event.attributes;
      if (!e.visible_in_church_center || e.link_only) continue;
      if (byEvent.has(event.id)) continue;
      byEvent.set(event.id, {
        id: event.id,
        name: a.name || e.name,
        summary: e.summary || null,
        starts_at: a.starts_at,
        ends_at: a.ends_at,
        all_day: !!a.all_day_event,
        location: a.location || null,
        recurrence: a.recurrence && a.recurrence !== "None" ? a.compact_recurrence_description : null,
        featured: !!e.featured,
        image: e.image_url || null,
        url: a.church_center_url || `${CC}/calendar/event/${inst.id}`,
        register_url: e.registration_url || null,
      });
    }
    url = pastHorizon ? null : body.links?.next;
  }
  return [...byEvent.values()];
}

async function signups() {
  const body = await pco("/registrations/v2/signups?filter=unarchived&include=next_signup_time&per_page=100");
  const included = indexIncluded(body.included);
  return body.data
    .filter((s) => s.attributes.open && !s.attributes.archived)
    .map((s) => {
      const ref = s.relationships?.next_signup_time?.data;
      const t = ref && included.get(`SignupTime:${ref.id}`)?.attributes;
      return {
        id: s.id,
        name: s.attributes.name,
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
    const [events, open] = await Promise.all([calendarEvents(), signups()]);
    // Fall back to the linked calendar event's image for signups without a logo.
    const imageByUrl = new Map(events.filter((e) => e.register_url).map((e) => [e.register_url, e.image]));
    for (const s of open) s.image = s.image || imageByUrl.get(s.url) || null;
    return Response.json(
      { updated: new Date().toISOString(), signups: open, events },
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
