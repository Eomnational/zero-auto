"""Verify the restored X session: load home, check account name + composer."""
import json
import os

from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
PROFILE = f"{HOME}/workspace/camoufox/profile-x"
PROXY = {"server": "http://127.0.0.1:18081"}
GEOIP = os.environ["GEOIP_IP"]

result = {"logged_in": False, "name_seen": False, "composer_seen": False, "error": None}
ctx = Camoufox(headless=True, persistent_context=True, user_data_dir=PROFILE,
               proxy=PROXY, geoip=GEOIP, os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    page = ctx.new_page()
    page.goto("https://x.com/home", timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(12000)
    body = page.evaluate("() => document.body.innerText.slice(0, 4000)")
    result["name_seen"] = "@xunana1017" in body
    try:
        page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=8000)
        result["composer_seen"] = True
    except Exception:
        result["composer_seen"] = False
    result["logged_in"] = result["name_seen"] or result["composer_seen"]
    result["body_snippet"] = body[:300].replace("\n", " | ")
    print("RESULT " + json.dumps(result, ensure_ascii=False))
except Exception as e:
    result["error"] = repr(e)[:300]
    print("RESULT " + json.dumps(result, ensure_ascii=False))
finally:
    ctx.__exit__(None, None, None)
