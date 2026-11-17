"""Operate a logged-in X account from its Camoufox profile.

Usage: x_ops.py <post|reply|like|follow|dm>

Env per action:
  post    TEXT to publish (must be Simplified Chinese — the script refuses
          Traditional Chinese, English-majority, or non-Chinese text).
          Prints POSTED plus the new post's status URL when it can be
          read back from the profile (best effort; plain POSTED otherwise)
  reply   TARGET_HANDLE and TEXT, replies to the target's latest non-pinned post
          (TEXT is at most 25 characters — the script refuses longer replies;
          TEXT must also be Simplified Chinese, same rule as post)
  like    TARGET_HANDLE, likes the target's latest non-pinned post
  follow  TARGET_HANDLE
  dm      TARGET_HANDLE and TEXT, uses CHAT_PIN when the X Chat passcode screen appears

Shared env:
  GEOIP_IP          current exit IP of the residential proxy (required)
  CAMOUFOX_PROFILE  profile dir (default ~/workspace/camoufox/profile-x)
  RELAY_URL         upstream proxy (default http://127.0.0.1:18081)
  CTL_DIR           screenshot dir (default ~/workspace/camoufox/ctl)

Hard rules baked in from field experience:
  Compose with page.keyboard.insert_text, never press_sequentially. The X
  composer scrambles the first CJK character to the end with sequential typing.
  Read the composer text back and only send when it matches exactly.
  Locate modal buttons with Playwright locators, not coordinates.
"""
import os, sys
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
CTL = os.environ.get("CTL_DIR", f"{HOME}/workspace/camoufox/ctl")
PROFILE = os.environ.get("CAMOUFOX_PROFILE", f"{HOME}/workspace/camoufox/profile-x")
PROXY = {"server": os.environ.get("RELAY_URL", "http://127.0.0.1:18081")}
GEOIP = os.environ["GEOIP_IP"]
ACTION = sys.argv[1]
TARGET = os.environ.get("TARGET_HANDLE", "").lstrip("@")
OWN = os.environ.get("OWN_HANDLE", "xunana1017")
TEXT = os.environ.get("TEXT", "")

# Hard reply limit (user rule, 2026-11-12): a reply is at most 25 characters.
# Refuse before opening the browser so an over-long reply never reaches X.
if ACTION == "reply" and len(TEXT) > 25:
    print(f"REPLY_TOO_LONG len={len(TEXT)} max=25", flush=True)
    sys.exit(2)

# Hard language rule (user rule, 2026-11-12): post and reply text must be
# Simplified Chinese. English technical terms / brand names (AI, X, API),
# digits, @handles, URLs and emoji are fine inside Chinese text; what is
# refused is Traditional-only characters, Japanese kana, Korean hangul, and
# text where Latin letters outnumber Chinese characters.
_TRADITIONAL_ONLY = set("們麼這個說國學對來開關見車馬長門問頭點還會經過邊遠運選讓實際幾廣廠寫樂親龍龜書畫話語讀聽買賣價錢鐵鋼電視覺觀歡難願應嗎髮幹隻麼乾餘衛為時於著發後裡種現當沒動進樣從軍無與機業將兩間體賺賬戶")

def check_simplified_chinese(text):
    """Return None when text is Simplified Chinese, else a reason string."""
    for ch in text:
        if ch in _TRADITIONAL_ONLY:
            return f"traditional character {ch!r}"
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF:
            return "japanese kana"
        if 0xAC00 <= o <= 0xD7A3:
            return "korean hangul"
    cjk = sum(1 for ch in text if 0x4E00 <= ord(ch) <= 0x9FFF or 0x3400 <= ord(ch) <= 0x4DBF)
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if cjk == 0:
        return "no simplified chinese characters"
    if latin > cjk:
        return f"latin letters outnumber chinese ({latin} > {cjk})"
    return None

# Refuse before opening the browser so a wrong-language post never reaches X.
# The automation's posts go through this script too, so they share this gate.
if ACTION in ("post", "reply"):
    _reason = check_simplified_chinese(TEXT)
    if _reason:
        print(f"NOT_SIMPLIFIED_CHINESE {_reason}", flush=True)
        sys.exit(2)

def text_of(page):
    try:
        return page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:
        return ""

def latest_post(page, handle):
    page.goto(f"https://x.com/{handle}", timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    arts = page.locator('article[data-testid="tweet"]')
    for i in range(min(arts.count(), 6)):
        a = arts.nth(i)
        try:
            tx = a.inner_text()
            author = a.evaluate("""el => { const u = el.querySelector('a[href^="/"]'); return u ? u.getAttribute('href') : ''; }""")
            if ("/" + handle).lower() in (author or "").lower() and "Pinned" not in tx:
                a.scroll_into_view_if_needed()
                page.wait_for_timeout(800)
                return a
        except Exception:
            pass
    return None

def find_area(page, extra=()):
    sels = list(extra) + ['[data-testid="dmComposerTextArea"]', '[data-testid="dmComposerTextarea"]',
                          'div[contenteditable="true"][role="textbox"]', 'div[contenteditable="true"]',
                          'textarea[placeholder*="message" i]', '[placeholder*="Message" i]', 'textarea']
    for i in range(14):
        for sel in sels:
            loc = page.locator(sel)
            try:
                if loc.count() > 0 and loc.first.is_visible():
                    return loc.first
            except Exception:
                pass
        page.wait_for_timeout(5000)
    return None

ctx = Camoufox(headless=True, persistent_context=True, user_data_dir=PROFILE,
               proxy=PROXY, geoip=GEOIP, os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    page = ctx.new_page()

    if ACTION == "post":
        page.goto("https://x.com/home", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(9000)
        box = page.locator('[data-testid="tweetTextarea_0"]').first
        box.click(timeout=20000)
        page.wait_for_timeout(2500)
        page.keyboard.insert_text(TEXT)
        page.wait_for_timeout(1200)
        got = box.inner_text()
        assert TEXT in got, f"composer mismatch: {got!r}"
        page.locator('[data-testid="tweetButtonInline"]').first.click(timeout=15000)
        page.wait_for_timeout(9000)
        # Capture the new post's status URL for the log and for the
        # first-floor follow-up: the newest non-pinned post on the own
        # profile is the one just published — accept it only when its
        # first line matches the text just posted, so a stale profile
        # can never hand back the previous post's URL. Best effort: a
        # failure here must not fail the post.
        url = ""
        try:
            a = latest_post(page, OWN)
            if a is not None:
                tx = a.inner_text()
                if TEXT.split("\n")[0][:30] in tx:
                    link = a.evaluate("""el => { const l = el.querySelector('a[href*="/status/"]'); return l ? l.getAttribute('href') : ''; }""")
                    if link:
                        url = "https://x.com" + link if link.startswith("/") else link
        except Exception:
            url = ""
        page.screenshot(path=f"{CTL}/shot-posted.png")
        print("POSTED" + (f" {url}" if url else ""), flush=True)

    elif ACTION == "reply":
        a = latest_post(page, TARGET)
        assert a is not None, "no target post found"
        a.locator('[data-testid="reply"]').first.click(timeout=15000)
        page.wait_for_timeout(4000)
        box = page.locator('[data-testid="tweetTextarea_0"]').first
        box.click(timeout=15000)
        page.wait_for_timeout(2500)
        page.keyboard.insert_text(TEXT)
        page.wait_for_timeout(1200)
        got = box.inner_text()
        assert TEXT in got, f"composer mismatch: {got!r}"
        page.locator('[data-testid="tweetButton"]').first.click(timeout=15000)
        page.wait_for_timeout(8000)
        page.screenshot(path=f"{CTL}/shot-reply.png")
        print("REPLIED", flush=True)

    elif ACTION == "like":
        a = latest_post(page, TARGET)
        assert a is not None, "no target post found"
        if a.locator('[data-testid="unlike"]').count() > 0:
            print("ALREADY LIKED", flush=True)
        else:
            a.locator('[data-testid="like"]').first.click(timeout=15000)
            page.wait_for_timeout(3000)
            assert a.locator('[data-testid="unlike"]').count() > 0, "like did not stick"
            print("LIKED", flush=True)
        page.screenshot(path=f"{CTL}/shot-like.png")

    elif ACTION == "follow":
        page.goto(f"https://x.com/{TARGET}", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
        if page.locator('[data-testid$="-unfollow"]').count() > 0:
            print("ALREADY FOLLOWING", flush=True)
        else:
            page.locator('[data-testid$="-follow"]').first.click(timeout=15000)
            page.wait_for_timeout(4000)
            assert page.locator('[data-testid$="-unfollow"]').count() > 0, "follow did not stick"
            print("FOLLOWED", flush=True)
        page.screenshot(path=f"{CTL}/shot-follow.png")

    elif ACTION == "dm":
        pin = os.environ.get("CHAT_PIN", "")
        page.goto(f"https://x.com/{TARGET}", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
        page.locator('[data-testid="sendDMFromProfile"], [aria-label="Message"]').first.click(timeout=15000)
        # The chat surface renders in shadow DOM. page.locator sees it, body innerText does not.
        for i in range(18):
            page.wait_for_timeout(4000)
            if "/pin/" in page.url and page.locator("input").count() >= 4:
                assert pin, "X Chat asks for the 4 digit passcode. Ask the user for it and set CHAT_PIN."
                ins = page.locator("input")
                ins.first.click(timeout=10000)
                page.wait_for_timeout(600)
                for d in pin:
                    page.keyboard.press(d)
                    page.wait_for_timeout(320)
                print("PIN TYPED", flush=True)
                page.wait_for_timeout(10000)
                break
            if "/pin/" not in page.url and i > 3:
                break
        area = find_area(page)
        assert area is not None, "no DM composer found"
        area.click(timeout=12000)
        page.wait_for_timeout(1000)
        page.keyboard.insert_text(TEXT)
        page.wait_for_timeout(1000)
        send = page.locator('[data-testid="dmComposerSendButton"], button[aria-label="Send"], [aria-label="Send message"]')
        if send.count() > 0:
            send.first.click(timeout=12000)
        else:
            page.keyboard.press("Enter")
        page.wait_for_timeout(6000)
        hits = page.locator(f':text("{TEXT}")').count()
        assert hits > 0, "message not visible after send"
        page.screenshot(path=f"{CTL}/shot-dm.png")
        print("DM SENT", flush=True)

    else:
        print("unknown action", ACTION)
        raise SystemExit(2)
finally:
    ctx.close()
print("OPS DONE", flush=True)
