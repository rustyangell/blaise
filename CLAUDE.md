# Working in this repo

House rules for Claude sessions. `README.md` has the full detail — this file is the short list of
things to get right without being told.

## How far to take a change

Default: **finish it and ship it.** Do the work, verify it, commit, open a PR, and merge once the
Netlify checks pass — merging `main` deploys to production. Report what shipped; don't wait for
permission at each step.

Stop and ask first when the change is structural (reworking navigation, restructuring pages),
destructive (deleting content or pages, cancelling services), or would change what visitors see in
a way the request didn't ask for. Scope creep is not a bonus — deliver what was asked, and raise
anything extra as a suggestion rather than shipping it.

## Verify before you push

A change can build cleanly and still be wrong. Every time:

1. `python3 src/build.py` — expect `Built 14 pages into …`.
2. **Look at the rendered page**, not just the diff. Headless render when there's no browser:
   `/opt/pw-browsers/chromium-*/chrome-linux/chrome --headless --no-sandbox --screenshot=out.png "file://$PWD/dist/<page>.html"`
3. Grep `dist/` to prove the change landed and nothing stale survived — especially for renames.

State plainly what you verified and what you couldn't. If something can't be checked from here
(external links, the Netlify redirect, anything behind the egress policy), say so rather than
implying it passed.

## Non-negotiables

- **Never hand-edit `dist/`.** It is generated and gitignored; fix the source and rebuild.
- **Never touch DNS nameservers, MX, or TXT records** for `blaisebaptist.org`. Mail is Google
  Workspace and depends on them. See the cutover runbook in `README.md`.
- **Test against `blaisebaptist.netlify.app`**, not `blaisebaptist.org` — the latter is still the
  old Wix site.

## Judgment calls that have already been made

- **Content that changes often belongs in Church Center**, not this repo. That boundary is what
  lets staff manage events, registrations, and forms without touching code. Apply it to new
  requests: if something needs editing monthly, the answer is usually a Church Center object the
  site links to, not new markup here.
- **Childcare is a business that employs staff**, not a volunteer ministry. Don't put
  "Interested in Serving" on that page. Job postings live at `classifieds.html`.
- **Registrations must not use the Church Center modal** — it hangs on an infinite spinner. Use
  `plain_link()`. Forms use `modal_link()`. Reasoning is in `README.md`.
- **Buttons inside `.page-hero`** sit on a dark gradient and need the overrides in `styles.css`.
  Render and confirm rather than assuming.

## Tone for site copy

Warm, plainspoken, specific — name Mocksville and Davie County. Write for a first-time visitor who
doesn't know the church's internal vocabulary: prefer the plain description over the branded
program name when the two compete.
