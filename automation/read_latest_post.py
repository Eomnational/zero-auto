"""Read-only: print a handle's latest non-pinned post text and status URL."""
import os, sys
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
PROFILE = os.environ.get("CAMOUFOX_PROFILE", f"{HOME}/workspace/camoufox/profile-x")
PROXY = {"server": os.environ.get("RELAY_URL", "http://127.0.0.1:18081")}
GEOIP = os.environ["GEOIP_IP"]
HANDLE = sys.argv[1].lstrip("@")

ctx = Camoufox(headless=True, persistent_context=True, user_data_dir=PROFILE,
               proxy=PROXY, geoip=GEOIP, os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    page = ctx.new_page()
    page.goto(f"https://x.com/{HANDLE}", timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    arts = page.locator('article[data-testid="tweet"]')
    found = None
    for i in range(min(arts.count(), 6)):
        a = arts.nth(i)
        try:
            tx = a.inner_text()
            author = a.evaluate("""el => { const u = el.querySelector('a[href^="/"]'); return u ? u.getAttribute('href') : ''; }""")
            if ("/" + HANDLE).lower() in (author or "").lower() and "Pinned" not in tx:
                link = a.evaluate("""el => { const l = el.querySelector('a[href*="/status/"]'); return l ? l.getAttribute('href') : ''; }""")
                found = (tx, link)
                break
        except Exception:
            pass
    if found:
        print("POST_TEXT_START")
        print(found[0])
        print("POST_TEXT_END")
        print("POST_URL: https://x.com" + found[1] if found[1].startswith("/") else "POST_URL: " + found[1])
    else:
        print("NO_POST_FOUND")
finally:
    ctx.__exit__(None, None, None)
