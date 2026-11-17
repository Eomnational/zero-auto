"""Read-only: print a handle's N most recent original posts (text + date + URL).

Loads the profile Posts tab, scrolls to load more, and collects the handle's
own posts only: skips the pinned post, skips reposts (another author's words),
skips media-only posts with no text. Prints one JSON array.
"""
import json, os, sys
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
PROFILE = os.environ.get("CAMOUFOX_PROFILE", f"{HOME}/workspace/camoufox/profile-x")
PROXY = {"server": os.environ.get("RELAY_URL", "http://127.0.0.1:18081")}
GEOIP = os.environ["GEOIP_IP"]
HANDLE = sys.argv[1].lstrip("@")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 15


def safe_wait(page, ms):
    try:
        page.wait_for_timeout(ms)
    except Exception:
        pass


ctx = Camoufox(headless=True, persistent_context=True, user_data_dir=PROFILE,
               proxy=PROXY, geoip=GEOIP, os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    page = ctx.new_page()
    page.goto(f"https://x.com/{HANDLE}", timeout=90000, wait_until="domcontentloaded")
    safe_wait(page, 8000)
    posts = {}  # url -> {text, dt, url}
    last_count = 0
    stall = 0
    for _ in range(14):
        arts = page.locator('article[data-testid="tweet"]')
        n = arts.count()
        for i in range(n):
            a = arts.nth(i)
            try:
                tx = a.inner_text()
                if "Pinned" in tx:
                    continue
                if "reposted" in tx.lower():
                    continue
                author = a.evaluate("""el => { const u = el.querySelector('a[href^="/"]'); return u ? u.getAttribute('href') : ''; }""")
                if ("/" + HANDLE).lower() not in (author or "").lower():
                    continue
                link = a.evaluate("""el => { const l = el.querySelector('a[href*="/status/"]'); return l ? l.getAttribute('href') : ''; }""")
                if not link:
                    continue
                url = "https://x.com" + link if link.startswith("/") else link
                if url in posts:
                    continue
                t = a.locator('div[data-testid="tweetText"]')
                text = t.first.inner_text() if t.count() else ""
                if not text.strip():
                    continue
                dt = a.evaluate("""el => { const tm = el.querySelector('time'); return tm ? tm.getAttribute('datetime') : ''; }""")
                posts[url] = {"text": text, "dt": dt, "url": url}
                if len(posts) >= N:
                    break
            except Exception:
                pass
        if len(posts) >= N:
            break
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        safe_wait(page, 3000)
        n2 = page.locator('article[data-testid="tweet"]').count()
        if n2 == last_count:
            stall += 1
            if stall >= 2:
                break
        else:
            stall = 0
        last_count = n2
    print(json.dumps(list(posts.values())[:N], ensure_ascii=False, indent=1))
    print(f"COLLECTED {len(posts)}", file=sys.stderr)
finally:
    ctx.__exit__(None, None, None)
