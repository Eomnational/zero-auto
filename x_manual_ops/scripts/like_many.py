"""One-off: like specific tweets by URL + text fragment.
Finds the matching article on each status page, clicks like if not already
liked, verifies it flips to unlike. Read-only apart from the likes."""
import json, os, sys
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
# args: pairs of URL and text fragment
pairs = [(sys.argv[i], sys.argv[i + 1]) for i in range(1, len(sys.argv), 2)]
ctx = Camoufox(headless=True, persistent_context=True,
               user_data_dir=f"{HOME}/workspace/camoufox/profile-x",
               proxy={"server": "http://127.0.0.1:18081"},
               geoip=os.environ["GEOIP_IP"], os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
results = []
try:
    page = ctx.new_page()
    for url, frag in pairs:
        page.goto(url, timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
        art = None
        for a in page.locator('article[data-testid="tweet"]').all():
            try:
                if frag in (a.inner_text() or ""):
                    art = a
                    break
            except Exception:
                pass
        if art is None:
            results.append({"url": url, "liked": False, "error": "tweet not found"})
            continue
        if art.locator('[data-testid="unlike"]').count() > 0:
            results.append({"url": url, "liked": True, "already": True})
            continue
        like = art.locator('[data-testid="like"]').first
        like.click(timeout=15000)
        page.wait_for_timeout(2500)
        ok = art.locator('[data-testid="unlike"]').count() > 0
        results.append({"url": url, "liked": ok})
    print("LIKE_RESULT " + json.dumps(results, ensure_ascii=False), flush=True)
finally:
    ctx.__exit__(None, None, None)
