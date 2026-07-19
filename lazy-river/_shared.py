"""
Shared template kit for the Lazy River sub-site (40+ pages). Same Web1.0
raw-table-and-font-tag design language as the original lazy-river.html and
the pigeons/ sub-site, extended with: a real two-track jukebox (Cure MIDI
renders), a bigger categorized pipe-nav (40 pages across 5 groups), the
waterfall tile/floating-waterfall/popup-ad system carried over from the
original single-page build, and an optional scattered-ninjas layer for
pages that specifically ask for it (only firehose.html, per spec).
"""
import base64
import json
import random

# ---------------------------------------------------------------- tiles --
def _svg_tile(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


WATERFALL_TILES = {
    "creek": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="60" height="30">'
        '<rect width="60" height="30" fill="#003366"/>'
        '<path d="M0 8 Q15 2 30 8 T60 8" stroke="#0099cc" stroke-width="2" fill="none"/>'
        '<path d="M0 18 Q15 12 30 18 T60 18" stroke="#00ccff" stroke-width="2" fill="none" opacity="0.7"/>'
        '<path d="M0 27 Q15 22 30 27 T60 27" stroke="#66e0ff" stroke-width="1.5" fill="none" opacity="0.5"/>'
        '</svg>'
    ),
    "cascade": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="50">'
        '<rect width="40" height="50" fill="#00263d"/>'
        '<rect x="4" y="0" width="3" height="50" fill="#ffffff" opacity="0.5"/>'
        '<rect x="14" y="0" width="2" height="50" fill="#aeeeff" opacity="0.6"/>'
        '<rect x="24" y="0" width="4" height="50" fill="#ffffff" opacity="0.4"/>'
        '<rect x="33" y="0" width="2" height="50" fill="#aeeeff" opacity="0.5"/>'
        '</svg>'
    ),
    "misty": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="70" height="40">'
        '<rect width="70" height="40" fill="#5a8ca6"/>'
        '<ellipse cx="15" cy="10" rx="18" ry="6" fill="#e8f6ff" opacity="0.4"/>'
        '<ellipse cx="50" cy="25" rx="22" ry="7" fill="#ffffff" opacity="0.35"/>'
        '<ellipse cx="30" cy="34" rx="16" ry="5" fill="#dff3ff" opacity="0.3"/>'
        '</svg>'
    ),
    "rocky": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
        '<rect width="50" height="50" fill="#3a3a35"/>'
        '<polygon points="0,50 10,30 20,50" fill="#55524a"/>'
        '<polygon points="18,50 30,25 42,50" fill="#4a473f"/>'
        '<rect x="0" y="0" width="50" height="18" fill="#0d3b52"/>'
        '<path d="M0 10 Q25 4 50 10" stroke="#8fe0ff" stroke-width="2" fill="none" opacity="0.7"/>'
        '</svg>'
    ),
    "tropical": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="55" height="45">'
        '<rect width="55" height="45" fill="#0b4d3a"/>'
        '<rect x="6" y="0" width="4" height="45" fill="#bff2ff" opacity="0.55"/>'
        '<rect x="24" y="0" width="3" height="45" fill="#ffffff" opacity="0.45"/>'
        '<circle cx="45" cy="10" r="6" fill="#146b4d"/><circle cx="12" cy="36" r="5" fill="#146b4d"/>'
        '</svg>'
    ),
}
WATERFALL_TILE_KEYS = list(WATERFALL_TILES.keys())


def random_bg(seed_key, no_bg_chance=0.35):
    rnd = random.Random(hash(seed_key) & 0xffffffff)
    if rnd.random() < no_bg_chance:
        return None
    return WATERFALL_TILES[rnd.choice(WATERFALL_TILE_KEYS)]


def bg_attr(tile):
    return f' background="{tile}"' if tile else ""


# ------------------------------------------------------------- popup ads --
POPUP_ADS = [
    ("RIVERBUM.EXE", "&#127754; STOP READING, START FLOATING &#127754;", "You have been staring at a table of lazy river statistics for 45 seconds. That is 45 seconds you could have spent floating an ACTUAL lazy river. We can't fix that. But we CAN sell you a snowmobile.", "../snowmobile-lifestlye.html", "SEE THE LIFESTYLE &rarr;"),
    ("RENTME.EXE", "&#127942; RENT YOUR OWN LAZY RIVER &#127942;", "Yes, this is real. Yes, you can rent one for your event. No, we will not explain the logistics here, that's what the Shop page is for.", "shop.html", "VISIT THE SHOP &rarr;"),
    ("TUBE911.EXE", "&#128680; TUBE EMERGENCY &#128680;", "Our records indicate you do NOT currently own a park-issued inner tube. This is a critical lifestyle failure. MEGAVISION recommends immediate corrective action.", "../snowmobile-lifestlye.html", "FIX MY LIFESTYLE &rarr;"),
    ("WINNER.EXE", "&#127942; CONGRATULATIONS!!! &#127942;", "You are the 1,000,000th visitor to float this page!!! Click below to claim your FREE Arctic Soul Seeker starter pack. Do not refresh!", "../snowmobile-lifestlye.html", "CLAIM PRIZE &rarr;"),
    ("HOSEIT.EXE", "&#128167; FEELING DRY? &#128167;", "There is a fully interactive firehose on this website RIGHT NOW and you are not currently spraying anything with it. Fix that immediately.", "firehose.html", "SPRAY SOMETHING &rarr;"),
]
POPUP_ADS_JSON = json.dumps([list(ad) for ad in POPUP_ADS])


def popup_ads_block():
    return f"""
<div id="lrvPopupLayer"></div>
<script>
(function() {{
  var popupAds = {POPUP_ADS_JSON};
  var layer = document.getElementById('lrvPopupLayer');
  var openPopups = 0;
  var MAX_POPUPS = 3;
  function spawnPopup() {{
    if (openPopups >= MAX_POPUPS) return;
    openPopups++;
    var ad = popupAds[Math.floor(Math.random() * popupAds.length)];
    var win = document.createElement('div');
    win.className = 'lrv-popup';
    var top = 10 + Math.random() * 60;
    var left = 5 + Math.random() * 60;
    win.style.top = top + '%';
    win.style.left = left + '%';
    win.innerHTML =
      '<div class="lrv-popup-titlebar"><span>' + ad[0] + '</span><button class="lrv-popup-close" type="button">&#10005;</button></div>' +
      '<div class="lrv-popup-body"><b>' + ad[1] + '</b>' + ad[2] +
      '<br><a class="lrv-popup-cta" href="' + ad[3] + '">' + ad[4] + '</a></div>';
    layer.appendChild(win);
    function close() {{
      if (win.parentNode) {{ win.parentNode.removeChild(win); openPopups--; }}
    }}
    win.querySelector('.lrv-popup-close').addEventListener('click', close);
    setTimeout(close, 9000 + Math.random() * 4000);
  }}
  function scheduleNextPopup() {{
    var delay = 6000 + Math.random() * 8000;
    setTimeout(function() {{ spawnPopup(); scheduleNextPopup(); }}, delay);
  }}
  scheduleNextPopup();
}})();
</script>"""


# --------------------------------------------------------- floating fx --
WATERFALL_EMOJI = ["&#127754;", "&#128167;", "&#127754;", "&#128167;"]


def floating_waterfalls(n=10):
    spans = "\n    ".join(
        f'<span class="lrv-fall" id="lrvFall{i}">{WATERFALL_EMOJI[i % len(WATERFALL_EMOJI)]}</span>'
        for i in range(n)
    )
    script = """
<script>
(function() {
  var falls = document.querySelectorAll('.lrv-fall');
  falls.forEach(function(el, i) {
    var lastX = 10 + (i * 8) % 80;
    function drift() {
      var x = 2 + Math.random() * 92;
      var y = 2 + Math.random() * 92;
      var facingLeft = x < lastX;
      var tilt = (Math.random() * 24 - 12).toFixed(1);
      var scale = (0.7 + Math.random() * 0.9).toFixed(2);
      el.style.left = x + '%';
      el.style.top = y + '%';
      el.style.transform = 'scaleX(' + (facingLeft ? -1 : 1) + ') rotate(' + tilt + 'deg) scale(' + scale + ')';
      lastX = x;
      setTimeout(drift, 2600 + Math.random() * 3200);
    }
    setTimeout(drift, i * 300);
  });
})();
</script>"""
    return f'<div class="lrv-fall-layer">{spans}</div>{script}'


def static_waterfall_bar(label):
    return f"""
  <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td>
    <div class="lrv-static-fall">
      <div class="lrv-static-fall-water"></div>
      <div class="lrv-static-fall-label">&#127754; {label} &#127754;</div>
    </div>
  </td></tr></table>"""


NINJA_SPOTS = [
    ("4%", "6%", -8, "2.6s"), ("8%", "92%", 10, "3.1s"), ("22%", "2%", -14, "2.3s"),
    ("62%", "93%", 12, "2.5s"), ("78%", "5%", -10, "3.2s"),
]


def scattered_ninjas():
    spans = "\n    ".join(
        f'<span class="lrv-ninja" style="top:{top};left:{left};--r:{rot}deg;animation-duration:{dur};">&#129399;</span>'
        for top, left, rot, dur in NINJA_SPOTS
    )
    return f'<div class="lrv-ninja-layer">{spans}</div>'


# -------------------------------------------------------------- jukebox --
def jukebox_block():
    return """
    <div class="lrv-jukebox">
      <button id="lrvPlayBtn" type="button" aria-label="Play/Pause">&#9654;</button>
      <div class="meta">
        <div class="now-playing">&#9835; Now Playing</div>
        <div class="track-name" id="lrvTrackName">Lullaby</div>
        <div class="track-credit">by The Cure &middot; MIDI arrangement, rendered from the original .mid</div>
      </div>
      <button id="lrvSkipBtn" type="button" aria-label="Skip">&#9197;</button>
      <audio id="lrvBgm" preload="auto"></audio>
    </div>
    <script>
    (function() {
      var playlist = [
        { src: 'lullaby.mp3', name: 'Lullaby' },
        { src: 'close-to-me.mp3', name: 'Close To Me' }
      ];
      var depth = (window.location.pathname.split('/lazy-river/')[1] || '').split('/').length - 1;
      var prefix = depth > 0 ? '../'.repeat(depth) : '';
      var idx = Math.floor(Math.random() * playlist.length);
      var bgm = document.getElementById('lrvBgm');
      var btn = document.getElementById('lrvPlayBtn');
      var skip = document.getElementById('lrvSkipBtn');
      var nameEl = document.getElementById('lrvTrackName');
      function load(i, autoplay) {
        idx = (i + playlist.length) % playlist.length;
        bgm.src = prefix + playlist[idx].src;
        nameEl.textContent = playlist[idx].name;
        if (autoplay) { tryPlay(); }
      }
      function setBtn() { btn.innerHTML = bgm.paused ? '&#9654;' : '&#10074;&#10074;'; }
      function tryPlay() {
        var p = bgm.play();
        if (p && p.catch) {
          p.then(setBtn).catch(function() {
            setBtn();
            document.addEventListener('click', function once() {
              bgm.play().then(setBtn);
              document.removeEventListener('click', once);
            }, { once: true });
          });
        }
      }
      btn.addEventListener('click', function() {
        if (bgm.paused) { bgm.play().then(setBtn); } else { bgm.pause(); setBtn(); }
      });
      skip.addEventListener('click', function() { load(idx + 1, true); });
      bgm.addEventListener('ended', function() { load(idx + 1, true); });
      bgm.addEventListener('play', setBtn);
      bgm.addEventListener('pause', setBtn);
      load(idx, true);
    })();
    </script>"""


# ------------------------------------------------------------ nav pages --
NAV_GROUPS = [
    ("Home", [
        ("index.html", "Home"),
        ("top-10.html", "Top 10 Rivers"),
        ("shop.html", "Rent-A-River Shop"),
        ("firehose.html", "Tap The Firehose"),
    ]),
    ("The Top 10 Rivers", [(f"river-{i:02d}.html", f"#{i} River") for i in range(1, 11)]),
    ("Rent-A-River Use Cases", [
        ("shop-bar-mitzvah.html", "Bar/Bat Mitzvah"),
        ("shop-pride.html", "Pride"),
        ("shop-quinceanera.html", "Quinceañera"),
        ("shop-wedding.html", "Wedding"),
        ("shop-corporate.html", "Corporate"),
        ("shop-birthday.html", "Birthday"),
        ("shop-bachelorette.html", "Bachelor(ette)"),
        ("shop-graduation.html", "Graduation"),
        ("shop-festival.html", "Festival"),
        ("shop-holiday.html", "Holiday Party"),
    ]),
    ("River Guide", [
        ("history.html", "History"),
        ("engineering.html", "Engineering"),
        ("tubes101.html", "Tubes 101"),
        ("safety.html", "Safety"),
        ("records.html", "World Records"),
        ("best-usa.html", "Best in USA"),
        ("best-europe.html", "Best in Europe"),
        ("best-asia.html", "Best in Asia"),
        ("pop-culture.html", "Pop Culture"),
    ]),
    ("More", [
        ("gallery1.html", "Gallery I"),
        ("gallery2.html", "Gallery II"),
        ("gallery3.html", "Gallery III"),
        ("faq.html", "FAQ"),
        ("links.html", "Links"),
        ("webmaster.html", "Webmaster"),
        ("guestbook.html", "Guestbook"),
    ]),
]

NAV_PAGES = [item for _, items in NAV_GROUPS for item in items]


def nav_block(current_file):
    rows = []
    for group_label, items in NAV_GROUPS:
        pipe = " | ".join(
            f'<b><font color="#ffff00">{label}</font></b>' if href == current_file
            else f'<a href="{href}">{label}</a>'
            for href, label in items
        )
        rows.append(
            f'<font size="1" color="#66ccff">&#9660; {group_label}</font><br>'
            f'<font size="2" color="#00ffff">{pipe}</font><br><br>'
        )
    return "".join(rows)


# ----------------------------------------------------------- page shell --
STYLE_BLOCK = """<style>
  @keyframes lrvBlink { 0%,45% {visibility:visible;} 50%,95% {visibility:hidden;} 100% {visibility:visible;} }
  .blk { animation: lrvBlink 0.8s steps(1) infinite; }

  @keyframes lrvFlow { 0% { background-position: 0 0; } 100% { background-position: 0 120px; } }
  .lrv-static-fall {
    position: relative; height: 60px; margin: 10px 0;
    background: repeating-linear-gradient(180deg, #003366 0px, #0099cc 20px, #66e0ff 40px, #0099cc 60px, #003366 80px);
    background-size: 100% 80px;
    animation: lrvFlow 1.1s linear infinite;
    border: 4px ridge #00ffff;
  }
  .lrv-static-fall-water {
    position: absolute; inset: 0;
    background: repeating-linear-gradient(180deg, transparent 0px, rgba(255,255,255,0.35) 4px, transparent 10px);
    background-size: 100% 22px;
    animation: lrvFlow 0.4s linear infinite;
  }
  .lrv-static-fall-label {
    position: relative; z-index: 2; text-align: center; padding-top: 18px;
    font-family: "Courier New", monospace; font-weight: bold; font-size: 14px;
    color: #ffff00; text-shadow: 2px 2px 0 #000;
  }

  .lrv-fall-layer { position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 400; }
  .lrv-fall {
    position: absolute; top: 20%; left: 20%; font-size: 28px;
    text-shadow: 0 3px 6px rgba(0,0,0,0.6);
    transition: left 2.8s ease-in-out, top 2.8s ease-in-out, transform 2.8s ease-in-out;
  }

  @keyframes lrvBob { 0%,100% { transform: translateY(0) rotate(var(--r,0deg)); } 50% { transform: translateY(-14px) rotate(var(--r,0deg)); } }
  .lrv-ninja-layer { position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 401; }
  .lrv-ninja {
    position: absolute; font-size: 28px; opacity: 0.85;
    animation: lrvBob ease-in-out infinite;
    filter: drop-shadow(0 2px 5px rgba(0,0,0,0.6));
  }

  .lrv-popup {
    position: fixed; z-index: 999; width: 250px;
    background: #c0c0c0; border: 2px outset #eee; box-shadow: 0 8px 24px rgba(0,0,0,0.8);
    font-family: Tahoma, "MS Sans Serif", sans-serif; color: #000;
  }
  .lrv-popup-titlebar {
    background: linear-gradient(90deg, #000080, #1084d0);
    color: #fff; font-size: 12px; font-weight: 700; padding: 3px 6px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .lrv-popup-close {
    background: #c0c0c0; border: 1px outset #fff; color: #000; font-size: 10px; font-weight: 900;
    width: 16px; height: 14px; line-height: 14px; text-align: center; cursor: pointer; padding: 0;
  }
  .lrv-popup-body { padding: 10px; font-size: 12px; line-height: 1.5; text-align: center; }
  .lrv-popup-body b { display: block; font-size: 14px; margin-bottom: 4px; color: #000080; }
  .lrv-popup-cta {
    display: inline-block; margin-top: 8px; background: #008000; color: #fff; font-weight: 800;
    text-decoration: none; padding: 6px 14px; border: 2px outset #0c0; font-size: 11px;
  }

  .lrv-jukebox {
    display: flex; align-items: center; gap: 10px; background: #001a33; border: 3px outset #0099cc;
    padding: 8px 12px; margin: 0 0 14px;
  }
  .lrv-jukebox button {
    background: #003366; color: #00ffff; border: 2px outset #0099cc; font-size: 16px; width: 34px; height: 30px; cursor: pointer;
  }
  .lrv-jukebox .meta { flex: 1; font-family: "Courier New", monospace; }
  .lrv-jukebox .now-playing { font-size: 10px; color: #66ccff; }
  .lrv-jukebox .track-name { font-size: 14px; color: #ffff00; font-weight: bold; }
  .lrv-jukebox .track-credit { font-size: 10px; color: #66ccff; }
</style>"""


def page(filename, title, center_content_html, page_index=0, extra_head=""):
    left_bg = random_bg("left" + filename)
    right_bg = random_bg("right" + filename)
    main_bg = random_bg("main" + filename)
    body_bg = random_bg("body" + filename, no_bg_chance=0.15)
    ninja_layer = scattered_ninjas() if filename == "firehose.html" else ""

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>*~*~* {title} *~*~* Lazy River Outpost *~*~*</title>
<link rel="icon" href="data:,">
{STYLE_BLOCK}
{extra_head}
</head>
<body bgcolor="#000033" text="#00FFFF" link="#0000FF" vlink="#800080" alink="#FF0000"{bg_attr(body_bg)}>

{floating_waterfalls(10)}
{ninja_layer}
{popup_ads_block()}

<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td>
  <marquee behavior="alternate" scrollamount="6" bgcolor="#000080">
    <font face="Arial Black, Impact" size="6" color="#ffff00"><b class="blk">WELCOME TO THE ULTIMATE LAZY RIVER OUTPOST!</b></font>
  </marquee>
</td></tr>
</table>

<hr size="6" color="#00ccff" noshade>

<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
  <td width="16%" valign="top" bgcolor="#001a33"{bg_attr(left_bg)} style="padding:8px;border:4px ridge #0099cc;">
    <font color="#ffff00" size="3" face="Arial, Helvetica, sans-serif"><b class="blk">&#9776; RIVER MENU &#9776;</b></font><br><br>
    {nav_block(filename)}
    <hr size="2" color="#0099cc">
    <font size="1" color="#66ccff">&#9888; Best viewed in Netscape Navigator 4.0 at 800&times;600. Waterfalls require ActiveX.</font>
  </td>

  <td width="68%" valign="top" bgcolor="#000022"{bg_attr(main_bg)} style="padding:12px;border:4px ridge #0099cc;">
    {jukebox_block()}
    {center_content_html}
    <hr size="4" color="#00ccff" noshade>
    <center><font size="1" color="#888">&#128679; This page is permanently under construction, much like the surge channel jets. &#128679;</font></center>
    <center><font size="1" color="#888">&#9888; Best viewed in Netscape Navigator. Waterfall physics not guaranteed accurate. &#9888;</font></center>
    <br>
    <center><font size="1" color="#444">&larr; <a href="../index.html">Back to MEGAVISION</a> &middot; <a href="index.html">Lazy River Home</a></font></center>
  </td>

  <td width="16%" valign="top" bgcolor="#001a33"{bg_attr(right_bg)} style="padding:8px;border:4px ridge #0099cc;">
    <font color="#00ffff" size="3" face="Arial, Helvetica, sans-serif"><b class="blk">&#127754; SPLASH ZONE &#127754;</b></font><br><br>
    <font size="1" color="#66ccff">
    &#128167; did you know? &#128167;<br>
    3,000 feet is longer than eight football fields laid end to end.<br><br>
    &#128167; fun fact &#128167;<br>
    A full loop takes about as long as a sitcom episode, minus the ads (this site has ads).<br><br>
    &#128167; river tip &#128167;<br>
    Hug the inside bend through the surge channel for maximum current boost.<br>
    </font>
    <hr size="2" color="#0099cc">
    <font size="1" color="#66ccff">&#9888; ActiveX required for full waterfall spray effect &#9888;</font>
  </td>
</tr>
</table>

<hr size="6" color="#00ccff" noshade>
<center><font size="1" color="#444">&larr; <a href="../index.html">Back to MEGAVISION</a></font></center>

</body>
</html>
"""
    with open(filename, "w") as f:
        f.write(html)
    print(f"wrote lazy-river/{filename}")
