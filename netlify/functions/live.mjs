// Reports whether the church is currently live on YouTube, for the home page hero.
// The API key comes from the Netlify env var YOUTUBE_API_KEY; it never reaches the browser.
// Without a key this returns {live:false}, so the page just keeps its hero photo.

const API = "https://www.googleapis.com/youtube/v3";
// @blaisebaptistchurch. Override with the YOUTUBE_CHANNEL_ID env var if the channel ever moves.
const CHANNEL_ID = process.env.YOUTUBE_CHANNEL_ID || "UCKEb9j6ULL2sKGwiOt_sYzQ";
const RECENT = 5;

async function yt(path) {
  const res = await fetch(`${API}/${path}&key=${process.env.YOUTUBE_API_KEY}`);
  if (!res.ok) throw new Error(`YouTube ${res.status} for ${path}`);
  return res.json();
}

// Two units per check. search.list?eventType=live would be one call instead of two, but it costs
// 100 units — enough to blow the 10,000/day quota at this poll rate. Live broadcasts show up in
// the uploads playlist, so we read that and ask videos.list what state those videos are in. If a
// broadcast ever fails to appear there, the fallback is a single search.list call.
async function currentLive() {
  const uploads = "UU" + CHANNEL_ID.slice(2);
  const list = await yt(`playlistItems?part=contentDetails&playlistId=${uploads}&maxResults=${RECENT}`);
  const ids = (list.items || []).map((i) => i.contentDetails?.videoId).filter(Boolean);
  if (!ids.length) return null;

  const videos = await yt(`videos?part=snippet,liveStreamingDetails&id=${ids.join(",")}`);
  for (const v of videos.items || []) {
    const d = v.liveStreamingDetails;
    if (v.snippet?.liveBroadcastContent !== "live") continue;
    if (!d?.actualStartTime || d.actualEndTime) continue;
    return { live: true, video_id: v.id, title: v.snippet.title, started_at: d.actualStartTime };
  }
  return null;
}

export default async () => {
  if (!process.env.YOUTUBE_API_KEY) {
    return Response.json({ live: false, reason: "not configured" }, { headers: { "Cache-Control": "public, max-age=300" } });
  }
  try {
    const found = await currentLive();
    return Response.json(found || { live: false }, {
      headers: {
        "Cache-Control": "public, max-age=15",
        // Short windows on purpose: a stale answer here is a hero that says "Live Now" after the
        // service has ended, or the photo still showing after it starts. 30s at the edge plus a
        // 30s stale window caps that at about a minute; the poll in assets/live.js does the rest.
        // Quota stays comfortable: ~2,880 origin checks/day x 2 units = 5,760 of 10,000.
        "Netlify-CDN-Cache-Control": "public, durable, s-maxage=30, stale-while-revalidate=30",
      },
    });
  } catch (err) {
    console.error(err);
    // Never fail loudly: the home page falls back to its hero photo.
    return Response.json({ live: false, reason: "error" }, { headers: { "Cache-Control": "no-store" } });
  }
};

export const config = { path: "/api/live" };
