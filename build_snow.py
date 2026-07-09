import random
from common import head, foot

FLAKE_CHARS = ["❄", "❅", "❆", "✳", "*"]
random.seed(42)
snow_spans = []
for i in range(45):
    ch = FLAKE_CHARS[i % len(FLAKE_CHARS)]
    left = random.uniform(0, 100)
    dur = random.uniform(7, 18)
    delay = random.uniform(-15, 0)
    size = random.uniform(11, 26)
    drift = random.choice([-1, 1]) * random.uniform(15, 60)
    opacity = random.uniform(0.35, 0.9)
    snow_spans.append(
        f'<span class="snowflake" style="left:{left:.2f}%;font-size:{size:.0f}px;'
        f'opacity:{opacity:.2f};--drift:{drift:.0f}px;'
        f'animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s;">{ch}</span>'
    )
snow_html = "\n      ".join(snow_spans)

BADGES = [
    ("#000080", "#fff", "BEST VIEWED IN<br>NETSCAPE 4.0<br>@ 800&times;600"),
    ("#c0c0c0", "#000", "POWERED BY<br><b>FrontPage&reg; 98</b>"),
    ("#ffcc00", "#000", "&#9889; Y2K<br>COMPLIANT &#9889;"),
    ("#008000", "#fff", "WEBRING<br>MEMBER<br>#0042"),
    ("#800080", "#fff", "MADE WITH<br><b>Notepad</b><br>not AI!"),
    ("#ff0000", "#fff", "GET<br><b>Internet<br>Explorer</b>"),
    ("#000", "#0f0", "HACKER<br>SAFE&trade;<br>CERTIFIED"),
    ("#ffd166", "#000", "&#11088; TOP 100<br>FANTASY<br>SITES &#11088;"),
]
badge_html = "\n      ".join(
    f'<div class="web1-badge" style="background:{bg};color:{fg};">{label}</div>'
    for bg, fg, label in BADGES
)

TRACK_URL = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Cheery%20Monday.mp3"
TRACK_TITLE = "Cheery Monday"
TRACK_ARTIST = "Kevin MacLeod (incompetech.com)"
TRACK_LICENSE = "CC BY 4.0"

SNOWMOBILES = [
    (1, "Ski-Doo Olympique", "1959", "The machine that created the industry. Bombardier built a sled small enough and cheap enough for a normal family driveway, and overnight snow stopped being an obstacle and became a playground. Every snowmobile made since owes it a debt.",
     "https://commons.wikimedia.org/wiki/Special:FilePath/Ski-doo_Olympique_12-3_1969.jpg"),
    (2, "Arctic Cat El Tigre", "1970s", "Built to win, not to cruise. The El Tigre turned trail racing into a genuine bloodsport and made Arctic Cat a name people feared on a starting line. Aggressive, loud, uncompromising.",
     "https://commons.wikimedia.org/wiki/Special:FilePath/Arctic_Cat_el_Tigre_400_Vintage_Snowmobiles_at_Tip-Up_Town,_Houghton_Lake,_MI_1-21-2012_(6743743895).jpg"),
    (3, "Polaris Indy", "1988", "Independent front suspension changed snowmobiling forever, and the Indy is the sled that proved it. It became the best-selling snowmobile in history for a reason: it simply rode better than anything else on the trail.",
     "https://commons.wikimedia.org/wiki/Special:FilePath/1988_Polaris_INDY_500.jpg"),
    (4, "Ski-Doo MXZ", "Modern Era", "The current benchmark for performance. Sharp, fast, and built to be thrown sideways through a corner without complaint. Every rival brand still measures itself against this chassis.",
     "https://commons.wikimedia.org/wiki/Special:FilePath/Snowmobile_Ski-Doo_MXZ_800.jpg"),
    (5, "Massey Ferguson Ski-Whiz", "1960s", "A tractor company built a snowmobile, and it worked. The Ski-Whiz proved winter machines could come from absolutely anywhere and still earn a place in the history books.",
     "https://commons.wikimedia.org/wiki/Special:FilePath/Ski_Whiz_by_Massey_Ferguson.jpg"),
]
sled_cards = "\n      ".join(
    f"""<div class="sled-card">
        <div class="sled-rank">#{rank}</div>
        <img src="{img}" alt="{name}" loading="lazy">
        <div class="sled-body">
          <div class="sled-name">{name}</div>
          <div class="sled-year">{year}</div>
          <p class="sled-blurb">{blurb}</p>
        </div>
      </div>"""
    for rank, name, year, blurb, img in SNOWMOBILES
)

TAGLINES = [
    ("Untamed Winter Destiny", "gold", "display", -4, "4%", "2%", "46px"),
    ("Awaken the Yetti", "pink", "script", 4, "12%", "55%", "58px"),
    ("Conquer", "blue", "display", -3, "24%", "78%", "64px"),
    ("White Wilderness Legacy", "violet", "sans", 3, "38%", "1%", "34px"),
    ("Ignite Your Arctic Soul", "crimson", "display", -5, "48%", "62%", "40px"),
    ("Redefine Freedom Through Snow Mastery", "gold", "sans", 2, "60%", "48%", "32px"),
    ("Transcend Ordinary", "blue", "script", -4, "70%", "2%", "52px"),
    ("Forge Your Winter Purpose", "pink", "display", 5, "80%", "58%", "34px"),
    ("Snow Life Command", "violet", "display", -2, "90%", "24%", "44px"),
]

FONT_STACKS = {
    "display": "Impact, Haettenschweiler, 'Arial Narrow Bold', sans-serif",
    "script": "'Brush Script MT', 'Segoe Script', cursive",
    "sans": "var(--mv-font)",
}

COLOR_VAR = {
    "gold": "var(--mv-gold)",
    "pink": "var(--mv-pink)",
    "blue": "var(--mv-blue)",
    "violet": "var(--mv-violet)",
    "crimson": "var(--mv-crimson)",
}

tagline_spans = []
for i, (text, color, font, rot, top, left, size) in enumerate(TAGLINES):
    blink = " retro-blink" if i % 3 == 0 else ""
    tagline_spans.append(f"""      <div class="retro-tagline{blink}" style="
        top:{top}; left:{left}; transform:rotate({rot}deg);
        color:{COLOR_VAR[color]}; font-family:{FONT_STACKS[font]}; font-size:{size};
      ">{text}</div>""")
tagline_html = "\n".join(tagline_spans)

page = head("Snowmobile Lifestyle", "snowmobile-lifestlye.html") + f"""
<style>
  @keyframes retroBlink {{ 0%, 45% {{ opacity: 1; }} 50%, 95% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
  @keyframes marqueeScroll {{ 0% {{ transform: translateX(8%); }} 100% {{ transform: translateX(-108%); }} }}
  @keyframes pulseGlow {{
    0%, 100% {{ box-shadow: 0 0 50px 10px rgba(124,58,237,0.45), 0 0 120px 30px rgba(230,63,176,0.15); }}
    50% {{ box-shadow: 0 0 80px 20px rgba(230,63,176,0.55), 0 0 160px 50px rgba(46,107,255,0.2); }}
  }}
  @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
  @keyframes spinReverse {{ from {{ transform: rotate(360deg); }} to {{ transform: rotate(0deg); }} }}
  @keyframes snowFall {{
    0% {{ transform: translateY(-10vh) translateX(0); }}
    50% {{ transform: translateY(50vh) translateX(var(--drift)); }}
    100% {{ transform: translateY(110vh) translateX(0); }}
  }}
  @keyframes sparkleFade {{
    0% {{ opacity: 1; transform: translate(-50%,-50%) scale(1) rotate(0deg); }}
    100% {{ opacity: 0; transform: translate(-50%,-50%) scale(0.2) rotate(90deg); }}
  }}
  @keyframes twinkle {{ 0%, 100% {{ opacity: 0.25; }} 50% {{ opacity: 0.75; }} }}

  .snow-layer {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
    z-index: 60;
  }}
  .snowflake {{
    position: absolute;
    top: -10%;
    color: #fff;
    text-shadow: 0 0 6px rgba(255,255,255,0.85);
    animation-name: snowFall;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
  }}

  .tagline-layer {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
    z-index: 55;
  }}
  .retro-tagline {{
    position: absolute;
    font-weight: 800;
    text-shadow: 0 3px 0 rgba(0,0,0,0.7), 0 0 26px currentColor;
    max-width: 320px;
    line-height: 1.1;
    opacity: 0.88;
  }}
  .retro-blink {{ animation: retroBlink 1.4s steps(1) infinite; }}

  .heli-layer {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
    z-index: 58;
  }}
  .heli {{
    position: absolute;
    top: 40%; left: 40%;
    font-size: 52px;
    text-shadow: 0 4px 10px rgba(0,0,0,0.6);
    transition: left 2.6s ease-in-out, top 2.6s ease-in-out, transform 2.6s ease-in-out;
    transform: scaleX(1) rotate(0deg);
  }}

  .retro-page {{
    position: relative;
    overflow-x: hidden;
    background:
      repeating-linear-gradient(135deg, rgba(124,58,237,0.10) 0px, rgba(124,58,237,0.10) 2px, transparent 2px, transparent 34px),
      repeating-linear-gradient(45deg, rgba(46,107,255,0.08) 0px, rgba(46,107,255,0.08) 2px, transparent 2px, transparent 34px),
      var(--mv-black);
    padding: 26px 0 60px;
  }}
  .retro-page::before {{
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
      radial-gradient(circle, rgba(255,255,255,0.9) 1px, transparent 1.4px),
      radial-gradient(circle, rgba(255,209,102,0.7) 1px, transparent 1.4px);
    background-size: 90px 90px, 140px 140px;
    background-position: 0 0, 45px 70px;
    animation: twinkle 2.6s ease-in-out infinite;
  }}

  .rainbow-hr {{
    height: 6px;
    border: none;
    border-radius: 3px;
    margin: 26px auto;
    max-width: 900px;
    background: linear-gradient(90deg, #ff0000, #ff9900, #ffee00, #33cc33, #3399ff, #6633ff, #ff33cc);
    box-shadow: 0 0 10px rgba(255,255,255,0.4);
  }}

  .badge-row {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    max-width: 820px;
    margin: 0 auto 20px;
    position: relative;
    z-index: 5;
  }}
  .web1-badge {{
    width: 88px;
    height: 31px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-size: 8px;
    line-height: 1.15;
    font-family: Tahoma, 'MS Sans Serif', Geneva, sans-serif;
    border: 2px outset #ddd;
    box-shadow: 1px 1px 0 rgba(0,0,0,0.6);
  }}

  .site-tools {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin: 0 auto 40px;
    position: relative;
    z-index: 5;
  }}
  .site-tools a {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--mv-black-3);
    border: 2px outset var(--mv-chrome-300);
    color: var(--mv-ink);
    text-decoration: none;
    font-size: 11px;
    font-weight: 700;
    padding: 7px 12px;
    border-radius: 3px;
  }}
  .site-tools a:active {{ border-style: inset; }}

  .jukebox {{
    max-width: 420px;
    margin: 0 auto 26px;
    background: var(--mv-black-2);
    border: 2px solid var(--mv-gold);
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    position: relative;
    z-index: 5;
    box-shadow: 0 0 20px rgba(255,209,102,0.25);
  }}
  .jukebox button {{
    flex: 0 0 auto;
    width: 34px; height: 34px;
    border-radius: 50%;
    border: 2px outset var(--mv-gold);
    background: var(--mv-gold);
    color: #14141a;
    font-size: 14px;
    font-weight: 900;
    cursor: pointer;
  }}
  .jukebox button:active {{ border-style: inset; }}
  .jukebox .meta {{ min-width: 0; flex: 1 1 auto; }}
  .jukebox .now-playing {{ font-size: 9px; letter-spacing: 0.08em; color: var(--mv-gold); text-transform: uppercase; }}
  .jukebox .track-name {{
    font-size: 12px; font-weight: 700; color: var(--mv-ink);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  .jukebox .track-credit {{ font-size: 10px; color: var(--mv-ink-muted); }}
  .jukebox .eq {{ display: flex; align-items: flex-end; gap: 2px; height: 18px; flex: 0 0 auto; }}
  .jukebox .eq span {{ width: 3px; background: var(--mv-gold); animation: eqBounce 0.9s ease-in-out infinite; }}
  @keyframes eqBounce {{ 0%, 100% {{ height: 4px; }} 50% {{ height: 18px; }} }}

  .sled-section {{
    max-width: 1180px;
    margin: 0 auto 20px;
    position: relative;
    z-index: 5;
    background: repeating-linear-gradient(45deg, #1a0033, #1a0033 10px, #24004d 10px, #24004d 20px);
    border: 4px ridge #ffd166;
    padding: 18px;
  }}
  .sled-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }}
  .sled-card {{
    background: #c0c0c0;
    border: 4px outset #eee;
    overflow: visible;
    position: relative;
    font-family: 'Comic Sans MS', 'Comic Sans', cursive;
  }}
  .sled-rank {{
    position: absolute; top: -14px; left: -14px; z-index: 2;
    background: #ff0000; color: #ffff00;
    font-weight: 900; font-size: 16px;
    width: 34px; height: 34px;
    border: 3px outset #ffff00;
    display: flex; align-items: center; justify-content: center;
    transform: rotate(-12deg);
    text-shadow: 1px 1px 0 #000;
  }}
  .sled-card img {{
    width: 100%;
    height: 140px;
    object-fit: fill;
    display: block;
    border-bottom: 4px inset #eee;
    filter: saturate(1.3) contrast(1.1);
  }}
  .sled-body {{ padding: 10px 12px 14px; background: #d8d8e8; }}
  .sled-name {{
    font-weight: 900; font-size: 15px; color: #000080;
    text-shadow: 1px 1px 0 #fff;
  }}
  .sled-year {{
    display: inline-block;
    font-size: 10px; color: #fff; font-weight: 700;
    background: #cc0000; padding: 1px 6px; margin: 4px 0 8px;
    border: 1px solid #700;
  }}
  .sled-blurb {{ font-size: 12px; line-height: 1.5; color: #1a1a1a; }}

  .marquee-wrap {{
    overflow: hidden;
    white-space: nowrap;
    background: var(--mv-black-2);
    border-top: 2px solid var(--mv-gold);
    border-bottom: 2px solid var(--mv-gold);
    padding: 10px 0;
    margin-bottom: 30px;
  }}
  .marquee-text {{
    display: inline-block;
    font-weight: 800;
    font-size: 15px;
    letter-spacing: 0.08em;
    color: var(--mv-gold);
    animation: marqueeScroll 16s linear infinite;
    text-transform: uppercase;
  }}

  .construction-bar {{
    background: repeating-linear-gradient(45deg, #1a1a10, #1a1a10 14px, var(--mv-gold) 14px, var(--mv-gold) 28px);
    color: #14141a;
    font-weight: 900;
    text-align: center;
    padding: 8px 10px;
    font-size: 12px;
    letter-spacing: 0.05em;
    text-shadow: 0 1px 0 rgba(255,255,255,0.5);
    border-radius: 8px;
    margin-bottom: 34px;
  }}

  .retro-hero-title {{
    text-align: center;
    font-size: 40px;
    line-height: 1.15;
    margin: 0 0 6px;
    letter-spacing: 0.02em;
  }}
  .retro-sub {{
    text-align: center;
    color: var(--mv-ink-muted);
    font-size: 14px;
    margin-bottom: 10px;
  }}
  .retro-stars {{
    text-align: center;
    color: var(--mv-gold);
    letter-spacing: 10px;
    margin-bottom: 30px;
  }}

  .retro-stage {{
    position: relative;
    max-width: 1300px;
    margin: 0 auto 40px;
    min-height: 920px;
  }}
  .retro-image-wrap {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 92%;
    max-width: 1180px;
    border-radius: 18px;
    animation: pulseGlow 3.5s ease-in-out infinite;
    z-index: 3;
  }}
  .retro-image-wrap img {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 18px;
    border: 3px solid var(--mv-chrome-300);
  }}
  .retro-burst {{
    position: absolute;
    top: 50%; left: 50%;
    width: 1360px; height: 1360px;
    margin: -680px 0 0 -680px;
    z-index: 1;
    pointer-events: none;
    background:
      conic-gradient(from 0deg, transparent 0deg 12deg, rgba(255,209,102,0.18) 12deg 14deg,
      transparent 14deg 30deg, rgba(230,63,176,0.14) 30deg 32deg, transparent 32deg);
    border-radius: 50%;
    animation: spin 40s linear infinite;
  }}
  .retro-burst.reverse {{
    width: 1180px; height: 1180px;
    margin: -590px 0 0 -590px;
    animation: spinReverse 30s linear infinite;
    background:
      conic-gradient(from 0deg, transparent 0deg 8deg, rgba(46,107,255,0.16) 8deg 10deg, transparent 10deg);
  }}

  .hit-counter {{
    max-width: 260px;
    margin: 0 auto 40px;
    text-align: center;
    background: #000;
    border: 2px solid var(--mv-chrome-600);
    border-radius: 6px;
    padding: 10px;
  }}
  .hit-counter .lbl {{
    font-size: 10px;
    letter-spacing: 0.1em;
    color: var(--mv-ink-muted);
    margin-bottom: 4px;
  }}
  .hit-counter .digits {{
    font-family: ui-monospace, 'Courier New', monospace;
    font-size: 24px;
    font-weight: 800;
    color: #3fd17a;
    letter-spacing: 4px;
  }}

  .retro-cta {{
    text-align: center;
    margin-bottom: 10px;
  }}
  .retro-cta a {{
    display: inline-block;
    background: linear-gradient(90deg, var(--mv-violet), var(--mv-pink));
    color: #fff;
    font-weight: 800;
    text-decoration: none;
    padding: 16px 34px;
    border-radius: 999px;
    font-size: 16px;
    letter-spacing: 0.03em;
    box-shadow: 0 0 30px rgba(230,63,176,0.5);
    border: 2px solid var(--mv-chrome-100);
  }}

  @media (max-width: 720px) {{
    .retro-stage {{ min-height: auto; padding-bottom: 20px; }}
    .retro-image-wrap {{ position: relative; top: auto; left: auto; transform: none; width: 90%; margin: 0 auto 24px; display: block; }}
    .retro-burst {{ display: none; }}
    .tagline-layer {{ display: none; }}
  }}
</style>

<div class="tagline-layer">
{tagline_html}
</div>

<div class="heli-layer">
  <span class="heli" id="mvHeli">&#128641;</span>
</div>

<div class="snow-layer">
  {snow_html}
</div>

<div class="retro-page">
  <div class="marquee-wrap">
    <span class="marquee-text">&#9733; UNTAMED WINTER DESTINY &#9733; AWAKEN THE YETTI &#9733; IGNITE YOUR ARCTIC SOUL &#9733; SNOW LIFE COMMAND &#9733; CONQUER &#9733; TRANSCEND ORDINARY &#9733; UNTAMED WINTER DESTINY &#9733; AWAKEN THE YETTI &#9733; IGNITE YOUR ARCTIC SOUL &#9733; SNOW LIFE COMMAND &#9733;</span>
  </div>

  <div class="wrap" style="padding-top:0;">
    <div class="construction-bar">&#128679; SITE UNDER CONSTRUCTION &mdash; NEW POWDER DROPPING SOON &#128679; &nbsp; (last updated: right now, probably)</div>

    <div class="jukebox">
      <button id="mvPlayBtn" type="button" aria-label="Play/Pause">&#9654;</button>
      <div class="meta">
        <div class="now-playing">&#9835; Now Playing</div>
        <div class="track-name">{TRACK_TITLE}</div>
        <div class="track-credit">by {TRACK_ARTIST} &middot; {TRACK_LICENSE}</div>
      </div>
      <div class="eq">
        <span style="animation-delay:0s;"></span>
        <span style="animation-delay:0.2s;"></span>
        <span style="animation-delay:0.4s;"></span>
        <span style="animation-delay:0.1s;"></span>
      </div>
      <audio id="mvBgm" loop autoplay preload="auto">
        <source src="{TRACK_URL}" type="audio/mpeg">
      </audio>
    </div>

    <div class="badge-row">
      {badge_html}
    </div>

    <h1 class="retro-hero-title mv-spark-text">MEGAVISION SNOWMOBILE LIFESTYLE</h1>
    <div class="retro-sub">Est. always &middot; Best viewed at any resolution &middot; 100% Arctic Approved</div>
    <div class="retro-stars">&#9733; &#9733; &#9733; &#9733; &#9733;</div>

    <hr class="rainbow-hr">

    <div class="retro-stage">
      <div class="retro-burst"></div>
      <div class="retro-burst reverse"></div>
      <div class="retro-image-wrap">
        <img src="megavision.jpg" alt="MEGAVISION Snowmobile Lifestyle">
      </div>
    </div>

    <hr class="rainbow-hr">

    <section class="sled-section">
      <h2 class="retro-hero-title mv-spark-text" style="font-size:26px;">TOP 5 SNOWMOBILES OF ALL TIME</h2>
      <div class="retro-sub" style="margin-bottom:20px;">No debate. This is the list.</div>
      <div class="sled-grid">
      {sled_cards}
      </div>
    </section>

    <hr class="rainbow-hr">

    <div class="hit-counter">
      <div class="lbl">YOU ARE ARCTIC EXPLORER NUMBER</div>
      <div class="digits">004269</div>
    </div>

    <div class="site-tools">
      <a href="mailto:webmaster@megavision.example">&#128231; Email the Webmaster</a>
      <a href="#">&#128213; Sign My Guestbook</a>
      <a href="#">&#11088; Add to Favorites</a>
      <a href="#">&#128273; Webring: Next &rarr;</a>
    </div>

    <div class="retro-cta">
      <a href="teams.html">&#10084; JOIN THE LIFESTYLE &rarr;</a>
    </div>
    <div class="retro-cta">
      <a href="snow-business-plan.html" style="background:linear-gradient(90deg, var(--mv-gold), var(--mv-crimson));font-size:13px;padding:12px 26px;">&#128176; INVESTORS: SEE THE BIZ PLAN &rarr;</a>
    </div>

    <hr class="rainbow-hr">
    <div class="retro-sub" style="font-size:11px;">&#128257; This page best experienced with the sound of a dial-up modem playing in another tab.</div>
  </div>
</div>

<script>
(function() {{
  var bgm = document.getElementById('mvBgm');
  var btn = document.getElementById('mvPlayBtn');
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
</script>

<script>
(function() {{
  var heli = document.getElementById('mvHeli');
  var lastX = 40, lastY = 40;
  function fly() {{
    var x = 4 + Math.random() * 88;
    var y = 6 + Math.random() * 82;
    var facingLeft = x < lastX;
    var tilt = (Math.random() * 16 - 8).toFixed(1);
    heli.style.left = x + '%';
    heli.style.top = y + '%';
    heli.style.transform = 'scaleX(' + (facingLeft ? -1 : 1) + ') rotate(' + tilt + 'deg)';
    lastX = x; lastY = y;
    setTimeout(fly, 2200 + Math.random() * 2200);
  }}
  fly();
}})();
</script>

<script>
(function() {{
  var chars = ['\\u2726', '\\u2727', '\\u2744', '\\u2b50', '\\u2733'];
  var colors = ['#ffd166', '#e63fb0', '#2e6bff', '#7c3aed', '#f0525c'];
  document.addEventListener('mousemove', function(e) {{
    if (Math.random() > 0.55) return;
    var s = document.createElement('span');
    s.textContent = chars[Math.floor(Math.random() * chars.length)];
    s.style.cssText = 'position:fixed;left:' + e.clientX + 'px;top:' + e.clientY + 'px;'
      + 'pointer-events:none;z-index:9999;font-size:' + (10 + Math.random() * 10) + 'px;'
      + 'color:' + colors[Math.floor(Math.random() * colors.length)] + ';'
      + 'animation:sparkleFade 0.8s ease-out forwards;';
    document.body.appendChild(s);
    setTimeout(function() {{ s.remove(); }}, 800);
  }});
}})();
</script>
""" + foot()

with open("snowmobile-lifestlye.html", "w") as f:
    f.write(page)

print("wrote snowmobile-lifestlye.html")
