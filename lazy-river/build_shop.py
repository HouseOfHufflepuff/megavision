import json
import urllib.parse

from _shared import page, static_waterfall_bar, showcase_carousel

CB = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def img(filename, w=200, caption=None):
    url = CB + urllib.parse.quote(filename)
    cap = f'<br><font size="1" color="#66ccff">{caption}</font>' if caption else ""
    return f'<img src="{url}" width="{w}" style="border:3px outset #fff;margin:4px;" alt="event photo">{cap}'


SHOP_IMAGES = json.load(open("shop_images.json"))

# (slug, filename, nav label, title, tagline, package name, package price, sell copy paragraphs, hero image or None)
USE_CASES = [
    ("bar-mitzvah", "shop-bar-mitzvah.html", "Bar/Bat Mitzvah",
     "&#127775; THE MITZVAH RIVER PACKAGE &#127775;",
     "He's a man now. Let him float like one.",
     "The Torah-To-Tube Package", "$14,999 + tube rental",
     ["Your kid just read from the Torah in front of 200 relatives. The DJ has a fog machine. The hora is happening. And you're telling us there's NO WATER FEATURE? Unacceptable.",
      "MEGAVISION Rent-A-River drops a fully-plumbed, temporary 400ft lazy river loop directly into your venue's parking lot, banquet hall lawn, or (with proper permitting, which is between you and the fire marshal) the actual ballroom.",
      "Package includes: 400ft of looping current, a candy-tube station instead of the traditional candy bar, custom monogrammed tubes with the guest of honor's Hebrew name airbrushed on, and a lifeguard who will absolutely still ask if you've had a bar mitzvah before."],
     None),
    ("pride", "shop-pride.html", "Pride",
     "&#127752; THE PRIDE FLOAT PACKAGE &#127752;",
     "The parade ends. The river begins.",
     "The Rainbow Current Package", "$18,499",
     ["Marching is exhausting. Your feet hurt. Your glitter is migrating to places glitter should not migrate. What you need after Pride is not a nap -- it's a current gently doing the walking FOR you.",
      "The Rainbow Current Package rings your whole block party or after-party venue with a color-changing LED lazy river, synced to whatever's coming out of the DJ booth. Six water jets, one per color of stripe (we're aware there are more than six, we're working on jet seven).",
      "Comes with float-friendly flags, a full bar built directly into the inside bend of the loop, and zero judgment about how many times you go around."],
     "images/pride-river.jpg"),
    ("quinceanera", "shop-quinceanera.html", "Quinceañera",
     "&#128142; THE QUINCE COURT PACKAGE &#128142;",
     "She's not a girl. She's basically a lazy river monarch now.",
     "The Corte de Honor Package", "$16,750",
     ["Fifteen court members. One honoree. Zero reasons they should all be standing around a cake table when they could be floating in a slow, majestic, extremely photographable circle in matching sashes.",
      "We build the river loop AROUND your existing dance floor tenting, so the vals, the surprise dance, and the float session can all happen in the same footprint without anyone changing shoes twice.",
      "Package includes a tiara-safe tube design (reinforced headrest, obviously), waterproof court sashes, and a slow-motion camera rig positioned at the surge channel for maximum quinceañera-movie-trailer energy."],
     "images/quince-anos.jpg"),
    ("wedding", "shop-wedding.html", "Wedding",
     "&#128141; THE ETERNAL CURRENT PACKAGE &#128141;",
     "Till death (or the pump maintenance contract) do you part.",
     "The Eternal Current Package", "$26,000",
     ["Your officiant says \"as this river flows, so shall your love.\" Cute metaphor. Now make it LITERAL. We build an actual 500ft ceremonial loop that the wedding party floats down the aisle in, in formation, in coordinated tubes.",
      "Reception guests get the full loop; the head table gets a private VIP eddy near the surge channel so they can still hear the toasts.",
      "Package includes a champagne float station, a designated \"first float\" moment for the couple (like a first dance, but wetter), and full coordination with your existing wedding planner, who will have several follow-up questions."],
     None),
    ("corporate", "shop-corporate.html", "Corporate",
     "&#128188; THE SYNERGY LOOP PACKAGE &#128188;",
     "Nothing builds trust like being gently pushed by the same current, together.",
     "The Synergy Loop Package", "$21,300 + AV",
     ["Trust falls are dated. Escape rooms are overdone. What your Q3 offsite actually needs is a mandatory, slow-moving, inescapable current that forces the entire sales team to be in one place for 25 uninterrupted minutes.",
      "We install directly in your office courtyard, parking structure roof, or (increasingly common request) the actual atrium, current permitting notwithstanding.",
      "Package includes waterproof name badges, a branded-tube option (logo placement available on up to 40 tubes), and a facilitator who will ask everyone to share one thing they learned while floating."],
     None),
    ("birthday", "shop-birthday.html", "Birthday",
     "&#127874; THE ANOTHER-YEAR-OLDER LOOP &#127874;",
     "You only turn this age once. Float accordingly.",
     "The Birthday Bend Package", "$9,999",
     ["Bounce houses are for people who haven't discovered currents yet. This year, the birthday kid (or adult, we don't ask, we don't judge, your money is your money) gets a real, temporary, professionally-plumbed lazy river in the backyard.",
      "Scales from a modest 150ft backyard loop up to a full 800ft block-party edition if the neighbors have already been warned.",
      "Package includes a floating snack barge, a designated \"birthday lane\" with priority current boost, and balloon arch integration over the launch dock."],
     None),
    ("bachelorette", "shop-bachelorette.html", "Bachelor(ette) Party",
     "&#127864; THE LAST FLOAT PACKAGE &#127864;",
     "One last lazy river before you're legally obligated to share the remote.",
     "The Last Float Package", "$19,200",
     ["The sash. The penis straws (we don't make the merchandise, we just provide the river). The group chat that's been planning this for eight months. All of it deserves a better backdrop than a rented Airbnb hot tub.",
      "We deliver a full loop to your venue with a built-in swim-up bar, a designated \"maid/man of honor\" throne float with an actual raised seat, and current strong enough to keep the group moving without anyone having to actually paddle in heels.",
      "Package includes matching tube monograms, a waterproof phone pouch for every guest (for the inevitable photos), and a strict no-questions-asked policy on what happens on the river."],
     None),
    ("graduation", "shop-graduation.html", "Graduation",
     "&#127891; THE DIPLOMA DRIFT PACKAGE &#127891;",
     "You crossed the stage. Now cross the surge channel.",
     "The Diploma Drift Package", "$13,400",
     ["Four (or more, no judgment) years of work deserves more than a sheet cake in the backyard. Float the entire graduating friend group down a real current while everyone's parents stand around the perimeter taking too many photos.",
      "We coordinate delivery around your actual commencement schedule so the loop is ready to go the second the ceremony wraps and everyone's still in their gowns (gowns are, for the record, extremely float-compatible).",
      "Package includes a cap-toss zone at the far bend of the loop and a diploma-safe dry box mounted at the dock so nobody loses their actual degree in the current."],
     None),
    ("festival", "shop-festival.html", "Festival",
     "&#127881; THE MAIN STAGE CURRENT PACKAGE &#127881;",
     "The lineup's great. The heat is not. Fix one of those problems.",
     "The Main Stage Current Package", "$34,500 + permitting",
     ["Your festival has three stages, twelve food trucks, and zero ways to cool 3,000 overheated fans without them abandoning the crowd entirely. Solve it with a full-perimeter lazy river ring around the main stage field.",
      "Attendees float the loop while still hearing (and, depending on speaker placement, feeling) the set. No one has to choose between the music and not passing out.",
      "Package includes wristband-gated access lanes, a floating merch barge, and a current strong enough to keep 500+ people moving through without a bottleneck at the surge channel."],
     None),
    ("holiday", "shop-holiday.html", "Holiday Party",
     "&#127876; THE FROSTY CURRENT PACKAGE &#127876;",
     "Yes, it's cold outside. That's what the heated current is for.",
     "The Frosty Current Package", "$22,750",
     ["Every office holiday party has the same three problems: a sad secret santa table, someone's aux cord privileges getting revoked, and absolutely nowhere interesting to stand. We fix problem three.",
      "Our heated-current winter configuration keeps the loop a comfortable 91&deg;F even when it's snowing directly onto the surface, because yes, we know that's the whole point, MEGAVISION invented this exact combination on the Snowmobile Lifestyle page.",
      "Package includes a floating hot cocoa station, twinkle-light rigging along the entire loop, and a strict HR-approved policy on what can be worn while floating past the CEO."],
     None),
    ("lan-party", "shop-lan-party.html", "LAN Party",
     "&#128421; THE PACKET LOSS PACKAGE &#128421;",
     "Ping's high. Current's low. Perfect combo.",
     "The Packet Loss Package", "$17,250 + extension cords",
     ["Your friend group has been playing the same four games in the same basement since 2004. It's time to upgrade the venue, not the graphics card. We drop a full retro-arcade lazy river loop into the backyard, complete with floating waterproof arcade pods.",
      "Each pod houses a real, playable cabinet (Pac-Man, Galaga, Space Invaders, your call) sealed under a dome, so you can float in a circle getting your high score taken by the guy who's been \"about to log off\" for six hours.",
      "Package includes a boombox-stack sound system loud enough to be heard over the pump jets, a zebra-print tube for whoever brought the good graphics card, and a strict policy that yes, the tiger floating nearby is also part of the package, we don't fully understand it either."],
     "images/lan-party.jpg"),
    ("petting-zoo", "shop-petting-zoo.html", "Petting Zoo",
     "&#129412; THE KOOL-AID KINGDOM PACKAGE &#129412;",
     "You asked for a petting zoo. We heard you. We also did some other stuff.",
     "The Kool-Aid Kingdom Package", "$28,800 (ask about the tiger)",
     ["Somewhere between \"rent a petting zoo\" and \"rent a lazy river,\" our sales team stopped listening and just combined both, then added a full 80s pool party, a pitcher-shaped mascot, and a fully grown tiger on an inner tube. We're not proud of it. We're also not changing it.",
      "This is, technically, still a petting zoo rental: there is an animal present. It is a tiger. It is on a float. Please do not actually pet it, that clause is in the contract for a reason.",
      "Package includes neon everything, a floating cooler stocked exclusively with a suspiciously familiar red beverage, and a live guitarist who will not stop playing regardless of how the event is going."],
     "images/petting-zoo.jpg"),
]


def gallery_html(slug):
    files = SHOP_IMAGES.get(slug, [])
    rows = []
    # simple 4-per-row grid
    cell_htmls = [f"<td align='center'>{img(f, 190)}</td>" for f in files]
    for i in range(0, len(cell_htmls), 4):
        rows.append("<tr>" + "".join(cell_htmls[i:i + 4]) + "</tr>")
    return f'<table width="100%" cellpadding="4" cellspacing="0" border="0">{"".join(rows)}</table>'


def build_use_case(slug, filename, nav_label, title, tagline, pkg_name, pkg_price, paragraphs, hero_image=None):
    body_paras = "".join(f"<p>{p}</p>" for p in paragraphs)
    hero_html = (
        f'<div style="border:6px ridge #00ffff;margin-bottom:12px;">'
        f'<img src="{hero_image}" width="100%" style="display:block;" alt="{nav_label} lazy river rental"></div>'
        if hero_image else ""
    )
    content = f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>{title}</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">{tagline}</font></center>

    {hero_html}

    {static_waterfall_bar(nav_label.upper() + " RENTAL")}

    <table width="100%" border="3" cellpadding="8" cellspacing="0" bgcolor="#003366" style="border-color:#00ffff;">
      <tr bgcolor="#000080"><td><font color="#ffff00" size="4"><b>&#128176; {pkg_name}</b></font><br>
      <font color="#fff" size="3">{pkg_price} &middot; pricing is a joke, please do not send us a deposit</font></td></tr>
    </table>
    <br>
    <font color="#fff" face="Arial, Helvetica, sans-serif" size="2">
    {body_paras}
    </font>

    {static_waterfall_bar("GALLERY")}
    {gallery_html(slug)}

    <br>
    <center><font size="2" color="#00ffff"><a href="shop.html">&larr; Back to the Rent-A-River Shop</a></font></center>
"""
    page(filename, f"{nav_label} Lazy River Rental", content)


for slug, filename, nav_label, title, tagline, pkg_name, pkg_price, paragraphs, hero_image in USE_CASES:
    build_use_case(slug, filename, nav_label, title, tagline, pkg_name, pkg_price, paragraphs, hero_image)


# ------------------------------------------------------------- shop hub --
hub_cards = []
for slug, filename, nav_label, title, tagline, pkg_name, pkg_price, paragraphs, hero_image in USE_CASES:
    if hero_image:
        thumb_html = f'<img src="{hero_image}" width="150" style="border:3px outset #fff;margin:4px;" alt="{nav_label}">'
    else:
        thumb = SHOP_IMAGES.get(slug, [None])[0]
        thumb_html = img(thumb, 150) if thumb else ""
    hub_cards.append(f"""
    <td align="center" valign="top" width="20%" style="padding:6px;">
      <table bgcolor="#001a33" border="2" cellpadding="6" style="border-color:#0099cc;">
        <tr><td align="center">
          {thumb_html}<br>
          <font color="#ffff00" size="2"><b>{nav_label}</b></font><br>
          <font color="#66ccff" size="1">{pkg_price}</font><br>
          <a href="{filename}"><font color="#00ffff" size="1">RENT THIS &rarr;</font></a>
        </td></tr>
      </table>
    </td>""")

rows = []
for i in range(0, len(hub_cards), 5):
    rows.append("<tr>" + "".join(hub_cards[i:i + 5]) + "</tr>")

hub_content = f"""
    <center><font face="Arial Black, Impact" size="7" color="#ffff00"><b class="blk">RENT-A-RIVER</b></font></center>
    <center><font face="Courier New, monospace" size="4" color="#00ffff">MEGAVISION's Lazy River Rental Shop &middot; bringing the current to YOU</font></center>

    {showcase_carousel("lrvShowcaseShop")}

    <font color="#fff" face="Arial, Helvetica, sans-serif" size="2">
    <p>Why rent a bounce house, a photo booth, or a taco truck when you could rent an entire looping,
    professionally-plumbed lazy river and drop it directly into your event? MEGAVISION Rent-A-River
    has spent years perfecting the logistics nobody asked us to perfect. We deliver, install, run,
    and disassemble a fully-functional lazy river loop for basically any occasion you can imagine.
    Below: twelve occasions we've already imagined for you.</p>
    </font>

    {static_waterfall_bar("PICK YOUR OCCASION")}

    <table width="100%" cellpadding="0" cellspacing="0">{"".join(rows)}</table>

    {static_waterfall_bar("HOW IT WORKS")}
    <table width="100%" border="3" cellpadding="8" cellspacing="0" bgcolor="#003366" style="border-color:#00ffff;">
      <tr bgcolor="#000080"><td colspan="3"><font color="#ffff00" size="3"><b>&#128203; THE PROCESS</b></font></td></tr>
      <tr>
        <td valign="top" width="33%"><font color="#00ffff"><b>1. You Pick a Package</b></font><br><font color="#fff" size="2">Browse the occasion cards above and choose the one closest to your event (or closest to your vibe, we won't check).</font></td>
        <td valign="top" width="33%"><font color="#00ffff"><b>2. We "Deliver"</b></font><br><font color="#fff" size="2">A fully imaginary fleet of trucks arrives with fully imaginary plumbing, jets, and tubes.</font></td>
        <td valign="top" width="33%"><font color="#00ffff"><b>3. Everyone Floats</b></font><br><font color="#fff" size="2">Your event now has a current. Nothing else about your event has changed. This is fine.</font></td>
      </tr>
    </table>
"""
page("shop.html", "Rent-A-River Shop", hub_content)

print(f"done: shop.html + {len(USE_CASES)} use-case pages")
