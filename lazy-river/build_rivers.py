import json
import os
import urllib.parse

from _shared import page, static_waterfall_bar

CB = "https://commons.wikimedia.org/wiki/Special:FilePath/"

FACTS = json.load(open("top10_facts.json"))
FACTS.sort(key=lambda r: r["rank"])

IMAGES = {}
if os.path.exists("top10_images.json"):
    raw = json.load(open("top10_images.json"))
    # normalize whatever key scheme the research agent used down to rank int,
    # by matching the leading number in each key (e.g. "01-bsr-waco" -> 1)
    for key, files in raw.items():
        digits = "".join(ch for ch in key if ch.isdigit())
        if digits:
            rank = int(digits[:2]) if len(digits) >= 2 else int(digits)
            IMAGES[rank] = files


def img(entry, w=200):
    filename = entry["filename"] if isinstance(entry, dict) else entry
    url = CB + urllib.parse.quote(filename)
    return f'<img src="{url}" width="{w}" style="border:3px outset #fff;margin:4px;" alt="lazy river photo">'


def gallery_for(rank):
    files = IMAGES.get(rank, [])
    if not files:
        return '<font color="#888" size="2">(photo research still pending for this river -- check back soon)</font>'
    cells = [f"<td align='center'>{img(f, 190)}</td>" for f in files]
    rows = []
    for j in range(0, len(cells), 3):
        rows.append("<tr>" + "".join(cells[j:j + 3]) + "</tr>")
    return f'<table width="100%" cellpadding="4" cellspacing="0" border="0">{"".join(rows)}</table>'


def sources_html(sources):
    return "<br>".join(
        f'&#128279; <a href="{s["url"]}" target="_blank" rel="noopener">{s["title"]}</a>' for s in sources
    )


def notes_html(notes):
    return "".join(f"<li>{n}</li>" for n in notes)


def build_river_page(entry):
    rank = entry["rank"]
    filename = f"river-{rank:02d}.html"
    ft = entry["length_ft"]
    m = entry["length_m"]
    content = f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#127942; #{rank}: {entry['river_name']} &#127942;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">{entry['park_name']} &middot; {entry['city']}, {entry['country']}</font></center>

    {static_waterfall_bar("VITAL STATISTICS")}
    <table width="100%" border="3" cellpadding="6" cellspacing="0" bgcolor="#003366" style="border-color:#00ffff;">
      <tr bgcolor="#000080"><td colspan="2"><font color="#ffff00" size="3"><b>&#128202; BY THE NUMBERS</b></font></td></tr>
      <tr bgcolor="#001a33"><td width="35%"><font color="#00ffff"><b>Length</b></font></td><td><font color="#fff">{ft:,} ft ({m:,.0f} m)</font></td></tr>
      <tr><td><font color="#00ffff"><b>Park</b></font></td><td><font color="#fff">{entry['park_name']}</font></td></tr>
      <tr bgcolor="#001a33"><td><font color="#00ffff"><b>Location</b></font></td><td><font color="#fff">{entry['city']}, {entry['country']}</font></td></tr>
      <tr><td><font color="#00ffff"><b>World Ranking</b></font></td><td><font color="#fff">#{rank} of 10 longest lazy rivers (per this research pass)</font></td></tr>
    </table>

    {static_waterfall_bar("WHAT WE FOUND")}
    <font color="#fff" face="Arial, Helvetica, sans-serif" size="2">
    <ul>{notes_html(entry['notes'])}</ul>
    </font>

    {static_waterfall_bar("PHOTOS")}
    {gallery_for(rank)}

    {static_waterfall_bar("SOURCES")}
    <font color="#00ffff" size="2">{sources_html(entry['sources'])}</font>

    <br>
    <center><font size="2" color="#00ffff"><a href="top-10.html">&larr; Back to the Top 10 ranking</a></font></center>
"""
    page(filename, f"#{rank} {entry['river_name']}", content)


for entry in FACTS:
    build_river_page(entry)


# ------------------------------------------------------------------ hub --
rows = []
for entry in FACTS:
    rank = entry["rank"]
    thumb_files = IMAGES.get(rank, [])
    thumb = img(thumb_files[0], 140) if thumb_files else '<font color="#888" size="1">(photo pending)</font>'
    rows.append(f"""
    <tr bgcolor="{'#001a33' if rank % 2 == 0 else ''}">
      <td align="center" valign="top" width="10%"><font color="#ffff00" size="5"><b>#{rank}</b></font></td>
      <td align="center" valign="top" width="20%">{thumb}</td>
      <td valign="top">
        <font color="#ffff00" size="3"><b>{entry['river_name']}</b></font><br>
        <font color="#fff" size="2">{entry['park_name']} &middot; {entry['city']}, {entry['country']}</font><br>
        <font color="#00ffff" size="2"><b>{entry['length_ft']:,} ft ({entry['length_m']:,.0f} m)</b></font><br>
        <a href="river-{rank:02d}.html"><font color="#0ff" size="2">FULL PROFILE &rarr;</font></a>
      </td>
    </tr>""")

hub_content = f"""
    <center><font face="Arial Black, Impact" size="7" color="#ffff00"><b class="blk">TOP 10 LONGEST LAZY RIVERS IN THE WORLD</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">researched across multiple sources &middot; ranked by reported length &middot; treated with appropriate skepticism</font></center>

    {static_waterfall_bar("THE RANKING")}
    <font color="#fff" face="Arial, Helvetica, sans-serif" size="2">
    <p>A note on methodology: nearly every park on this list markets its own lazy river as "the world's longest"
    in some form. Very few of those claims are backed by an independently verifiable, currently-active Guinness
    World Records certification we could locate. What follows is a best-effort ranking by the most consistently
    reported length figures across multiple independent sources, with discrepancies and marketing-vs-verified
    gaps called out on each river's own page. Click through for the full breakdown and cited sources.</p>
    </font>

    <table width="100%" border="3" cellpadding="8" cellspacing="0" bgcolor="#003366" style="border-color:#00ffff;">
    {"".join(rows)}
    </table>
"""
page("top-10.html", "Top 10 Longest Lazy Rivers", hub_content)

print(f"done: top-10.html + {len(FACTS)} river profile pages")
