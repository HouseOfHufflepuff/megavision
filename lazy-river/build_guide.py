from _shared import page, static_waterfall_bar


def table_row(label, text):
    return f'<tr><td width="25%" valign="top"><font color="#00ffff"><b>{label}</b></font></td><td><font color="#fff">{text}</font></td></tr>'


def fact_table(title, rows, alt=True):
    trs = "".join(
        f'<tr bgcolor="{"#001a33" if i % 2 == 0 else ""}">{r}</tr>' if alt else r
        for i, r in enumerate(rows)
    )
    return f"""<table width="100%" border="3" cellpadding="6" cellspacing="0" bgcolor="#003366" style="border-color:#00ffff;">
      <tr bgcolor="#000080"><td colspan="2"><font color="#ffff00" size="3"><b>{title}</b></font></td></tr>
      {trs}
    </table>"""


def para_block(paragraphs):
    return '<font color="#fff" face="Arial, Helvetica, sans-serif" size="2">' + "".join(f"<p>{p}</p>" for p in paragraphs) + "</font>"


PAGES = []


def register(filename, title, content_fn):
    PAGES.append((filename, title, content_fn))


# ---------------------------------------------------------------- history --
def history_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#127754; A HISTORY OF THE LAZY RIVER &#127754;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">from novelty pool feature to 3,000-foot arms race</font></center>

    {static_waterfall_bar("THE ORIGIN")}
    {para_block([
        "The lazy river as we know it traces back to the late 1970s, when American water parks began experimenting with slow-moving current channels as a low-intensity alternative to slides and wave pools. "
        "Wildwater Kingdom in West Mifflin, Pennsylvania is widely credited with debuting one of the very first true lazy rivers, the Emerald Pool, around 1979 -- a simple looping current channel that let guests float on inner tubes without any effort of their own.",
        "The concept spread fast through the 1980s and 1990s as water parks realized a lazy river solves a real design problem: not every guest wants a 60-foot drop slide, but almost every guest will float in a gentle loop holding a drink. It became the connective tissue of the modern water park -- the thing you do between the big rides, or the thing you do all day if you brought a cooler.",
        "By the 2000s, resort water parks and mega-parks started treating lazy river length as a bragging right in its own right, not just a filler attraction. That arms race is what produced the mile-plus loops at the top of today's leaderboard -- see our <a href=\"top-10.html\">Top 10 Longest Lazy Rivers</a> page for the current ranking, and a note on how many of these \"world's longest\" claims turned out to be marketing rather than independently certified records."
    ])}

    {static_waterfall_bar("A ROUGH TIMELINE")}
    {fact_table("&#128197; MILESTONES", [
        table_row("Late 1970s", "First true looping lazy river currents appear at American water parks."),
        table_row("1980s&ndash;90s", "Lazy rivers become a standard water park attraction category worldwide."),
        table_row("2000s", "Resort mega-parks begin competing on lazy river length and theming as a headline feature."),
        table_row("2018&ndash;2020s", "Several parks (Waco Surf, Chimelong, Siam Park, and others) separately market their own rivers as the \"world's longest\" -- see the Top 10 page for how these claims stack up against each other."),
    ])}

    <p><font size="1" color="#66ccff">Sources for the origin claim vary somewhat between parks and historians -- several 1970s-80s water parks have made similar first-lazy-river claims. We've gone with the most commonly cited account; if you have a correction, <a href="guestbook.html">sign the guestbook</a>.</font></p>
"""


register("history.html", "History of the Lazy River", history_content)


# ------------------------------------------------------------ engineering --
def engineering_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#9881; HOW A LAZY RIVER ACTUALLY WORKS &#9881;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">it is not magic, it is just a lot of pumps</font></center>

    {static_waterfall_bar("THE CURRENT")}
    {para_block([
        "A lazy river's current is almost never produced by gravity or a slope -- most loops are essentially flat. Instead, parks use one of two main propulsion methods: submerged jet nozzles positioned along the channel walls or floor that continuously push water (and everyone floating in it) in one direction, or large recirculating pumps that draw water from one point in the loop and discharge it further along, creating a steady flow.",
        "Most rivers run at a gentle 1-2.5 mph current -- fast enough that you never have to paddle, slow enough that nobody's inner tube becomes a projectile. Parks that want a more thrilling stretch (often marketed as a \"surge channel\" or \"rapids section\") simply add more jets or narrow the channel, which speeds the same volume of water up through a smaller cross-section.",
        "The water itself is filtered and treated continuously, same as a swimming pool, just at a much larger and more continuously-circulating scale given the length of the loop."
    ])}

    {static_waterfall_bar("BUILDING THE CHANNEL")}
    {fact_table("&#128295; THE BASICS", [
        table_row("Propulsion", "Submerged jets and/or recirculating pumps, not gravity"),
        table_row("Typical current speed", "1&ndash;2.5 mph, faster in \"surge\" sections"),
        table_row("Typical depth", "3&ndash;4 ft, shallow enough to stand in most spots"),
        table_row("Channel material", "Reinforced concrete or fiberglass shell, gunite finish, non-slip decking"),
        table_row("Filtration", "Continuous recirculating filtration, same principle as a swimming pool"),
    ])}
"""


register("engineering.html", "Lazy River Engineering", engineering_content)


# ------------------------------------------------------------- tubes 101 --
def tubes_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#128721; TUBES 101 &#128721;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">a field guide to the inner tube</font></center>

    {static_waterfall_bar("TUBE TYPES")}
    {fact_table("&#128721; THE LINEUP", [
        table_row("Single Tube", "The standard. One rider, one hole in the middle, maximum spinning potential."),
        table_row("Double Tube", "Two riders, figure-8 shaped, requires actual cooperation to steer, which it will not get."),
        table_row("Family Raft", "Four-plus riders, flat bottom, basically a floating living room."),
        table_row("Backrest Tube", "Single tube with an inflatable headrest, favored by people who intend to nap."),
        table_row("Mesh-Bottom Tube", "Lets your legs dangle through, cooler in the water, terrifying the first time."),
    ])}

    {static_waterfall_bar("TUBE ETIQUETTE")}
    {para_block([
        "Hold the tube handles, not your neighbor's tube handles, unless you've discussed it. Don't paddle against the current -- you will not win, and you will annoy everyone behind you. If you stop moving for a photo, expect to be gently bumped by six other tubes; this is not an insult, it's just current.",
        "Most parks require closed-toe or strapped footwear to be removed before entering, and most require riders under a certain height to wear a life vest regardless of tube type. Always check individual park rules before you float -- see our <a href=\"safety.html\">Safety</a> page."
    ])}
"""


register("tubes101.html", "Tubes 101", tubes_content)


# ------------------------------------------------------------------ safety --
def safety_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#9888; LAZY RIVER SAFETY &amp; ETIQUETTE &#9888;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">yes, you can drown in something called "lazy," pay attention</font></center>

    {static_waterfall_bar("THE RULES")}
    {fact_table("&#9888; GENERAL GUIDELINES", [
        table_row("Life vests", "Required for most children under 48in, regardless of swimming ability, at most parks."),
        table_row("Supervision", "Young children should be within arm's reach of an adult at all times, even in a \"lazy\" current."),
        table_row("Entry/exit", "Only enter and exit at designated docks and ramps, never climb the channel walls."),
        table_row("Swim direction", "Always float with the current, never swim against it -- exit and re-enter if you need to go back."),
        table_row("Health conditions", "Check with your doctor before floating if you have a cardiac condition -- the current, gentle as it is, is still continuous exertion for some riders."),
    ])}

    {static_waterfall_bar("WHY THIS MATTERS")}
    {para_block([
        "\"Lazy\" refers to the effort required, not the risk level. Drowning can happen in any body of water, and lazy rivers see real incidents every season, usually tied to unsupervised children, alcohol, or riders entering/exiting outside designated zones. Lifeguards stationed along the loop are there for a reason -- listen to them.",
        "This page is general guidance, not a substitute for the posted rules at your specific park, which vary by state, country, and insurance policy."
    ])}
"""


register("safety.html", "Safety & Etiquette", safety_content)


# ----------------------------------------------------------------- records --
def records_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#127942; WORLD RECORDS ROUNDUP &#127942;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">the numbers people actually argue about</font></center>

    {static_waterfall_bar("THE HEADLINE CLAIM")}
    {fact_table("&#127942; LONGEST LAZY RIVER (BY MOST-REPORTED LENGTH)", [
        table_row("Current #1", "River Ride, Aquaventure Waterpark, Atlantis The Palm, Dubai"),
        table_row("Reported length", "&asymp; 7,546 ft / 2.3 km"),
        table_row("Certification", "Not independently confirmed as Guinness-certified in this research pass -- see Top 10 page"),
    ])}
    <font size="1" color="#66ccff">Multiple parks on our <a href="top-10.html">Top 10 list</a> separately market themselves as "the world's longest lazy river" -- Waco Surf (Texas) is the most widely repeated of these claims in press coverage, but we could not locate a verifiable, currently-active Guinness World Records certificate for it, and the reported length has shifted over time across different sources (see the Waco Surf profile page for the full discrepancy). Treat any single "world's longest" claim, including ours, with appropriate skepticism.</font>

    {static_waterfall_bar("OTHER SUPERLATIVES")}
    {para_block([
        "Beyond outright length, water parks compete on a handful of other lazy-river-adjacent superlatives: widest channel, most themed zones along a single loop, longest continuously-operating lazy river (some 1980s-era loops are still running on original infrastructure), and highest total water volume moved per hour.",
        "Nearly all of these secondary claims are self-reported by parks in press materials rather than independently verified, so treat them as marketing rather than record book fact. See our <a href=\"top-10.html\">Top 10 Longest Lazy Rivers</a> page for the full ranking with cited sources per entry."
    ])}
"""


register("records.html", "World Records Roundup", records_content)


# ----------------------------------------------------------- best-by-region --
def best_region(region_label, region_adj, blurb):
    def fn():
        return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#127754; BEST LAZY RIVERS IN {region_label.upper()} &#127754;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">a regional guide</font></center>

    {static_waterfall_bar(region_label.upper() + " SPOTLIGHT")}
    {para_block([blurb])}

    <p><font color="#66ccff" size="2">For the full worldwide ranking by length with cited sources, see our <a href="top-10.html">Top 10 Longest Lazy Rivers</a> page -- several {region_adj} entries appear there too.</font></p>
"""
    return fn


register("best-usa.html", "Best Lazy Rivers in the USA", best_region(
    "the USA", "American",
    "The United States has more water parks, and more lazy rivers, than anywhere else in the world -- the format was essentially invented here in the late 1970s and has been iterated on for decades since, from resort mega-parks in Texas and Florida to regional parks across the Midwest. American parks tend to lean hardest into raw length and themed zones, chasing headline stats like Guinness World Records."
))
register("best-europe.html", "Best Lazy Rivers in Europe", best_region(
    "Europe", "European",
    "European water parks and resort spas favor a different lazy river philosophy: shorter loops, but heavier theming, indoor/outdoor hybrid designs for year-round use in colder climates, and integration with adjacent thermal or wellness facilities rather than pure thrill-park stacking."
))
register("best-asia.html", "Best Lazy Rivers in Asia", best_region(
    "Asia", "Asian",
    "Asia's newest mega-resorts, particularly in China, Japan, and Southeast Asia, have been building some of the largest integrated water park complexes in the world over the past two decades, frequently pairing enormous lazy river loops with resort-scale wave pools and indoor climate-controlled halls that operate regardless of season."
))


# ------------------------------------------------------------- pop culture --
def pop_culture_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#127916; LAZY RIVERS IN POP CULTURE &#127916;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">the current shows up more than you'd think</font></center>

    {static_waterfall_bar("WHERE YOU'VE SEEN IT")}
    {para_block([
        "The lazy river has become visual shorthand across film, TV, and advertising for a very specific kind of leisure: effortless, communal, slightly absurd. It shows up constantly in water park movies and summer-vacation episodes of sitcoms as the backdrop for a slow-burn conversation scene, precisely because two characters floating past each other on tubes is a naturally funny, naturally intimate staging device.",
        "Reality TV loves it for the same reason -- a lazy river forces a fixed pace and fixed proximity, which is great for capturing dialogue without a director having to block anything. It's also become a staple of resort and cruise ship marketing imagery, usually as the establishing shot that says \"you have nothing to do here, and that's the point.\"",
        "This page is intentionally general rather than a list of specific unverified movie/show appearances -- lazy rivers appear so often as generic background set dressing across so much media that attributing specific unconfirmed cameos would mostly be guesswork."
    ])}
"""


register("pop-culture.html", "Lazy Rivers in Pop Culture", pop_culture_content)


# -------------------------------------------------------------------- faq --
def faq_content():
    faqs = [
        ("Is this a real website?", "Extremely real. The facts about actual lazy rivers are researched and sourced. Everything else -- the rental packages, the firehose game, the popups -- is a joke."),
        ("Can I actually rent a lazy river?", "In real life, yes, event-scale portable lazy river rentals do exist from specialty vendors. Our specific pricing and packages on the Shop pages, however, are not real, please do not attempt to book them."),
        ("Why does this page have a jukebox?", "Because it should. It's playing real MIDI-rendered Cure songs. Use the skip button if Lullaby isn't hitting."),
        ("Are the waterfalls interactive?", "The floating ones drift around on their own. The static ones just sit there looking wet. Neither will actually get you wet, despite what the ActiveX warning implies."),
        ("Where do the images on this site come from?", "Wikimedia Commons, real freely-licensed photos, same as the rest of this site's sub-pages."),
    ]
    rows = "".join(f'<tr bgcolor="{"#001a33" if i % 2 == 0 else ""}"><td valign="top" width="35%"><font color="#ffff00"><b>Q: {q}</b></font></td><td><font color="#fff">{a}</font></td></tr>' for i, (q, a) in enumerate(faqs))
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#10067; FREQUENTLY ASKED QUESTIONS &#10067;</b></font></center>
    {static_waterfall_bar("ANSWERS")}
    <table width="100%" border="3" cellpadding="8" cellspacing="0" bgcolor="#003366" style="border-color:#00ffff;">{rows}</table>
"""


register("faq.html", "FAQ", faq_content)


# ------------------------------------------------------------------ links --
def links_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#128279; LINKS &#128279;</b></font></center>
    {static_waterfall_bar("WEBRING")}
    {para_block([
        "This page would traditionally list a bunch of other 90s personal homepages about water parks. We don't have those. Instead, here's the rest of the MEGAVISION universe:"
    ])}
    <font color="#00ffff" size="2">
    &#128167; <a href="../index.html">MEGAVISION Home</a><br>
    &#128167; <a href="../snowmobile-lifestlye.html">Snowmobile Lifestyle</a><br>
    &#128167; <a href="../soccer.html">Mega Penalty Shootout</a><br>
    &#128167; <a href="../pigeons/index.html">Pigeon Pages</a><br>
    &#128167; <a href="index.html">Lazy River Home</a><br>
    </font>
"""


register("links.html", "Links", links_content)


# -------------------------------------------------------------- webmaster --
def webmaster_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#128421; ABOUT THE WEBMASTER &#128421;</b></font></center>
    {static_waterfall_bar("BIO")}
    <table bgcolor="#222" border="3" cellpadding="10"><tr>
      <td width="140" valign="top">
        <table bgcolor="#001a33" border="2"><tr><td>
          <font color="#00ffff" size="1">[WEBCAM.JPG]<br>
          <div style="width:120px;height:120px;background:repeating-linear-gradient(45deg,#0a2a3a,#0a2a3a 4px,#001522 4px,#001522 8px);filter:hue-rotate(180deg) saturate(2);"></div>
          low-res, heavy blue tint, as required by law
          </font>
        </td></tr></table>
      </td>
      <td valign="top">
        <font color="#00ffff" size="4"><b>Hi, I'm the Lazy River Webmaster</b></font><br>
        <font color="#ccc" size="2">
        I've never actually been on a lazy river longer than about 400 feet but I have very strong opinions about
        surge channels. I built this entire sub-site using a Python script and a genuinely alarming number of
        Wikimedia Commons API calls. My favorite lazy river is whichever one has the fewest children in it.
        Email me if you have corrections to any of the facts on this site -- I did try to get them right.
        </font>
      </td>
    </tr></table>
"""


register("webmaster.html", "Webmaster", webmaster_content)


# ------------------------------------------------------------- guestbook --
def guestbook_content():
    return f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#128214; SIGN THE GUESTBOOK &#128214;</b></font></center>
    {static_waterfall_bar("LEAVE YOUR MARK")}
    <table bgcolor="#663300" cellpadding="8" border="4" width="100%" style="border-style:ridge;">
      <tr><td>
        <form action="#" onsubmit="alert('Thank you for signing! (this form does not actually go anywhere)'); return false;">
          <table cellpadding="3">
            <tr><td align="right"><font size="2" color="#fff">Name:</font></td><td><input type="text" name="name" size="30"></td></tr>
            <tr><td align="right"><font size="2" color="#fff">Favorite Lazy River:</font></td><td><input type="text" name="river" size="30"></td></tr>
            <tr><td align="right"><font size="2" color="#fff">Tube Preference:</font></td><td><input type="text" name="tube" size="30"></td></tr>
            <tr><td align="right" valign="top"><font size="2" color="#fff">Message:</font></td><td><textarea name="message" rows="4" cols="35"></textarea></td></tr>
          </table>
          <input type="submit" value="FLOAT ON!" style="background:#ffcc00;border:4px outset #fff;font-weight:bold;font-size:16px;padding:6px 20px;">
        </form>
      </td></tr>
    </table>
"""


register("guestbook.html", "Guestbook", guestbook_content)


for filename, title, content_fn in PAGES:
    page(filename, title, content_fn())

print(f"done: {len(PAGES)} guide/info pages")
