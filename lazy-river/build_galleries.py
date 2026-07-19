import json
import urllib.parse

from _shared import page, static_waterfall_bar

CB = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def img(filename, w=220, caption=None):
    url = CB + urllib.parse.quote(filename)
    cap = f'<br><font size="1" color="#66ccff">{caption}</font>' if caption else ""
    return f'<img src="{url}" width="{w}" style="border:3px outset #fff;margin:4px;" alt="lazy river / water park photo">{cap}'


IMAGES = json.load(open("gallery_images.json"))
CHUNKS = [IMAGES[0:10], IMAGES[10:20], IMAGES[20:29]]

for i, chunk in enumerate(CHUNKS, start=1):
    cells = [f"<td align='center'>{img(f, 200)}</td>" for f in chunk]
    rows = []
    for j in range(0, len(cells), 3):
        rows.append("<tr>" + "".join(cells[j:j + 3]) + "</tr>")
    content = f"""
    <center><font face="Arial Black, Impact" size="6" color="#ffff00"><b>&#128247; LAZY RIVER GALLERY {['I','II','III'][i-1]} &#128247;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">real photos of real lazy rivers and water parks, via Wikimedia Commons</font></center>
    {static_waterfall_bar("PHOTOS " + str((i-1)*10 + 1) + "-" + str((i-1)*10 + len(chunk)))}
    <table width="100%" cellpadding="4" cellspacing="0" border="0">{"".join(rows)}</table>
    <p><font size="1" color="#66ccff">Images sourced from Wikimedia Commons; click through file names on Commons for individual photographer credit and license.</font></p>
"""
    page(f"gallery{i}.html", f"Gallery {['I','II','III'][i-1]}", content)

print(f"done: {len(CHUNKS)} gallery pages, {len(IMAGES)} total images")
