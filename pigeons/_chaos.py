"""
Shared 1990s web-anarchy chaos kit for the Pigeon Pages sub-site.

Deliberately built the OLD way: <table>-based layout, inline presentational
attributes (bgcolor, text, link, vlink, alink, background), <marquee>
(still genuinely functional in every modern browser as a legacy element),
and a small amount of <style> ONLY where there is truly no other way to
get the effect (blink simulation, since the <blink> tag itself has been
dead in every browser for over a decade; and tiled background patterns,
since we don't have real animated GIFs to host -- these are generated as
tiny inline SVG data URIs and applied via the classic HTML `background=`
attribute, not CSS background-image on a modern layout).

No flexbox, no grid, no frameworks. This is intentional -- see the design
brief. It looks broken on purpose.
"""
import base64
import json
import random

random.seed(77)

# ---------------------------------------------------------------- palette --
BODY_ATTRS = 'bgcolor="#000000" text="#00FF00" link="#0000FF" vlink="#800080" alink="#FF0000"'


def _svg_tile(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


TILES = {
    "stone": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20">'
        '<rect width="40" height="20" fill="#6b6b6b"/>'
        '<rect x="0" y="0" width="18" height="9" fill="#8a8a8a" stroke="#2b2b2b" stroke-width="1"/>'
        '<rect x="20" y="0" width="18" height="9" fill="#7d7d7d" stroke="#2b2b2b" stroke-width="1"/>'
        '<rect x="-10" y="10" width="18" height="9" fill="#828282" stroke="#2b2b2b" stroke-width="1"/>'
        '<rect x="10" y="10" width="18" height="9" fill="#767676" stroke="#2b2b2b" stroke-width="1"/>'
        '<rect x="30" y="10" width="18" height="9" fill="#828282" stroke="#2b2b2b" stroke-width="1"/></svg>'
    ),
    "galaxy": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60">'
        '<rect width="60" height="60" fill="#1a0033"/>'
        '<circle cx="6" cy="8" r="1.4" fill="#fff"/><circle cx="22" cy="40" r="1" fill="#fff"/>'
        '<circle cx="45" cy="15" r="1.6" fill="#ffd166"/><circle cx="52" cy="50" r="1.2" fill="#fff"/>'
        '<circle cx="30" cy="5" r="0.8" fill="#e63fb0"/><circle cx="12" cy="30" r="1" fill="#fff"/>'
        '<circle cx="38" cy="35" r="1.3" fill="#fff"/><circle cx="55" cy="25" r="0.9" fill="#7c3aed"/></svg>'
    ),
    "matrix": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="30">'
        '<rect width="20" height="30" fill="#000"/>'
        '<rect x="2" y="0" width="2" height="12" fill="#00ff41"/>'
        '<rect x="2" y="16" width="2" height="6" fill="#004411" opacity="0.6"/>'
        '<rect x="10" y="6" width="2" height="18" fill="#00ff41" opacity="0.7"/>'
        '<rect x="16" y="0" width="2" height="8" fill="#008822"/></svg>'
    ),
    "parchment": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
        '<rect width="50" height="50" fill="#e8dcb5"/>'
        '<circle cx="8" cy="10" r="2" fill="#d8c896" opacity="0.5"/>'
        '<circle cx="30" cy="35" r="3" fill="#cbb87f" opacity="0.4"/>'
        '<circle cx="42" cy="8" r="1.5" fill="#d8c896" opacity="0.5"/>'
        '<circle cx="18" cy="42" r="2.2" fill="#cbb87f" opacity="0.4"/></svg>'
    ),
    "checkerplate": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30">'
        '<rect width="30" height="30" fill="#9099a2"/>'
        '<rect width="30" height="30" fill="none" stroke="#6b727a" stroke-width="1"/>'
        '<circle cx="8" cy="8" r="2.4" fill="#b8c0c8"/><circle cx="22" cy="22" r="2.4" fill="#b8c0c8"/>'
        '<circle cx="22" cy="8" r="1.2" fill="#6b727a"/><circle cx="8" cy="22" r="1.2" fill="#6b727a"/></svg>'
    ),
    "flag": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
        '<rect width="40" height="40" fill="#b22234"/>'
        '<rect y="0" width="40" height="8" fill="#fff"/><rect y="16" width="40" height="8" fill="#fff"/>'
        '<rect y="32" width="40" height="8" fill="#fff"/><rect width="16" height="16" fill="#3c3b6e"/></svg>'
    ),
    "hazard": _svg_tile(
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
        '<rect width="40" height="40" fill="#111"/>'
        '<polygon points="0,40 20,0 30,0 10,40" fill="#ffcc00"/>'
        '<polygon points="30,40 40,10 40,0 20,40" fill="#ffcc00"/></svg>'
    ),
}

BLINK_STYLE = """<style>
  @keyframes chaosBlink { 0%,45% {visibility:visible;} 50%,95% {visibility:hidden;} 100% {visibility:visible;} }
  .blk { animation: chaosBlink 0.8s steps(1) infinite; }
  @keyframes chaosBlink2 { 0%,55% {visibility:visible;} 60%,95% {visibility:hidden;} 100% {visibility:visible;} }
  .blk2 { animation: chaosBlink2 0.6s steps(1) infinite; }
</style>"""

# ------------------------------------------------------------ banner stack --
BANNER_TEXTS = [
    ("&#9733; ARCHIE'S UNDERGROUND HACKER ZONE v3.2 &#9733;", "#111", "#00ff41", "#ff0000"),
    ("WELCOME TO THE INFOBAHN", "#000080", "#ffd700", "#fff"),
    ("!! DOWNLOAD ZONE !!", "#800000", "#ffff00", "#fff"),
    ("&#128330; PIGEON PALACE ONLINE &#128330;", "#4b0082", "#00ffff", "#ff00ff"),
    ("YOU ARE VISITOR #999999 -- THANK YOU!", "#003300", "#ccff00", "#fff"),
]


def banner_stack():
    rows = []
    for text, bg, fg, sh in BANNER_TEXTS:
        rows.append(
            f'<tr><td align="center" bgcolor="{bg}" style="padding:6px;">'
            f'<font face="Arial Black, Impact" size="6" color="{fg}">'
            f'<b style="text-shadow: 3px 3px 0 {sh}, -1px -1px 0 #000;">{text}</b></font></td></tr>'
        )
    return '<table width="100%" cellpadding="2" cellspacing="0" border="0">' + "".join(rows) + "</table>"


# ------------------------------------------------------------------ marquees --
def marquee_block():
    return f"""
  <marquee behavior="scroll" direction="left" scrollamount="15" bgcolor="#000080" style="color:#ffff00;font-weight:bold;font-size:16px;">
    &#9733; PIGEON PAGES &#9733; 20+ PAGES OF PURE PIGEON POWER &#9733; NOW ONLINE &#9733; TELL YOUR FRIENDS &#9733; PIGEON PAGES &#9733;
  </marquee>
  <marquee behavior="scroll" direction="right" scrollamount="8" bgcolor="#330033" style="color:#00ffff;font-size:14px;">
    &lt;&lt; best viewed in Netscape Navigator 4.0 at 800x600 &gt;&gt; no framez required &gt;&gt; 100% pigeon approved &gt;&gt;
  </marquee>
  <marquee behavior="alternate" scrollamount="6" bgcolor="#800000" style="color:#fff;font-weight:bold;">
    &#128330; BOUNCE BOUNCE BOUNCE &#128330; THIS TEXT CANNOT DECIDE WHERE IT WANTS TO GO &#128330;
  </marquee>
  <marquee behavior="scroll" direction="left" scrollamount="2" bgcolor="#003300" style="color:#00ff00;font-size:11px;">
    slow.......dial....up.......modem.......speeds.......connecting.......please.......wait.......
  </marquee>
  <marquee behavior="scroll" direction="left" scrollamount="30" bgcolor="#000" style="color:#ff00ff;font-size:20px;">
    FAST!!! FAST!!! FAST!!!
  </marquee>
  <table width="100%"><tr>
    <td width="70%">
      <marquee behavior="alternate" scrollamount="10" bgcolor="#1a0033" style="color:#ffd700;">
        &#9917;&#9733;&#9917; nested marquee inside a table cell because we can &#9733;&#9917;&#9733;
      </marquee>
    </td>
    <td width="30%" valign="top">
      <marquee behavior="scroll" direction="up" scrollamount="3" height="60" bgcolor="#000" style="color:#00ff00;font-size:10px;">
        PGN +0.02!!!<br>DOVE -0.01<br>SQUAB +1.40!!!<br>LOFT&amp;CO steady<br>!!!!!!!!!!!!<br>BUY BUY BUY
      </marquee>
    </td>
  </tr></table>
"""


# ----------------------------------------------------------------- badges --
BADGES = [
    ("#000080", "#fff", "Netscape<br>Navigator 4.0<br><b>Enhanced</b>"),
    ("#c0c0c0", "#000", "Made with<br><b>Notepad</b>"),
    ("#800000", "#fff", "Internet<br>Explorer<br><b>ENEMY</b>"),
    ("#003366", "#0ff", "Get <b>ICQ</b><br>Now! &#128172;"),
    ("#330066", "#fff", "<b>RealAudio</b><br>Enabled"),
    ("#ff6600", "#000", "<b>Winamp</b><br>It Really Kicks<br>the Ass"),
    ("#996600", "#fff", "&#9749; <b>Java</b><br>Powered"),
    ("#111", "#0f0", "<b>DirectX</b><br>6.0 Ready"),
]


def badge_stack():
    cells = "".join(
        f'<tr><td align="center" bgcolor="{bg}" width="88" height="31" style="border:2px outset #ccc;">'
        f'<font face="Arial" size="1" color="{fg}">{txt}</font></td></tr><tr><td height="4"></td></tr>'
        for bg, fg, txt in BADGES
    )
    webring = """
    <table bgcolor="#000066" cellpadding="4" border="2" width="130">
      <tr><td align="center"><font color="#ffff00" size="2"><b>&#128371; The Paranormal<br>Pigeon WebRing &#128371;</b></font></td></tr>
      <tr><td align="center"><font color="#fff" size="1">
        [<a href="#">Prev</a>] [<a href="#">Next</a>]<br>[<a href="#">Random</a>] [<a href="#">List All</a>]
      </font></td></tr>
      <tr><td align="center"><font color="#ccc" size="1">Site 47 of 212</font></td></tr>
    </table>"""
    return f'<table cellpadding="0" cellspacing="0">{cells}</table><br>{webring}'


# ------------------------------------------------------------- left sidebar --
BULLET_ICONS = ["&#128128;", "&#9762;", "&#128293;", "&#128340;", "&#128679;"]


def left_sidebar(links):
    """links: list of (label, href) tuples. Every other link is a fake/broken one automatically mixed in."""
    rows = []
    fake_targets = ["#", "http://localhost/coolstuff.html", "#", "http://geocities.com/pigeonzone/", "#"]
    for i, (label, href) in enumerate(links):
        icon = BULLET_ICONS[i % len(BULLET_ICONS)]
        rows.append(f'<font size="5" style="font-size:26px;">{icon} <a href="{href}">{label}</a></font><br>')
        if i % 2 == 1:
            fake = fake_targets[i % len(fake_targets)]
            rows.append(f'<font size="4" style="font-size:20px;">{BULLET_ICONS[(i+1) % len(BULLET_ICONS)]} <a href="{fake}">&gt;&gt; secret bonus link &lt;&lt;</a></font><br>')
    return "".join(rows)


# ------------------------------------------------------------- hit counters --
def hit_counters():
    def odometer(digits, label, color="#00ff00"):
        cells = "".join(
            f'<td bgcolor="#000" style="border:1px solid {color};padding:2px 4px;">'
            f'<font face="Courier New" size="5" color="{color}"><b>{d}</b></font></td>'
            for d in digits
        )
        return (
            f'<table cellpadding="0" cellspacing="1" bgcolor="{color}"><tr>{cells}</tr></table>'
            f'<center><font size="1" color="#ccc">{label}</font></center>'
        )
    return f"""<table><tr>
    <td align="center">{odometer("000342", "Hits Today")}</td>
    <td width="14"></td>
    <td align="center">{odometer("999999", "Total Visitors Since 1995", "#ffd700")}</td>
    <td width="14"></td>
    <td align="center">{odometer("ERR-42", "ERROR: COUNTER.PL NOT FOUND", "#ff0000")}</td>
  </tr></table>"""


# ------------------------------------------------------------- guestbook --
def guestbook_form():
    fields = ["Name", "Alias", "Handle", "ICQ UIN", "Email", "Homepage URL",
              "Browser Version", "Favorite UFO Incident"]
    rows = "".join(
        f'<tr><td align="right"><font size="2">{f}:</font></td>'
        f'<td><input type="text" name="{f.lower().replace(" ", "_")}" size="30"></td></tr>'
        for f in fields
    )
    return f"""
  <table bgcolor="#663300" cellpadding="8" border="4" style="border-style:ridge;">
    <tr><td>
      <center><font size="5" color="#ffd700"><b>&#128214; Sign My Guestbook! &#128214;</b></font><br>
      <font size="2" color="#fff">(spinning 3D book with quill pen goes here -- use your imagination, it's the 90s)</font></center>
      <form action="#" onsubmit="alert('Thank you for signing! (this form does not actually go anywhere, it is 1997)'); return false;">
        <table cellpadding="3">
          {rows}
        </table>
        <font size="2" color="#fff">Leave a cool message for the webmaster:</font><br>
        <textarea name="message" rows="5" cols="50" bgcolor="#fff"></textarea><br><br>
        <input type="submit" value="BLAST OFF!" style="background:#ffcc00;border:4px outset #fff;font-weight:bold;font-size:16px;padding:6px 20px;">
        &nbsp;&nbsp;
        <input type="reset" value="WIPE CLEAN!" style="background:#cc0000;color:#fff;border:4px outset #fff;font-weight:bold;font-size:16px;padding:6px 20px;">
      </form>
    </td></tr>
  </table>"""


# ------------------------------------------------------- dead-end buttons --
DEAD_END_LABELS = [
    "DO NOT PRESS", "FREE MP3s", "SECRET AREA", "WIN A CORVETTE", "THE MATRIX",
    "COOL JAVASCRIPT", "CLICK FOR PRIZE", "PIGEON GENERATOR", "??? MYSTERY ???",
    "1000 FREE AOL HOURS", "HACK THE PLANET", "NUCLEAR CODES", "TIME MACHINE",
    "INVISIBILITY", "X-RAY VISION", "MEET THE WEBMASTER", "DELETE INTERNET",
    "PIGEON FACTS.EXE", "RANDOM BUTTON", "DO NOT PRESS TWICE",
]
DEAD_END_MSGS = [
    "Under Construction! Come back in 1997!", "Error 404: Brain Not Found!",
    "This feature requires a 56k modem.", "Access Denied by the Pigeon Council.",
    "You have been visited by the Squab of Good Fortune.",
]
DEAD_END_COLORS = ["#ff0000", "#00ff00", "#ffff00", "#00ffff", "#ff00ff", "#ff8800", "#8800ff", "#00ff88"]


def dead_end_buttons():
    random.seed(99)
    cells = []
    for i, label in enumerate(DEAD_END_LABELS):
        color = DEAD_END_COLORS[i % len(DEAD_END_COLORS)]
        msg = DEAD_END_MSGS[i % len(DEAD_END_MSGS)]
        cells.append(
            f'<td align="center" style="padding:4px;">'
            f'<button onclick="alert(&quot;{msg}&quot;)" '
            f'style="background:{color};border:3px outset #fff;font-weight:bold;font-size:11px;padding:8px;width:120px;">'
            f'{label}</button></td>'
        )
    rows = []
    for i in range(0, len(cells), 4):
        rows.append("<tr>" + "".join(cells[i:i + 4]) + "</tr>")
    return f'<table cellpadding="2" cellspacing="4" align="center">{"".join(rows)}</table>'


# ------------------------------------------------------------ media bombs --
ASCII_PIGEON = r"""
        __
      <(o )___
       ( ._> /
        `---'   coo... coo... coo...
"""

def warning_banner():
    return (
        '<marquee behavior="alternate" scrollamount="4" bgcolor="#ff0000">'
        '<font size="4" color="#ffff00"><b class="blk">'
        'SITE BEST VIEWED IN 800x600 RESOLUTION WITH 16-BIT HIGH COLOR. '
        'IF YOU USE OPERA, LEAVE NOW.</b></font></marquee>'
    )


def ascii_art_block():
    return (
        f'<pre style="background:#000;color:#00ff41;padding:10px;border:2px solid #00ff41;'
        f'font-size:14px;text-shadow:0 0 6px #00ff41;">{ASCII_PIGEON}</pre>'
    )


def construction_zone():
    return f"""
  <table width="100%" background="{TILES['hazard']}" border="4" style="border-style:ridge;border-color:#ffcc00;">
    <tr><td align="center" style="padding:14px;">
      <font size="6">&#128679;&#128679;&#128679;</font><br>
      <font color="#ffcc00" size="5"><b class="blk2">PARDON OUR DUST!</b></font><br>
      <font color="#fff" size="3">This section is currently being constructed by the webmaster's cousin!</font><br>
      <font size="6">&#9888;&#128119;&#9888;</font>
    </td></tr>
  </table>"""


def webmaster_bio():
    return """
  <table bgcolor="#222" border="3" cellpadding="10">
    <tr>
      <td width="140" valign="top">
        <table bgcolor="#001a00" border="2"><tr><td>
          <font color="#00ff00" size="1">[WEBCAM.JPG]<br>
          <div style="width:120px;height:120px;background:repeating-linear-gradient(45deg,#0a2a0a,#0a2a0a 4px,#001500 4px,#001500 8px);filter:hue-rotate(60deg) saturate(2);"></div>
          low-res, heavy green tint, as required by law
          </font>
        </td></tr></table>
      </td>
      <td valign="top">
        <font color="#00ff00" size="4"><b>&#128421; About The Webmaster &#128421;</b></font><br>
        <font color="#ccc" size="2">
        Hi!!! I'm the webmaster of Pigeon Pages!!! I am a high school student who is REALLY into
        DOOM, UFOs, and skateboarding (in that order, mostly). I built this entire site by myself
        using Notepad and a 28.8k modem. My favorite pigeon breed is the Jacobin because it looks
        like it's wearing a tiny cape. I believe pigeons may be government surveillance drones but
        I keep them anyway because they're cool. Email me if you also think the moon landing and
        pigeon domestication are connected somehow (they're not, I checked, but email me anyway).
        </font>
      </td>
    </tr>
  </table>"""


def mouse_trail_note():
    return (
        '<font size="1" color="#888">'
        '&#9888; ActiveX controls must be enabled to view the trailing fire particle cursor effect. '
        '&#9888;</font>'
    )


BGSOUND_FILE = "allstar.mp3"


def bgsound_tags():
    # a real <audio> so it genuinely plays, PLUS the cosmetic <bgsound> tag
    # for period authenticity (a true no-op in every modern browser).
    # NOTE: <embed autostart> used to be here too, but modern browsers give
    # it a real native audio player and actually autoplay it -- that was
    # duplicating the <audio> track and playing the song twice. Dropped it.
    return f"""
  <bgsound src="{BGSOUND_FILE}" loop="infinite">
  <audio id="chaosBgm" autoplay loop style="display:none;"><source src="{BGSOUND_FILE}" type="audio/mpeg"></audio>
  <script>
    (function() {{
      var a = document.getElementById('chaosBgm');
      if (!a) return;
      var p = a.play();
      if (p && p.catch) {{
        p.catch(function() {{
          document.addEventListener('click', function once() {{
            a.play();
            document.removeEventListener('click', once);
          }}, {{ once: true }});
        }});
      }}
    }})();
  </script>"""


# ------------------------------------------------------------- page shell --
NAV_PAGES = [
    ("index.html", "Home"),
    ("history.html", "History"),
    ("war-pigeons.html", "War Pigeons"),
    ("famous-fanciers.html", "Famous Fanciers"),
    ("famous-pigeons.html", "Famous Pigeons"),
    ("breeds-fancy1.html", "Fancy Breeds I"),
    ("breeds-fancy2.html", "Fancy Breeds II"),
    ("breeds-racing.html", "Racing Breeds"),
    ("breeds-utility.html", "Utility Breeds"),
    ("anatomy.html", "Anatomy"),
    ("homing-navigation.html", "Homing Navigation"),
    ("pigeon-racing.html", "The Sport"),
    ("pigeon-post.html", "Pigeon Post"),
    ("building-lofts.html", "Lofts"),
    ("feeding-care.html", "Feeding &amp; Care"),
    ("health.html", "Health"),
    ("breeding.html", "Breeding"),
    ("behavior.html", "Behavior"),
    ("mythology.html", "Myth &amp; Culture"),
    ("gallery1.html", "Gallery I"),
    ("gallery2.html", "Gallery II"),
    ("gallery3.html", "Gallery III"),
    ("gallery4.html", "Gallery IV"),
    ("gallery5.html", "Gallery V"),
    ("faq.html", "FAQ"),
    ("guestbook.html", "Guestbook"),
    ("links.html", "Links"),
    ("webmaster.html", "Webmaster"),
]

RIGHT_TILES = ["stone", "galaxy", "matrix", "parchment", "checkerplate", "flag"]

FLYING_LAYER_STYLE = """<style>
  @keyframes chaosBob { 0%,100% { transform: translateY(0) rotate(var(--r,0deg)); } 50% { transform: translateY(-14px) rotate(var(--r,0deg)); } }
  .pg-flying-layer, .pg-ninja-layer { position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 500; }
  .pg-pigeon {
    position: absolute; top: 30%; left: 30%; font-size: 34px;
    text-shadow: 0 3px 6px rgba(0,0,0,0.6);
    transition: left 2.4s ease-in-out, top 2.4s ease-in-out, transform 2.4s ease-in-out;
  }
  .pg-ninja {
    position: absolute; font-size: 26px; opacity: 0.85;
    animation: chaosBob ease-in-out infinite;
    filter: drop-shadow(0 2px 5px rgba(0,0,0,0.6));
  }
</style>"""

PIGEON_EMOJIS = ["&#128330;", "&#128059;"]  # dove-of-peace + bird


def flying_pigeons_layer(n=12):
    spans = "\n    ".join(
        f'<span class="pg-pigeon" id="pgBird{i}">{PIGEON_EMOJIS[i % 2]}</span>' for i in range(n)
    )
    script = f"""
<script>
(function() {{
  var birds = document.querySelectorAll('.pg-pigeon');
  birds.forEach(function(b, i) {{
    var lastX = 20 + (i * 7) % 80;
    function fly() {{
      var x = 4 + Math.random() * 88;
      var y = 4 + Math.random() * 88;
      var facingLeft = x < lastX;
      var tilt = (Math.random() * 20 - 10).toFixed(1);
      b.style.left = x + '%';
      b.style.top = y + '%';
      b.style.transform = 'scaleX(' + (facingLeft ? -1 : 1) + ') rotate(' + tilt + 'deg)';
      lastX = x;
      setTimeout(fly, 1800 + Math.random() * 2200);
    }}
    setTimeout(fly, i * 260);
  }});
}})();
</script>"""
    return f'<div class="pg-flying-layer">{spans}</div>{script}'


# ---- win95-style popup ads advertising the snowmobile lifestyle page ----
POPUP_STYLE = """<style>
  .pg-popup {
    position: fixed; z-index: 999; width: 240px;
    background: #c0c0c0; border: 2px outset #eee; box-shadow: 0 8px 24px rgba(0,0,0,0.8);
    font-family: Tahoma, "MS Sans Serif", sans-serif; color: #000;
  }
  .pg-popup-titlebar {
    background: linear-gradient(90deg, #000080, #1084d0);
    color: #fff; font-size: 12px; font-weight: 700; padding: 3px 6px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .pg-popup-close {
    background: #c0c0c0; border: 1px outset #fff; color: #000; font-size: 10px; font-weight: 900;
    width: 16px; height: 14px; line-height: 14px; text-align: center; cursor: pointer; padding: 0;
  }
  .pg-popup-body { padding: 10px; font-size: 12px; line-height: 1.5; text-align: center; }
  .pg-popup-body b { display: block; font-size: 14px; margin-bottom: 4px; color: #cc0000; }
  .pg-popup-cta {
    display: inline-block; margin-top: 8px; background: #008000; color: #fff; font-weight: 800;
    text-decoration: none; padding: 6px 14px; border: 2px outset #0c0; font-size: 11px;
  }
</style>"""

POPUP_ADS = [
    ("SNOWMOBILE.EXE", "&#10024; STOP LOOKING AT PIGEONS &#10024;", "There is an ENTIRE Snowmobile Lifestyle happening RIGHT NOW while you sit here reading about birds. Don't you want more out of life???", "SEE THE LIFESTYLE &rarr;"),
    ("YETIFUEL.EXE", "&#128293; YOUR BLOOD IS TOO WARM &#128293;", "Pigeons don't need Yeti Fuel Energy Elixir because pigeons are already cold-blooded enough. YOU are not a pigeon. Fix that.", "FUEL UP NOW &rarr;"),
    ("WINNER.EXE", "&#127942; CONGRATULATIONS!!! &#127942;", "You are the LUCKY visitor!!! Click below to claim your FREE trip to the Snowmobile Lifestyle before this window closes forever!", "CLAIM NOW &rarr;"),
    ("ARCTIC.EXE", "&#10084; UNTAMED WINTER DESTINY &#10084;", "This pigeon site is great and all, but have you considered a SNOWMOBILE? MEGAVISION thinks you should. MEGAVISION is always right.", "ENTER THE LIFESTYLE &rarr;"),
]
POPUP_ADS_JSON = json.dumps([list(ad) for ad in POPUP_ADS])


def popup_ads_block():
    return f"""
<div id="pgPopupLayer"></div>
<script>
(function() {{
  var popupAds = {POPUP_ADS_JSON};
  var linkPrefix = "../";
  var layer = document.getElementById('pgPopupLayer');
  var openPopups = 0;
  var MAX_POPUPS = 3;

  function spawnPopup() {{
    if (openPopups >= MAX_POPUPS) return;
    openPopups++;
    var ad = popupAds[Math.floor(Math.random() * popupAds.length)];
    var win = document.createElement('div');
    win.className = 'pg-popup';
    var top = 10 + Math.random() * 60;
    var left = 5 + Math.random() * 60;
    win.style.top = top + '%';
    win.style.left = left + '%';
    win.innerHTML =
      '<div class="pg-popup-titlebar"><span>' + ad[0] + '</span><button class="pg-popup-close" type="button">&#10005;</button></div>' +
      '<div class="pg-popup-body"><b>' + ad[1] + '</b>' + ad[2] +
      '<br><a class="pg-popup-cta" href="' + linkPrefix + 'snowmobile-lifestlye.html">' + ad[3] + '</a></div>';
    layer.appendChild(win);
    function close() {{
      if (win.parentNode) {{ win.parentNode.removeChild(win); openPopups--; }}
    }}
    win.querySelector('.pg-popup-close').addEventListener('click', close);
    setTimeout(close, 9000 + Math.random() * 4000);
  }}

  function scheduleNextPopup() {{
    var delay = 6000 + Math.random() * 8000;
    setTimeout(function() {{ spawnPopup(); scheduleNextPopup(); }}, delay);
  }}
  scheduleNextPopup();
}})();
</script>"""


# ---- gigantic, deliberately inconsistent "NEXT" button at the bottom of every page --
NEXT_BUTTON_VARIANTS = [
    dict(size=72, bg="#ff0000", fg="#ffff00", font="Impact, 'Arial Black', sans-serif", align="center", rotate=0, blink=True, label="&#9654;&#9654;&#9654; NEXT &#9654;&#9654;&#9654;"),
    dict(size=26, bg="#00ff00", fg="#000000", font="'Comic Sans MS', cursive", align="left", rotate=-3, blink=False, label="click here for next page..."),
    dict(size=90, bg="#000080", fg="#00ffff", font="'Courier New', monospace", align="right", rotate=2, blink=True, label="NEXT &gt;&gt;&gt;"),
    dict(size=44, bg="#ffcc00", fg="#800080", font="'Arial Black', sans-serif", align="center", rotate=-6, blink=False, label="MORE PIGEONS THIS WAY &#128330;"),
    dict(size=60, bg="#800000", fg="#00ff00", font="Impact, sans-serif", align="left", rotate=4, blink=True, label="CONTINUE &#9654;"),
    dict(size=18, bg="#ffffff", fg="#ff00ff", font="'Times New Roman', serif", align="right", rotate=0, blink=False, label="(next page)"),
    dict(size=80, bg="#00ffff", fg="#ff0000", font="Haettenschweiler, Impact, sans-serif", align="center", rotate=8, blink=True, label="NEXT PAGE NOW!!!"),
    dict(size=34, bg="#4b0082", fg="#ffd700", font="Verdana, sans-serif", align="left", rotate=-2, blink=False, label="&gt;&gt; onward, pigeon friend &gt;&gt;"),
]


def giant_next_button(page_index):
    v = NEXT_BUTTON_VARIANTS[page_index % len(NEXT_BUTTON_VARIANTS)]
    next_index = (page_index + 1) % len(NAV_PAGES)
    href, _ = NAV_PAGES[next_index]
    blink_cls = ' class="blk"' if v["blink"] else ""
    pad_v = max(6, v["size"] // 4)
    pad_h = max(10, v["size"] // 2)
    return f"""
  <div align="{v['align']}" style="margin:26px 0;">
    <a href="{href}"{blink_cls} style="display:inline-block;font-family:{v['font']};font-size:{v['size']}px;
      font-weight:900;background:{v['bg']};color:{v['fg']};padding:{pad_v}px {pad_h}px;border:6px outset #fff;
      text-decoration:none;transform:rotate({v['rotate']}deg);text-shadow:2px 2px 0 #000;">{v['label']}</a>
  </div>"""


NINJA_SPOTS = [
    ("4%", "6%", -8, "2.6s"), ("8%", "92%", 10, "3.1s"), ("22%", "2%", -14, "2.3s"),
    ("35%", "95%", 6, "3.4s"), ("50%", "3%", -6, "2.8s"), ("62%", "93%", 12, "2.5s"),
    ("78%", "5%", -10, "3.2s"), ("88%", "90%", 8, "2.7s"),
]


def scattered_ninjas():
    spans = "\n    ".join(
        f'<span class="pg-ninja" style="top:{top};left:{left};--r:{rot}deg;animation-duration:{dur};">&#129399;</span>'
        for top, left, rot, dur in NINJA_SPOTS
    )
    return f'<div class="pg-ninja-layer">{spans}</div>'


def page(filename, title, center_content_html, tile_key="galaxy", page_index=0):
    left_links = [(label, href) for href, label in NAV_PAGES if href != filename]
    right_tile = RIGHT_TILES[page_index % len(RIGHT_TILES)]
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>*~*~* {title} *~*~* Pigeon Pages *~*~*</title>
<link rel="icon" href="data:,">
{BLINK_STYLE}
{FLYING_LAYER_STYLE}
{POPUP_STYLE}
</head>
<body {BODY_ATTRS}>
{bgsound_tags()}
{flying_pigeons_layer(12)}
{scattered_ninjas()}
{popup_ads_block()}
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td colspan="3">
{banner_stack()}
{marquee_block()}
</td></tr>
<tr>
  <td width="17%" valign="top" background="{TILES['stone']}" style="padding:8px;border:4px ridge #888;">
    <font color="#ffff00" size="3"><b class="blk">&#9776; NAVIGATION &#9776;</b></font><br><br>
    {left_sidebar(left_links)}
    <br><hr>
    {mouse_trail_note()}
  </td>
  <td width="66%" valign="top" background="{TILES['parchment']}" style="padding:10px;border:4px ridge #444;">
    <table width="100%" bgcolor="#000000" style="border:3px double #ffd700;" cellpadding="14">
    <tr><td>
      <font color="#00ff00">
      {center_content_html}
      </font>
      {giant_next_button(page_index)}
    </td></tr>
    </table>
  </td>
  <td width="17%" valign="top" background="{TILES[right_tile]}" style="padding:8px;border:4px ridge #888;">
    <font color="#00ffff" size="3"><b class="blk2">&#9733; COOL LINKS &amp; BADGES &#9733;</b></font><br><br>
    {badge_stack()}
  </td>
</tr>
<tr><td colspan="3">
  {warning_banner()}
  <center>{hit_counters()}</center>
  <br>
  <marquee behavior="scroll" direction="left" scrollamount="12" bgcolor="#000">
    <font color="#00ff00" size="1">&copy; forever &middot; Pigeon Pages is not affiliated with any actual pigeons &middot; view source if you dare &middot; &lt;a href="../index.html"&gt;back to MEGAVISION&lt;/a&gt;</font>
  </marquee>
</td></tr>
</table>
<center><font size="1" color="#444">&larr; <a href="../index.html">Back to MEGAVISION</a></font></center>
</body>
</html>
"""
    with open(filename, "w") as f:
        f.write(html)
    print(f"wrote pigeons/{filename}")
