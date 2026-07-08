from common import head, foot

PRODUCTS = [
    ("&#127939;", "FunBoy Snowmobile &amp; Tube Rentals", "Resort-side rental fleet — the exact rainbow-striped sleds from the ad, ready to book by the hour."),
    ("&#129505;", "Arctic Soul Apparel Co.", "Retro rainbow-stripe snowsuits, gloves, and goggles. If it's in the photo, you can buy it."),
    ("&#10024;", "Yeti Fuel", "Arctic-themed energy drink line. Caffeine, electrolytes, and questionable levels of glitter."),
    ("&#127956;", "White Wilderness Expeditions", "Guided backcountry snowmobile tours for people who think chairlifts are for cowards."),
    ("&#128241;", "Snow Life Command App", "Trail tracking, gamified badges, leaderboards. Basically Mega League energy, but for mountains."),
    ("&#129504;", "Winter Purpose Retreats", "Corporate wellness &amp; team-building weekends. Trust falls, but on snowmobiles."),
    ("&#127942;", "MEGAVISION &times; Mega League Crossover Merch", "Stadium-branded snowmobiles and jackets for the true dual-fandom completionist."),
    ("&#127916;", "Conquer Media", "In-house docuseries and branded content studio. Think extreme sports, but with a marketing budget."),
    ("&#128142;", "Untamed Destiny Membership Club", "Recurring dues, trail access, gear discounts. The Costco card of arctic self-actualization."),
    ("&#128220;", "Brand Licensing", "License the MEGAVISION mark to actual snowmobile manufacturers. Let them do the hard part."),
]

REVENUE = [
    ("Rentals", "Per-hour / per-day tube &amp; sled rental fees at resort kiosks"),
    ("Apparel", "Direct-to-consumer + wholesale margin on the retro gear line"),
    ("Membership Club", "Recurring monthly / annual dues"),
    ("App", "Freemium, with a premium trail-pass upsell + anonymized trail data licensing"),
    ("Expeditions", "Package pricing per tour, upsell photography &amp; video add-ons"),
    ("Media", "Sponsorships + branded content deals"),
    ("Licensing", "Royalty % on licensed MEGAVISION-branded snowmobiles"),
]

PHASES = [
    ("Phase 1", "Ignite", "Q1", "Launch one flagship rental kiosk, seed influencer content, drop VHS-style promo videos on social."),
    ("Phase 2", "Awaken", "Q2&ndash;Q3", "Expand rentals to 3 resorts, launch the apparel line, open the membership club waitlist."),
    ("Phase 3", "Conquer", "Q4&ndash;Year 2", "Ship the app, scale guided expeditions, sign the first brand licensing deal."),
    ("Phase 4", "Transcend", "Year 2+", "National franchise model, launch the media studio, expand past the border."),
]

product_cards = "\n      ".join(
    f"""<div class="mv-team-card" style="cursor:default;">
        <div class="code" style="font-size:20px;background:none;border:none;padding:0;">{icon}</div>
        <div class="name">{name}</div>
        <div class="owners">{pitch}</div>
      </div>"""
    for icon, name, pitch in PRODUCTS
)

revenue_rows = "\n            ".join(
    f"<tr><td style='font-weight:700;color:var(--mv-gold);'>{stream}</td><td>{desc}</td></tr>"
    for stream, desc in REVENUE
)

phase_cards = "\n      ".join(
    f"""<div class="mv-stat" style="text-align:left;padding:18px;">
        <div class="label">{p} &middot; {q}</div>
        <div class="value mv-spark-text" style="font-size:20px;">{name}</div>
        <div style="font-size:13px;color:var(--mv-ink-muted);margin-top:6px;">{desc}</div>
      </div>"""
    for p, name, q, desc in PHASES
)

page = head("Snow Business Plan", "snow-business-plan.html") + f"""
<style>
  .plan-page {{ padding-top: 6px; }}
  .marquee-wrap-sm {{
    overflow: hidden; white-space: nowrap;
    background: var(--mv-black-2);
    border-top: 2px solid var(--mv-gold); border-bottom: 2px solid var(--mv-gold);
    padding: 8px 0; margin-bottom: 30px;
  }}
  .marquee-text-sm {{
    display: inline-block; font-weight: 800; font-size: 13px; letter-spacing: 0.06em;
    color: var(--mv-gold); animation: marqueeScroll2 20s linear infinite; text-transform: uppercase;
  }}
  @keyframes marqueeScroll2 {{ 0% {{ transform: translateX(6%); }} 100% {{ transform: translateX(-106%); }} }}

  .plan-title {{
    text-align: center; font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', sans-serif;
    font-size: 40px; letter-spacing: 0.02em; margin: 0 0 6px;
  }}
  .plan-sub {{ text-align: center; color: var(--mv-ink-muted); font-size: 14px; margin-bottom: 34px; }}

  .plan-products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 14px; }}
  .plan-phase-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 8px; }}
</style>

<div class="plan-page">
  <div class="marquee-wrap-sm">
    <span class="marquee-text-sm">&#9733; PROJECTED TO CHANGE THE GAME &#9733; FISCAL RESPONSIBILITY MEETS ARCTIC DESTINY &#9733; ASK US ABOUT OUR SYNERGY &#9733; PROJECTED TO CHANGE THE GAME &#9733; FISCAL RESPONSIBILITY MEETS ARCTIC DESTINY &#9733;</span>
  </div>

  <div class="wrap" style="padding-top:0;">
    <h1 class="plan-title mv-spark-text">THE MEGAVISION SNOWMOBILE BUSINESS PLAN</h1>
    <div class="plan-sub">Confidential-ish &middot; For Investor Eyes &middot; Prepared With Maximum Synergy&trade;</div>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Executive Summary</h2>
      <div class="sub">The pitch, in one breath</div>
      <p style="font-size:14px;line-height:1.7;color:var(--mv-ink);">
        MEGAVISION built a fantasy soccer dashboard. Then we looked at one photo of two people
        joyfully tubing behind a rainbow-striped snowmobile and realized: this is the real business.
        We are pivoting &mdash; well, <em>expanding</em>, legal made us say expanding &mdash; into the
        arctic lifestyle space. Rentals, apparel, an app, a media studio, and a membership club, all
        under one chrome-and-neon logo that already looks incredible on a mountain at night.
      </p>
    </section>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Products &amp; Services</h2>
      <div class="sub">Ten ways this pays for itself</div>
      <div class="plan-products-grid">
      {product_cards}
      </div>
    </section>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Revenue Streams</h2>
      <div class="sub">How the money actually shows up</div>
      <div class="mv-table-scroll">
        <table class="mv-table">
          <thead><tr><th>Stream</th><th>Mechanism</th></tr></thead>
          <tbody>
            {revenue_rows}
          </tbody>
        </table>
      </div>
    </section>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Go-To-Market Roadmap</h2>
      <div class="sub">Four phases, zero snow days off</div>
      <div class="plan-phase-grid">
      {phase_cards}
      </div>
    </section>

    <section class="card mv-card">
      <h2 class="mv-chrome-text">Target Customer</h2>
      <div class="sub">Meet the Arctic Soul Seeker</div>
      <p style="font-size:14px;line-height:1.7;color:var(--mv-ink);">
        25&ndash;44, disposable income, owns at least one fleece with a company logo on it.
        Already fantasy-league-pilled from MEGAVISION's core product, primed to spend the offseason
        proving something to nobody in particular on a snowmobile. Wants content for the group chat.
        Will absolutely buy the energy drink.
      </p>
    </section>

    <p style="text-align:center;margin-top:8px;">
      <a href="snowmobile-lifestlye.html" style="color:var(--mv-violet);font-weight:600;font-size:14px;text-decoration:none;">&larr; Back to the Lifestyle</a>
    </p>
  </div>
</div>
""" + foot()

with open("snow-business-plan.html", "w") as f:
    f.write(page)

print("wrote snow-business-plan.html")
