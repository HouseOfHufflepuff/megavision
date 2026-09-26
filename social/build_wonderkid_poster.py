"""Build the 'Wonderkid Index' X infographic (1200x1500, 4:5) from wonderkid_index_u18.json and render it to PNG
with headless Chrome.  python3 build_wonderkid_poster.py"""
import html, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "wonderkid_index_u18.json"), encoding="utf-8"))[:20]
esc = html.escape


def last_name(full):
    p = full.split()
    return " ".join(p[-2:]) if len(p) > 2 and p[-2].lower() in ("de", "van", "von", "da") else (p[-1] if len(p) > 1 else full)


def first_names(full):
    p = full.split()
    n = 2 if len(p) > 2 and p[-2].lower() in ("de", "van", "von", "da") else 1
    return " ".join(p[:-n]) if len(p) > n else ""


def club_html(r):
    if r["moved_to"]:
        return f'{esc(r["club"])} <i>→</i> <b>{esc(r["moved_to"])}</b>'
    return esc(r["club"])


def stat_line(r):
    if r["gp"] is None:
        return '<span class="na">25/26 stats n/a</span>'
    return f'{r["gp"]} GP · <span class="pos">{r["g"] + r["a"]} G+A</span>'


def podium(r):
    gold = " gold" if r["rank"] == 1 else ""
    fn = first_names(r["name"])
    return f'''<div class="card{gold}">
  <div class="card-top"><span class="rk">{r["rank"]:02d}</span><span class="chip">{esc(r["pos"])}</span><span class="chip">AGE {r["age"]}</span></div>
  <div class="fn">{esc(fn.upper())}</div>
  <div class="ln">{esc(last_name(r["name"]).upper())}</div>
  <div class="club">{club_html(r)}</div>
  <div class="idx"><span class="idx-n">{r["score"]:.1f}</span><span class="idx-l">MEGABOT<br>INDEX</span></div>
  <div class="gauges">
    <div class="g"><span>POT</span><div class="track"><div class="fill" style="width:{r["pot"]}%"></div></div><em>{r["pot"]}</em></div>
    <div class="g"><span>OVR</span><div class="track"><div class="fill" style="width:{r["ovr"]}%"></div></div><em>{r["ovr"]}</em></div>
  </div>
  <div class="line">25/26 · {stat_line(r)}</div>
</div>'''


def row(r, top):
    w = max(6, r["score"] / top * 100)
    return f'''<div class="row">
  <span class="rk2">{r["rank"]:02d}</span>
  <span class="who"><b>{esc(r["name"])}</b><small>{club_html(r)}</small></span>
  <span class="chip s">{esc(r["pos"])}</span>
  <span class="age">{r["age"]}</span>
  <span class="bar"><span class="bar-fill" style="width:{w:.1f}%"></span><em>{r["score"]:.1f}</em></span>
  <span class="num">{r["pot"]}</span>
  <span class="num">{r["ovr"]}</span>
  <span class="st">{stat_line(r)}</span>
</div>'''


ticker = "   ·   ".join(f'#{r["rank"]} {last_name(r["name"]).upper()} {r["score"]:.1f}' for r in data[:6])
top = data[0]["score"]
page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>The Wonderkid Index</title>
<style>
@font-face{{font-family:"BC";src:url("fonts/BarlowCondensed-ExtraBold.ttf");font-weight:800}}
@font-face{{font-family:"BC";src:url("fonts/BarlowCondensed-Bold.ttf");font-weight:700}}
@font-face{{font-family:"BC";src:url("fonts/BarlowCondensed-SemiBold.ttf");font-weight:600}}
@font-face{{font-family:"PM";src:url("fonts/IBMPlexMono-Medium.ttf");font-weight:500}}
@font-face{{font-family:"PM";src:url("fonts/IBMPlexMono-SemiBold.ttf");font-weight:600}}
:root{{--ground:#0A1030;--panel:#111A47;--panel2:#16215A;--line:rgba(146,164,255,.16);--ink:#F3F5FF;--muted:#8E99CB;
  --accent:#FF5B3A;--gold:#FFC44D;--pos:#35D39A}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:var(--ground)}}
.poster{{width:1200px;height:1500px;position:relative;overflow:hidden;color:var(--ink);font-family:"PM",monospace;
  background:radial-gradient(900px 500px at 92% -6%,rgba(255,91,58,.22),transparent 60%),
  linear-gradient(var(--line) 1px,transparent 1px) 0 0/100% 50px,
  linear-gradient(90deg,var(--line) 1px,transparent 1px) 0 0/50px 100%,var(--ground);padding:46px 56px 0}}
.tag{{display:flex;align-items:center;gap:14px;font-size:15px;letter-spacing:2px;color:var(--muted)}}
.pill{{background:var(--accent);color:#fff;font-weight:600;padding:7px 14px;border-radius:4px;letter-spacing:2px}}
h1{{font-family:"BC";font-weight:800;font-size:88px;line-height:.92;letter-spacing:-1px;margin:14px 0 8px;text-transform:uppercase}}
h1 span{{color:var(--accent)}}
.sub{{font-size:15px;color:var(--muted);letter-spacing:.4px;line-height:1.4}}
.tickerbar{{margin:14px -56px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:rgba(17,26,71,.7);
  padding:8px 56px;font-size:13px;color:var(--ink);letter-spacing:1px;white-space:nowrap;overflow:hidden}}
.tickerbar b{{color:var(--accent)}}
.podium{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px}}
.card{{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:10px;padding:12px 18px 11px;position:relative}}
.card.gold{{border-color:var(--gold);box-shadow:0 0 0 1px rgba(255,196,77,.35),0 12px 40px rgba(255,196,77,.12)}}
.card-top{{display:flex;align-items:center;gap:8px}}
.rk{{font-family:"BC";font-weight:800;font-size:38px;line-height:1;color:var(--accent);margin-right:auto}}
.gold .rk{{color:var(--gold)}}
.chip{{font-size:12px;font-weight:600;letter-spacing:1.4px;padding:4px 8px;border:1px solid var(--line);border-radius:4px;color:var(--ink);background:rgba(255,255,255,.04)}}
.chip.s{{text-align:center;justify-self:start}}
.fn{{font-size:12px;letter-spacing:2px;color:var(--muted);margin-top:4px;height:15px;white-space:nowrap}}
.ln{{font-family:"BC";font-weight:800;font-size:50px;line-height:.95;letter-spacing:-.5px;white-space:nowrap}}
.club{{font-size:13px;color:var(--muted);margin-top:4px;letter-spacing:.5px;white-space:nowrap}}
.club i,.who small i{{color:var(--accent);font-style:normal}}
.club b,.who small b{{color:var(--ink);font-weight:600}}
.idx{{display:flex;align-items:flex-end;gap:10px;margin-top:6px}}
.idx-n{{font-size:52px;font-weight:600;line-height:.9;letter-spacing:-2px}}
.gold .idx-n{{color:var(--gold)}}
.idx-l{{font-size:11px;letter-spacing:1.6px;color:var(--muted);line-height:1.3;padding-bottom:4px}}
.gauges{{margin-top:8px;display:grid;gap:5px}}
.g{{display:grid;grid-template-columns:34px 1fr 30px;align-items:center;gap:8px;font-size:12px;color:var(--muted)}}
.g em{{font-style:normal;color:var(--ink);text-align:right;font-weight:600}}
.track{{height:6px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden}}
.fill{{height:100%;background:linear-gradient(90deg,var(--accent),#FF9A6B);border-radius:3px}}
.line{{margin-top:8px;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:6px}}
.pos{{color:var(--pos);font-weight:600}}
.na{{color:var(--muted)}}
.thead,.row{{display:grid;grid-template-columns:44px 318px 54px 40px 1fr 46px 46px 150px;gap:10px;align-items:center}}
.thead{{margin-top:16px;font-size:11px;letter-spacing:1.6px;color:var(--muted);padding:0 8px 6px;border-bottom:1px solid var(--line)}}
.thead span:nth-child(n+6){{text-align:right}}
.row{{height:40px;padding:0 8px;border-bottom:1px solid rgba(146,164,255,.09);font-size:14px}}
.row:nth-child(odd){{background:rgba(255,255,255,.02)}}
.rk2{{font-family:"BC";font-weight:800;font-size:24px;color:var(--accent)}}
.who{{display:flex;flex-direction:column;line-height:1.1;overflow:hidden}}
.who>b{{font-family:"BC";font-weight:700;font-size:22px;letter-spacing:.2px;white-space:nowrap}}
.who small{{font-size:11px;color:var(--muted);letter-spacing:.4px;white-space:nowrap;margin-top:1px}}
.age{{color:var(--muted);text-align:center}}
.bar{{position:relative;height:22px;background:rgba(255,255,255,.05);border-radius:3px;overflow:hidden;display:block}}
.bar-fill{{position:absolute;inset:0 auto 0 0;background:linear-gradient(90deg,rgba(255,91,58,.85),rgba(255,154,107,.85))}}
.bar em{{position:absolute;right:8px;top:0;line-height:22px;font-style:normal;font-weight:600;font-size:14px;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.5)}}
.num{{text-align:right;font-weight:600}}
.st{{text-align:right;font-size:12.5px;color:var(--muted);white-space:nowrap}}
.method{{position:absolute;left:56px;right:56px;bottom:58px;font-size:11.5px;line-height:1.5;color:var(--muted);letter-spacing:.3px}}
.method b{{color:var(--ink);font-weight:600}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:46px;background:var(--accent);display:flex;align-items:center;justify-content:space-between;padding:0 56px;color:#fff;font-size:14px;letter-spacing:1.6px;font-weight:600}}
.foot b{{font-family:"BC";font-weight:800;font-size:24px;letter-spacing:1.5px}}
</style></head><body>
<div class="poster">
  <div class="tag"><span class="pill">THE WONDERKID INDEX</span><span>26/27 KICKOFF · AGES 18 &amp; UNDER · ALL LEAGUES</span></div>
  <h1>The 20 best<br>players <span>18 &amp; under</span></h1>
  <div class="sub">Ranked by the MegaBot Index: potential, rating, strength of games, end product. No draft rules.</div>
  <div class="tickerbar"><b>▲ INDEX</b> &nbsp; {esc(ticker)}</div>
  <div class="podium">{''.join(podium(r) for r in data[:3])}</div>
  <div class="thead"><span>#</span><span>PLAYER · 25/26 CLUB</span><span>POS</span><span>AGE</span><span>MEGABOT INDEX</span><span>POT</span><span>OVR</span><span>25/26 OUTPUT</span></div>
  {''.join(row(r, top) for r in data[3:])}
  <div class="method"><b>INDEX</b> = 40% FC potential · 25% FC overall · 15% strength of games (25/26 games weighted by league tier) · 10% goals + assists · 5% Goal.com NXGN rank · 5% pace. Ratings: EA FC26. Stats: Transfermarkt, Highlightly. Age on Aug 1, 2026. Arrows mark moves confirmed by club or major-outlet reports; other summer moves may not be reflected. <b>n/a</b> = stats unavailable.</div>
  <div class="foot"><b>MEGAVISION × MEGABOT</b><span>houseofhufflepuff.github.io/megavision</span></div>
</div></body></html>'''
open(os.path.join(HERE, "wonderkid_index_u18.html"), "w", encoding="utf-8").write(page)

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
out = os.path.join(HERE, "wonderkid_index_u18.png")
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                "--window-size=1200,1500", "--virtual-time-budget=4000", f"--screenshot={out}",
                "file://" + os.path.join(HERE, "wonderkid_index_u18.html")], check=True, capture_output=True, timeout=120)
print("wrote", out, os.path.getsize(out))
