"""
WebCrawler â€” a spider crawls over a real webpage; when its leg tips touch
links/elements, their text pops out as floating labels (inspired by @rybinfx).

Usage:
    python crawler.py [start_url] [--port 8000]

Then open http://localhost:8000
"""
import argparse
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
HERE = os.path.dirname(os.path.abspath(__file__))

# Some Windows trust stores ship expired roots; verify first, fall back if needed.
SSL_CTX = ssl.create_default_context()
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass


def fetch_html(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX)
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLError):
            resp = urllib.request.urlopen(req, timeout=timeout,
                                          context=ssl._create_unverified_context())
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
    """Rewrite relative href/src against the page URL."""
    def fix(match):
        attr, quote, value = match.group(1), match.group(2), match.group(3)
        if value.startswith(("data:", "javascript:", "#", "mailto:", "http")):
            return match.group(0)
        try:
            return f'{attr}={quote}{urllib.parse.urljoin(base, value)}{quote}'
        except Exception:
            return match.group(0)
    return re.sub(r"(href|src)=(\"|')([^\"']+)", fix, html)


def clean(html, base):
    """Make a remote page safe & same-origin-renderable in an iframe."""
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


class CrawlerHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def translate_path(self, path):
        # serve the URL-substituted index as the homepage
        if path in ("/", "/index.html"):
            path = "/_start.html"
        return super().translate_path(path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/proxy":
            qs = urllib.parse.parse_qs(parsed.query)
            target = (qs.get("url") or [""])[0]
            if not target.startswith(("http://", "https://")):
                self.send_error(400, "url param required")
                return
            try:
                body = clean(fetch_html(target), target)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8", "ignore"))
            except Exception as e:
                msg = ("<h2 style='font-family:monospace;color:#f0f'>could not fetch "
                       f"{target}<br>{e}</h2>").encode()
                self.send_response(502)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(msg)
            return
        super().do_GET()


def main():
    ap = argparse.ArgumentParser(description="Spider-crawls a real webpage and pops its text")
    ap.add_argument("start", nargs="?", default="https://en.wikipedia.org/wiki/Spider")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    index_path = os.path.join(HERE, "index.html")
    html = open(index_path, encoding="utf-8").read().replace("__START_URL__", args.start)
    open(os.path.join(HERE, "_start.html"), "w", encoding="utf-8").write(html)

    srv = ThreadingHTTPServer(("0.0.0.0", args.port), CrawlerHandler)
    print(f"[*] WebCrawler running -> http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Bye.")


if __name__ == "__main__":
    main()

