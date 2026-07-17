"""
soccer.html -- an early-web1-style penalty shootout minigame. Deliberately
busy: marquees, floating text in a dozen fonts, blinking everything, a
real goal-click aim-and-shoot game, ~50/50 odds, 90s square-wave sound
effects via Web Audio (no external files needed), and "My Name Is Jonas"
(the same real mp3 used on the snowmobile lifestyle page) firing on every
kick. Ten seconds after a shot, the lifestyle page loads into an on-page
frame.
"""
import json
import random

from common import head, foot

random.seed(11)

FLOATERS = [
    ("KICK IT!!!", "gold", -6, "4%", "3%", "30px"),
    ("100% Real Soccer Action", "pink", 4, "6%", "68%", "16px"),
    ("Est. Whenever", "blue", -3, "18%", "84%", "14px"),
    ("Awesome Graphics!", "violet", 5, "30%", "1%", "18px"),
    ("Now In Stereo Sound", "crimson", -4, "40%", "80%", "15px"),
    ("Y2K Ready", "gold", 3, "58%", "2%", "16px"),
    ("Best Goalie AI Ever", "blue", -5, "66%", "82%", "15px"),
    ("Download More RAM", "pink", 2, "78%", "4%", "14px"),
    ("You vs The Machine", "violet", -2, "86%", "76%", "18px"),
]

COLOR_VAR = {
    "gold": "var(--mv-gold)", "pink": "var(--mv-pink)", "blue": "var(--mv-blue)",
    "violet": "var(--mv-violet)", "crimson": "var(--mv-crimson)",
}

floater_html = "\n      ".join(
    f'<div class="sc-float blink" style="top:{top};left:{left};font-size:{size};'
    f'color:{COLOR_VAR[color]};transform:rotate({rot}deg);">{text}</div>'
    for text, color, rot, top, left, size in FLOATERS
)

BADGES = [
    ("#000080", "#fff", "BEST VIEWED IN<br>NETSCAPE 4.0<br>@ 800&times;600"),
    ("#006400", "#fff", "100% PURE<br>SOCCER<br>ACTION"),
    ("#ffd166", "#000", "&#9917; GOAL OF<br>THE<br>CENTURY"),
    ("#800080", "#fff", "POWERED BY<br><b>Java Applets</b>"),
    ("#c00", "#fff", "HACKER<br>SAFE&trade;<br>CERTIFIED"),
    ("#000", "#0f0", "98% UPTIME<br>GUARANTEED*"),
]
badge_html = "\n      ".join(
    f'<div class="web1-badge" style="background:{bg};color:{fg};">{label}</div>'
    for bg, fg, label in BADGES
)

# 5 helicopters, flying around the whole page independently (same random-walk
# pattern as the snowmobile lifestyle page)
heli_html = "\n    ".join(f'<span class="sc-heli" id="scHeli{i}">&#128641;</span>' for i in range(5))

# extra decorative ninjas (the goalkeeper stays a ninja too -- this is on
# purpose) scattered around the page with a lazy idle bob
NINJA_SPOTS = [
    ("6%", "10%", -10, "3.1s"), ("10%", "88%", 8, "2.6s"), ("40%", "6%", -6, "3.6s"),
    ("55%", "90%", 12, "2.9s"), ("85%", "8%", -12, "3.3s"), ("90%", "85%", 6, "2.4s"),
]
ninja_html = "\n    ".join(
    f'<span class="sc-ninja" style="top:{top};left:{left};--r:{rot}deg;animation-duration:{dur};">&#129399;</span>'
    for top, left, rot, dur in NINJA_SPOTS
)

# bouncing soccer balls scattered across the page, each losing height on
# every bounce like it's actually got gravity
random.seed(22)
BALL_COUNT = 10
bounce_balls = []
for i in range(BALL_COUNT):
    left = random.uniform(2, 94)
    size = random.randint(20, 40)
    dur = random.uniform(2.2, 4.0)
    delay = random.uniform(0, 2.5)
    bounce_balls.append(
        f'<span class="sc-bounce-ball" style="left:{left:.1f}%;font-size:{size}px;'
        f'animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s;">&#9917;</span>'
    )
bounce_ball_html = "\n    ".join(bounce_balls)

# ---- banner ads + popup ads advertising the snowmobile lifestyle page,
# firing at random while you play ----
BANNER_ADS = [
    ("#000080", "#ffd166", "&#9973; GET WILD!!! Visit the SNOWMOBILE LIFESTYLE page NOW &#9973; &#128072; CLICK HERE &#128072;"),
    ("#800080", "#fff", "&#127942; YOU could be Arctic Explorer #1,000,000 &#127942; ENTER THE LIFESTYLE &rarr;"),
    ("#006400", "#fff", "&#10024; 100% FREE Snowmobile Rides (offer not real) &#10024; CLICK NOW!!!"),
    ("#c00", "#ffd166", "&#128293; HOT HOT HOT Winter Deals Inside &#128293; DO NOT MISS OUT"),
]
banner_html = "\n    ".join(
    f'<div class="sc-banner-ad" data-bg="{bg}" data-fg="{fg}" style="display:none;background:{bg};color:{fg};">'
    f'<a href="snowmobile-lifestlye.html" style="color:{fg};text-decoration:none;">{copy}</a></div>'
    for bg, fg, copy in BANNER_ADS
)

POPUP_ADS = [
    ("AD.EXE", "&#127942; CONGRATULATIONS!!! &#127942;", "You are the LUCKY visitor!!! Click below to claim your FREE trip to the Snowmobile Lifestyle!"),
    ("WINNER.EXE", "&#10024; YOU'VE WON! &#10024;", "Our system has selected YOU for a complimentary Arctic Soul Seeker starter pack. Do not refresh!"),
    ("HOTDEAL.EXE", "&#128293; LAST CHANCE &#128293;", "Prices this low will NEVER be seen again. The Lifestyle is calling. Answer it."),
]
popup_ads_json = json.dumps([list(ad) for ad in POPUP_ADS])

page = head("Soccer", "soccer.html") + f"""
<style>
  @keyframes scBlink {{ 0%, 45% {{ opacity: 1; }} 50%, 95% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
  .blink {{ animation: scBlink 1s steps(1) infinite; }}
  @keyframes scMarquee {{ 0% {{ transform: translateX(6%); }} 100% {{ transform: translateX(-106%); }} }}
  @keyframes scKeeper {{ 0%, 100% {{ left: 14%; }} 50% {{ left: 74%; }} }}
  @keyframes scSpin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
  @keyframes scConfetti {{
    0% {{ transform: translateY(-20px) rotate(0deg); opacity: 1; }}
    100% {{ transform: translateY(420px) rotate(540deg); opacity: 0; }}
  }}
  @keyframes scPulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.15); }} }}
  @keyframes scShake {{ 0%,100% {{ transform: translateX(0); }} 20% {{ transform: translateX(-8px); }} 40% {{ transform: translateX(8px); }} 60% {{ transform: translateX(-6px); }} 80% {{ transform: translateX(6px); }} }}
  @keyframes scBob {{ 0%, 100% {{ transform: translateY(0) rotate(var(--r, 0deg)); }} 50% {{ transform: translateY(-14px) rotate(var(--r, 0deg)); }} }}
  @keyframes scBounce {{
    0%   {{ transform: translateY(0) scale(1, 1); }}
    12%  {{ transform: translateY(-160px) scale(1, 1); }}
    24%  {{ transform: translateY(0) scale(1.2, 0.8); }}
    36%  {{ transform: translateY(-90px) scale(1, 1); }}
    48%  {{ transform: translateY(0) scale(1.15, 0.85); }}
    60%  {{ transform: translateY(-45px) scale(1, 1); }}
    72%  {{ transform: translateY(0) scale(1.1, 0.9); }}
    84%  {{ transform: translateY(-16px) scale(1, 1); }}
    92%  {{ transform: translateY(0) scale(1.05, 0.95); }}
    100% {{ transform: translateY(0) scale(1, 1); }}
  }}

  .sc-heli-layer {{ position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 60; }}
  .sc-heli {{
    position: absolute; top: 30%; left: 30%; font-size: 46px;
    text-shadow: 0 4px 10px rgba(0,0,0,0.6);
    transition: left 2.6s ease-in-out, top 2.6s ease-in-out, transform 2.6s ease-in-out;
  }}
  .sc-ninja {{
    position: absolute; font-size: 30px; z-index: 2; opacity: 0.85;
    animation: scBob ease-in-out infinite;
    filter: drop-shadow(0 2px 6px rgba(0,0,0,0.6));
  }}
  .sc-bounce-layer {{ position: absolute; inset: 0; bottom: 0; pointer-events: none; overflow: hidden; z-index: 1; }}
  .sc-bounce-ball {{
    position: absolute; bottom: 0; animation: scBounce ease-out infinite;
    filter: drop-shadow(0 4px 4px rgba(0,0,0,0.5));
  }}

  .sc-page {{
    position: relative;
    overflow: hidden;
    background:
      repeating-linear-gradient(45deg, rgba(124,58,237,0.08) 0px, rgba(124,58,237,0.08) 2px, transparent 2px, transparent 30px),
      repeating-linear-gradient(-45deg, rgba(46,107,255,0.06) 0px, rgba(46,107,255,0.06) 2px, transparent 2px, transparent 30px),
      var(--mv-black);
    padding: 24px 0 60px;
  }}
  .sc-float {{ position: absolute; font-weight: 800; z-index: 2; text-shadow: 0 2px 0 rgba(0,0,0,0.7), 0 0 14px currentColor; max-width: 180px; line-height: 1.2; }}

  .sc-marquee-wrap {{
    background: var(--mv-black-2); border-top: 2px solid var(--mv-gold); border-bottom: 2px solid var(--mv-gold);
    overflow: hidden; white-space: nowrap; padding: 8px 0; margin-bottom: 22px;
  }}
  .sc-marquee-text {{
    display: inline-block; padding-left: 100%; animation: scMarquee 15s linear infinite;
    font-weight: 800; color: var(--mv-gold); letter-spacing: 0.06em; font-size: 14px; text-transform: uppercase;
  }}

  .sc-title {{
    text-align: center; font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', sans-serif;
    font-size: 40px; margin: 6px 0; text-shadow: 3px 3px 0 #000, -1px -1px 0 var(--mv-gold);
  }}
  .sc-sub {{ text-align: center; color: var(--mv-ink-muted); font-size: 13px; margin-bottom: 18px; }}

  .sc-badge-row {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin-bottom: 20px; position: relative; z-index: 5; }}
  .web1-badge {{
    width: 88px; height: 31px; display: flex; align-items: center; justify-content: center; text-align: center;
    font-size: 8px; font-weight: 700; line-height: 1.15; color: #000; border: 2px outset #eee; font-family: Tahoma, sans-serif;
  }}

  .sc-scoreboard {{
    display: flex; justify-content: center; gap: 24px; margin-bottom: 18px; position: relative; z-index: 5;
  }}
  .sc-scorebox {{
    background: #000; border: 2px solid var(--mv-chrome-600); border-radius: 6px; padding: 8px 18px; text-align: center;
    font-family: ui-monospace, monospace;
  }}
  .sc-scorebox .lbl {{ font-size: 9px; color: var(--mv-ink-muted); letter-spacing: 0.1em; }}
  .sc-scorebox .val {{ font-size: 22px; font-weight: 800; color: #3fd17a; }}

  .sc-arena {{ max-width: 640px; margin: 0 auto 20px; position: relative; z-index: 5; }}
  .sc-goal-frame {{
    position: relative;
    padding: 0 16px 0 16px;
    background: linear-gradient(180deg, #1a6b33 0%, #0d3d1f 70%, #0a2a15 100%);
    box-shadow: 0 0 40px rgba(255,209,102,0.25), inset 0 -20px 40px rgba(0,0,0,0.4);
  }}
  .sc-crossbar {{
    height: 16px;
    background: linear-gradient(180deg, #fff 0%, #d8d8e0 45%, #9a9aa8 55%, #fff 100%);
    border-radius: 6px;
    box-shadow: 0 3px 6px rgba(0,0,0,0.5);
    margin: 0 -16px;
  }}
  .sc-post {{
    position: absolute;
    top: 0; bottom: 0;
    width: 16px;
    background: linear-gradient(90deg, #fff 0%, #d8d8e0 45%, #9a9aa8 55%, #fff 100%);
    box-shadow: 0 0 6px rgba(0,0,0,0.5);
  }}
  .sc-post.left {{ left: 0; }}
  .sc-post.right {{ right: 0; }}
  .sc-goal {{
    position: relative;
    height: 320px;
    background:
      repeating-linear-gradient(45deg, rgba(255,255,255,0.16) 0 1px, transparent 1px 16px),
      repeating-linear-gradient(-45deg, rgba(255,255,255,0.16) 0 1px, transparent 1px 16px),
      repeating-linear-gradient(45deg, rgba(255,255,255,0.08) 0 1px, transparent 1px 32px),
      repeating-linear-gradient(-45deg, rgba(255,255,255,0.08) 0 1px, transparent 1px 32px),
      linear-gradient(180deg, #0d3d1f, #0a2a15);
    cursor: crosshair;
    overflow: hidden;
  }}
  .sc-keeper {{
    position: absolute; bottom: 6px; font-size: 46px; left: 14%;
    animation: scKeeper 2.1s ease-in-out infinite;
    filter: drop-shadow(0 4px 6px rgba(0,0,0,0.6));
    z-index: 3; pointer-events: none;
  }}
  .sc-ball {{
    position: absolute; left: 50%; top: 92%; font-size: 34px; transform: translate(-50%, -50%);
    z-index: 4; pointer-events: none; filter: drop-shadow(0 3px 5px rgba(0,0,0,0.6));
  }}
  .sc-instructions {{ text-align: center; font-size: 12px; color: var(--mv-gold); font-weight: 700; margin-top: 10px; }}

  .sc-result {{
    position: absolute; inset: 0; display: none; align-items: center; justify-content: center;
    flex-direction: column; z-index: 6; pointer-events: none; overflow: hidden;
  }}
  .goal-text {{
    font-family: Impact, sans-serif; font-size: 46px; color: var(--mv-gold);
    text-shadow: 3px 3px 0 #c00, -2px -2px 0 #fff; animation: scPulse 0.5s ease-in-out infinite;
  }}
  .miss-x {{ font-size: 140px; animation: scShake 0.5s ease-in-out; filter: drop-shadow(0 0 20px red); }}
  .miss-text {{ font-family: Impact, sans-serif; font-size: 26px; color: #ff3b3b; text-shadow: 2px 2px 0 #000; margin-top: 6px; }}
  .confetti {{ position: absolute; top: -20px; font-size: 22px; animation: scConfetti 1.8s ease-in forwards; }}

  .sc-frame-wrap {{ max-width: 640px; margin: 0 auto 20px; position: relative; z-index: 5; }}
  .sc-frame-label {{
    background: #000; color: var(--mv-gold); font-size: 11px; font-weight: 800; letter-spacing: 0.08em;
    text-align: center; padding: 6px; border: 2px solid var(--mv-gold); border-bottom: none;
  }}
  .sc-frame-box {{ border: 6px ridge var(--mv-chrome-300); background: #000; height: 340px; overflow: hidden; }}
  .sc-frame-box iframe {{ width: 100%; height: 100%; border: none; }}
  .sc-frame-placeholder {{
    height: 100%; display: flex; align-items: center; justify-content: center; text-align: center;
    color: var(--mv-ink-muted); font-family: ui-monospace, monospace; font-size: 13px; padding: 20px;
    background: repeating-linear-gradient(45deg, #111 0 10px, #000 10px 20px);
  }}

  .sc-hitcounter {{ max-width: 260px; margin: 20px auto; text-align: center; background: #000; border: 2px solid var(--mv-chrome-600); border-radius: 6px; padding: 8px; }}
  .sc-hitcounter img {{ height: 28px; }}

  .sc-tools {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; margin: 16px 0; position: relative; z-index: 5; }}
  .sc-tools a {{ background: var(--mv-black-3); border: 2px outset var(--mv-chrome-300); color: var(--mv-ink); text-decoration: none; font-size: 11px; font-weight: 700; padding: 6px 10px; border-radius: 3px; }}

  audio {{ display: none; }}

  /* ---- banner ad dock (bottom, cycling) ---- */
  .sc-banner-dock {{
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 150;
    display: flex; justify-content: center;
  }}
  .sc-banner-ad {{
    width: 100%; max-width: 468px; height: 60px;
    display: flex; align-items: center; justify-content: center; text-align: center;
    font-family: 'Comic Sans MS', 'Comic Sans', cursive;
    font-weight: 800; font-size: 13px; line-height: 1.3; padding: 4px 14px;
    border: 3px outset #fff; box-shadow: 0 -2px 14px rgba(0,0,0,0.6);
    animation: scBlink 1.3s steps(1) infinite;
  }}

  /* ---- popup ad windows (spawned randomly, Windows-95-ish) ---- */
  .sc-popup {{
    position: fixed; z-index: 200; width: 250px;
    background: #c0c0c0; border: 2px outset #eee; box-shadow: 0 8px 24px rgba(0,0,0,0.7);
    font-family: Tahoma, 'MS Sans Serif', sans-serif; color: #000;
  }}
  .sc-popup-titlebar {{
    background: linear-gradient(90deg, #000080, #1084d0);
    color: #fff; font-size: 12px; font-weight: 700; padding: 3px 6px;
    display: flex; justify-content: space-between; align-items: center;
    cursor: default;
  }}
  .sc-popup-close {{
    background: #c0c0c0; border: 1px outset #fff; color: #000; font-size: 10px; font-weight: 900;
    width: 16px; height: 14px; line-height: 14px; text-align: center; cursor: pointer; padding: 0;
  }}
  .sc-popup-body {{ padding: 10px; font-size: 12px; line-height: 1.5; text-align: center; }}
  .sc-popup-body b {{ display: block; font-size: 14px; margin-bottom: 4px; }}
  .sc-popup-cta {{
    display: inline-block; margin-top: 8px; background: #008000; color: #fff; font-weight: 800;
    text-decoration: none; padding: 6px 14px; border: 2px outset #0c0; font-size: 11px;
  }}
</style>

<div class="sc-heli-layer">
  {heli_html}
</div>

<div class="sc-page">
  {floater_html}
  {ninja_html}
  <div class="sc-bounce-layer">
    {bounce_ball_html}
  </div>

  <div class="sc-marquee-wrap">
    <span class="sc-marquee-text">&#9917; MEGA PENALTY SHOOTOUT &#9917; AIM WITH YOUR MOUSE &#9917; CLICK TO SHOOT &#9917; NOW WITH REAL AUDIO &#9917; MEGA PENALTY SHOOTOUT &#9917; AIM WITH YOUR MOUSE &#9917; CLICK TO SHOOT &#9917;</span>
  </div>

  <div class="wrap" style="padding-top:0;">
    <h1 class="sc-title mv-spark-text blink">&#9917; MEGA PENALTY SHOOTOUT &#9917;</h1>
    <div class="sc-sub">Click anywhere inside the goal to aim &amp; shoot. The keeper never stops moving. Good luck.</div>

    <div class="sc-badge-row">
      {badge_html}
    </div>

    <div class="sc-scoreboard">
      <div class="sc-scorebox"><div class="lbl">GOALS</div><div class="val" id="scoreCount">0</div></div>
      <div class="sc-scorebox"><div class="lbl">SHOTS</div><div class="val" id="attemptsCount">0</div></div>
    </div>

    <div class="sc-arena">
      <div class="sc-goal-frame">
        <div class="sc-crossbar"></div>
        <div class="sc-post left"></div>
        <div class="sc-post right"></div>
        <div class="sc-goal" id="goalBox">
          <div class="sc-keeper" id="keeper">&#129399;</div>
          <div class="sc-ball" id="ball">&#9917;</div>
          <div class="sc-result" id="resultOverlay"></div>
        </div>
      </div>
      <div class="sc-instructions blink">&#128071; CLICK INSIDE THE GOAL TO AIM AND FIRE &#128071;</div>
    </div>

    <div class="sc-frame-wrap">
      <div class="sc-frame-label" id="frameStatus">LIVE FEED: STANDBY &mdash; TAKE A SHOT TO CONNECT</div>
      <div class="sc-frame-box">
        <div class="sc-frame-placeholder" id="framePlaceholder">
          &#128225;<br>NO SIGNAL<br><span style="font-size:10px;">(take a shot -- the feed connects 10 seconds later)</span>
        </div>
        <iframe id="liveFrame" style="display:none;" title="Live Feed"></iframe>
      </div>
    </div>

    <div class="sc-hitcounter">
      <img src="https://hits.sh/houseofhufflepuff.github.io/megavision/soccer.svg?label=SHOOTERS+SO+FAR&labelColor=0a0a10&color=13131b&style=flat-square" alt="hit counter">
    </div>

    <div class="sc-tools">
      <a href="#">&#128213; Sign My Guestbook</a>
      <a href="#">&#128231; Email The Webmaster</a>
      <a href="#">&#11088; Add to Favorites</a>
      <a href="snowmobile-lifestlye.html">&#10024; Visit the Lifestyle Page Now &rarr;</a>
    </div>

    <audio id="jonasAudio" preload="auto">
      <source src="jonas.mp3" type="audio/mpeg">
    </audio>
  </div>
</div>

<div class="sc-banner-dock" id="bannerDock">
  {banner_html}
</div>
<div id="popupLayer"></div>

<script>
(function() {{
  var goal = document.getElementById('goalBox');
  var keeper = document.getElementById('keeper');
  var ball = document.getElementById('ball');
  var resultOverlay = document.getElementById('resultOverlay');
  var scoreEl = document.getElementById('scoreCount');
  var attemptsEl = document.getElementById('attemptsCount');
  var jonas = document.getElementById('jonasAudio');
  var frame = document.getElementById('liveFrame');
  var placeholder = document.getElementById('framePlaceholder');
  var frameStatus = document.getElementById('frameStatus');
  var score = 0, attempts = 0, busy = false, frameTimer = null;

  function beep(freqs, dur, type) {{
    try {{
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var t = ctx.currentTime;
      freqs.forEach(function(f, i) {{
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = type || 'square';
        osc.frequency.value = f;
        gain.gain.setValueAtTime(0.16, t + i * dur);
        gain.gain.exponentialRampToValueAtTime(0.001, t + (i + 1) * dur);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t + i * dur);
        osc.stop(t + (i + 1) * dur);
      }});
    }} catch (e) {{}}
  }}
  function kickSound() {{ beep([130], 0.1, 'square'); }}
  function goalSound() {{ beep([523, 659, 784, 1047], 0.13, 'square'); }}
  function missSound() {{ beep([320, 260, 200, 140], 0.17, 'sawtooth'); }}

  function celebrate() {{
    var html = '<div class="goal-text">GOOOOOAL!!!</div>';
    for (var i = 0; i < 36; i++) {{
      var left = Math.random() * 100;
      var delay = Math.random() * 0.6;
      var chars = ['\\u2726', '\\u2605', '\\u26bd', '\\u2733', '\\ud83c\\udf89', '\\ud83c\\udf8a'];
      var ch = chars[Math.floor(Math.random() * chars.length)];
      var color = ['#ffd166', '#e63fb0', '#2e6bff', '#7c3aed', '#f0525c'][Math.floor(Math.random() * 5)];
      html += '<span class="confetti" style="left:' + left + '%;animation-delay:' + delay + 's;color:' + color + ';">' + ch + '</span>';
    }}
    resultOverlay.innerHTML = html;
    resultOverlay.style.display = 'flex';
  }}
  function showMiss() {{
    resultOverlay.innerHTML = '<div class="miss-x">&#10060;</div><div class="miss-text blink">MISSED!!! TRY AGAIN, CHAMP!!!</div>';
    resultOverlay.style.display = 'flex';
  }}

  goal.addEventListener('click', function(e) {{
    if (busy) return;
    busy = true;
    var rect = goal.getBoundingClientRect();
    var x = Math.max(20, Math.min(rect.width - 20, e.clientX - rect.left));
    var y = Math.max(20, Math.min(rect.height - 20, e.clientY - rect.top));

    kickSound();
    jonas.currentTime = 0;
    jonas.play().catch(function() {{}});

    ball.style.transition = 'left 0.42s ease-in, top 0.42s ease-in, transform 0.42s ease-in';
    ball.style.left = x + 'px';
    ball.style.top = y + 'px';
    ball.style.transform = 'translate(-50%,-50%) scale(0.55) rotate(720deg)';

    attempts++;
    attemptsEl.textContent = attempts;

    setTimeout(function() {{
      var scored = Math.random() < 0.5;
      if (scored) {{
        score++;
        scoreEl.textContent = score;
        goalSound();
        celebrate();
      }} else {{
        missSound();
        showMiss();
      }}
      setTimeout(function() {{
        ball.style.transition = 'none';
        ball.style.left = '50%';
        ball.style.top = '92%';
        ball.style.transform = 'translate(-50%,-50%) scale(1) rotate(0deg)';
        resultOverlay.style.display = 'none';
        resultOverlay.innerHTML = '';
        busy = false;
      }}, 2200);
    }}, 440);

    if (frameTimer) clearInterval(frameTimer);
    var countdown = 10;
    frameStatus.textContent = 'LIVE FEED CONNECTING IN ' + countdown + '...';
    frameTimer = setInterval(function() {{
      countdown--;
      if (countdown > 0) {{
        frameStatus.textContent = 'LIVE FEED CONNECTING IN ' + countdown + '...';
      }} else {{
        clearInterval(frameTimer);
        frameStatus.textContent = 'CONNECTED &mdash; ENJOY THE FEED';
        placeholder.style.display = 'none';
        frame.style.display = 'block';
        frame.src = 'snowmobile-lifestlye.html?noauto=1';
      }}
    }}, 1000);
  }});
}})();
</script>

<script>
(function() {{
  var helis = document.querySelectorAll('.sc-heli');
  helis.forEach(function(heli, i) {{
    var lastX = 20 + i * 15;
    function fly() {{
      var x = 4 + Math.random() * 88;
      var y = 6 + Math.random() * 82;
      var facingLeft = x < lastX;
      var tilt = (Math.random() * 16 - 8).toFixed(1);
      heli.style.left = x + '%';
      heli.style.top = y + '%';
      heli.style.transform = 'scaleX(' + (facingLeft ? -1 : 1) + ') rotate(' + tilt + 'deg)';
      lastX = x;
      setTimeout(fly, 2000 + Math.random() * 2400);
    }}
    setTimeout(fly, i * 400);
  }});
}})();
</script>

<script>
(function() {{
  // ---- banner ad dock: cycle through the ads every few seconds ----
  var banners = document.querySelectorAll('.sc-banner-ad');
  var bi = 0;
  function showBanner() {{
    banners.forEach(function(b) {{ b.style.display = 'none'; }});
    banners[bi].style.display = 'flex';
    bi = (bi + 1) % banners.length;
  }}
  if (banners.length) {{
    showBanner();
    setInterval(showBanner, 5500);
  }}

  // ---- popup ads: spawn at random intervals, random position, max 3 at once ----
  var popupAds = {popup_ads_json};
  var layer = document.getElementById('popupLayer');
  var openPopups = 0;
  var MAX_POPUPS = 3;

  function spawnPopup() {{
    if (openPopups >= MAX_POPUPS) return;
    openPopups++;
    var ad = popupAds[Math.floor(Math.random() * popupAds.length)];
    var win = document.createElement('div');
    win.className = 'sc-popup';
    var top = 10 + Math.random() * 60;
    var left = 5 + Math.random() * 60;
    win.style.top = top + '%';
    win.style.left = left + '%';
    win.innerHTML =
      '<div class="sc-popup-titlebar"><span>' + ad[0] + '</span><button class="sc-popup-close" type="button">&#10005;</button></div>' +
      '<div class="sc-popup-body"><b>' + ad[1] + '</b>' + ad[2] +
      '<br><a class="sc-popup-cta" href="snowmobile-lifestlye.html">ENTER THE LIFESTYLE &rarr;</a></div>';
    layer.appendChild(win);
    function close() {{
      if (win.parentNode) {{ win.parentNode.removeChild(win); openPopups--; }}
    }}
    win.querySelector('.sc-popup-close').addEventListener('click', close);
    setTimeout(close, 9000 + Math.random() * 4000);
  }}

  function scheduleNextPopup() {{
    var delay = 7000 + Math.random() * 9000;
    setTimeout(function() {{ spawnPopup(); scheduleNextPopup(); }}, delay);
  }}
  scheduleNextPopup();
}})();
</script>
""" + foot()

with open("soccer.html", "w") as f:
    f.write(page)

print("wrote soccer.html")
