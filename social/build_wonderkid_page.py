"""Wrapper page for the Wonderkid Index infographic (published as an Artifact)."""
import html, json, os, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "wonderkid_index_u18.json"), encoding="utf-8"))
esc = html.escape
def club(r): return esc(r["club"]) + (f' → <b>{esc(r["moved_to"])}</b>' if r["moved_to"] else "")
def out(r): return "n/a" if r["gp"] is None else f'{r["gp"]} / {r["g"]} / {r["a"]}'
def trs(rows): return "".join(f'<tr><td>{r["rank"]}</td><td class="nm">{esc(r["name"])}</td><td>{club(r)}</td><td>{r["age"]}</td><td>{esc(r["pos"])}</td><td class="n idx">{r["score"]:.1f}</td><td class="n">{r["pot"]}/{r["ovr"]}</td><td class="n">{out(r)}</td></tr>' for r in rows)
tweet = ("The 20 best players in the world aged 18 & under, ranked on potential, rating, strength of games and output.\n\n"
         "1. Mastantuono\n2. Karetsas\n3. Mokio\n4. Bouaddi\n5. Ngumoha\n\nFull index below.")
intent = "https://x.com/intent/post?text=" + urllib.parse.quote(tweet)
head = "<thead><tr><th>#</th><th>Player</th><th>25/26 club</th><th>Age</th><th>Pos</th><th class=n>Index</th><th class=n>Pot/Ovr</th><th class=n>GP / G / A</th></tr></thead>"
page = f'''<title>Wonderkid Index</title>
<style>
:root{{color-scheme:dark;--ground:#0A1030;--panel:#111A47;--line:rgba(146,164,255,.18);--ink:#F3F5FF;--muted:#9AA5D6;--accent:#FF5B3A;--pos:#35D39A}}
*{{box-sizing:border-box}}
body{{background:var(--ground);color:var(--ink);font:15px/1.55 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding-inline:16px;padding-block:28px}}
.wrap{{max-width:1120px;margin:0 auto;display:grid;grid-template-columns:minmax(0,560px) minmax(0,1fr);gap:32px;align-items:start}}
@media(max-width:860px){{.wrap{{grid-template-columns:1fr}}}}
img.poster{{width:100%;height:auto;display:block;border-radius:6px;border:1px solid var(--line)}}
h1{{font:800 44px/1 "Arial Narrow","Helvetica Neue",Arial,sans-serif;letter-spacing:.5px;text-transform:uppercase;margin:0 0 6px}}
h1 span{{color:var(--accent)}}
p{{margin:0 0 12px;color:var(--muted);max-width:62ch}}
.box{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px;margin:18px 0}}
.box h2,h2{{font-size:12px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);margin:0 0 10px;font-weight:600}}
textarea{{width:100%;min-height:150px;background:#0A1030;color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:10px;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;resize:vertical}}
.btns{{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}}
button,a.btn{{background:var(--accent);color:#fff;border:0;border-radius:6px;padding:10px 16px;font:600 14px/1 inherit;text-decoration:none;cursor:pointer}}
a.btn.alt,button.alt{{background:transparent;border:1px solid var(--line);color:var(--ink)}}
button:focus-visible,a.btn:focus-visible,textarea:focus-visible{{outline:2px solid var(--pos);outline-offset:2px}}
.tw{{overflow-x:auto;margin-top:6px}}
table{{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums;min-width:640px}}
th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap}}
th{{font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:var(--muted);font-weight:600}}
td.n,th.n{{text-align:right}} td.nm{{font-weight:600}} td.idx{{color:var(--accent);font-weight:700}} td b{{color:var(--ink)}}
ul{{margin:0;padding-left:18px;color:var(--muted)}} li{{margin-bottom:6px;max-width:66ch}}
.full{{grid-column:1/-1}}
</style>
<div class="wrap">
  <div><img class="poster" src="wonderkid_index_u18.png" alt="Infographic: the 20 best players aged 18 and under, ranked by the MegaBot Index. Mastantuono, Karetsas, Mokio, Bouaddi and Ngumoha lead."></div>
  <div>
    <h1>Wonderkid <span>Index</span></h1>
    <p>The 20 best players in the world aged 18 or under at the start of 26/27, every league, no draft rules. Save the image (right-click or long-press) and post it.</p>
    <div class="box"><h2>Post copy</h2>
      <textarea id="tweet" aria-label="Post text">{esc(tweet)}</textarea>
      <div class="btns"><button id="copy" type="button">Copy text</button><a class="btn alt" href="{intent}" target="_blank" rel="noopener">Open X composer</a></div>
    </div>
    <h2>How it works</h2>
    <ul>
      <li>MegaBot Index: 40% FC potential, 25% FC overall, 15% strength of games, 10% goals plus assists, 5% Goal.com NXGN rank, 5% pace.</li>
      <li>Strength of games: 25/26 games played, weighted by league. Premier League 100, Bundesliga / La Liga / Ligue 1 80, other European leagues 60, non-European 20, youth sides 0 (Serie A falls in the 60 group).</li>
      <li>Ratings are EA FC26. FC27 has no machine-readable source yet. EA does not rate players born 2009 or later, so Dowman and Sullivan cannot be ranked.</li>
      <li>Stats come from Transfermarkt and Highlightly. Kader Meïté moved to Al Hilal in February, so his 25/26 output is unavailable and his index uses a neutral value.</li>
      <li>The club column is the club for most of 25/26. Arrows mark moves confirmed by club or major-outlet reports; other summer moves may not be reflected.</li>
    </ul>
  </div>
  <div class="full"><h2>Top 20</h2><div class="tw"><table>{head}<tbody>{trs(d[:20])}</tbody></table></div></div>
  <div class="full"><h2>Next 10</h2><div class="tw"><table>{head}<tbody>{trs(d[20:30])}</tbody></table></div></div>
</div>
<script>
document.getElementById("copy").addEventListener("click",function(){{
  var t=document.getElementById("tweet"),b=this;
  function ok(){{b.textContent="Copied";setTimeout(function(){{b.textContent="Copy text"}},1600)}}
  if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(t.value).then(ok,function(){{t.select()}})}}else{{t.select()}}
}});
</script>'''
open(os.path.join(HERE, "wonderkid_page.html"), "w", encoding="utf-8").write(page)
print(len(page))
