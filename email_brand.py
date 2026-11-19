"""POLYSCI is the MEGAVISION league sponsor. Every MegaBot mail uses this.

The only link is the X profile. Images are https URLs on the live site.
Gmail rewrites cid: attachments to a content-id the file does not have
(GW11 went out as cid:att0 and arrived as cid:att0_<hash>, broken).
file:// URLs are broken in every inbox. Do not emit either.

Jer 2026-11-10: league recap/preview in Gmail -- CTA button yes, banner PNG no.
The lower wordmark looked bad in Gmail. Owner mail never used the banner.
The header mark is logo-polysci.png, the wordmark tx_nrg_v6 uses.
"""
from pathlib import Path

POLYSCI_URL = "https://x.com/0xPOLYSCI"
POLYSCI_TAGLINE = "POLYSCI finds and exploits dislocations in capital markets."
SITE = "https://houseofhufflepuff.github.io/megavision"
WORDMARK_URL = f"{SITE}/brand/logo-polysci.png"
# Local copy of the same file, for the site build. Not an email src.
WORDMARK_PATH = Path(__file__).resolve().parent / "brand" / "logo-polysci.png"
PINK = "#FF3EB5"
BLACK = "#000000"
PAPER = "#EFEEEE"
INK = "#0F0F0F"
MUTED = "#545464"


def sponsor_cta():
    return (
        f"MEGAVISION, sponsored by POLYSCI. {POLYSCI_TAGLINE} {POLYSCI_URL}"
    )


def owner_header():
    return "MEGAVISION by POLYSCI"


def https_img(src, width, alt):
    """An image tag only when src is a live https URL. Anything else is omitted."""
    if not (src or "").startswith("https://"):
        return ""
    return (
        f'<img src="{src}" width="{width}" alt="{alt}" '
        f'style="display:block;width:{width}px;max-width:100%;height:auto;border:0">'
    )


def wordmark_html(src=None):
    """Header wordmark. src is ignored unless it is https. Defaults to the hosted logo."""
    img = https_img(src if (src or "").startswith("https://") else WORDMARK_URL, 220, "polysci")
    if not img:
        return ""
    return (
        f'<tr><td bgcolor="{BLACK}" style="background:{BLACK};padding:22px 28px 18px">'
        f'<a href="{POLYSCI_URL}" style="text-decoration:none">{img}</a></td></tr>'
    )


def owner_header_html():
    return (
        f'<p style="margin:0 0 4px;font-family:Arial,Helvetica,sans-serif;'
        f'font-size:13px;letter-spacing:2px;font-weight:700;color:{INK}">'
        f'MEGAVISION by <a href="{POLYSCI_URL}" style="color:{PINK};text-decoration:none">POLYSCI</a></p>'
    )


def owner_link_line():
    return POLYSCI_URL


def owner_link_html():
    return (
        f'<p style="margin:16px 0 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px">'
        f'<a href="{POLYSCI_URL}" style="color:{PINK}">{POLYSCI_URL}</a></p>'
    )


def wrap_owner_html(plain_body):
    """Owner mail: header + preformatted body + a plain X link. No banner."""
    import html as html_lib
    body = plain_body
    for prefix in (owner_header() + "\n" + POLYSCI_URL + "\n\n",
                   owner_header() + "\n\n",
                   owner_header() + "\n"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    if body.endswith("\n" + POLYSCI_URL):
        body = body[: -len(POLYSCI_URL)].rstrip()
    return f'''<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:{PAPER};font-family:Arial,Helvetica,sans-serif;color:{INK}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER}">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:#ffffff;border:1px solid #ddd">
<tr><td style="padding:28px">
{owner_header_html()}
{owner_link_html()}
<pre style="margin:18px 0 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.5;white-space:pre-wrap">{html_lib.escape(body)}</pre>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
'''


def sponsor_cta_html(include_banner=False, banner_cid=None, banner_src=None):
    # The lower banner stays off. A cid or file src is never written.
    banner = ""
    img = https_img(banner_src, 600, "polysci") if include_banner else ""
    if img:
        banner = (
            f'<tr><td style="padding:0">'
            f'<a href="{POLYSCI_URL}" style="text-decoration:none">{img}</a></td></tr>'
        )
    button = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:12px 0 0 0">'
        '<tr><td bgcolor="#FF3EB5" style="background-color:#FF3EB5;padding:12px 25px;border-radius:3px">'
        f'<a href="{POLYSCI_URL}" style="color:{BLACK};font-family:Arial,Helvetica,sans-serif;'
        'font-size:14px;font-weight:500;letter-spacing:2px;text-transform:uppercase;'
        f'text-decoration:none"><font color="{BLACK}">Follow POLYSCI on X</font></a>'
        '</td></tr></table>'
    )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:18px 0 0 0">'
        '<tr><td style="padding:0 28px 16px 28px;font-family:Arial,Helvetica,sans-serif">'
        f'<p style="margin:0 0 6px 0;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{MUTED}">'
        'Official MEGAVISION sponsor</p>'
        f'<p style="margin:0 0 10px 0;font-size:15px;line-height:22px;color:{INK}">'
        f'{POLYSCI_TAGLINE}</p>'
        f'{button}'
        '</td></tr>'
        f"{banner}"
        '</table>'
    )


# Back-compat names used by older roster mail.
def two_halves_cta_html():
    return sponsor_cta_html(include_banner=False)


def two_halves_cta_text():
    return sponsor_cta()


def ensure_two_halves_cta(html_body):
    if "0xPOLYSCI" in html_body or "polysci" in html_body.lower():
        return html_body
    marker = "-- MegaBot"
    cta = sponsor_cta_html(include_banner=False)
    return html_body.replace(marker, cta + marker, 1) if marker in html_body else html_body + cta
