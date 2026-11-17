"""Transplant x.com session cookies from a Chromium run into a Camoufox profile.

Reads cookies saved by chrome_google_login.py and adds them one by one to a
persistent Camoufox profile, then verifies https://x.com/home shows the account.
Delete CTL_DIR/cookies.json after a successful transplant. The session then
lives inside the Camoufox profile only.

Required env:
  GEOIP_IP   current exit IP of the residential proxy (must match the live exit)
Optional env:
  CAMOUFOX_PROFILE  profile dir (default ~/workspace/camoufox/profile-x)
  RELAY_URL         upstream proxy (default http://127.0.0.1:18081)
  CTL_DIR           status and output dir (default ~/workspace/camoufox/ctl)
"""
import json, os
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
CTL = os.environ.get("CTL_DIR", f"{HOME}/workspace/camoufox/ctl")
PROFILE = os.environ.get("CAMOUFOX_PROFILE", f"{HOME}/workspace/camoufox/profile-x")
PROXY = {"server": os.environ.get("RELAY_URL", "http://127.0.0.1:18081")}
GEOIP = os.environ["GEOIP_IP"]

cookies = json.load(open(os.path.join(CTL, "cookies.json")))
print("cookies loaded:", len(cookies), flush=True)
clean = []
for c in cookies:
    nc = {"name": c["name"], "value": c["value"], "domain": c["domain"], "path": c.get("path", "/")}
    if c.get("expires", -1) and c["expires"] > 0:
        nc["expires"] = c["expires"]
    nc["httpOnly"] = bool(c.get("httpOnly", False))
    nc["secure"] = bool(c.get("secure", False))
    ss = c.get("sameSite")
    if ss in ("Strict", "Lax", "None"):
        nc["sameSite"] = ss
    clean.append(nc)

ctx = Camoufox(headless=True, persistent_context=True, user_data_dir=PROFILE,
               proxy=PROXY, geoip=GEOIP, os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    ok = fail = 0
    for c in clean:
        try:
            ctx.add_cookies([c])
            ok += 1
        except Exception:
            fail += 1
    print("added:", ok, "failed:", fail, flush=True)
    names = {c["name"] for c in ctx.cookies()}
    print("auth_token present:", "auth_token" in names, flush=True)
    page = ctx.new_page()
    page.goto("https://x.com/home", timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(12000)
    t = page.evaluate("() => document.body ? document.body.innerText.slice(0, 900) : ''")
    logged_in = "Log in" not in t[:200] and ("Home timeline" in t or "For you" in t)
    print("LOGGED IN:", logged_in, flush=True)
    print("HOME HEAD:", t[:220].replace("\n", " "), flush=True)
    page.screenshot(path=os.path.join(CTL, "shot-home.png"))
finally:
    ctx.close()
print("TRANSPLANT DONE", flush=True)
