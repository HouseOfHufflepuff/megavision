"""
Pigeon Pages -- a 20+ page 1990s-web-anarchy fan site about keeping pigeons
as pets, covering history, breeds, war pigeons, racing, biology, and
culture. All facts sourced from Wikipedia (Domestic pigeon, War pigeon,
Pigeon racing, List of pigeon breeds, Doves as symbols); all images are
real, hotlinked from Wikimedia Commons.

Run: cd pigeons && python3 build_pigeons.py
"""
import json
import os
import urllib.parse

import _chaos as chaos
from _chaos import page, ascii_art_block, construction_zone, webmaster_bio, guestbook_form, dead_end_buttons

CB = "https://commons.wikimedia.org/wiki/Special:FilePath/"

with open("images.json") as f:
    IMAGES = json.load(f)


def img(filename, w=220, caption=None):
    # full URL-encode (not just spaces) -- some real Commons filenames carry
    # quotes, parens, ampersands etc. that would otherwise break the src="..." attribute
    url = CB + urllib.parse.quote(filename)
    cap = f'<br><font size="1" color="#ccc">{caption}</font>' if caption else ""
    return f'<img src="{url}" width="{w}" style="border:3px outset #fff;margin:4px;" alt="pigeon">{cap}'


def gallery_grid(files, w=150, cols=5):
    cells = "".join(f'<td align="center">{img(f, w)}</td>' for f in files)
    rows = []
    cells_list = [f'<td align="center">{img(f, w)}</td>' for f in files]
    for i in range(0, len(cells_list), cols):
        rows.append("<tr>" + "".join(cells_list[i:i + cols]) + "</tr>")
    return f'<table cellpadding="4" cellspacing="0" align="center">{"".join(rows)}</table>'


def h1(t):
    return f'<font size="7" color="#ffd700"><b class="blk">&#9733; {t} &#9733;</b></font><br><hr>'


def para(t):
    return f'<font size="3" color="#00ff00">{t}</font><br><br>'


PAGE_ORDER = [f for f, _ in chaos.NAV_PAGES]

# ==========================================================================
# 1. HOME
# ==========================================================================
body = f"""
{h1("WELCOME TO PIGEON PAGES")}
<center>{img(IMAGES.get("hero", IMAGES["domestic"][0]), 380, "The humble domestic pigeon: 5,000+ years of friendship with humanity")}</center>
{para("Welcome, traveler of the Information Superhighway, to <b>PIGEON PAGES</b> -- the "
      "Internet's #1 unofficial, unaffiliated, totally home-grown resource for keeping "
      "pigeons as domesticated pets!!! This site has been lovingly hand-coded across "
      "<b>20+ pages</b> covering the history, breeds, biology, war heroics, sporting glory, "
      "and cultural legacy of <i>Columba livia domestica</i> -- the domestic pigeon.")}
{para("Pigeons are one of humanity's OLDEST domesticated animals, with evidence of "
      "domestication stretching back <b>more than 5,000 years</b> to Mesopotamian cuneiform "
      "tablets and Egyptian hieroglyphs. Some researchers believe it may go back as far as "
      "<b>10,000 years</b>. That's older than the wheel in some estimates! Use the navigation "
      "frame on the left to explore the site. There is a LOT here.")}
{ascii_art_block()}
{para("<b>SITE HIGHLIGHTS:</b> Meet Cher Ami, the pigeon who saved 194 soldiers. Learn how "
      "Charles Darwin used pigeon breeding to help write <i>On the Origin of Species</i>. "
      "Discover why a pigeon named New Kim sold for <b>$1.9 MILLION DOLLARS</b>. Find out "
      "which world-famous boxer keeps a rooftop full of tumblers. It's all here. Dive in!")}
<center>
<table><tr><td>
<a href="history.html"><button style="background:#ffd700;border:4px outset #fff;font-weight:bold;padding:10px 24px;font-size:14px;">ENTER THE SITE &rarr;</button></a>
</td></tr></table>
</center>
"""
page("index.html", "Home", body, "galaxy", 0)

# ==========================================================================
# 2. HISTORY
# ==========================================================================
body = f"""
{h1("A HISTORY OF PIGEON DOMESTICATION")}
{para("Domestic pigeons descend entirely from the wild <b>rock dove</b> (<i>Columba livia</i>), "
      "and rank among humanity's very earliest domesticated birds. Genetic evidence traces "
      "their origin to the Middle East, particularly the <b>Syria&ndash;Jordan&ndash;Iraq&ndash;"
      "Arabian Peninsula</b> region, where wild rock doves nested on cliff faces -- a habit "
      "that made them naturally comfortable moving into human-built structures.")}
<center>{img(IMAGES["rockdove"][0] if IMAGES.get("rockdove") else IMAGES["domestic"][1], 300, "Columba livia -- the wild rock dove, ancestor of every pigeon breed on Earth")}</center>
{para("Pigeons were most likely domesticated first as a reliable FOOD SOURCE. Unlike many "
      "animals, they need only a steady supply of grain and water to breed successfully, and "
      "they breed FAST -- with no defined breeding season and rapid maturity, a single pair "
      "could keep a family fed indefinitely. The rocky ledges early farmers built for grain "
      "storage happened to look exactly like a rock dove's natural cliffside home.")}
{para("Around the <b>18th century</b>, a second wave of pigeon-mania swept Europe -- this time "
      "for FANCY, not food. Breeders imported exotic stock from the Middle East and South Asia "
      "and began obsessively cross-breeding for looks, producing over <b>350 distinct breeds</b> "
      "recognized today. One of these breeders was a young naturalist named Charles Darwin "
      "(see our <a href=\"famous-fanciers.html\">Famous Fanciers</a> page).")}
{para("European colonists brought pigeons to the New World as both food and messengers, "
      "introducing the species to North America around <b>1606</b> at Port Royal, Nova Scotia "
      "-- or possibly a little later at Plymouth or Jamestown. From there, escaped and released "
      "birds slowly built the feral pigeon populations that fill city squares worldwide today.")}
{construction_zone()}
"""
page("history.html", "History", body, "parchment", 1)

# ==========================================================================
# 3. WAR PIGEONS
# ==========================================================================
body = f"""
{h1("WAR PIGEONS: FEATHERED HEROES OF THE BATTLEFIELD")}
{para("For over three thousand years, militaries have trusted pigeons to carry messages no "
      "wire or radio could. <b>Cyrus the Great</b> used them across the Persian Empire in the "
      "6th century BC. <b>Julius Caesar</b> used them to reach Gaul. But it was the 19th and "
      "20th centuries that turned the war pigeon into a genuine battlefield hero.")}
<center>{img(IMAGES.get("cherami", ["Cher Ami.jpg"])[0], 260, "Cher Ami, taxidermied and on permanent display at the Smithsonian's National Museum of American History")}</center>
{para("<b>THE FRANCO-PRUSSIAN WAR (1870&ndash;71):</b> During the four-month Prussian siege of "
      "Paris, the French smuggled homing pigeons OUT of the city by hot air balloon, then flew "
      "messages back in past enemy lines. Across the siege, roughly <b>400 birds carried nearly "
      "115,000 official government messages and almost a million private ones</b>. Prussia "
      "responded by training hawks specifically to hunt French pigeons.")}
{para("<b>CHER AMI</b> is the single most famous war pigeon in history. A Blue Check cock "
      "(confirmed by DNA testing in 2021) serving with the US Army Signal Corps, Cher Ami "
      "delivered 12 critical messages during the WWI Battle of Verdun, earning the French "
      "<b>Croix de Guerre with Palm</b>. His legendary final mission came in October 1918: shot "
      "clean through the breast during the Battle of the Argonne, blinded in one eye, and "
      "with a leg hanging by a tendon, he flew <b>25 miles in 25 minutes</b> to deliver a "
      "message that saved <b>194 American soldiers</b> of the trapped 77th Infantry Division "
      "-- the famous \"Lost Battalion.\" He is taxidermied and on display at the Smithsonian "
      "to this day.")}
{para("<b>WORLD WAR II</b> saw pigeons deployed at massive scale: the US trained "
      "<b>54,000 homing pigeons</b>, with over 36,000 serving overseas across 12 Signal Pigeon "
      "Companies. Britain used roughly <b>250,000 birds</b>. The <b>Dickin Medal</b> -- the "
      "highest award for animal valor -- was given to 32 pigeons, including G.I. Joe, Winkie, "
      "Mary of Exeter, and Paddy. In one of history's stranger wartime collaborations, the Army "
      "partnered with the <b>Maidenform Brassiere Company</b> to manufacture 28,500 \"pigeon "
      "vests\" so paratroopers could carry birds hands-free into combat.")}
{para("Naval aviators achieved a stunning <b>95% message delivery success rate</b> using "
      "pigeons carried aboard aircraft -- more reliable than most radio equipment of the era. "
      "Even in the 21st century, pigeons occasionally reappear in military/intelligence "
      "contexts: Indian authorities have detained multiple pigeons suspected of carrying "
      "messages across the Pakistan border as recently as the 2010s.")}
"""
page("war-pigeons.html", "War Pigeons", body, "hazard", 2)

# ==========================================================================
# 4. FAMOUS FANCIERS
# ==========================================================================
body = f"""
{h1("FAMOUS PEOPLE WHO KEPT PIGEONS")}
{para("You are in GOOD COMPANY as a pigeon fancier. Some of history's most brilliant, "
      "talented, and dangerous people have all shared your passion:")}
<table width="100%" cellpadding="10">
<tr><td width="30%" valign="top">{img(IMAGES.get("darwin", IMAGES["domestic"][0]) if isinstance(IMAGES.get("darwin"), str) else (IMAGES.get("darwin", [IMAGES["domestic"][0]])[0]), 200)}</td>
<td valign="top">{para("<b>CHARLES DARWIN</b> began serious pigeon-breeding research in 1855 and "
"built a dedicated pigeon house in his garden. He bred them with as much obsessive attention "
"to type and color as any Victorian fancier -- but for Darwin, the birds were also DATA. His "
"detailed observations of how selective breeding could reshape a species over generations "
"became a key building block for <i>On the Origin of Species</i>.")}</td></tr>
<tr><td width="30%" valign="top">{img(IMAGES["domestic"][2] if len(IMAGES.get("domestic", [])) > 2 else IMAGES["domestic"][0], 200)}</td>
<td valign="top">{para("<b>NIKOLA TESLA</b> loved pigeons -- genuinely, deeply loved them. He fed "
"the pigeons of Central Park a special seed mix prepared by the chef at the Hotel New Yorker, "
"where he lived, and would bring injured birds up to his hotel room to nurse them back to "
"health. Tesla once said he loved one particular white pigeon \"as a man loves a woman.\"")}</td></tr>
<tr><td width="30%" valign="top">{img(IMAGES["domestic"][3] if len(IMAGES.get("domestic", [])) > 3 else IMAGES["domestic"][0], 200)}</td>
<td valign="top">{para("<b>MIKE TYSON</b> is today's most visibly enthusiastic celebrity pigeon "
"fancier. He's bred pigeons since boyhood in Brooklyn, belonged to the Eastern Tumbler Club, "
"and still raises Flights, Rollers, and Clean Leg Tumblers on a New York rooftop.")}</td></tr>
<tr><td width="30%" valign="top">{img(IMAGES["fantail"][0] if IMAGES.get("fantail") else IMAGES["domestic"][0], 200)}</td>
<td valign="top">{para("<b>PABLO PICASSO</b> kept Fantail pigeons and loved them so much he named "
"his daughter <b>Paloma</b> -- Spanish for \"pigeon.\" His peace dove lithograph (see our "
"<a href=\"mythology.html\">Myth &amp; Culture</a> page) became one of the most reproduced "
"images of the 20th century.")}</td></tr>
<tr><td width="30%" valign="top">{img(IMAGES["jacobin"][0] if IMAGES.get("jacobin") else IMAGES["domestic"][0], 200)}</td>
<td valign="top">{para("<b>QUEEN ELIZABETH II</b> maintained royal pigeon lofts at Sandringham "
"-- a tradition started by her grandfather King George V after King Leopold II of Belgium "
"gifted breeding stock to the Royal Family in 1886. Her favorite breed: the Jacobin.")}</td></tr>
</table>
"""
page("famous-fanciers.html", "Famous Fanciers", body, "checkerplate", 3)

# ==========================================================================
# 5. FAMOUS PIGEONS
# ==========================================================================
body = f"""
{h1("FAMOUS PIGEONS IN HISTORY")}
{para("Not every hero wears a cape. Some have feathers. Here are history's most legendary "
      "individual pigeons:")}
{para("<b>CHER AMI</b> (WWI) &mdash; delivered the message that saved the \"Lost Battalion,\" "
      "197 US soldiers, despite being shot through the chest. Croix de Guerre recipient. See our "
      "full <a href=\"war-pigeons.html\">War Pigeons</a> page.")}
{para("<b>G.I. JOE</b> (WWII) &mdash; an American pigeon credited with saving the lives of over "
      "1,000 British troops by delivering a message that stopped a planned bombing raid on an "
      "already-captured town in Italy. Dickin Medal recipient (1946) and later awarded the "
      "Animals in War &amp; Peace Medal of Bravery in 2019.")}
{para("<b>WINKIE</b> (WWII) &mdash; one of the very first Dickin Medal recipients, Winkie flew "
      "over 100 miles back to her Scottish loft after her aircraft ditched in the North Sea, "
      "her exhausted, oil-soaked arrival alerting rescuers to search in time to save the crew.")}
{para("<b>MARY OF EXETER</b> (WWII) &mdash; survived being shot at, attacked by hawks, and "
      "injured in bombing raids across multiple missions, earning the Dickin Medal in 1945 "
      "for sheer battlefield endurance.")}
{para("<b>NEW KIM</b> (modern era) &mdash; not a war hero, but a RECORD BREAKER: this Belgian "
      "racing hen was sold at auction in November 2020 for a jaw-dropping "
      "<b>$1.9 MILLION DOLLARS</b> to a Chinese bidder, the most expensive pigeon ever sold.")}
<center>{img(IMAGES.get("racing", [IMAGES["domestic"][0]])[0], 300, "Racing pigeons -- the same bloodlines that produced record-breaking auction birds like New Kim")}</center>
{dead_end_buttons()}
"""
page("famous-pigeons.html", "Famous Pigeons", body, "flag", 4)

# ==========================================================================
# 6. FANCY BREEDS I
# ==========================================================================
body = f"""
{h1("FANCY PIGEON BREEDS -- PART I")}
{para("Of the 350+ recognized pigeon breeds, the \"fancy\" or exhibition breeds are bred purely "
      "for looks -- and some of them look almost nothing like a pigeon at all.")}
<table width="100%"><tr>
<td width="50%" valign="top">{img(IMAGES["fantail"][0] if IMAGES.get("fantail") else IMAGES["domestic"][0], 260)}
{para("<b>FANTAIL</b> &mdash; instantly recognizable by its dramatically fanned, peacock-like "
"tail, held erect and spread. Fantails carry their heads pulled back so far they nearly touch "
"their own tail feathers. A favorite of Pablo Picasso.")}</td>
<td width="50%" valign="top">{img(IMAGES["jacobin"][0] if IMAGES.get("jacobin") else IMAGES["domestic"][0], 260)}
{para("<b>JACOBIN</b> &mdash; wears an elaborate feathered \"hood\" or mane around its head and "
"neck, resembling a monk's cowl (hence the name, after the Jacobin friars). Queen Elizabeth "
"II's personal favorite breed.")}</td>
</tr><tr>
<td width="50%" valign="top">{img(IMAGES.get("pouter", [IMAGES["domestic"][0]])[0], 260)}
{para("<b>ENGLISH POUTER</b> &mdash; famous for its dramatically inflated crop, which it puffs "
"up like a balloon, combined with a long, elegant, upright body. One of the oldest and most "
"exaggerated fancy breeds.")}</td>
<td width="50%" valign="top">{img(IMAGES.get("frillback", [IMAGES["domestic"][0]])[0], 260)}
{para("<b>FRILLBACK</b> &mdash; its wing and body feathers curl and frill at the edges, giving "
"it a wonderfully textured, almost curly-haired appearance unlike any other breed.")}</td>
</tr></table>
"""
page("breeds-fancy1.html", "Fancy Breeds I", body, "galaxy", 5)

# ==========================================================================
# 7. FANCY BREEDS II
# ==========================================================================
body = f"""
{h1("FANCY PIGEON BREEDS -- PART II")}
<table width="100%"><tr>
<td width="50%" valign="top">{img(IMAGES.get("tumbler", [IMAGES["domestic"][0]])[0], 260)}
{para("<b>TUMBLER</b> &mdash; bred to perform backward somersaults mid-flight, a trait rooted "
"in the natural predator-evasion instincts of wild rock doves, exaggerated into a spectacular "
"aerial display. Many regional variants exist (German Long-faced, Berlin Short-faced, etc).")}</td>
<td width="50%" valign="top">{img(IMAGES.get("modena", [IMAGES["domestic"][0]])[0], 260)}
{para("<b>MODENA</b> &mdash; a stocky, broad-chested Italian show breed prized for its huge "
"variety of color and pattern combinations, sometimes called the \"gentle giant\" of fancy "
"pigeons for its calm, friendly temperament.")}</td>
</tr><tr>
<td width="50%" valign="top">{img(IMAGES["domestic"][0], 260)}
{para("<b>ARCHANGEL</b> &mdash; displays a stunning iridescent metallic sheen across its "
"plumage, shimmering bronze, copper and gold in the light. Named for its almost supernatural "
"glow.")}</td>
<td width="50%" valign="top">{img(IMAGES["domestic"][1] if len(IMAGES["domestic"]) > 1 else IMAGES["domestic"][0], 260)}
{para("<b>OWL PIGEONS</b> &mdash; a whole family of breeds (African Owl, English Owl, Chinese "
"Owl) defined by a very short, thick beak and a compact head with large, prominent eyes -- "
"giving them an unmistakably owl-like face.")}</td>
</tr></table>
{ascii_art_block()}
"""
page("breeds-fancy2.html", "Fancy Breeds II", body, "matrix", 6)

# ==========================================================================
# 8. RACING BREEDS
# ==========================================================================
body = f"""
{h1("RACING &amp; HOMING BREEDS")}
{para("These breeds exist for one purpose: to fly home, fast, from very far away.")}
<center>{img(IMAGES.get("homing", [IMAGES["domestic"][0]])[0], 340, "The Racing Homer -- developed in 19th century Belgium and England by crossing the Smerle, French Cumulet, English Carrier, Dragoon, and Horseman")}</center>
{para("<b>RACING HOMER</b> &mdash; developed simultaneously by Belgian and English fanciers in "
      "the 1800s by crossing several older breeds. From the high-flying Cumulet, the Homer "
      "inherited its endurance; from the others, its speed and unmatched homing instinct. A "
      "trained Racing Homer can average <b>97 km/h (60 mph)</b> and has been recorded flying "
      "as far as <b>1,800 km</b> in a single race.")}
{para("<b>TIPPLER</b> &mdash; not bred to travel far, but to stay UP: Tipplers are bred purely "
      "for flight endurance, capable of hovering and circling for many hours at a stretch "
      "without landing.")}
{para("<b>DRAGOON</b> and <b>HORSEMAN</b> &mdash; two of the foundational breeds crossed to "
      "create the modern Racing Homer, prized in their own era for a combination of power, "
      "keen eyesight, and strong homing drive.")}
{para("See our <a href=\"pigeon-racing.html\">Pigeon Racing</a> page for the full story of the "
      "sport these birds built, and our <a href=\"homing-navigation.html\">Homing Navigation</a> "
      "page for the science of exactly how they find their way home.")}
"""
page("breeds-racing.html", "Racing Breeds", body, "stone", 7)

# ==========================================================================
# 9. UTILITY BREEDS
# ==========================================================================
body = f"""
{h1("UTILITY (MEAT) BREEDS")}
{para("Before pigeon-keeping was a hobby, it was often a FOOD SOURCE -- and \"utility\" breeds "
      "were purpose-built for the table, valued for size and tender young squabs rather than "
      "looks or flight.")}
<center>{img(IMAGES.get("king", [IMAGES["domestic"][0]])[0], 300, "The King Pigeon -- developed specifically for commercial squab production")}</center>
{para("<b>KING PIGEON</b> &mdash; a large, typically white breed developed specifically for "
      "commercial meat production. Its size and rapid growth made it the standard \"squab "
      "breed\" of the American pigeon meat industry.")}
{para("<b>CARNEAU</b> &mdash; a medium-to-large French breed available in red, white, and "
      "yellow, historically raised across Europe and North America for meat.")}
{para("<b>RUNT</b> &mdash; despite the name, among the LARGEST pigeon breeds in existence "
      "(American Giant Runt, Groninger Slenke). \"Runt\" is an old term for the biggest, "
      "heftiest class of utility pigeon, not a small one.")}
{para("Squabs (baby pigeons, still in the nest) are fed a substance unique to pigeons and "
      "doves called <b>crop milk</b> -- a protein- and fat-rich secretion produced by BOTH "
      "parents, unrelated to true mammalian milk but serving the same nutritional purpose.")}
"""
page("breeds-utility.html", "Utility Breeds", body, "parchment", 8)

# ==========================================================================
# 10. ANATOMY
# ==========================================================================
body = f"""
{h1("PIGEON ANATOMY &amp; BIOLOGY")}
{para("Domestic pigeons differ from their wild rock dove ancestors in several visible ways: "
      "thicker bills, larger fleshy ceres at the base of the beak, flatter head profiles, and "
      "paler eye-rings -- all side effects of centuries of selective breeding.")}
<center>{img(IMAGES["domestic"][2] if len(IMAGES["domestic"]) > 2 else IMAGES["domestic"][0], 300)}</center>
{para("<b>COLOR GENETICS:</b> Pigeons carry three main base colors -- wild-type blue, brown, "
      "and ash-red -- inherited in a sex-linked pattern. Cockbirds inherit color genes from "
      "BOTH parents, while hens only inherit color from their father. Ash-red dominates the "
      "other base colors; blue dominates brown. Wing pattern comes in four forms: bar, check, "
      "T-check, and barless.")}
{para("<b>SPECIALIZED MUTATIONS:</b> The crested-feather look (seen in Jacobins and others) "
      "traces to a recessive allele in the <i>EphB2</i> gene. Feathered feet/legs result from "
      "altered expression of the <i>PITX1</i> and <i>Tbx5</i> genes. The Pouter's inflatable "
      "crop is an inheritable, partially dominant trait more pronounced in males.")}
{para("<b>REPRODUCTION:</b> A mated pair builds a flimsy stick nest and lays exactly two eggs, "
      "incubated for <b>17 to 19 days</b>. Squabs are fed crop milk by both parents, reach "
      "adult size around 4 weeks, and fledge within about a month. Pigeons lack a defined "
      "breeding season, allowing much faster reproduction than most wild birds.")}
{para("<b>INTELLIGENCE:</b> Pigeons can be trained to tell a Picasso from a Monet (literally "
      "-- they can be trained to distinguish cubist from impressionist paintings), show real "
      "orthographic (reading-related) processing skills, basic numerical ability, and have even "
      "been trained to help detect cancer in medical scans.")}
"""
page("anatomy.html", "Anatomy", body, "checkerplate", 9)

# ==========================================================================
# 11. HOMING NAVIGATION
# ==========================================================================
body = f"""
{h1("HOW DO THEY FIND THEIR WAY HOME??")}
{para("A trained homing pigeon can find its way back to its loft from up to "
      "<b>1,000 km (620 miles)</b> away, over completely unfamiliar terrain, in conditions "
      "that would leave a human hopelessly lost. How?")}
{para("Scientists believe pigeon navigation runs on two combined systems: a <b>\"map sense\"</b> "
      "(knowing WHERE they currently are relative to home) and a <b>\"compass sense\"</b> "
      "(knowing which direction to fly). The leading theory for the map sense is "
      "<b>magnetoception</b> -- tiny magnetically-sensitive tissues in the pigeon's head that "
      "can detect Earth's magnetic field, with pigeons able to sense magnetic anomalies as "
      "faint as <b>1.86 gauss</b>. Brain regions responding to magnetic input include the "
      "posterior vestibular nuclei, dorsal thalamus, hippocampus, and visual hyperpallium.")}
<center>{img(IMAGES.get("flock", [IMAGES["domestic"][0]])[0], 320, "A flock in flight -- each bird independently tracking home")}</center>
{para("Additional/alternate cues researchers have identified: sun-compass navigation (tracking "
      "the sun's position and adjusting for time of day), star patterns for night flying, "
      "visual landmarks (rivers, roads, coastlines), low-frequency infrasound \"maps,\" "
      "polarized light patterns invisible to human eyes, and even olfactory (smell) cues.")}
{para("Modern researchers now strap tiny GPS loggers onto racing pigeons to record exact "
      "flight paths, and have found that experienced birds develop personal, often quite "
      "idiosyncratic preferred routes home -- essentially memorizing their own private roads "
      "in the sky.")}
"""
page("homing-navigation.html", "Homing Navigation", body, "matrix", 10)

# ==========================================================================
# 12. PIGEON RACING (the sport)
# ==========================================================================
body = f"""
{h1("THE SPORT OF PIGEON RACING")}
{para("Pigeon racing has been called \"the sport with a single starting gate and a thousand "
      "finish lines.\" Competing birds are trucked from their home lofts to a shared release "
      "point, often hundreds of kilometers away, then set loose all at once -- and every single "
      "one has to find its own way to a DIFFERENT finish line: its own loft.")}
<center>{img(IMAGES.get("racing", [IMAGES["domestic"][0]])[0], 320)}</center>
{para("<b>ORIGINS:</b> Organized pigeon racing may date back to at least 220 AD, and the "
      "Sultan of Baghdad ran a pigeon post system as early as 1150 AD. The MODERN sport was "
      "born in mid-19th century Belgium, where fanciers crossed several breeds to create the "
      "Racing Homer, which then spread worldwide.")}
{para("<b>HOW WINNERS ARE DECIDED:</b> It's not just who lands first -- since every bird flies "
      "a different distance to its own loft, officials calculate <b>average speed</b> (distance "
      "&divide; time) for every bird. Traditionally, handlers sealed a rubber ring from the "
      "bird's leg into a special timing clock the instant it landed; modern lofts increasingly "
      "use RFID chip rings read automatically by an antenna at the loft entrance.")}
{para("<b>BIG MONEY:</b> The most expensive pigeon ever sold, <b>New Kim</b>, went for "
      "<b>$1.9 million</b> in 2020. South Africa's Sun City Million Dollar Pigeon Race is the "
      "richest one-loft race on Earth: 4,300 birds, 25 countries, a $1.3 million prize pool, "
      "and a $200,000 top prize.")}
{para("<b>AROUND THE WORLD:</b> Belgium remains the sport's spiritual home. <b>Taiwan</b> has "
      "more racing events than anywhere else on Earth -- 2&ndash;3 million birds and nearly "
      "500,000 active racers. The US introduced the sport around 1875 and today counts roughly "
      "15,000 registered lofts. The British Royal Family raced pigeons from 1886 (a gift from "
      "King Leopold II of Belgium) until King Charles III recently ended royal patronage.")}
{para("<b>TRAINING:</b> Young birds begin flying tiny circles around the loft at 6&ndash;7 "
      "weeks old, then are gradually \"tossed\" from increasing distances to build homing "
      "confidence. Many competitive lofts use the <b>widowhood system</b>, which exploits a "
      "mated pair's reproductive bond -- separating mates except immediately after a race or "
      "training flight -- to give returning birds real urgency.")}
"""
page("pigeon-racing.html", "The Sport", body, "flag", 11)

# ==========================================================================
# 13. PIGEON POST
# ==========================================================================
body = f"""
{h1("PIGEON POST: THE ORIGINAL WIRELESS NETWORK")}
{para("Long before telegraphs, radios, or the Information Superhighway you're using RIGHT NOW "
      "to read this page, humans used pigeons as a genuine long-distance communication "
      "NETWORK -- complete with relay stations, scheduled routes, and paying customers.")}
{para("The Sultan of Baghdad organized a formal pigeon post system as early as <b>1150 AD</b>. "
      "Centuries later, before electronic communications existed, the news agency "
      "<b>Reuters</b> famously operated a pigeon service to carry stock prices between Belgium "
      "and Germany faster than any land-based courier could manage -- an early, feathery "
      "ancestor of the modern stock ticker.")}
<center>{img(IMAGES.get("pigeonpost", [IMAGES["domestic"][0]])[0], 300)}</center>
{para("During the 1870&ndash;71 Siege of Paris, pigeon post briefly became a nation's ENTIRE "
      "communications backbone: messages were photographically shrunk onto microfilm, "
      "thousands of copies loaded onto a single bird to guard against losses, and flown over "
      "Prussian lines into the besieged capital.")}
{para("See our <a href=\"war-pigeons.html\">War Pigeons</a> page for how this same messaging "
      "network was weaponized across two World Wars.")}
"""
page("pigeon-post.html", "Pigeon Post", body, "galaxy", 12)

# ==========================================================================
# 14. BUILDING LOFTS
# ==========================================================================
body = f"""
{h1("BUILDING A PIGEON LOFT")}
{para("A \"loft\" (also called a dovecote when built as freestanding architecture) is the "
      "pigeon-keeper's most important investment -- part shelter, part nursery, part homing "
      "beacon your birds will cross hundreds of kilometers to return to.")}
<center>{img(IMAGES.get("loft", [IMAGES["domestic"][0]])[0], 320)}</center>
{para("Historic dovecotes were often substantial standalone stone or brick buildings, "
      "sometimes centuries old, built with hundreds of internal nesting boxes -- a single "
      "dovecote could house well over a thousand birds and functioned as a serious food "
      "production facility for a manor estate.")}
{para("Modern hobbyist lofts are far more modest: a dry, well-ventilated, predator-proof "
      "structure with individual nesting compartments, a sheltered landing platform (\"trap\") "
      "the birds enter through, and enough floor space to prevent overcrowding and disease. "
      "Orientation matters too -- most keepers face the entrance away from prevailing winds "
      "and toward the morning sun.")}
{construction_zone()}
"""
page("building-lofts.html", "Lofts", body, "stone", 13)

# ==========================================================================
# 15. FEEDING & CARE
# ==========================================================================
body = f"""
{h1("FEEDING &amp; DAILY CARE")}
{para("Pigeons are grain-eaters at heart -- a diet of mixed seeds (corn, wheat, peas, milo, "
      "safflower) covers their core nutrition, supplemented with grit (crushed oyster shell or "
      "mineral grit) which they need to mechanically digest whole seeds in their gizzard, since "
      "pigeons -- like all birds -- have no teeth.")}
<center>{img(IMAGES["domestic"][0], 300)}</center>
{para("Fresh water must be available at all times, both for drinking and bathing -- pigeons "
      "bathe frequently and it's an important part of feather and skin health. Daily loft "
      "cleaning helps prevent the respiratory and fungal issues covered on our "
      "<a href=\"health.html\">Health</a> page.")}
{para("Nesting pairs need extra care: while raising squabs, both parents produce crop milk "
      "and need higher protein intake. Most keepers increase feed quantity and protein content "
      "noticeably during active breeding periods.")}
"""
page("feeding-care.html", "Feeding &amp; Care", body, "parchment", 14)

# ==========================================================================
# 16. HEALTH
# ==========================================================================
body = f"""
{h1("COMMON PIGEON HEALTH ISSUES")}
{para("Keeping pigeons is generally low-risk, but there are a handful of real conditions every "
      "keeper should know about -- for the birds' sake and your own.")}
{para("<b>Bird fancier's lung</b> (a.k.a. \"pigeon lung\") is a hypersensitivity pneumonitis "
      "that can affect KEEPERS, caused by repeatedly inhaling proteins from feather dust and "
      "dried droppings. Good loft ventilation and basic dust masks during cleaning go a long way.")}
{para("Pathogens to watch for include <i>Chlamydophila psittaci</i> (psittacosis), "
      "<i>Histoplasma capsulatum</i> (histoplasmosis), and <i>Cryptococcus neoformans</i> "
      "(cryptococcosis) -- all linked to accumulated droppings in poorly-cleaned lofts. Avian "
      "paramyxovirus can cause serious neurological symptoms in unvaccinated birds, and mites "
      "are a common (if less dramatic) nuisance.")}
<center>{img(IMAGES["domestic"][1] if len(IMAGES["domestic"]) > 1 else IMAGES["domestic"][0], 280)}</center>
{para("The good news: regular loft cleaning, fresh water, good ventilation, and routine "
      "observation catch the overwhelming majority of issues early. A healthy pigeon is "
      "alert, active, and has smooth, glossy plumage.")}
"""
page("health.html", "Health", body, "checkerplate", 15)

# ==========================================================================
# 17. BREEDING
# ==========================================================================
body = f"""
{h1("BREEDING &amp; GENETICS")}
{para("Pigeons mate for the long haul -- pairs typically bond for life and share incubation "
      "and squab-rearing duties roughly equally, which is part of why Charles Darwin found "
      "them such a rich subject for studying inherited traits (see "
      "<a href=\"famous-fanciers.html\">Famous Fanciers</a>).")}
<center>{img(IMAGES.get("squab", [IMAGES["domestic"][0]])[0], 280, "A squab, just days old -- pigeons hatch nearly featherless and grow astonishingly fast")}</center>
{para("A clutch is almost always exactly <b>two eggs</b>, incubated 17-19 days by both "
      "parents in shifts. Squabs are fed crop milk exclusively for their first days, then a "
      "mix of crop milk and softened seed, reaching full adult size in about 4 weeks -- a "
      "remarkably fast growth curve.")}
{para("For fanciers breeding toward a specific look, color genetics get complicated fast: "
      "three base colors (blue, brown, ash-red), sex-linked inheritance, four wing patterns, "
      "and modifier genes for spread and dilute coloring all interact. See our "
      "<a href=\"anatomy.html\">Anatomy</a> page for the full genetic rundown.")}
"""
page("breeding.html", "Breeding", body, "matrix", 16)

# ==========================================================================
# 18. BEHAVIOR
# ==========================================================================
body = f"""
{h1("BEHAVIOR &amp; INTELLIGENCE")}
{para("Pigeons are smarter than most people give them credit for. Documented abilities "
      "include distinguishing cubist from impressionist paintings, basic numerical reasoning, "
      "orthographic (letter-pattern) processing similar to early reading skills, and -- in "
      "genuine medical research trials -- learning to flag potential cancer signs in imaging "
      "scans about as accurately as trained humans.")}
<center>{img(IMAGES.get("flock", [IMAGES["domestic"][0]])[0], 300)}</center>
{para("Socially, pigeons are fiercely bonded and territorial: mated pairs defend their nest "
      "site vigorously against intruders, and flocks maintain surprisingly stable social "
      "structures and pecking orders over time.")}
{para("Feral pigeons -- the ones you see in every city square on Earth -- are almost entirely "
      "descended from escaped domestic and racing birds, not wild rock doves directly. Genetic "
      "studies show feral populations closely resemble homing pigeon bloodlines, suggesting "
      "most trace back to lost racers or abandoned lofts rather than any single wild source.")}
"""
page("behavior.html", "Behavior", body, "galaxy", 17)

# ==========================================================================
# 19. MYTHOLOGY & CULTURE
# ==========================================================================
body = f"""
{h1("PIGEONS &amp; DOVES IN MYTH, RELIGION &amp; ART")}
{para("Few animals carry as much symbolic weight across as many civilizations as the humble "
      "pigeon/dove (biologically the same bird -- \"dove\" is simply the word we reach for "
      "when talking about the sacred or symbolic version).")}
{para("<b>ANCIENT MESOPOTAMIA:</b> doves symbolized <b>Inanna-Ishtar</b>, goddess of love and "
      "war, appearing on cultic objects as far back as the 3rd millennium BC. The Greeks later "
      "carried this association to <b>Aphrodite</b>, and the Romans to <b>Venus</b> and "
      "<b>Fortuna</b>.")}
{para("<b>JUDAISM &amp; CHRISTIANITY:</b> in Genesis, Noah releases a dove to search for dry "
      "land after the Flood; it returns with an olive leaf, forever linking doves with "
      "renewal and hope. Christianity later added the dove as the visual form of the "
      "<b>Holy Spirit</b> at Jesus's baptism, cementing the dove-with-olive-branch as a "
      "universal peace symbol.")}
{para("<b>ISLAM:</b> tradition holds that a pair of pigeons (with a spider's web) helped "
      "conceal the Prophet Muhammad from pursuers during his flight to Medina, nesting at the "
      "mouth of the cave he sheltered in.")}
{para("<b>MODERN PEACE SYMBOLISM:</b> Pablo Picasso's dove lithograph, created for the 1950 "
      "World Peace Congress, became the official emblem of the World Peace Council and remains "
      "one of the most recognized peace symbols on Earth. Picasso himself was, of course, a "
      "real-life pigeon keeper -- see <a href=\"famous-fanciers.html\">Famous Fanciers</a>.")}
{ascii_art_block()}
"""
page("mythology.html", "Myth &amp; Culture", body, "parchment", 18)

# ==========================================================================
# 20-24. GALLERIES (five of them, to actually show off 897 real photos)
# ==========================================================================
gallery_pools = [
    ("domestic", "fantail", "jacobin", "pouter"),
    ("tumbler", "frillback", "modena", "king"),
    ("racing", "homing", "loft", "flock"),
    ("war", "cherami", "darwin", "dovecote", "squab", "feral"),
    ("npa", "scandaroon", "trumpeter", "owl", "nun", "archangel", "breeds", "breeder", "fancier"),
]
gallery_titles = [
    "General &amp; Fancy Breeds",
    "More Breeds &amp; Utility Birds",
    "Racing, Lofts &amp; Flocks",
    "History: War, Darwin &amp; Dovecotes",
    "Rare Breed Showcase (82-Bird Spectacular!)",
]
for gi, (pool, title) in enumerate(zip(gallery_pools, gallery_titles), start=1):
    files = []
    for key in pool:
        files.extend(IMAGES.get(key, []))
    if not files:
        files = IMAGES["domestic"]
    body = f"""
    {h1(f"PHOTO GALLERY {gi}: {title}")}
    {para(f"{len(files)} real, freely-licensed photographs from Wikimedia Commons. Click any "
          "thumbnail's alt text if your browser supports that sort of thing (most don't, this "
          "is 1997, be patient).")}
    {gallery_grid(files, w=140, cols=5)}
    """
    page(f"gallery{gi}.html", f"Gallery {gi}", body, ["matrix", "hazard", "checkerplate", "stone", "galaxy"][gi - 1], 18 + gi)

# ==========================================================================
# 25. FAQ
# ==========================================================================
body = f"""
{h1("FREQUENTLY ASKED QUESTIONS")}
{para("<b>Q: Are pigeons and doves the same bird?</b><br>A: Biologically, yes! Both belong to "
      "the family Columbidae. \"Dove\" tends to get used for smaller/white/symbolic birds and "
      "\"pigeon\" for larger ones, but there's no hard scientific line.")}
{para("<b>Q: How is a pigeon 'trained' to fly home?</b><br>A: It isn't, really -- homing is "
      "instinctual. Keepers simply raise birds AT the loft they want them to return to, then "
      "gradually release them from farther and farther away. See "
      "<a href=\"homing-navigation.html\">Homing Navigation</a>.")}
{para("<b>Q: Can pigeons really navigate by magnetic fields?</b><br>A: The leading scientific "
      "theory says yes, via specialized magnetically-sensitive tissue, combined with sun "
      "position, landmarks, and possibly smell.")}
{para("<b>Q: Is it legal to keep pigeons where I live?</b><br>A: It varies enormously by city "
      "and country -- some cities (like Chicago, for racing specifically) have restricted or "
      "banned it, others actively support pigeon fancier clubs. Check local ordinances.")}
{para("<b>Q: What do baby pigeons eat?</b><br>A: Crop milk, a protein- and fat-rich secretion "
      "produced by BOTH parent pigeons -- unrelated to mammal milk, but nutritionally similar "
      "in purpose.")}
{dead_end_buttons()}
"""
page("faq.html", "FAQ", body, "flag", 24)

# ==========================================================================
# 24. GUESTBOOK
# ==========================================================================
body = f"""
{h1("GUESTBOOK")}
{para("Been enjoying Pigeon Pages? Let us know! Sign below!!!")}
{guestbook_form()}
"""
page("guestbook.html", "Guestbook", body, "galaxy", 25)

# ==========================================================================
# 25. LINKS
# ==========================================================================
body = f"""
{h1("COOL PIGEON LINKS")}
{para("A hand-picked selection of the finest pigeon resources the Information Superhighway "
      "has to offer!!! (Note: some links may be broken. This is normal. This is the internet.)")}
<font size="3">
&#128330; <a href="https://en.wikipedia.org/wiki/Domestic_pigeon">Wikipedia: Domestic Pigeon</a> (actually works)<br>
&#128330; <a href="https://en.wikipedia.org/wiki/Pigeon_racing">Wikipedia: Pigeon Racing</a> (actually works)<br>
&#128330; <a href="#">Bob's Pigeon Loft Blueprints</a> (broken since 1998)<br>
&#128330; <a href="http://localhost/coolstuff.html">My Other Really Cool Pigeon Page</a><br>
&#128330; <a href="#">The Official Fantail Fanciers Webring</a><br>
&#128330; <a href="#">Download PigeonTracker 95 Shareware (14 day trial)</a><br>
&#128330; <a href="../soccer.html">MEGA Penalty Shootout Game</a> (actually works, also on this site!)<br>
&#128330; <a href="../snowmobile-lifestlye.html">MEGAVISION Snowmobile Lifestyle</a> (actually works)<br>
</font>
"""
page("links.html", "Links", body, "checkerplate", 26)

# ==========================================================================
# 26. WEBMASTER
# ==========================================================================
body = f"""
{h1("ABOUT THE WEBMASTER")}
{webmaster_bio()}
<br>
{para("This entire 26-page site was hand-coded in a single sitting using nothing but "
      "&lt;table&gt; tags, &lt;marquee&gt;, and pure spite for modern web design trends. All "
      "pigeon facts sourced from Wikipedia. All 200+ photographs are real, freely-licensed "
      "images hotlinked from Wikimedia Commons. No pigeons were harmed in the making of this "
      "website, several were mildly inconvenienced by being photographed.")}
"""
page("webmaster.html", "Webmaster", body, "stone", 27)

print("wrote all pigeon pages")
