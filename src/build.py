#!/usr/bin/env python3
"""Static site builder for Blaise Baptist Church. Renders PAGES into dist/."""
import os, shutil

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
    "groups": f"{CC}/groups",
    "calendar": f"{CC}/calendar",
    "give": "https://app.easytithe.com/App/Giving/blaise",
}

NAV_ITEMS = [
    ("index.html", "Home"),
    ("about.html", "About"),
]

MINISTRY_ITEMS = [
    ("students.html", "Students"),
    ("children.html", "Children"),
    ("small-groups.html", "Small Groups"),
    ("childcare.html", "Childcare"),
    ("celebrate-recovery.html", "Celebrate Recovery"),
    ("missions.html", "Missions"),
]

NAV_ITEMS_AFTER = [
    ("events.html", "Events"),
    ("contact.html", "Contact"),
]

LOGO_GREEN = '<img src="assets/logo-green.png" alt="Blaise Baptist Church" class="brand-mark">'
LOGO_INVERSE = '<img src="assets/logo-green.png" alt="Blaise Baptist Church" class="logo-inverse">'
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

    ministry_active = any(href == active for href, _ in MINISTRY_ITEMS)
    ministry_links = "\n".join(
        f'<li><a href="{href}"{active_style if href == active else ""}>{label}</a></li>'
        for href, label in MINISTRY_ITEMS
    )

    return f"""
<nav class="site-nav">
  <a class="brand" href="index.html">
    {LOGO_GREEN}
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
      <li>
        <details class="nav-dropdown">
          <summary{active_style if ministry_active else ""}>Ministries</summary>
          <ul>
            {ministry_links}
          </ul>
        </details>
      </li>
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
      {LOGO_INVERSE}
      <h4>Blaise Baptist Church</h4>
      <p>Rooted in Christ &bull; Growing Together &bull; Reaching Others</p>
      <p>A disciple-making church in Mocksville, NC &mdash; Davie County.</p>
    </div>
    <div>
      <h4>Visit</h4>
      <ul>
        <li>134 Blaise Church Rd<br>Mocksville, NC 27028</li>
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
    <span>Facebook &middot; YouTube</span>
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
<script src="https://js.churchcenter.com/modal/v1"></script>
<script src="assets/events.js" defer></script>
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


def render(path, title, description, content):
    html = PAGE_TEMPLATE.format(
        title=title,
        description=description,
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
    print(f"Built {len(PAGES)} pages into {DIST}")


# ---------------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------------

def home():
    return f"""
<section class="hero">
  <div>
    <span class="eyebrow">Mocksville, North Carolina</span>
    <h1>A place to belong.</h1>
    <p class="lede">A faith worth living.</p>
    <p>Blaise Baptist is a church in Davie County where real people are known by name, Scripture is taught straight, and following Jesus is a community endeavor &mdash; not a solo project.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="about.html">Plan Your Visit</a>
      <a class="btn btn-outline" href="https://www.facebook.com/blaisebaptist" target="_blank" rel="noopener">Watch Online</a>
    </div>
  </div>
  <div class="hero-art">{LOGO_INVERSE}</div>
</section>

<section class="section-tight section-soft">
  <div class="wrap grid-2">
    <div class="schedule-row"><span class="time">9:30 AM</span><div><strong>Bible Fellowship</strong><br>Classes for every age</div></div>
    <div class="schedule-row"><span class="time">10:30 AM</span><div><strong>Worship Service</strong><br>Family Life Center &mdash; streamed live on Facebook &amp; YouTube starting at 10:20am</div></div>
  </div>
</section>

<section class="stripe">
  <div class="wrap" style="text-align:center;">
    <h2>Rooted in Christ. Growing Together. Reaching Others.</h2>
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
      <h3 style="margin-bottom:4px;">Fun in the Son &amp; Shining Son Childcare</h3>
      <p style="margin:0;">Summer day camp and before/after school care in a Christian environment.</p>
    </div>
    <a class="btn btn-primary" href="childcare.html">Learn More</a>
  </div>
</section>
"""


def about():
    staff = [
        ("Rev. Ken Furches", "Senior Pastor", "ken.furches@blaisebaptist.org"),
        ("Michael Hanna", "Youth Pastor", "michael.hanna@blaisebaptist.org"),
        ("Kristen Hollars", "Children's Outreach Director", "kristen.hollars@blaisebaptist.org"),
        ("Jennifer Hanna", "Church Secretary", "jennifer.hanna@blaisebaptist.org"),
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
    <div class="grid-4">{staff_cards}</div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap grid-2">
    <div class="schedule-row"><span class="time">9:30 AM</span><div><strong>Bible Fellowship</strong></div></div>
    <div class="schedule-row"><span class="time">10:30 AM</span><div><strong>Worship</strong><br>Family Life Center</div></div>
  </div>
</section>

<section>
  <div class="wrap">
    <h2>Frequently Asked Questions</h2>
    <div class="grid-3">{faq_html}</div>
  </div>
</section>

<section class="stripe">
  <div class="wrap">
    <h2>Getting Here</h2>
    <p>134 Blaise Church Rd, Mocksville, NC 27028</p>
    <p>From I-40, take exit 170 onto Hwy 601 North. Turn at Blaise Church Road (beside the Citgo) &mdash; Blaise Church will be on your right.</p>
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
    <div class="schedule-row"><span class="time">10:30 AM</span><div><strong>Worship Hour</strong><br>Nursery, plus Children's Church for ages 4&ndash;1st grade</div></div>
    <h2 style="margin-top:40px;">Wednesdays, 6:30&ndash;7:45 PM</h2>
    <div class="schedule-row"><span class="time">Mission Friends</span><div>Age 3 (potty trained) &ndash; Kindergarten</div></div>
    <div class="schedule-row"><span class="time">Mission Journey</span><div>1st&ndash;5th Grade</div></div>
    <div class="callout" style="margin-top:32px;">
      <h3>Celebrating a Parent/Child Dedication?</h3>
      <p>Child Dedication is a chance to publicly give thanks for your child and commit, with the congregation, to raise them in the Lord.</p>
      {modal_link(LINKS['dedication_form'], "I'm Interested")}
    </div>
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
    <span class="eyebrow">Before/After School Care &amp; Summer Day Camp</span>
    <h1>Childcare at Blaise</h1>
  </div>
</div>
<section>
  <div class="wrap grid-2">
    <div class="card">
      <h3>Shining Son</h3>
      <p><strong>Before &amp; After School Care</strong> &mdash; serving multiple schools with safe, reliable transportation, quality counselors, homework help, and activities in a biblical, value-based environment. Grades K&ndash;8.</p>
      <p>Contact Director Kristen Hollars: <a href="tel:3366958937">336-695-8937</a></p>
    </div>
    <div class="card">
      <h3>Fun in the Son &amp; Summer Madness</h3>
      <p><strong>Fun in the Son</strong> Summer Day Camp is for rising kindergarten through completed 5th grade: Bible lessons, worship, swimming, sports, crafts, and field trips. <strong>Summer Madness</strong> serves completed grades 6&ndash;8 with the same spirit, built for middle schoolers.</p>
      <p>Pricing: <a href="mailto:blaisechildcare@gmail.com">blaisechildcare@gmail.com</a></p>
    </div>
  </div>
  <div class="wrap" style="margin-top:32px;">
    <div class="placeholder-note">
      Registration is opening soon here &mdash; in the meantime, contact us at <a href="mailto:blaisechildcare@gmail.com">blaisechildcare@gmail.com</a> to register.
    </div>
  </div>
</section>
"""


def celebrate_recovery():
    return """
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
      <h3>Visit or Reach Out</h3>
      <p>134 Blaise Church Rd<br>Mocksville, NC 27028</p>
      <p><a href="tel:3367513639">(336) 751-3639</a><br><a href="mailto:info@blaisebaptist.org">info@blaisebaptist.org</a></p>
    </div>
    <div class="callout">
      <h3>Have a question?</h3>
      <p>Fill out our Connection Form and we'll get back to you shortly.</p>
      {modal_link(LINKS['connection_form'], 'Fill Out the Connection Form')}
      <p style="margin-top:20px;">Interested in Baptism?</p>
      {modal_link(LINKS['baptism_form'], "I'm Interested in Baptism", "btn btn-outline")}
    </div>
  </div>
</section>
"""


PAGES = [
    ("index.html", "Home", "A place to belong. A faith worth living. Blaise Baptist Church, Mocksville, NC.", home),
    ("about.html", "About", "Staff, service times, and what to expect at Blaise Baptist Church.", about),
    ("students.html", "Students", "Blaise Youth (Y4J) for 6th grade through high school seniors.", students),
    ("children.html", "Children", "Blaise Kids ministry for birth through 5th grade.", children),
    ("small-groups.html", "Small Groups", "Find a small group at Blaise Baptist Church.", small_groups),
    ("childcare.html", "Childcare", "Shining Son before/after school care and Fun in the Son summer day camp.", childcare),
    ("celebrate-recovery.html", "Celebrate Recovery", "A biblical recovery program for hurts, habits, and hang-ups.", celebrate_recovery),
    ("missions.html", "Missions", "Local and global missions at Blaise Baptist Church.", missions),
    ("events.html", "Events", "Upcoming events and the full Blaise Baptist Church calendar.", events),
    ("contact.html", "Contact", "Get in touch with Blaise Baptist Church.", contact),
]

if __name__ == "__main__":
    build()
