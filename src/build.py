#!/usr/bin/env python3
"""Static site builder for Blaise Baptist Church. Renders PAGES into dist/."""
import html, json, os, re, shutil
from urllib.parse import quote_plus

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")

CC = "https://blaisebaptist.churchcenter.com"
LINKS = {
    "connection_form": f"{CC}/people/forms/306668",
    "baptism_form": f"{CC}/people/forms/945693",
    "dedication_form": f"{CC}/people/forms/945729",
    "serving_form": f"{CC}/people/forms/1202575",
    "missions_form": f"{CC}/people/forms/1236262",
    # Childcare enrollment lives in ProCare, not Church Center. Every childcare
    # call-to-action reads from this one constant.
    "childcare_registration": "https://schools.procareconnect.com/register/shining-son",
    "groups": f"{CC}/groups",
    "calendar": f"{CC}/calendar",
    "give": "https://app.easytithe.com/App/Giving/blaise",
    "facebook": "https://www.facebook.com/BlaiseChurch",
    "youtube": "https://www.youtube.com/@blaisebaptistchurch",
    "directions": "https://www.google.com/maps/dir/?api=1&destination=Blaise+Baptist+Church%2C+134+Blaise+Church+Rd%2C+Mocksville%2C+NC+27028",
    "map_embed": "https://www.google.com/maps?q=Blaise+Baptist+Church,+134+Blaise+Church+Rd,+Mocksville,+NC+27028&output=embed",
    "bfm": "https://bfm.sbc.net/bfm2000/",
}

# Campus buildings: id, name, and short description. Single source of truth for the campus map.
with open(os.path.join(SRC, "buildings.json")) as f:
    BUILDINGS = json.load(f)
BUILDINGS_BY_ID = {b["id"]: b for b in BUILDINGS}

# Where each regular ministry meets, by building id. Ministry/event pages get their "Find it on the map"
# link from here, and the campus map's panel builds each building's ministry list from the same rows.
MINISTRY_LOCATIONS = [
    # (ministry, page or None, building id, when). A page's first row is its primary building
    # (the one its "Find it on the map" link opens).
    ("Sunday Worship", "about.html", "family-life-center", "Sundays, 10:30 AM"),
    ("Sunday Bible Fellowship", None, "family-life-center", "Sundays, 9:30 AM"),
    ("Wednesday Meals", "events.html", "family-life-center", "Wednesdays"),
    ("Men&rsquo;s &amp; Women&rsquo;s Wednesday Night Groups", "small-groups.html", "family-life-center", "Wednesday nights"),
    ("Bible Fellowship", None, "sanctuary", "Sundays, 9:30 AM"),
    ("Celebrate Recovery", "celebrate-recovery.html", "educational", "Tuesdays, 6:00 PM (starts here, then moves to the Sanctuary)"),
    ("Children&rsquo;s Ministry", "children.html", "educational", "Sundays &amp; Wednesdays"),
    ("Student Ministry", "students.html", "educational", "Sundays &amp; Wednesdays"),
    ("Special Friends", None, "educational", ""),
    ("Bible Fellowship", None, "educational", "Sundays, 9:30 AM"),
    ("Bible Fellowship", None, "classrooms", "Sundays, 9:30 AM"),
    ("Small Groups (various)", "small-groups.html", "classrooms", ""),
    ("Church Offices", "contact.html", "offices", "Weekdays"),
    ("Bible Fellowship", None, "offices", "Sundays, 9:30 AM"),
    # Secondary locations go last, after every page's primary row.
    ("Celebrate Recovery", "celebrate-recovery.html", "sanctuary", "Tuesdays, 7:00 PM (after supper in the 300 building)"),
]
for _m in MINISTRY_LOCATIONS:
    if _m[2] not in BUILDINGS_BY_ID:
        raise SystemExit(f"MINISTRY_LOCATIONS: unknown building id {_m[2]!r} for {_m[0]}")


def map_url(building_id):
    return f"/about?building={building_id}#campus-map"


def find_on_map(page):
    """"Find it on the map" link for the building this page's ministry meets in."""
    building_id = next(m[2] for m in MINISTRY_LOCATIONS if m[1] == page)
    name = BUILDINGS_BY_ID[building_id]["name"]
    return f'<a class="map-link" href="{map_url(building_id)}">Find it on the map <span class="map-link-where">({name})</span></a>'


NAV_ITEMS = [
    ("index.html", "Home"),
]

ABOUT_ITEMS = [
    ("about.html", "About Us"),
    ("beliefs.html", "Beliefs &amp; Core Values"),
    ("baptism.html", "Baptism"),
]

MINISTRY_ITEMS = [
    ("students.html", "Students"),
    ("children.html", "Children"),
    ("senior-adults.html", "Senior Adults"),
    ("small-groups.html", "Small Groups"),
    ("celebrate-recovery.html", "Celebrate Recovery"),
    ("missions.html", "Missions"),
]

NAV_ITEMS_AFTER = [
    # Top level, not under Ministries: parents often come to the site for this alone.
    ("childcare.html", "Childcare"),
    ("events.html", "Events"),
    ("contact.html", "Contact"),
]

LOGO_NAV = '<img src="assets/logo-green.png" alt="Blaise Baptist Church" class="brand-mark">'
LOGO_FOOTER = '<img src="assets/mark-panes.png" alt="Blaise Baptist Church" class="footer-mark">'
def icon_badge(src, alt, extra_class=""):
    return f'<span class="icon-badge {extra_class}"><img src="{src}" alt="{alt}"></span>'


ICON_MEN = icon_badge("assets/icon-men.png", "Blaise Men")
ICON_WOMEN = icon_badge("assets/icon-women.png", "Blaise Women")
ICON_YOUTH = icon_badge("assets/icon-youth.png", "Blaise Youth")
ICON_CHILDREN = icon_badge("assets/icon-children.png", "Blaise Kids")
ICON_YOUTH_LG = icon_badge("assets/icon-youth.png", "Blaise Youth", "icon-badge-lg")
ICON_CHILDREN_LG = icon_badge("assets/icon-children.png", "Blaise Kids", "icon-badge-lg")


def modal_link(url, label, classes="btn btn-primary"):
    return f'<a href="{url}" target="_blank" rel="noopener" data-open-in-church-center-modal="true" class="{classes}">{label}</a>'


def plain_link(url, label, classes="btn btn-primary"):
    # Registrations can involve payment; those pages appear to block being
    # framed (the modal hangs on an infinite spinner), so these open normally.
    return f'<a href="{url}" target="_blank" rel="noopener" class="{classes}">{label}</a>'


def nav(active):
    active_style = ' style="color:var(--forest)"'

    def link_items(pairs):
        return "\n".join(
            f'<li><a href="{href}"{active_style if href == active else ""}>{label}</a></li>'
            for href, label in pairs
        )

    def dropdown(label, pairs):
        is_active = any(href == active for href, _ in pairs)
        return f"""<li>
        <!-- Shared name= makes these an exclusive accordion: opening one
             dropdown closes the other, so their panels can't overlap. -->
        <details class="nav-dropdown" name="nav-menu">
          <summary{active_style if is_active else ""}>{label}</summary>
          <ul>
            {link_items(pairs)}
          </ul>
        </details>
      </li>"""

    return f"""
<nav class="site-nav">
  <a class="brand" href="index.html">
    {LOGO_NAV}
    <span class="brand-text"><strong>BLAISE BAPTIST</strong><span>Mocksville, NC</span></span>
  </a>
  <input type="checkbox" id="nav-toggle" class="nav-toggle-input">
  <label for="nav-toggle" class="nav-toggle" aria-label="Toggle menu">
    <span></span><span></span><span></span>
  </label>
  <label for="nav-toggle" class="nav-backdrop" aria-hidden="true"></label>
  <div class="nav-drawer">
    <label for="nav-toggle" class="nav-close" aria-label="Close menu">&times;</label>
    <ul class="nav-links">
      {link_items(NAV_ITEMS)}
      {dropdown("About", ABOUT_ITEMS)}
      {dropdown("Ministries", MINISTRY_ITEMS)}
      {link_items(NAV_ITEMS_AFTER)}
      <li>{modal_link(LINKS['give'], 'Give', 'btn btn-outline')}</li>
    </ul>
  </div>
</nav>
"""


FOOTER = f"""
<footer>
  <div class="wrap">
    <div>
      {LOGO_FOOTER}
      <h4>Blaise Baptist Church</h4>
      <p>Rooted in Christ &bull; Growing Together &bull; Reaching Others</p>
      <p>A disciple-making church in Mocksville, NC &mdash; Davie County.</p>
    </div>
    <div>
      <h4>Visit</h4>
      <ul>
        <li>134 Blaise Church Rd<br>Mocksville, NC 27028</li>
        <li><a href="{LINKS['directions']}" target="_blank" rel="noopener">Get Directions</a></li>
        <li><a href="tel:3367513639">(336) 751-3639</a></li>
        <li><a href="mailto:info@blaisebaptist.org">info@blaisebaptist.org</a></li>
      </ul>
    </div>
    <div>
      <h4>Connect</h4>
      <ul>
        <li><a href="events.html">Events &amp; Calendar</a></li>
        <li><a href="small-groups.html">Small Groups</a></li>
        <li><a href="{LINKS['give']}" target="_blank" rel="noopener">Give</a></li>
        <li><a href="contact.html">Contact Us</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom wrap">
    <span>&copy; 2026 Blaise Baptist Church</span>
    <span><a href="{LINKS['facebook']}" target="_blank" rel="noopener">Facebook</a> &middot; <a href="{LINKS['youtube']}" target="_blank" rel="noopener">YouTube</a></span>
  </div>
</footer>
"""

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Blaise Baptist Church</title>
<meta name="description" content="{description}">
{head_extra}<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
<script src="https://js.churchcenter.com/modal/v1"></script>
<script src="assets/events.js" defer></script>
<script src="assets/nav.js" defer></script>
</head>
<body>
{nav}
<main>
{content}
</main>
{footer}
</body>
</html>
"""


def render(path, title, description, content, head_extra=""):
    html = PAGE_TEMPLATE.format(
        title=title,
        description=description,
        head_extra=head_extra,
        nav=nav(path),
        content=content,
        footer=FOOTER,
    )
    with open(os.path.join(DIST, path), "w") as f:
        f.write(html)


def build():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copy(os.path.join(SRC, "styles.css"), os.path.join(DIST, "styles.css"))
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(DIST, "assets"))
    for path, title, description, content_fn in PAGES:
        render(path, title, description, content_fn())
    # Reachable by direct URL only: not in the nav, footer, or any page, and kept out of search.
    for path, title, description, content_fn in UNLISTED_PAGES:
        render(path, title, description, content_fn(), '<meta name="robots" content="noindex, nofollow">\n')
    print(f"Built {len(PAGES) + len(UNLISTED_PAGES)} pages into {DIST}")


def directions_block():
    return f"""<div class="map-block">
      <iframe class="map-embed" src="{LINKS['map_embed']}" title="Map to Blaise Baptist Church" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
      <div class="map-info">
        <h3>Blaise Baptist Church</h3>
        <p>134 Blaise Church Rd<br>Mocksville, NC 27028</p>
        <a class="btn btn-primary" href="{LINKS['directions']}" target="_blank" rel="noopener">Get Directions</a>
      </div>
    </div>"""


def campus_svg(filename, label):
    """Inline one of the campus SVGs, making every data-building shape a focusable, labelled button."""
    with open(os.path.join(SRC, filename)) as f:
        svg = re.sub(r"<!--.*?-->\s*", "", f.read(), flags=re.S)
    svg = re.sub(r'<svg class="([^"]+)"', lambda m: f'<svg class="{m.group(1)}" role="group" aria-label="{label}"', svg, count=1)

    def button(m):
        b = BUILDINGS_BY_ID.get(m.group(1))
        if not b:
            raise SystemExit(f"{filename}: unknown building id {m.group(1)!r}")
        name = html.escape(f'{b["name"]} ({b["number"]})')
        classes = " ".join(["campus-building"] + re.findall(r'class="([^"]*)"', m.group(2) or ""))
        return f'data-building="{b["id"]}" class="{classes}" tabindex="0" role="button" aria-pressed="false" aria-label="{name}"'

    return re.sub(r'data-building="([a-z-]+)"( class="[^"]*")?', button, svg)


def campus_map():
    svg = campus_svg("campus-map.svg", "Campus map. Select a building for details.")
    inset = campus_svg("underground-inset.svg", "Inset: Youth Underground, lower level of the Educational Building.")
    for b in BUILDINGS:
        if f'data-building="{b["id"]}"' not in svg:
            raise SystemExit(f"campus-map.svg has no shape for building {b['id']!r}")
    data = {
        b["id"]: {
            "name": b["name"],
            "number": b["number"],
            "description": b["description"],
            "hover": b["hover"],
            "ministries": [{"name": html.unescape(n), "url": pg, "when": html.unescape(w)} for n, pg, bid, w in MINISTRY_LOCATIONS if bid == b["id"]],
        }
        for b in BUILDINGS
    }
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<section id="campus-map" class="campus-section">
  <div class="wrap">
    <h2>Campus Map</h2>
    <p class="campus-intro">Select a building on the map to see its name, details, and the ministries that meet there.</p>
    <div class="campus-map">
      <div class="campus-canvas">
        {svg}
        <figure class="campus-inset" id="campus-inset" hidden>{inset}<figcaption>Inset: lower level of the Educational Building (300)</figcaption></figure>
        <div class="campus-tip" role="tooltip" hidden></div>
      </div>
      <aside class="campus-panel" id="campus-panel" aria-labelledby="campus-panel-title" hidden>
        <button type="button" class="campus-panel-close" aria-label="Close building details">&times;</button>
        <span class="campus-panel-number"></span>
        <h3 id="campus-panel-title"></h3>
        <p class="campus-panel-desc"></p>
        <h4>Regular ministries</h4>
        <ul class="campus-panel-list"></ul>
      </aside>
    </div>
  </div>
  <script type="application/json" id="campus-data">{data_json}</script>
  <script src="assets/campus-map.js" defer></script>
</section>"""


def serve_callout(area):
    return f"""<div class="callout" style="margin-top:40px;">
      <h3>Want to serve with {area}?</h3>
      <p>We'd love to have you on the team. Let us know you're interested and we'll follow up.</p>
      {modal_link(LINKS['serving_form'], "I'm Interested in Serving")}
    </div>"""


# ---------------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------------

def home():
    return f"""
<section class="stripe stripe-home">
  <div class="wrap" style="text-align:center;">
    <h2 class="tagline"><span class="t-sage">Rooted in Christ.</span> <span class="t-teal">Growing Together.</span> <span class="t-gold">Reaching Others.</span></h2>
  </div>
</section>

<div class="hero-photo">
  <img src="assets/hero-church.webp" srcset="assets/hero-church-900.webp 900w, assets/hero-church.webp 2000w" sizes="100vw" width="2000" height="741" alt="The Blaise Baptist Church building">
</div>

<section class="section-tight section-soft">
  <div class="wrap">
    <h2>Sunday Mornings</h2>
  </div>
  <div class="wrap grid-2">
    <div class="schedule-row pane-teal"><span class="time">9:30 AM</span><div><strong>Bible Fellowship</strong><br>Classes for every age</div></div>
    <div class="schedule-row pane-gold"><span class="time">10:30 AM</span><div><strong>Worship Service</strong><br>Family Life Center &mdash; streamed live on Facebook &amp; YouTube starting at 10:20am</div></div>
  </div>
  <div class="wrap">
    <div class="hero-actions">
      <a class="btn btn-primary" href="about.html">Plan Your Visit</a>
      <a class="btn btn-outline" href="{LINKS['youtube']}" target="_blank" rel="noopener">Watch Online</a>
    </div>
  </div>
</section>


<section>
  <div class="wrap">
    <span class="eyebrow">Upcoming</span>
    <h2>What's happening at Blaise</h2>
    <p>See the full calendar and sign up for anything below &mdash; everything's handled through Church Center.</p>
    <div class="grid-3" data-pco="home" data-limit="3">
      <div class="event-card"><h3>See what's coming up</h3><p>Our full calendar and registrations live on Church Center.</p><a class="btn btn-primary" href="{LINKS['calendar']}" target="_blank" rel="noopener">Open the Calendar</a></div>
    </div>
    <p style="margin-top:24px;"><a class="btn btn-outline" href="events.html">See All Events &amp; the Full Calendar</a></p>
  </div>
</section>

<section class="section-tight section-soft">
  <div class="wrap card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">
    <div>
      <h3 style="margin-bottom:4px;">Blaise Childcare</h3>
      <p style="margin:0;">Before &amp; after school care and summer day camp in a Christian environment.</p>
    </div>
    <div class="hero-actions" style="margin:0;">
      {plain_link(LINKS['childcare_registration'], "Enroll Your Child")}
      <a class="btn btn-outline" href="childcare.html">Learn More</a>
    </div>
  </div>
</section>
"""


def about():
    staff = [
        ("Rev. Ken Furches", "Senior Pastor", "ken.furches@blaisebaptist.org"),
        ("Michael Hanna", "Youth Director", "michael.hanna@blaisebaptist.org"),
        ("Kristen Hollars", "Children's Outreach Director", "kristen.hollars@blaisebaptist.org"),
    ]
    staff_cards = "\n".join(
        f'<div class="card"><h3>{name}</h3><p style="margin-bottom:4px;">{role}</p><a href="mailto:{email}">{email}</a></div>'
        for name, role, email in staff
    )
    faqs = [
        ("What should I wear?", "Casual and comfortable. For many that's business casual, for some a suit, for others jeans and a t-shirt. What matters most is the attitude of your heart."),
        ("What's the worship style?", "A praise team leads a mix of hymns, praise songs, and contemporary music &mdash; instrumentation varies, but the focus is always on exalting Jesus."),
        ("What Bible translation do you use?", "No single required version. Our Bible Fellowship teachers use KJV, NKJV, ESV, CSB, or NIV, whichever they prefer."),
    ]
    faq_html = "\n".join(f'<div class="card"><h3>{q}</h3><p style="margin:0;">{a}</p></div>' for q, a in faqs)
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">About Blaise</span>
    <h1>Who we are, and why we're here.</h1>
    <p>An autonomous Southern Baptist Convention church, devoted to making disciples who are rooted in Christ, growing together, and reaching people. Our beliefs align with the Baptist Faith and Message.</p>
  </div>
</div>

<section>
  <div class="wrap">
    <h2>Our Staff</h2>
    <div class="grid-3">{staff_cards}</div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap">
    <h2>Sunday Mornings</h2>
  </div>
  <div class="wrap grid-2">
    <div class="schedule-row pane-teal"><span class="time">9:30 AM</span><div><strong>Bible Fellowship</strong></div></div>
    <div class="schedule-row pane-gold"><span class="time">10:30 AM</span><div><strong>Worship</strong><br><a href="{map_url('family-life-center')}">Family Life Center</a></div></div>
  </div>
</section>

<section>
  <div class="wrap">
    <h2>Frequently Asked Questions</h2>
    <div class="grid-3">{faq_html}</div>
  </div>
</section>

{campus_map()}

<section class="section-soft">
  <div class="wrap">
    <h2>Getting Here</h2>
    {directions_block()}
  </div>
</section>
"""


def students():
    return f"""
<div class="page-hero" style="background:var(--youth);">
  <div class="wrap hero-icon-row">
    {ICON_YOUTH_LG}
    <div>
      <span class="eyebrow" style="color:#fff;">Middle &amp; High School</span>
      <h1 style="color:#fff;">Blaise Youth</h1>
      <p style="color:#fff;">Built for the real terrain of the teen years &mdash; a community that challenges students to keep climbing toward Christ.</p>
    </div>
  </div>
</div>
<section>
  <div class="wrap">
    <p>Blaise Youth (Y4J &mdash; Youth 4 Jesus) is for 6th grade through high school seniors. We're focused on growing into vibrant, enthusiastic followers of Jesus Christ &mdash; studying the Bible, praying for each other, ministering to people, playing games, and going on mission trips from Davie County to South America.</p>
    <div class="schedule-row"><span class="time">Sundays</span><div><strong>Bible Fellowship</strong><br>9:30 AM</div></div>
    <div class="schedule-row"><span class="time">Wednesdays</span><div><strong>Youth Night</strong><br>6:30&ndash;7:45 PM</div></div>
    {find_on_map("students.html")}
    {serve_callout("Blaise Youth")}
  </div>
</section>
"""


def children():
    return f"""
<div class="page-hero" style="background:var(--kids);">
  <div class="wrap hero-icon-row">
    {ICON_CHILDREN_LG}
    <div>
      <span class="eyebrow" style="color:#fff;">Birth &ndash; 5th Grade</span>
      <h1 style="color:#fff;">Blaise Kids</h1>
      <p style="color:#fff;">A safe, joyful place where children are rooted in faith from the earliest age.</p>
    </div>
  </div>
</div>
<section>
  <div class="wrap">
    <h2>Sundays</h2>
    <div class="schedule-row"><span class="time">9:30&ndash;10:30</span><div><strong>Bible Fellowship Classes</strong><br>Nursery (infant&ndash;3yrs) &middot; Pre-K&ndash;2nd Grade &middot; 3rd&ndash;5th Grade</div></div>
    <div class="schedule-row pane-gold"><span class="time">10:30 AM</span><div><strong>Worship Hour</strong><br>Nursery, plus Children's Church for ages 4&ndash;1st grade</div></div>
    <h2 style="margin-top:40px;">Wednesdays, 6:30&ndash;7:45 PM</h2>
    <div class="schedule-row"><span class="time">Mission Friends</span><div>Age 3 (potty trained) &ndash; Kindergarten</div></div>
    <div class="schedule-row"><span class="time">Mission Journey</span><div>1st&ndash;5th Grade</div></div>
    {find_on_map("children.html")}
    <div class="callout" style="margin-top:32px;">
      <h3>Celebrating a Parent/Child Dedication?</h3>
      <p>Child Dedication is a chance to publicly give thanks for your child and commit, with the congregation, to raise them in the Lord.</p>
      {modal_link(LINKS['dedication_form'], "I'm Interested")}
    </div>
    {serve_callout("Blaise Kids")}
  </div>
</section>
"""


def senior_adults():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Senior Adults</span>
    <h1>Good Life</h1>
    <p>Our senior adult ministry at Blaise Baptist Church.</p>
  </div>
</div>
<section>
  <div class="wrap">
    <h2>Coming Soon</h2>
    <p>This page will be updated soon with all of the details about our senior adults ministry, which we call <strong>Good Life</strong>.</p>
  </div>
</section>
"""


def small_groups():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Get Connected</span>
    <h1>Small Groups</h1>
    <p>Getting involved in a community of believers at Blaise is easy &mdash; there's a group for every season of life.</p>
  </div>
</div>
<section>
  <div class="wrap">
    <div class="grid-4">
      <div class="ministry-card mc-women">{ICON_WOMEN}<h3>Women</h3><p>Bible studies &amp; ministry teams</p></div>
      <div class="ministry-card mc-men">{ICON_MEN}<h3>Men</h3><p>Man Church &amp; discipleship groups</p></div>
      <div class="ministry-card mc-youth">{ICON_YOUTH}<h3>Students</h3><p>Wednesday nights, 6:30&ndash;7:45</p></div>
      <div class="ministry-card mc-kids">{ICON_CHILDREN}<h3>Families</h3><p>Parents of Youth &amp; more</p></div>
    </div>
    <div class="callout" style="margin-top:32px;text-align:center;">
      <h3>See every group &amp; find one that fits</h3>
      <p>Our full group directory &mdash; men's, women's, college &amp; young adult, Bible studies, and ministry teams &mdash; lives on Church Center.</p>
      <a class="btn btn-primary" href="{LINKS['groups']}" target="_blank" rel="noopener">Browse All Groups</a>
    </div>
    <div class="callout" style="margin-top:24px;text-align:center;">
      <h3>Interested in leading a group?</h3>
      <p>Let us know &mdash; at your home or on the Blaise campus.</p>
      {modal_link(LINKS['serving_form'], "I'm Interested in Leading")}
    </div>
  </div>
</section>
"""


def childcare():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Before &amp; After School Care &amp; Summer Day Camp</span>
    <h1>Blaise Childcare</h1>
    <p>Safe, dependable care for grades K&ndash;8 in a Christian environment &mdash; during the school year and all summer long.</p>
    <div class="hero-actions">
      {plain_link(LINKS['childcare_registration'], "Enroll Your Child")}
      <a class="btn btn-outline" href="tel:3366958937">Call 336-695-8937</a>
    </div>
  </div>
</div>
<section>
  <div class="wrap grid-2">
    <div class="card">
      <h3>Before &amp; After School Care</h3>
      <p>Grades K&ndash;8 during the school year. Safe, reliable transportation from multiple schools, quality counselors, homework help, and activities in a biblical, value-based environment.</p>
      <p>Questions? Director Kristen Hollars: <a href="tel:3366958937">336-695-8937</a></p>
    </div>
    <div class="card">
      <h3>Summer Day Camp</h3>
      <p>Rising kindergarten through completed 8th grade. Bible lessons, worship, swimming, sports, crafts, and field trips &mdash; with the older grades grouped separately so camp fits middle schoolers too.</p>
      <p>Pricing: <a href="mailto:childcare@blaisebaptist.org">childcare@blaisebaptist.org</a></p>
    </div>
  </div>
  <div class="wrap" style="margin-top:32px;">
    <div class="callout">
      <h3>Questions before you enroll?</h3>
      <p>Email <a href="mailto:childcare@blaisebaptist.org">childcare@blaisebaptist.org</a> or call Kristen
      at <a href="tel:3366958937">336-695-8937</a> and we'll walk you through it.</p>
      {plain_link(LINKS['childcare_registration'], "Enroll Your Child")}
    </div>
  </div>
</section>
"""


def celebrate_recovery():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Hurts, Habits &amp; Hang-Ups</span>
    <h1>Celebrate Recovery</h1>
    <p>If you have a desire to see broken people transformed by the power of Christ, come check out CR &mdash; a biblical and balanced program that helps us overcome our hurts, hang-ups, and habits.</p>
  </div>
</div>
<section>
  <div class="wrap">
    <p>The principles of CR are based on the actual words of Jesus rather than psychological theory. Celebrate Recovery launched at Saddleback Church 25 years ago with 43 people &mdash; today it's in over 29,000 churches worldwide.</p>
    <p style="font-style:italic;color:var(--sage);">"But we will give ourselves continually to prayer, and to the ministry of the word." &mdash; Acts 6:4</p>
    <h2 style="margin-top:32px;">Tuesdays</h2>
    <div class="schedule-row"><span class="time">6:00 PM</span><div>Supper (suggested $3 donation)</div></div>
    <div class="schedule-row"><span class="time">7:00 PM</span><div>Worship / Large Group (personal testimony, music)</div></div>
    <div class="schedule-row"><span class="time">8:00 PM</span><div>Open Share Small Groups &mdash; Men's Addictions, Women's Addictions, Men's A&ndash;Z, Women's A&ndash;Z</div></div>
    <div class="schedule-row"><span class="time">9:00 PM</span><div>Solid Rock Cafe &mdash; coffee, desserts, fellowship, mentoring</div></div>
    {find_on_map("celebrate-recovery.html")}
    {serve_callout("Celebrate Recovery")}
  </div>
</section>
"""


def missions():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Local &amp; Global</span>
    <h1>Missions</h1>
    <p>Blaise supports missions right here in Davie County and around the world &mdash; our students have traveled as far as Peru to share the Gospel.</p>
  </div>
</div>
<section>
  <div class="wrap callout" style="text-align:center;">
    <h3>Want to be part of it?</h3>
    <p>Whether it's local outreach or an international trip, let us know you're interested and we'll follow up.</p>
    {modal_link(LINKS['missions_form'], "I'm Interested in Missions")}
  </div>
</section>
<section style="padding-top:0;">
  <div class="wrap">
    {serve_callout("our missions team")}
  </div>
</section>
"""


def events():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Stay in the Loop</span>
    <h1>Events &amp; Calendar</h1>
    <p>Everything happening at Blaise lives on our Church Center calendar &mdash; browse it, subscribe, and register right there.</p>
    <a class="btn btn-primary" href="{LINKS['calendar']}" target="_blank" rel="noopener">Open the Full Calendar</a>
  </div>
</div>
<section>
  <div class="wrap">
    <h2>Open for Registration</h2>
    <div class="grid-2" data-pco="signups" data-empty="Nothing is open for registration right now &mdash; check back soon.">
      <div class="event-card"><h3>Registrations</h3><p>See everything open for sign-up on Church Center.</p><a class="btn btn-primary" href="{CC}/registrations" target="_blank" rel="noopener">View Registrations</a></div>
    </div>
    <h2 style="margin-top:48px;">Coming Up</h2>
    <div class="grid-3" data-pco="events" data-empty="No upcoming events posted yet.">
      <div class="event-card"><h3>Full calendar</h3><p>Browse every upcoming event on Church Center.</p><a class="btn btn-primary" href="{LINKS['calendar']}" target="_blank" rel="noopener">Open the Calendar</a></div>
    </div>
  </div>
</section>
"""


def contact():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">We'd Love to Hear From You</span>
    <h1>Contact Us</h1>
  </div>
</div>
<section>
  <div class="wrap grid-2">
    <div class="card">
      <h3>Have a question?</h3>
      <p>Call or email the church office and we'll get back to you.</p>
      <p><a href="tel:3367513639">(336) 751-3639</a><br><a href="mailto:info@blaisebaptist.org">info@blaisebaptist.org</a></p>
      <p>134 Blaise Church Rd<br>Mocksville, NC 27028</p>
      <p>{find_on_map("contact.html")}</p>
      <a class="btn btn-outline" href="{LINKS['directions']}" target="_blank" rel="noopener">Get Directions</a>
    </div>
    <div class="callout">
      <h3>Ready to get plugged in?</h3>
      <p>New to Blaise or looking for your place here? Fill out our Connection Form and we'll help you get connected.</p>
      {modal_link(LINKS['connection_form'], 'Fill Out the Connection Form')}
      <p style="margin-top:20px;">Interested in Baptism?</p>
      {modal_link(LINKS['baptism_form'], "I'm Interested in Baptism", "btn btn-outline")}
    </div>
  </div>
</section>
"""


def scripture_links(refs):
    """Link each reference in a "Book 1:2; 3:4; Other 5" list to Bible Gateway (NIV).
    A segment with no book name (e.g. "4:24") continues the previous book."""
    links, book = [], ""
    for seg in refs.split("; "):
        m = re.match(r"((?:I{1,3} )?[A-Z][a-z]+) (.+)", seg)
        if m:
            book, verses = m.groups()
        else:
            verses = seg
        search_book = re.sub(r"^(I{1,3}) ", lambda n: f"{len(n.group(1))} ", book)
        search = f"{search_book} {verses}".replace("&ndash;", "-").replace(" ", "")
        search = re.sub(r"(\d)[ab]\b", r"\1", search)  # "47a" -> "47"
        search = re.sub(r"^(\d?)([A-Za-z]+)", r"\1 \2 ", search).strip()
        url = f"https://www.biblegateway.com/passage/?search={quote_plus(search)}&version=NIV"
        links.append(f'<a href="{url}" target="_blank" rel="noopener">{seg}</a>')
    return "; ".join(links)


def beliefs():
    statements = [
        ("the Bible is the verbally and plenarily inspired Word of God, inerrant in its original manuscripts. The Bible is our supreme and final authority in faith and life.", "II Timothy 3:16; II Peter 1:20, 21"),
        ("in one God, eternally existing in three persons; Father, Son, and Holy Spirit.", "Genesis 1:1, 26; Matthew 28:19; John 1:1, 3; 4:24; Acts 5:3, 4; Romans 1:20; Ephesians 4:5, 6; II Corinthians 13:14"),
        ("that Jesus Christ was conceived by the Holy Spirit, and born of the Virgin Mary, and is true God and true man.", "Matthew 1:18&ndash;25; Luke 1:26&ndash;38; Romans 9:5; Titus 2:13"),
        ("that man was created in the image of God, that he sinned and thereby incurred not only physical death but also that spiritual death which is separation from God, and that all human beings are born with a sinful nature, and become guilty sinners in thought, word, and deed.", "Genesis 1:26, 27; 3:1&ndash;24; Romans 3:25; 5:12&ndash;18; I John 1:8"),
        ("that the Lord Jesus died for our sins according to the scriptures as a representative and substitutionary sacrifice; that He rose victorious from the grave on the third day; and that all who believe in Him are justified on the ground of His shed blood.", "Isaiah 53; Matthew 20:28; John 3:16; Romans 3:24&ndash;26; 5:1; I Corinthians 15:3; II Corinthians 5:21; Ephesians 1:7; I John 2:2; Matthew 28:6; Romans 10:9; I Corinthians 15:14"),
        ("in the personal and imminent return of our Lord Jesus Christ.", "Acts 1:11; I Thessalonians 4:16, 17"),
        ("that all who come by grace through faith to accept the Lord Jesus Christ are born again of the Holy Spirit and thereby become children of God.", "John 3:3, 5; 1:12, 13; James 1:18; I Peter 1:23; Ephesians 2:8, 9"),
        ("in the bodily resurrection of the just and the unjust, the everlasting joy of the saved and the everlasting conscious punishment of the lost.", "John 5:28&ndash;29; I Corinthians 15; II Corinthians 5:10; Matthew 25:31&ndash;46; Revelation 20:4&ndash;6, 11&ndash;15"),
        ("that all Christians are baptized by the Holy Spirit when they are born again. We believe that water baptism by immersion is the biblical testimony of the professed believer in the name of the Father, Son, and Holy Spirit.", "Acts 2:38&ndash;41, 47; Matthew 28:18&ndash;20; Acts 8:36&ndash;40; 10:47; 18:8; Romans 6:3, 4; I Corinthians 12:13"),
        ("that those who partake of the Lord&rsquo;s Supper should be born-again believers, walking in fellowship with the Lord Jesus Christ.", "Acts 2:42&ndash;46; I Corinthians 11:23&ndash;29"),
        ("that as Christians we are to meet together regularly for worship, ordinances, and the encouragement of each other.", "Hebrews 10:24, 25; Acts 2:42, 46, 47a"),
    ]
    items = "\n".join(
        f'<li><p><strong>We believe</strong> {text}</p><span class="refs">{scripture_links(refs)}</span></li>'
        for text, refs in statements
    )
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">About Blaise</span>
    <h1>Beliefs &amp; Core Values</h1>
    <p>We are an autonomous Southern Baptist church, and our beliefs align with the Baptist Faith and Message.</p>
  </div>
</div>
<section>
  <div class="wrap">
    <h2>Our Core Values</h2>
    <div class="grid-3">
      <div class="card value-card pane-sage"><h3>Rooted in Christ</h3><p style="margin:0;">Everything starts with Jesus and His Word.</p></div>
      <div class="card value-card pane-teal"><h3>Growing Together</h3><p style="margin:0;">Following Jesus is a community endeavor, not a solo project.</p></div>
      <div class="card value-card pane-gold"><h3>Reaching Others</h3><p style="margin:0;">From Davie County to the nations, we share the Gospel.</p></div>
    </div>
  </div>
</section>
<section class="section-soft">
  <div class="wrap">
    <h2>What We Believe</h2>
    <ol class="beliefs">
      {items}
    </ol>
    <p style="margin-top:32px;">Want to go deeper? Read the full statement of faith Southern Baptists share.</p>
    <a class="btn btn-outline" href="{LINKS['bfm']}" target="_blank" rel="noopener">The Baptist Faith &amp; Message</a>
  </div>
</section>
"""


def baptism():
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Next Steps</span>
    <h1>Baptism</h1>
    <p>A public profession of faith in Jesus Christ, and an outward expression of the inward change He has made in us.</p>
  </div>
</div>
<section>
  <div class="wrap grid-2">
    <div>
      <p>Here at Blaise Baptist Church we understand baptism to be a public profession of our faith in Jesus Christ and outward expression of the inward change that Christ has made in us.</p>
      <p>Baptism by immersion is a one-time act of obedient identification with Jesus as Lord. It serves as an outward sign of our conscious confession of repentance and faith.</p>
    </div>
    <div class="callout">
      <h3>Ready to take the next step?</h3>
      <p>Fill out the baptism form and one of our pastors will follow up with you very soon.</p>
      {modal_link(LINKS['baptism_form'], "I'm Interested in Baptism")}
    </div>
  </div>
</section>
"""


def classifieds():
    openings = [
        ("Part-Time Church Admin", "Administrative &amp; Communications Assistant, about 25 hours per week.", "assets/jobs/part-time-church-admin.pdf"),
        ("Part-Time Church Bookkeeper", "Financial record-keeping and support for the church office.", "assets/jobs/part-time-church-bookkeeper.pdf"),
    ]
    cards = "\n".join(
        f'<div class="card"><h3>{title}</h3><p>{blurb}</p><a class="btn btn-primary" href="{pdf}" target="_blank" rel="noopener">Job Description (PDF)</a></div>'
        for title, blurb, pdf in openings
    )
    return f"""
<div class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Join Our Team</span>
    <h1>Open Positions</h1>
    <p>Please find the job description below for each available position. If you're interested, download the document and follow the instructions to submit your application. We look forward to hearing from you!</p>
  </div>
</div>
<section>
  <div class="wrap grid-2">
    {cards}
  </div>
</section>
"""


PAGES = [
    ("index.html", "Home", "A place to belong. A faith worth living. Blaise Baptist Church, Mocksville, NC.", home),
    ("about.html", "About", "Staff, service times, and what to expect at Blaise Baptist Church.", about),
    ("beliefs.html", "Beliefs & Core Values", "What Blaise Baptist Church believes.", beliefs),
    ("baptism.html", "Baptism", "Baptism at Blaise Baptist Church.", baptism),
    ("students.html", "Students", "Blaise Youth (Y4J) for 6th grade through high school seniors.", students),
    ("children.html", "Children", "Blaise Kids ministry for birth through 5th grade.", children),
    ("senior-adults.html", "Senior Adults", "Good Life, the senior adult ministry at Blaise Baptist Church.", senior_adults),
    ("small-groups.html", "Small Groups", "Find a small group at Blaise Baptist Church.", small_groups),
    ("childcare.html", "Childcare", "Before and after school care and summer day camp for grades K-8 at Blaise Baptist Church in Mocksville, NC.", childcare),
    ("celebrate-recovery.html", "Celebrate Recovery", "A biblical recovery program for hurts, habits, and hang-ups.", celebrate_recovery),
    ("missions.html", "Missions", "Local and global missions at Blaise Baptist Church.", missions),
    ("events.html", "Events", "Upcoming events and the full Blaise Baptist Church calendar.", events),
    ("contact.html", "Contact", "Get in touch with Blaise Baptist Church.", contact),
]

UNLISTED_PAGES = [
    ("classifieds.html", "Open Positions", "Job openings at Blaise Baptist Church.", classifieds),
]

if __name__ == "__main__":
    build()
