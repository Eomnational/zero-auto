"""Complete a Google sign-in for X in Playwright Chromium and save the session cookies.

Why: Google sign-in completed inside Firefox or Camoufox is rejected by X with
"An unexpected error occurred". The same sign-in in Chromium succeeds, and the
resulting x.com cookies can be transplanted into the Camoufox profile.

Required env:
  X_EMAIL        Google account email used to sign in to X
  GOOGLE_PW      Google account password (pass through env only, never write to a file)
Optional env:
  CHROME_PROFILE persistent Chromium profile dir (default ~/workspace/camoufox/chrome-profile)
  RELAY_URL      upstream proxy for the browser (default http://127.0.0.1:18081)
  CTL_DIR        status and output dir (default ~/workspace/camoufox/ctl)

Writes CTL_DIR/status.json while running and CTL_DIR/cookies.json on success.
If Google shows a device prompt, status becomes need_user_verify with the number
to tap on the phone. Touching CTL_DIR/resend.txt clicks Resend once.
Touching CTL_DIR/close.txt stops the session gracefully.
"""
import json, os, re, time
from playwright.sync_api import sync_playwright

HOME = os.path.expanduser("~")
CTL = os.environ.get("CTL_DIR", f"{HOME}/workspace/camoufox/ctl")
PROXY = {"server": os.environ.get("RELAY_URL", "http://127.0.0.1:18081")}
PROFILE = os.environ.get("CHROME_PROFILE", f"{HOME}/workspace/camoufox/chrome-profile")
EMAIL = os.environ["X_EMAIL"]
PW = os.environ.get("GOOGLE_PW", "")

def set_status(**kw):
    kw["ts"] = time.strftime("%H:%M:%S")
    with open(os.path.join(CTL, "status.json"), "w") as f:
        json.dump(kw, f, ensure_ascii=False)
    print("STATUS:", kw, flush=True)

def text_of(page):
    try:
        return page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:
        return ""

def safe_wait(p, ms):
    try:
        p.wait_for_timeout(ms)
    except Exception:
        pass

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        PROFILE,
        headless=False,
        proxy=PROXY,
        locale="en-US",
        timezone_id="America/New_York",
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
    )
    page = ctx.new_page()
    try:
        def has_auth():
            try:
                return "auth_token" in {c["name"] for c in ctx.cookies()}
            except Exception:
                return False
        page.goto("https://x.com/", timeout=90000, wait_until="domcontentloaded")
        safe_wait(page, 9000)
        if has_auth():
            set_status(step="chrome_already_logged_in")
            raise SystemExit
        btn = page.locator('button:has-text("Continue with Google"), [role="button"]:has-text("Continue with Google")')
        popup = None
        try:
            with ctx.expect_page(timeout=20000) as pinfo:
                btn.first.click(timeout=20000)
            popup = pinfo.value
        except Exception as e:
            print("POPUP WAIT:", repr(e)[:120], flush=True)
        g = popup if popup is not None else page
        safe_wait(g, 6000)
        deadline = time.time() + 600
        last_num = None
        verify_noted = False
        while time.time() < deadline:
            if os.path.exists(os.path.join(CTL, "close.txt")):
                set_status(step="aborted")
                raise SystemExit
            if has_auth():
                with open(os.path.join(CTL, "cookies.json"), "w") as f:
                    json.dump(ctx.cookies(), f)
                set_status(step="chrome_logged_in", url=page.url)
                page.goto("https://x.com/home", timeout=60000, wait_until="domcontentloaded")
                safe_wait(page, 6000)
                page.screenshot(path=os.path.join(CTL, "shot-chrome-home.png"))
                break
            try:
                t = text_of(g)
            except Exception:
                t = ""
            low = t.lower()
            url = ""
            try:
                url = g.url
            except Exception:
                pass
            print("LOOP:", url[:80], "|", t[:80].replace("\n", " "), flush=True)
            if "not be secure" in low or "browser or app may not be secure" in low:
                set_status(step="google_blocked_browser", text=t[:300])
                raise SystemExit
            if "accountchooser" in url or "选择账号" in t:
                g.locator(f'li:has-text("{EMAIL}")').first.click(timeout=10000)
                print("  -> chooser", flush=True)
                safe_wait(g, 6000)
                continue
            if ("您将共享" in t or "continue to x" in low) and ("继续" in t or "Continue" in t):
                cb = g.locator('button:has-text("继续"), button:has-text("Continue")')
                if cb.count() > 0:
                    cb.last.click()
                    print("  -> consent", flush=True)
                    safe_wait(g, 7000)
                    continue
            ein = g.locator('input[type="email"], input[name="identifier"]')
            try:
                if ein.count() > 0 and ein.first.is_visible():
                    ein.first.click()
                    ein.first.press_sequentially(EMAIL, delay=50)
                    g.locator('#identifierNext button, button:has-text("Next"), button:has-text("下一步")').first.click()
                    print("  -> email", flush=True)
                    safe_wait(g, 6000)
                    continue
            except Exception:
                pass
            pin = g.locator('input[type="password"], input[name="Passwd"]')
            try:
                if pin.count() > 0 and pin.first.is_visible():
                    pin.first.click()
                    pin.first.press_sequentially(PW, delay=50)
                    g.locator('#passwordNext button, button:has-text("Next"), button:has-text("下一步")').first.click()
                    print("  -> password", flush=True)
                    safe_wait(g, 8000)
                    t2 = text_of(g)
                    if "wrong password" in t2.lower() or "密码不正确" in t2:
                        set_status(step="wrong_google_password", text=t2[:200])
                        raise SystemExit
                    continue
            except SystemExit:
                raise
            except Exception:
                pass
            m = re.search(r"tap (\d+) on your phone", t)
            if m:
                if m.group(1) != last_num:
                    last_num = m.group(1)
                    set_status(step="need_user_verify", number=last_num, text=t[:260])
                if os.path.exists(os.path.join(CTL, "resend.txt")):
                    os.remove(os.path.join(CTL, "resend.txt"))
                    try:
                        rs = g.locator('button:has-text("Resend"), [role="button"]:has-text("Resend"), a:has-text("Resend"), span:has-text("Resend")')
                        if rs.count() > 0:
                            rs.first.click(timeout=8000)
                            print("  -> resend clicked", flush=True)
                            last_num = None
                    except Exception as e:
                        print("resend err", repr(e)[:120], flush=True)
                safe_wait(g, 5000)
                continue
            if ("verify it" in low or "确认是您本人" in t) and not verify_noted:
                verify_noted = True
                g.screenshot(path=os.path.join(CTL, "shot-chrome-verify.png"))
                set_status(step="chrome_verify_screen", text=t[:400])
            safe_wait(g, 4000)
        else:
            set_status(step="chrome_unknown_final", text=text_of(page)[:260])
        end = time.time() + 30
        while time.time() < end and not os.path.exists(os.path.join(CTL, "close.txt")):
            time.sleep(3)
    finally:
        try:
            ctx.close()
        except Exception:
            pass
        try:
            set_status(step="closed")
        except Exception:
            pass
