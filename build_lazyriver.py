redirect_html = """<!doctype html>
<html>
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QHQQ6Z45Q5"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-QHQQ6Z45Q5');
</script>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=lazy-river/index.html">
<title>Lazy River has moved</title>
</head>
<body bgcolor="#000033" text="#00FFFF" link="#0000FF">
<p>This page has moved to the new 40+ page <a href="lazy-river/index.html">Lazy River Outpost</a>.</p>
</body>
</html>
"""

with open("lazy-river.html", "w") as f:
    f.write(redirect_html)

print("wrote lazy-river.html (redirect stub -> lazy-river/index.html)")
