"""
THE ADAM ARMSTRONG EXPERIENCE -- a deliberately unhinged 90s-web1-style fan
site. Disregards the main MEGAVISION style guide entirely: green/white/gold
soccer palette, Comic Sans, beveled tables, tons of effects, some of which
do nothing on purpose. Nine standalone pages, each generated independently
(no shared CSS file) so they feel disconnected the way real ad-hoc 90s fan
sites did.

All images are hotlinked from Wikimedia Commons (Special:FilePath, verified
live) or are real local assets committed to the repo. All bio/stat facts
are sourced from Wikipedia. Nothing here is fabricated as fact -- anything
speculative is labeled as a joke.
"""
import random

CB = "https://commons.wikimedia.org/wiki/Special:FilePath/"

# ---------------------------------------------------------------- images --

ARMSTRONG_IMAGES = [
    "Adam Armstrong 22112025 (1).jpg",
    "Adam Armstrong 22112025 (2).jpg",
    "Adam Armstrong 22112025 (3).jpg",
    "Adam Armstrong 22112025 (4).jpg",
    "Adam Armstrong and Lloyd Jones 22112025 (1).jpg",
    "Kayne Ramsay, Adam Armstrong and Lloyd Jones 22112025 (1).jpg",
    "Kayne Ramsay, Adam Armstrong and Lloyd Jones 22112025 (2).jpg",
    "Adam Armstrong and Kayne Ramsay 22112025 (1).jpg",
    "Joe Rankin-Costello and Adam Armstrong 22112025 (1).jpg",
    "Joe Rankin-Costello and Adam Armstrong 22112025 (2).jpg",
    "Joe Rankin-Costello and Adam Armstrong 22112025 (3).jpg",
    "Joe Rankin-Costello, Adam Armstrong and Conor Coventry 22112025 (1).jpg",
    "Tom Fellows and Adam Armstrong 22112025 (1).jpg",
    "Macaulay Gillesphey, Adam Armstrong, Rob Apter and Conor Coventry 22112025 (1).jpg",
    "Southampton Starting Eleven 22112025 (1).jpg",
    "Southampton Starting Eleven 22112025 (2).jpg",
    "Fulham v Southampton 22122024 (1).jpg",
    "Fulham v Southampton 22122024 (2).jpg",
    "Alex McCarthy 22112025 (2).jpg",
] + [f"Charlton Athletic v Southampton 22112025 ({n}).jpg" for n in range(1, 22)]

assert len(ARMSTRONG_IMAGES) == 40, len(ARMSTRONG_IMAGES)

DINKLAGE_IMAGES = [
    "Peter Dinklage by Gage Skidmore.jpg",
    "Peter Dinklage 2012 cropped.jpg",
    "Peter Dinklage-32.jpg",
]
GOBLIN_IMAGES = [
    "Comiccon France 2025 - Orc.jpg",
    "Montreal Comiccon 2016 - Orc (27643956974).jpg",
    "Savage Orc by farmerownia.jpg",
]

HYPE = [
    "BEHOLD!", "WITNESS THIS!", "UNREAL!", "LOOK AT THIS MAN!", "INCREDIBLE!",
    "YOU WON'T BELIEVE THIS!", "STOP WHAT YOU'RE DOING!", "THIS IS THE ONE!",
    "CHILLS!", "GOOSEBUMPS!", "HISTORY IN THE MAKING!", "PURE MAGIC!",
    "THE STUFF OF LEGEND!", "ABSOLUTE CINEMA!", "SOMEBODY CALL THE PRESS!",
    "SCREENSHOT THIS!", "FRAME THIS!", "MOUNT THIS ON YOUR WALL!",
    "SHOW YOUR GRANDCHILDREN THIS!", "THIS CHANGED EVERYTHING!",
]
SELL = [
    "This is what greatness looks like.", "This single photo could end wars.",
    "Scientists are still studying this image.", "10/10, no notes, perfection.",
    "This is why we watch football.", "Somewhere, a Southampton fan is crying tears of joy.",
    "This photo alone justifies the price of admission.",
    "We printed this out and framed it. No regrets.",
    "This is the definition of main character energy.",
    "We have watched this photo for eleven hours straight.",
    "This is going in the Louvre. We've made calls.",
    "Do NOT scroll past this without appreciating it fully.",
    "This is a certified moment.", "The goblins agree: iconic.",
    "Words cannot fully capture this. But we're trying anyway.",
]

random.seed(7)


def caption_for(filename):
    subjects = filename.rsplit(" 2", 1)[0].rsplit(" (", 1)[0]
    subjects = subjects.replace("Charlton Athletic v Southampton", "the legendary Charlton Athletic clash")
    subjects = subjects.replace("Fulham v Southampton", "the unforgettable Fulham showdown")
    subjects = subjects.replace("Southampton Starting Eleven", "THE STARTING ELEVEN ITSELF")
    subjects = subjects.replace("Alex McCarthy", "teammate and noted goalkeeper Alex McCarthy")
    hype = random.choice(HYPE)
    sell = random.choice(SELL)
    return f"{hype} {subjects}. {sell}"


# ------------------------------------------------------------------ nav ---

PAGES = [
    ("armstrong-1.html", "HOME"),
    ("armstrong-2.html", "BIO"),
    ("armstrong-3.html", "EARLY YEARS"),
    ("armstrong-4.html", "BLACKBURN"),
    ("armstrong-5.html", "SAINTS+"),
    ("armstrong-6.html", "ENGLAND"),
    ("armstrong-7.html", "STATS"),
    ("armstrong-8.html", "GALLERY"),
    ("armstrong-9.html", "FAN ZONE"),
]

PAGE_ACCENTS = [
    "#ffd700", "#ffffff", "#ffd700", "#f2c14e", "#ffffff",
    "#ffd700", "#f2c14e", "#ffffff", "#ffd700",
]

MARQUEES = [
    "&#9917; ADAM ARMSTRONG DOT COM &#9917; THE UNOFFICIAL UNAUTHORIZED FAN EXPERIENCE &#9917; 40 PHOTOS INSIDE &#9917; NOW WITH SOUND &#9917;",
    "&#9917; BIOGRAPHY ZONE &#9917; EVERYTHING YOU NEVER ASKED TO KNOW &#9917; PRESS PLAY ON THE JUKEBOX &#9917;",
    "&#9917; NEWCASTLE &#9917; COVENTRY &#9917; BARNSLEY &#9917; BOLTON &#9917; THE GRIND BEFORE THE GLORY &#9917;",
    "&#9917; BLACKBURN ROVERS &#9917; 49 GOALS &#9917; THREE HAT-TRICKS &#9917; PLAYER OF THE SEASON 2019-20 &#9917;",
    "&#9917; SOUTHAMPTON &#9917; PROMOTION HERO &#9917; WEST BROM &#9917; WOLVES &#9917; THE SAGA CONTINUES &#9917;",
    "&#9917; ENGLAND YOUTH INTERNATIONAL &#9917; TWO WORLD TITLES &#9917; ABSOLUTE UNIT &#9917;",
    "&#9917; STATS DO NOT LIE &#9917; 485 APPEARANCES &#9917; 141 GOALS &#9917; CALCULATOR REQUIRED &#9917;",
    "&#9917; 40 PHOTOGRAPHS &#9917; ZERO CHILL &#9917; ALL GAS NO BRAKES &#9917;",
    "&#9917; FAN ZONE &#9917; SIGN THE GUESTBOOK &#9917; THIS IS PAGE 9 OF 9 &#9917; YOU MADE IT &#9917;",
]


def soccer_balls(n=22):
    spans = []
    for i in range(n):
        size = random.randint(26, 64)
        left = random.uniform(2, 92)
        top = random.uniform(2, 88)
        spans.append(f'<span class="ball" id="ball{i}" style="left:{left:.1f}%;top:{top:.1f}%;font-size:{size}px;">&#9917;</span>')
    return "\n    ".join(spans), n


def easter_eggs(page_index):
    """A couple of tiny, unlabeled goblin/Dinklage images tucked in corners.
    Different pages get different eggs so they don't all look the same."""
    pool = [(f, "goblin") for f in GOBLIN_IMAGES] + [(f, "dinklage") for f in DINKLAGE_IMAGES]
    random.seed(page_index * 13 + 3)
    picks = random.sample(pool, 2)
    spots = [
        "top:6px;left:6px;", "top:6px;right:6px;", "bottom:6px;left:6px;",
        "bottom:6px;right:6px;", "top:40%;left:2px;", "top:60%;right:2px;",
    ]
    random.shuffle(spots)
    out = []
    for i, (fname, kind) in enumerate(picks):
        rot = random.randint(-25, 25)
        out.append(
            f'<img class="egg" src="{CB}{fname.replace(" ", "%20")}" alt="" '
            f'style="{spots[i]}transform:rotate({rot}deg);" loading="lazy">'
        )
    return "\n  ".join(out)


def az_style(accent):
    return f"""<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: 'Comic Sans MS', 'Comic Sans', 'Chalkboard SE', cursive;
    background:
      repeating-linear-gradient(180deg, #1a7a3c 0px, #1a7a3c 40px, #167034 40px, #167034 80px);
    color: #fff;
  }}
  a {{ color: {accent}; }}
  .stripe-top {{
    height: 10px;
    background: repeating-linear-gradient(90deg, #fff 0 20px, #0a0a0a 20px 40px);
  }}
  marquee, .fake-marquee {{
    display: block;
    background: #0a0a0a;
    color: {accent};
    font-weight: 900;
    font-size: 15px;
    padding: 8px 0;
    border-top: 3px solid #fff;
    border-bottom: 3px solid #fff;
    white-space: nowrap;
    overflow: hidden;
  }}
  .fake-marquee span {{
    display: inline-block;
    padding-left: 100%;
    animation: azMarquee 18s linear infinite;
  }}
  @keyframes azMarquee {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
  @keyframes azBlink {{ 0%, 45% {{ opacity:1; }} 50%,95% {{ opacity:0; }} 100% {{ opacity:1; }} }}
  .blink {{ animation: azBlink 1.1s steps(1) infinite; }}
  @keyframes ballSpin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}

  .ball-layer {{ position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 90; }}
  .ball {{
    position: absolute;
    animation: ballSpin 1s linear infinite;
    filter: drop-shadow(0 4px 6px rgba(0,0,0,0.6));
    transition: left 2.4s ease-in-out, top 2.4s ease-in-out;
  }}

  .egg {{
    position: fixed;
    width: 42px; height: 42px;
    object-fit: cover;
    border-radius: 50%;
    border: 2px solid #fff;
    opacity: 0.85;
    z-index: 40;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
  }}

  table.az-frame {{ width: 100%; border-collapse: collapse; background: #0a0a0a; }}
  .az-nav-cell {{
    background: repeating-linear-gradient(45deg, #0a0a0a, #0a0a0a 10px, #143 10px, #143 20px);
    border-right: 6px double #fff;
    padding: 10px 6px;
    vertical-align: top;
    width: 150px;
  }}
  .az-nav-cell a {{
    display: block;
    background: #0a0a0a;
    border: 2px outset {accent};
    color: {accent};
    text-decoration: none;
    font-weight: 900;
    font-size: 11px;
    text-align: center;
    padding: 8px 4px;
    margin-bottom: 6px;
  }}
  .az-nav-cell a.here {{ border-style: inset; background: {accent}; color: #0a0a0a; }}
  .az-content-cell {{ padding: 14px 18px; vertical-align: top; }}

  .az-title {{
    font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', sans-serif;
    font-size: 38px;
    text-align: center;
    color: #fff;
    text-shadow: 3px 3px 0 #0a0a0a, -1px -1px 0 {accent};
    margin: 10px 0;
  }}
  .az-box {{
    background: #0a0a0a;
    border: 4px ridge {accent};
    padding: 14px 16px;
    margin: 16px 0;
  }}
  .az-box h2 {{ color: {accent}; font-family: Impact, sans-serif; margin-top:0; }}
  .az-badge-row {{ display:flex; flex-wrap:wrap; gap:6px; justify-content:center; margin:14px 0; }}
  .az-badge {{
    width: 88px; height: 31px;
    display:flex; align-items:center; justify-content:center; text-align:center;
    font-size: 8px; font-weight:700; line-height:1.15; color:#000;
    border: 2px outset #eee; font-family: Tahoma, sans-serif;
  }}
  .az-huge-btn {{
    display: block;
    margin: 24px auto;
    width: 220px; height: 220px;
    border-radius: 50%;
    border: 8px solid #0a0a0a;
    background:
      radial-gradient(circle at 35% 30%, #fff 0 18%, transparent 19%),
      radial-gradient(circle at 65% 30%, #fff 0 18%, transparent 19%),
      radial-gradient(circle at 50% 65%, #fff 0 18%, transparent 19%),
      #eee;
    cursor: pointer;
    font-family: Impact, sans-serif;
    font-size: 20px;
    color: #0a0a0a;
    text-shadow: 0 1px 0 #fff;
    box-shadow: 0 0 0 6px #fff, 0 10px 24px rgba(0,0,0,0.5);
  }}
  .az-huge-btn:active {{ transform: translateY(2px); }}

  .gallery-grid {{ display:grid; grid-template-columns: repeat(auto-fill,minmax(210px,1fr)); gap:14px; }}
  .gcard {{ background:#0a0a0a; border:3px outset #eee; }}
  .gcard img {{ width:100%; height:150px; object-fit:cover; display:block; border-bottom:3px inset #eee; }}
  .gcard p {{ font-size:11px; padding:8px; margin:0; color:{accent}; }}

  .jukebox {{
    max-width: 420px; margin: 14px auto;
    background: linear-gradient(180deg,#eee,#0a0a0a 8%,#0a0a0a 92%,#eee);
    border: 3px outset #fff; border-radius: 6px; padding: 8px;
    display:flex; align-items:center; gap:8px;
  }}
  .jukebox button {{
    width:36px;height:36px;border-radius:50%;border:2px outset {accent};
    background:{accent};color:#0a0a0a;font-weight:900;cursor:pointer;
  }}
  .jukebox .meta {{ flex:1; min-width:0; }}
  .jukebox .tn {{ font-size:11px; font-weight:800; color:{accent}; font-family: ui-monospace, monospace; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .jukebox .tc {{ font-size:9px; color:#9be6ac; font-family: ui-monospace, monospace; }}

  .hit-counter {{ max-width:280px;margin:16px auto;text-align:center;background:#000;border:2px solid #fff;padding:8px; }}
  .hit-counter img {{ height: 30px; }}

  .page-strip {{ display:flex; flex-wrap:wrap; justify-content:center; gap:4px; margin: 18px 0; }}
  .page-strip a {{
    background:#0a0a0a; border:2px outset {accent}; color:{accent};
    text-decoration:none; font-size:11px; font-weight:800; padding:6px 9px;
  }}
  .page-strip a.here {{ background:{accent}; color:#0a0a0a; border-style:inset; }}

  .rule {{ height:5px; border:none; margin:18px 0; background: repeating-linear-gradient(90deg,#fff 0 14px,#0a0a0a 14px 28px); }}

  table.stat-table {{ width:100%; border-collapse:collapse; background:#0a0a0a; font-size:13px; }}
  table.stat-table th, table.stat-table td {{ border: 2px solid {accent}; padding:6px 8px; text-align:center; }}
  table.stat-table th {{ background:{accent}; color:#0a0a0a; }}

  .dead-link {{ color: #8bd; text-decoration: underline; cursor: pointer; }}
  footer.az-foot {{ text-align:center; font-size:11px; color:#cde; padding:20px 0 40px; }}
</style>"""


def az_head(title, page_index):
    active_file, _ = PAGES[page_index]
    accent = PAGE_ACCENTS[page_index]
    nav_cells = "\n    ".join(
        f'<a href="{f}"{" class=\"here\"" if i == page_index else ""}>{i+1}. {label}</a>'
        for i, (f, label) in enumerate(PAGES)
    )
    balls_html, n = soccer_balls(22)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} :: AdamArmstrongExperience.net</title>
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
{az_style(accent)}
</head>
<body>
<div class="ball-layer" id="ballLayer">
    {balls_html}
</div>
{easter_eggs(page_index)}
<div class="stripe-top"></div>
<div class="fake-marquee"><span>{MARQUEES[page_index]}</span></div>
<table class="az-frame"><tr>
<td class="az-nav-cell">
    <div style="text-align:center;color:{accent};font-weight:900;font-size:10px;margin-bottom:8px;">SITE MAP</div>
    {nav_cells}
    <div class="jukebox">
      <button id="azPlay" type="button">&#9654;</button>
      <div class="meta">
        <div class="tn">I Wish</div>
        <div class="tc">Skee-Lo &middot; MIDI (1995)</div>
      </div>
      <audio id="azBgm" src="iwish.mp3" loop autoplay preload="auto"></audio>
    </div>
    <div class="hit-counter">
      <img src="https://hits.sh/houseofhufflepuff.github.io/megavision/armstrong.svg?label=VISITOR+NUMBER&labelColor=0a0a0a&color=0b3d1f&style=flat-square" alt="hit counter">
    </div>
    <a href="index.html" style="margin-top:10px;">&larr; MEGAVISION Home</a>
</td>
<td class="az-content-cell">
"""


def az_foot(page_index):
    strip = "\n    ".join(
        f'<a href="{f}"{" class=\"here\"" if i == page_index else ""}>PAGE {i+1}</a>'
        for i, (f, _) in enumerate(PAGES)
    )
    return f"""
  <div class="page-strip">
    {strip}
  </div>
  <div class="az-badge-row">
    <div class="az-badge" style="background:#000080;color:#fff;">BEST VIEWED IN<br>NETSCAPE 4.0<br>@ 800&times;600</div>
    <div class="az-badge" style="background:#0b6e2f;color:#fff;">100% GRASS<br>FED<br>CONTENT</div>
    <div class="az-badge" style="background:#ffd700;color:#000;">&#9917; OFFICIAL<br>UNOFFICIAL<br>FAN SITE</div>
    <div class="az-badge" style="background:#d61f26;color:#fff;">RED CARD<br>TO ALL<br>HATERS</div>
    <div class="az-badge" style="background:#000;color:#0f0;">HACKER<br>SAFE&trade;<br>CERTIFIED</div>
  </div>
  <p style="text-align:center;">
    <a class="dead-link">Sign My Guestbook</a> &middot;
    <a class="dead-link">Email The Webmaster</a> &middot;
    <a class="dead-link">Join The Webring</a> &middot;
    <a class="dead-link">Vote For Adam (Poll Closed In 2019)</a>
  </p>
</td>
</tr></table>
<footer class="az-foot">
  &copy; forever &middot; This is an unofficial fan project, not affiliated with Adam Armstrong, Southampton FC, Wolverhampton Wanderers FC, or anyone with legal authority to stop us.
  <br>Bio &amp; stats sourced from Wikipedia. Photos via Wikimedia Commons. Music: real 1995 MIDI, rendered locally so it actually plays.
</footer>
<script>
(function() {{
  var bgm = document.getElementById('azBgm');
  var btn = document.getElementById('azPlay');
  function setBtn() {{ btn.innerHTML = bgm.paused ? '&#9654;' : '&#10074;&#10074;'; }}
  function tryPlay() {{
    var p = bgm.play();
    if (p && p.catch) {{
      p.then(setBtn).catch(function() {{
        setBtn();
        document.addEventListener('click', function once() {{
          bgm.play().then(setBtn);
          document.removeEventListener('click', once);
        }}, {{ once: true }});
      }});
    }}
  }}
  btn.addEventListener('click', function() {{
    if (bgm.paused) {{ bgm.play().then(setBtn); }} else {{ bgm.pause(); setBtn(); }}
  }});
  bgm.addEventListener('play', setBtn);
  bgm.addEventListener('pause', setBtn);
  tryPlay();
}})();
(function() {{
  var layer = document.getElementById('ballLayer');
  var balls = layer.querySelectorAll('.ball');
  balls.forEach(function(ball, i) {{
    function fly() {{
      var x = 2 + Math.random() * 90;
      var y = 4 + Math.random() * 86;
      ball.style.left = x + '%';
      ball.style.top = y + '%';
      setTimeout(fly, 1400 + Math.random() * 2600);
    }}
    setTimeout(fly, i * 90);
  }});
}})();
</script>
</body>
</html>
"""


def page(filename, index, title, body):
    with open(filename, "w") as f:
        f.write(az_head(title, index) + body + az_foot(index))
    print(f"wrote {filename}")


# ================================================================== PAGE 1
page("armstrong-1.html", 0, "Home", f"""
<div class="az-title blink">&#9917; THE ADAM ARMSTRONG EXPERIENCE &#9917;</div>
<div style="text-align:center;color:#ffd700;font-weight:800;margin-bottom:10px;">WELCOME, VISITOR. YOU HAVE BEEN CHOSEN.</div>

<div class="az-box" style="text-align:center;">
  <img src="adam-armstrong-goblin.png" alt="Adam Armstrong" style="max-width:100%;border:5px solid #ffd700;">
  <p style="font-size:13px;color:#9be6ac;">(photographic evidence has been lightly enhanced for maximum vibes)</p>
</div>

<div class="az-box">
  <h2>WHO IS ADAM ARMSTRONG?</h2>
  <p style="line-height:1.7;">He is a striker. He is a father. He is a two-time World and European
  youth champion. He has scored 141 professional goals with his actual feet. He once scored a
  hat-trick. THREE TIMES. This website exists because one (1) human being decided that the internet
  needed a complete, unauthorized, extremely enthusiastic archive of Adam James Armstrong, and that
  human being was <b>us</b>. Explore the site using the frame on the left. There are NINE pages.
  You will not be the same person after finishing all nine.</p>
</div>

<button class="az-huge-btn" type="button" onclick="return false;">CLICK<br>THE<br>BALL</button>
<p style="text-align:center;font-size:11px;color:#9be6ac;">(warning: does absolutely nothing. we tested it 40 times.)</p>

<div class="az-badge-row">
  <div class="az-badge" style="background:#fff;color:#000;">NEW!!<span class="blink">&#9733;</span></div>
  <div class="az-badge" style="background:#0a0a0a;color:#ffd700;">EST.<br>WHENEVER<br>WE MADE THIS</div>
  <div class="az-badge" style="background:#0b6e2f;color:#fff;">NOW WITH<br>40<br>PHOTOS</div>
</div>

<div class="az-box">
  <h2>SITE INDEX</h2>
  <div class="gallery-grid">
""" + "\n".join(
    f'<div class="gcard" style="text-align:center;padding:14px 6px;"><a href="{f}" style="color:#ffd700;font-weight:800;text-decoration:none;">PAGE {i+1}<br>{label}</a></div>'
    for i, (f, label) in enumerate(PAGES)
) + """
  </div>
</div>
""")

# ================================================================== PAGE 2
page("armstrong-2.html", 1, "Bio", f"""
<div class="az-title">WHO IS THIS MAN?</div>

<div class="az-box">
  <h2>THE VITALS</h2>
  <table class="stat-table">
    <tr><th>Field</th><th>Answer</th></tr>
    <tr><td>Full Name</td><td>Adam James Armstrong</td></tr>
    <tr><td>Born</td><td>10 February 1997, Newcastle upon Tyne, England</td></tr>
    <tr><td>Height</td><td>5 ft 8 in (1.72 m) &mdash; a UNIT, pound for pound</td></tr>
    <tr><td>Position</td><td>Striker (the exciting kind)</td></tr>
    <tr><td>Current Club</td><td>Wolverhampton Wanderers, squad no. 10</td></tr>
    <tr><td>Signed</td><td>2 February 2026, three-and-a-half-year deal</td></tr>
  </table>
</div>

<div class="az-box">
  <h2>FAMILY LIFE</h2>
  <p style="line-height:1.7;">Armstrong married his partner Rebecca in 2021. Their son, Axel Thomas
  Armstrong, was born on 21 November 2022. By all accounts Adam is a private, grounded family man
  who has settled comfortably away from the spotlight &mdash; which, frankly, only makes us respect
  him MORE, because it means everything on this website is information he did NOT want us to
  compile this thoroughly.</p>
</div>

<div class="az-box">
  <h2>HOBBIES &amp; INTERESTS <span style="font-size:11px;color:#9be6ac;">(citation needed)</span></h2>
  <p style="line-height:1.7;">Adam Armstrong keeps his personal life extremely private, so, in the
  proud tradition of 90s fan sites everywhere, here is a LIST OF THINGS WE ASSUME HE LIKES based on
  absolutely no evidence whatsoever:</p>
  <ul style="line-height:1.9;">
    <li>Scoring goals (confirmed, 141 times, this one is real)</li>
    <li>Being 5'8" and doing it anyway</li>
    <li>Spending time with Rebecca and Axel (probably his favorite hobby, honestly)</li>
    <li>Staying humble despite being a two-time world champion at YOUTH level alone</li>
    <li>We choose to believe he collects vintage MIDI files. No proof. Just vibes.</li>
  </ul>
</div>
""")

# ================================================================== PAGE 3
page("armstrong-3.html", 2, "Early Years", f"""
<div class="az-title">THE EARLY YEARS</div>
<div class="az-box">
  <h2>NEWCASTLE UNITED (2014&ndash;2018)</h2>
  <p style="line-height:1.7;">A Newcastle upon Tyne boy who came up through his hometown club's
  academy. Made his professional debut on 15 March 2014 against Fulham. 17 Premier League
  appearances for the Magpies before the loan odyssey began. Every legend needs an origin story.
  This is his.</p>
</div>
<div class="az-box">
  <h2>COVENTRY CITY (Loan, 2015&ndash;16)</h2>
  <p style="line-height:1.7;">40 appearances. 20 goals. FIVE goals in his opening five games.
  League One Player of the Month for August 2015. PFA Team of the Year. An eighteen-year-old
  announcing himself to English football with maximum violence (the good kind, the goal-scoring
  kind).</p>
</div>
<div class="az-box">
  <h2>BARNSLEY (Loan, 2016&ndash;17)</h2>
  <p style="line-height:1.7;">34 appearances, 6 goals. Debut 10 September 2016 vs Preston North
  End. The consolidation season. Every champion needs one of these. Adam had his.</p>
</div>
<div class="az-box">
  <h2>BOLTON WANDERERS (Loan, 2017)</h2>
  <p style="line-height:1.7;">20 appearances, 1 goal, before being recalled in January 2018. A
  brief chapter. But EVERY chapter matters in the Adam Armstrong story. We will not be skipping
  it. We considered it. We did not.</p>
</div>
<div class="gallery-grid">
  <div class="gcard"><img src="{CB}{ARMSTRONG_IMAGES[0].replace(' ','%20')}" loading="lazy"><p>{caption_for(ARMSTRONG_IMAGES[0])}</p></div>
  <div class="gcard"><img src="{CB}{ARMSTRONG_IMAGES[1].replace(' ','%20')}" loading="lazy"><p>{caption_for(ARMSTRONG_IMAGES[1])}</p></div>
</div>
""")

# ================================================================== PAGE 4
page("armstrong-4.html", 3, "Blackburn", f"""
<div class="az-title">BLACKBURN GLORY DAYS</div>
<div class="az-box">
  <h2>BLACKBURN ROVERS (Loan 2017&ndash;18, Permanent 2018&ndash;2021)</h2>
  <p style="line-height:1.7;">21 appearances and 9 goals on loan convinced Rovers to make it
  permanent: &pound;1.75 million, signed 6 August 2018. What followed was, frankly, one of the
  great modern Championship striker runs: <b>130 appearances, 49 goals</b>. THREE hat-tricks in
  the 2020-21 season alone. Voted Blackburn Rovers Player of the Season for 2019-20. If you know,
  you know. If you don't know, you are about to know, because we are about to tell you three more
  times on this page.</p>
  <p style="line-height:1.7;">Three hat-tricks. In one season. We are going to say it again for
  the people in the back: <b>THREE HAT-TRICKS.</b></p>
</div>
<div class="az-box">
  <h2>PFA TEAM OF THE YEAR</h2>
  <p style="line-height:1.7;">2020-21 Championship Team of the Year. This was not a fluke season.
  This was a MAN AT WORK.</p>
</div>
<div class="gallery-grid">
  <div class="gcard"><img src="{CB}{ARMSTRONG_IMAGES[2].replace(' ','%20')}" loading="lazy"><p>{caption_for(ARMSTRONG_IMAGES[2])}</p></div>
  <div class="gcard"><img src="{CB}{ARMSTRONG_IMAGES[3].replace(' ','%20')}" loading="lazy"><p>{caption_for(ARMSTRONG_IMAGES[3])}</p></div>
</div>
""")

# ================================================================== PAGE 5
page("armstrong-5.html", 4, "Saints+", f"""
<div class="az-title">SOUTHAMPTON SAINT &amp; BEYOND</div>
<div class="az-box">
  <h2>SOUTHAMPTON FC (2021&ndash;2025)</h2>
  <p style="line-height:1.7;">Joined 10 August 2021 for a reported &pound;15 million. Scored ON
  HIS DEBUT against Everton. 148 appearances, 38 goals across four seasons on the South Coast.
  When it mattered most &mdash; the 2024 Championship play-offs &mdash; he scored in BOTH the
  semi-final AND the final, helping fire Southampton back to the Premier League. Voted Southampton
  Supporters' Player of the Season 2023-24. A goblin-approved, promotion-securing, generational
  Hampshire hero.</p>
</div>
<div class="az-box">
  <h2>WEST BROMWICH ALBION (Loan, 2024&ndash;25)</h2>
  <p style="line-height:1.7;">16 appearances, 3 goals. Debut 8 February 2025 vs Sheffield
  Wednesday. A short chapter, but every chapter matters (see: Bolton, page 3).</p>
</div>
<div class="az-box">
  <h2>WOLVERHAMPTON WANDERERS (2026&ndash;present)</h2>
  <p style="line-height:1.7;">Signed 2 February 2026 on a three-and-a-half-year contract. 14
  appearances, 2 goals and counting. The story is still being written. We will be here, refreshing
  Wikipedia, updating this page by hand, for as long as it takes.</p>
</div>
<div class="gallery-grid">
  <div class="gcard"><img src="{CB}{ARMSTRONG_IMAGES[16].replace(' ','%20')}" loading="lazy"><p>{caption_for(ARMSTRONG_IMAGES[16])}</p></div>
  <div class="gcard"><img src="{CB}{ARMSTRONG_IMAGES[17].replace(' ','%20')}" loading="lazy"><p>{caption_for(ARMSTRONG_IMAGES[17])}</p></div>
</div>
""")

# ================================================================== PAGE 6
page("armstrong-6.html", 5, "England", f"""
<div class="az-title">ENGLAND &amp; HONOURS</div>
<div class="az-box">
  <h2>ENGLAND YOUTH CAPS</h2>
  <table class="stat-table">
    <tr><th>Level</th><th>Caps</th><th>Goals</th></tr>
    <tr><td>U16</td><td>6</td><td>2</td></tr>
    <tr><td>U17</td><td>12</td><td>10</td></tr>
    <tr><td>U18</td><td>9</td><td>8</td></tr>
    <tr><td>U19</td><td>9</td><td>3</td></tr>
    <tr><td>U20</td><td>13</td><td>7</td></tr>
    <tr><td>U21</td><td>5</td><td>1</td></tr>
  </table>
</div>
<div class="az-box">
  <h2>TWO. WORLD TITLES.</h2>
  <p style="line-height:1.7;">2014 UEFA European Under-17 Championship: <b>WON.</b><br>
  2017 FIFA U-20 World Cup: <b>WON</b> &mdash; and he scored in the OPENING GAME, against
  Argentina, on the biggest stage a teenager can be handed. Most people never win one
  international tournament in their life. Adam Armstrong won two before he could legally rent a
  car in the United States.</p>
</div>
<div class="az-box">
  <h2>PFA TEAM OF THE YEAR (x3)</h2>
  <p style="line-height:1.7;">2015-16 (League One), 2020-21 (Championship), 2023-24
  (Championship). Three different divisions, three different decades of his career, the same
  result: the best players in the league had to make room for him.</p>
</div>
""")

# ================================================================== PAGE 7
page("armstrong-7.html", 6, "Stats", f"""
<div class="az-title">STATS CENTRAL</div>
<div class="az-box" style="text-align:center;">
  <h2>CAREER TOTALS</h2>
  <p style="font-size:34px;font-weight:900;color:#ffd700;margin:4px 0;">485 APPS &middot; 141 GOALS</p>
  <p style="color:#9be6ac;">approx. 0.29 goals per appearance. A CALCULATOR CONFIRMED THIS.</p>
</div>
<div class="az-box">
  <h2>PER-CLUB BREAKDOWN</h2>
  <table class="stat-table">
    <tr><th>Club</th><th>Spell</th><th>Apps</th><th>Goals</th></tr>
    <tr><td>Newcastle United</td><td>2014&ndash;18</td><td>17</td><td>0</td></tr>
    <tr><td>Coventry City (loan)</td><td>2015&ndash;16</td><td>40</td><td>20</td></tr>
    <tr><td>Barnsley (loan)</td><td>2016&ndash;17</td><td>34</td><td>6</td></tr>
    <tr><td>Bolton Wanderers (loan)</td><td>2017</td><td>20</td><td>1</td></tr>
    <tr><td>Blackburn Rovers (loan)</td><td>2017&ndash;18</td><td>21</td><td>9</td></tr>
    <tr><td>Blackburn Rovers</td><td>2018&ndash;21</td><td>130</td><td>49</td></tr>
    <tr><td>Southampton</td><td>2021&ndash;25</td><td>148</td><td>38</td></tr>
    <tr><td>West Brom (loan)</td><td>2024&ndash;25</td><td>16</td><td>3</td></tr>
    <tr><td>Wolverhampton Wanderers</td><td>2026&ndash;</td><td>14</td><td>2</td></tr>
  </table>
</div>
<div class="az-box">
  <h2>HAT-TRICK COUNT</h2>
  <p style="font-size:28px;text-align:center;font-weight:900;color:#ffd700;">3 &#9917;&#9917;&#9917;</p>
  <p style="text-align:center;color:#9be6ac;">all in the 2020-21 season, all at Blackburn Rovers.</p>
</div>
""")

# ================================================================== PAGE 8
_gallery_cards = "\n  ".join(
    f'<div class="gcard"><img src="{CB}{f.replace(" ", "%20")}" alt="Adam Armstrong photo {i+1}" loading="lazy">'
    f'<p><b>#{i+1}.</b> {caption_for(f)}</p></div>'
    for i, f in enumerate(ARMSTRONG_IMAGES)
)
page("armstrong-8.html", 7, "Gallery", f"""
<div class="az-title blink">THE MEGA GALLERY</div>
<div style="text-align:center;color:#ffd700;font-weight:800;margin-bottom:14px;">40 PHOTOGRAPHS. ZERO RESTRAINT.</div>
<div class="az-box">
  <p style="line-height:1.7;">Every image below is a real, freely-licensed photograph sourced from
  Wikimedia Commons, most from Southampton's 22 November 2025 match against Charlton Athletic.
  We have described each one with the emotional intensity it deserves.</p>
</div>
<div class="gallery-grid">
  {_gallery_cards}
</div>
""")

# ================================================================== PAGE 9
page("armstrong-9.html", 8, "Fan Zone", f"""
<div class="az-title">FAN ZONE</div>
<div style="text-align:center;color:#ffd700;font-weight:800;">PAGE 9 OF 9 &mdash; YOU MADE IT</div>

<div class="az-box">
  <h2>GUESTBOOK</h2>
  <table class="stat-table" style="font-size:12px;">
    <tr><th>Name</th><th>Message</th></tr>
    <tr><td>xXGoblinFan97Xx</td><td>found this site by accident. never leaving. 10/10</td></tr>
    <tr><td>SaintsForever</td><td>the hat-trick section made me cry actual tears</td></tr>
    <tr><td>anonymous</td><td>why is there a goblin in the crowd photo. WHY. i love it</td></tr>
    <tr><td>PeterD_stan</td><td>i keep seeing a familiar face somewhere on this site... coincidence?</td></tr>
  </table>
  <p style="font-size:11px;color:#9be6ac;">(guestbook submissions are currently closed. they were never actually open.)</p>
</div>

<button class="az-huge-btn" type="button" onclick="return false;">CLICK<br>FOR<br>MORE</button>
<p style="text-align:center;font-size:11px;color:#9be6ac;">(this one also does nothing. consistency matters.)</p>

<div class="az-box">
  <h2>CREDITS</h2>
  <p style="line-height:1.7;">Bio &amp; career stats: Wikipedia. Photography: Wikimedia Commons
  contributors, with thanks. Music: a real 1995 Skee-Lo MIDI file, rendered to audio so your
  browser could actually play it. Goblins: unrelated, yet somehow everywhere. Adam Armstrong: not
  affiliated with this website in any way, and, if he is reading this, we are so sorry, and also
  you're welcome.</p>
</div>

<div class="rule"></div>
<p style="text-align:center;font-weight:900;color:#ffd700;">&#9917; THE END &#9917;</p>
<p style="text-align:center;"><a href="armstrong-1.html">&larr; back to page 1, obviously</a></p>
""")

print("done -- 9 pages generated")
