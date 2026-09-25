"""Write the Content-Security-Policy into index.html.

The policy allows only the page's own inline script, pinned by its SHA-256
hash, so re-run this after ANY edit to the <script> in index.html, or the
browser will refuse to run it:  python update_csp.py
"""
import base64, hashlib, re, sys
from pathlib import Path

PAGE = Path(__file__).with_name("index.html")

POLICY = [
    "default-src 'none'",
    "script-src {hash}",
    "worker-src 'self'",
    "connect-src 'self' https://raw.githubusercontent.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "img-src 'self' https://commons.wikimedia.org https://upload.wikimedia.org https://thumb.wikimedia.org",
    "media-src https://archive.org https://*.archive.org",
    "manifest-src 'self'",
    "base-uri 'none'",
    "form-action 'none'",
    "object-src 'none'",
]
MARK = '<meta http-equiv="Content-Security-Policy"'

html = PAGE.read_text(encoding="utf-8")
scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
if len(scripts) != 1:
    sys.exit(f"expected exactly one inline <script>, found {len(scripts)}")
digest = base64.b64encode(hashlib.sha256(scripts[0].encode("utf-8")).digest()).decode()
meta = MARK + ' content="' + "; ".join(POLICY).format(hash=f"'sha256-{digest}'") + '">'

if MARK in html:
    html = re.sub(re.escape(MARK) + r'[^>]*>', lambda m: meta, html, count=1)
else:
    html = html.replace('<meta charset="UTF-8">',
                        '<meta charset="UTF-8">\n' + meta +
                        '\n<meta name="referrer" content="no-referrer">', 1)
PAGE.write_text(html, encoding="utf-8", newline="")
print("CSP updated, script hash sha256-" + digest)
