from common import head, foot

TAGLINES = [
    ("Untamed Winter Destiny", "gold", "display", -4, "1%", "3%", "26px"),
    ("Awaken the Yetti", "pink", "script", 4, "1%", "58%", "34px"),
    ("Conquer", "blue", "display", -3, "10%", "80%", "38px"),
    ("White Wilderness Legacy", "violet", "sans", 3, "50%", "2%", "19px"),
    ("Ignite Your Arctic Soul", "crimson", "display", -5, "50%", "76%", "20px"),
    ("Redefine Freedom Through Snow Mastery", "gold", "sans", 2, "90%", "52%", "18px"),
    ("Transcend Ordinary", "blue", "script", -4, "92%", "3%", "28px"),
    ("Forge Your Winter Purpose", "pink", "display", 5, "84%", "24%", "18px"),
    ("Snow Life Command", "violet", "display", -2, "6%", "28%", "24px"),
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

  .retro-page {{
    overflow-x: hidden;
    background:
      repeating-linear-gradient(135deg, rgba(124,58,237,0.10) 0px, rgba(124,58,237,0.10) 2px, transparent 2px, transparent 34px),
      repeating-linear-gradient(45deg, rgba(46,107,255,0.08) 0px, rgba(46,107,255,0.08) 2px, transparent 2px, transparent 34px),
      var(--mv-black);
    padding: 26px 0 60px;
  }}

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

  .retro-tagline {{
    position: absolute;
    z-index: 4;
    font-weight: 800;
    text-shadow: 0 2px 0 rgba(0,0,0,0.6), 0 0 18px currentColor;
    max-width: 220px;
    line-height: 1.15;
  }}
  .retro-blink {{ animation: retroBlink 1.4s steps(1) infinite; }}

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
    .retro-tagline {{ position: static; display: inline-block; margin: 6px 10px; transform: none !important; }}
  }}
</style>

<div class="retro-page">
  <div class="marquee-wrap">
    <span class="marquee-text">&#9733; UNTAMED WINTER DESTINY &#9733; AWAKEN THE YETTI &#9733; IGNITE YOUR ARCTIC SOUL &#9733; SNOW LIFE COMMAND &#9733; CONQUER &#9733; TRANSCEND ORDINARY &#9733; UNTAMED WINTER DESTINY &#9733; AWAKEN THE YETTI &#9733; IGNITE YOUR ARCTIC SOUL &#9733; SNOW LIFE COMMAND &#9733;</span>
  </div>

  <div class="wrap" style="padding-top:0;">
    <div class="construction-bar">&#9888; SITE UNDER CONSTRUCTION &mdash; NEW POWDER DROPPING SOON &#9888;</div>

    <h1 class="retro-hero-title mv-spark-text">MEGAVISION SNOWMOBILE LIFESTYLE</h1>
    <div class="retro-sub">Est. always &middot; Best viewed at any resolution &middot; 100% Arctic Approved</div>
    <div class="retro-stars">&#9733; &#9733; &#9733; &#9733; &#9733;</div>

    <div class="retro-stage">
      <div class="retro-burst"></div>
      <div class="retro-burst reverse"></div>
{tagline_html}
      <div class="retro-image-wrap">
        <img src="megavision.jpg" alt="MEGAVISION Snowmobile Lifestyle">
      </div>
    </div>

    <div class="hit-counter">
      <div class="lbl">YOU ARE ARCTIC EXPLORER NUMBER</div>
      <div class="digits">004269</div>
    </div>

    <div class="retro-cta">
      <a href="teams.html">&#10084; JOIN THE LIFESTYLE &rarr;</a>
    </div>
    <div class="retro-cta">
      <a href="snow-business-plan.html" style="background:linear-gradient(90deg, var(--mv-gold), var(--mv-crimson));font-size:13px;padding:12px 26px;">&#128176; INVESTORS: SEE THE BIZ PLAN &rarr;</a>
    </div>
  </div>
</div>
""" + foot()

with open("snowmobile-lifestlye.html", "w") as f:
    f.write(page)

print("wrote snowmobile-lifestlye.html")
