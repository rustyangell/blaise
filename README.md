# Blaise Baptist Church — website redesign

Static site replacing the church's current Wix site (`blaisebaptist.org`), built to hand off day-to-day
events/forms/groups/calendar to Planning Center Church Center instead of duplicating them in the site itself.

**Live preview:** https://blaisebaptist.netlify.app (Netlify project `blaisebaptist`, id
`64f6e724-fa41-4cc5-bbf1-df1232a4876d`). Not connected to any custom domain yet — this is a preview site,
separate from the live `blaisebaptist.org` Wix site, which this is not touching.

## How this is built

Plain HTML/CSS, no framework, no JS dependency for anything except the Planning Center embed script.
`src/build.py` is a small generator (Python stdlib only) that renders every page from shared nav/footer
templates into `dist/`, which is what actually gets deployed.

```bash
python3 src/build.py                # writes dist/
```

## Deploying

The Netlify project is Git-connected to this repo, so deploys are automatic:

- **Merge a PR into `main`** → Netlify runs `python3 src/build.py` and publishes to production.
- **Open a PR** → Netlify builds a deploy preview at its own URL, so a change can be reviewed
  before it goes live.

Build settings live in `netlify.toml` (build command, publish dir, functions dir) — Netlify reads
them from the repo, so there is nothing to configure in the dashboard.

Manual deploy from a laptop, if ever needed:

```bash
python3 src/build.py
netlify deploy --prod --site 64f6e724-fa41-4cc5-bbf1-df1232a4876d --dir=dist --functions=netlify/functions
```

`dist/` is gitignored — it's fully regenerated from `src/` every time, never hand-edited.

## Brand system

Source: `Brand Guide One-Pager.pdf` in the client's branding folder (Downloads/Blaise Branding on Rusty's
machine). Tokens are duplicated as CSS custom properties at the top of `src/styles.css`:

- Forest Green `#1A3A1A` (headlines), Sage `#8CA08C` (support only), Off White `#F5F5F0` (background),
  Near Black `#1A1A1A` (body text)
- Ministry colors: Kids Teal `#00A878`, Youth Orange `#F08C00`, Men Navy `#142864`, Women Mauve `#6B3D52`
- Font: Josefin Sans (Google Fonts) — Bold headings, Regular body, Light fine print only
- Voice: warm, plainspoken, specific (name Mocksville/Davie County) — not marketing copy
- Real logo/ministry-icon PNGs live in `src/assets/`, copied from the brand kit. Note: the brand kit has
  no true light-colored logo file, so `.logo-inverse` uses a CSS filter to flatten the green mark to white
  for dark backgrounds (see comment in `styles.css`). Ministry icon art is tinted close to its own
  ministry color, so icons sit on a white `.icon-badge` for contrast rather than being recolored.

## Planning Center integration — how the links behave, and why

All form/event/group links point to `blaisebaptist.churchcenter.com` (URLs collected in the `LINKS` dict
at the top of `src/build.py`). Two different link behaviors, deliberately:

- **People Forms** (Connection Form, Baptism Interest, Parent/Child Dedication, Interested in Serving,
  Missions Interest) use Planning Center's official popup embed: a `<script src="https://js.churchcenter.com/modal/v1">`
  tag plus `data-open-in-church-center-modal="true"` on the link (see `modal_link()`). These open as a
  modal right over the page. Confirmed working live.
- **Registrations/reservations** (Kairos, Bunco, Women's Night, Wednesday Meals) use `plain_link()` —
  a normal link that opens in a new tab. **Do not put these in the modal** — tried it, and the modal hangs
  on an infinite spinner and never loads. Best-grounded guess: those pages can involve payment, and
  payment pages commonly refuse to be framed for clickjacking-security reasons. Not documented explicitly
  by Planning Center, but reproducible. These links also point to the event's public **info page**
  (`/registrations/events/{id}`), not straight to `/reservations/new` — the info page loads with no
  sign-in required and lets people read details before registering.

## Known gaps / next steps

- **Childcare registration** (`childcare.html`) has a placeholder ("Registration opening soon — contact
  us to register"). The church uses **ProCare**, not Planning Center, for this ministry. Build the
  registration form in ProCare (Enrollment → Registration → Create Registration, recipient type "Active
  Student"), matching the field list that was on the old Wix site's "Returning Camper Registration" form
  (Name of Child, Birthday, Name of Parents, Address, School & Grade Completed, Phone, Allergies, T-shirt
  Size, Full/Part Time, Pay in full/daily). ProCare gives a link or embeddable button — drop it into
  `childcare()` in `build.py` in place of the `.placeholder-note` block.
- **Small Group Leader interest** is intentionally *not* a separate form — it routes to the existing
  PCO "Interested in Serving?" form (id 1202575), which already has a "Small Groups" checkbox option.
- **Celebrate Recovery** has no PCO group link on the site — the CR group in Planning Center is currently
  unlisted/private (common for anonymity). Stays informational-only unless that's changed deliberately.
- **Going live**: when the redesign is approved, `blaisebaptist.org`'s domain needs to move from the old
  Wix site to wherever this ends up hosted. That's a separate, deliberate step — not done as part of
  building this.

## Full page/content audit this was built from

See prior conversation history for the full page-by-page audit of the old Wix site (what existed, what
was flagged for removal, what was missing). Not duplicated here — this README covers only what a fresh
session needs to keep working on the code itself.

## Live events from the Planning Center API

`netlify/functions/events.mjs` serves `/api/events`: upcoming (90 days) Calendar events marked *Visible in
Church Center*, plus every open, unarchived Registrations signup. It authenticates with a Personal Access
Token stored as Netlify env vars `PCO_APP_ID` / `PCO_SECRET` (secret; set in the Netlify UI, never in the
repo). The CDN caches the response for 15 minutes and serves the last good copy for a day if Planning
Center is down.

`src/assets/events.js` fills any `data-pco="signups" | "events" | "home"` container on the events and home
pages. Those containers ship with a Church Center link as fallback content. Calendar events whose
registration URL matches an open signup are shown once, as the signup. To hide an event from the site,
set it to Hidden in Church Center; there is nothing to edit here.
