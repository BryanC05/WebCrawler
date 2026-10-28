from http.server import BaseHTTPRequestHandler
from urllib import request, parse, error
import re
import ssl
import os

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
SSL_CTX = ssl.create_default_context()
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    pass

def fetch_html(url, timeout=15):
    req = request.Request(url, headers=UA)
    try:
        resp = request.urlopen(req, timeout=timeout, context=SSL_CTX)
    except error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLError):
            resp = request.urlopen(req, timeout=timeout, context=ssl._create_unverified_context())
        else:
            raise
    ctype = resp.headers.get("Content-Type", "")
    if "html" not in ctype:
        raise ValueError(f"not html: {ctype}")
    charset = "utf-8"
    m = re.search(r"charset=([\w-]+)", ctype)
    if m:
        charset = m.group(1)
    return resp.read().decode(charset, "ignore")

def absolutize(html, base):
    def fix(match):
        attr, quote, value = match.group(1), match.group(2), match.group(3)
        if value.startswith(("data:", "javascript:", "#", "mailto:", "http")):
            return match.group(0)
        try:
            return f'{attr}={quote}{parse.urljoin(base, value)}{quote}'
        except Exception:
            return match.group(0)
    return re.sub(r"(href|src)=(\"|')([^\"']+)", fix, html)

def clean(html, base):
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S | re.I)
    html = re.sub(r"<script\b[^>]*/?>", "", html, flags=re.I)
    html = re.sub(r'on\w+\s*=\s*("|\').*?\1', "", html, flags=re.S | re.I)
    html = re.sub(r"<meta[^>]+http-equiv=[\"']?refresh[^>]*>", "", html, flags=re.I)
    html = re.sub(r'(?i)integrity\s*=\s*("|\')[^"\']*\1\s*', "", html)
    html = re.sub(r'(?i)nonce\s*=\s*("|\')[^"\']*\1\s*', "", html)
    html = absolutize(html, base)
    inject = ("<base target='_blank'>"
              "<style>html{scrollbar-width:thin}::selection{background:#0f05}</style>")
    if "</head>" in html.lower():
        return re.sub(r"</head>", inject + "</head>", html, count=1, flags=re.I)
    return inject + html

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = parse.urlparse(self.path)
        qs = parse.parse_qs(parsed.query)
        target = (qs.get("url") or [""])[0]
        if not target.startswith(("http://", "https://")):
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h2>url param required</h2>")
            return
        try:
            body = clean(fetch_html(target), target)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            # Remove frame blocking headers
            self.send_header("X-Frame-Options", "ALLOWALL")
            self.end_headers()
            self.wfile.write(body.encode("utf-8", "ignore"))
        except Exception as e:
            msg = f"<h2>could not fetch {target}<br>{e}</h2>".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(msg)
    
    def log_message(self, *args):
        pass
