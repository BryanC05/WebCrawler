# WebCrawler

WebCrawler turns a live webpage into a small interactive scene. It serves a target page through a local proxy, draws a wandering spider over it, and reveals floating labels when the spider touches links, images, or short numeric values.

![WebCrawler running in a browser](shot.png)

## Requirements

- Python 3.8 or newer
- Internet access to load the page you want to explore

The project uses only the Python standard library. Installing [`certifi`](https://pypi.org/project/certifi/) is optional and can help on Windows systems with incomplete certificate stores:

```powershell
python -m pip install certifi
```

## Run

Start the crawler with its default target, the Wikipedia Spider article:

```powershell
python crawler.py
```

Then open [http://localhost:8000](http://localhost:8000).

To begin on a different page or use another port:

```powershell
python crawler.py https://example.com --port 8080
```

Open `http://localhost:8080` when using a custom port. Stop the server with `Ctrl+C`.

## Use

- Enter a URL in the bar at the bottom of the page and choose **crawl**, or press `Enter`.
- The spider roams automatically and keeps a running count of caught items and distance travelled.
- A first contact with a link, image, or focused numeric value produces a floating label. Repeated contacts with the same item are rate-limited.
- Caught links are visually consumed; caught images are hidden while their layout remains in place.

## How It Works

`crawler.py` starts a threaded local web server. Its `/proxy` endpoint fetches the requested HTML, removes scripts and event handlers, rewrites relative `href` and `src` attributes to absolute URLs, and serves the cleaned page to the browser.

`index.html` renders that proxied page in a full-screen iframe and places a canvas-based, eight-legged spider above it. Because the iframe is served from the local proxy, the overlay can inspect visible page elements and respond to leg contacts.

## Project Files

| File | Purpose |
| --- | --- |
| `crawler.py` | Local HTTP server and remote-page proxy/cleaner. |
| `index.html` | Interactive WebCrawler interface and spider animation. |
| `qa.mjs` | Browser-test helper that waits for the animation, records UI state, and writes `shot.png`. |
| `shot.png` | Example browser capture. |

## Notes

- Only `http://` and `https://` URLs are accepted by the proxy.
- Some websites may not render fully because they require JavaScript, block automated requests, or depend on browser security policies. The proxy deliberately removes page scripts before rendering.
- This is a local exploratory tool, not a full web scraper. Be mindful of the sites you visit and their terms of use.
