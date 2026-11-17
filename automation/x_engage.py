"""Browser primitives for X engagement. Each subcommand prints one JSON line.

Subcommands:
  foryou                 list candidate posts from the home For You feed
  comment URL            reply to the post at URL with TEXT env, then like it
                         within 5 seconds of submitting (hard rule)
  notifications          list actionable mention or reply notifications
  reply_like URL         reply to the tweet at URL with TEXT env, then like it
                         within 5 seconds of submitting (hard rule)
  firstfloor URL         reply to the own post at URL with TEXT env (the
                         first-floor follow-up: links, handouts, extra
                         detail). No 25-character limit — it is a follow-up
                         post, not an engagement reply — but Simplified
                         Chinese still applies. Idempotent: if a self-reply
                         with the same text is already on the post, reports
                         already=true without sending.
  followers              list verified followers not yet followed back
  follow HANDLE          follow HANDLE
  stats                  own profile counts plus today's post view counts

Shared env: GEOIP_IP (required), CAMOUFOX_PROFILE, RELAY_URL, CTL_DIR, OWN_HANDLE.
TEXT env carries the comment or reply text for the writing actions.
Comment and reply text follow exactly the same hard constraints as a manual
reply in x_manual_ops: at most 25 characters and Simplified Chinese, enforced
below before the browser opens (same gates as x_ops.py). First-floor text
shares only the Simplified Chinese gate — no 25-character limit.
"""
import json, os, sys, time
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
CTL = os.environ.get("CTL_DIR", f"{HOME}/workspace/camoufox/ctl")
PROFILE = os.environ.get("CAMOUFOX_PROFILE", f"{HOME}/workspace/camoufox/profile-x")
PROXY = {"server": os.environ.get("RELAY_URL", "http://127.0.0.1:18081")}
GEOIP = os.environ["GEOIP_IP"]
OWN = os.environ.get("OWN_HANDLE", "xunana1017")
CMD = sys.argv[1]
ARG = sys.argv[2] if len(sys.argv) > 2 else ""
TEXT = os.environ.get("TEXT", "")

# Hard comment/reply limits (user rule, 2026-11-12): automation comments and
# notification replies follow exactly the same constraints as manual replies
# in x_manual_ops — at most 25 characters, Simplified Chinese. Same gates as
# x_ops.py, refused before the browser opens so a non-compliant draft never
# reaches X. A refusal publishes nothing and counts as no action; the worker
# trims or rewrites the text and retries once in the same run.
# First-floor follow-ups (firstfloor) share only the Simplified Chinese gate:
# no 25-character limit, because a first floor carries links, handouts or
# extra detail that cannot fit in 25 characters.
if CMD in ("comment", "reply_like") and len(TEXT) > 25:
    print(f"REPLY_TOO_LONG len={len(TEXT)} max=25", flush=True)
    sys.exit(2)

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

if CMD in ("comment", "reply_like", "firstfloor"):
    _reason = check_simplified_chinese(TEXT)
    if _reason:
        print(f"NOT_SIMPLIFIED_CHINESE {_reason}", flush=True)
        sys.exit(2)

def out(obj):
    print("RESULT " + json.dumps(obj, ensure_ascii=False), flush=True)

OVERLAY_MARKERS = ("Unlock more on X", "To make X great for everyone")

def overlay_present(page):
    try:
        body = page.locator("body").inner_text(timeout=5000)
    except Exception:
        return False
    return any(m in body for m in OVERLAY_MARKERS)

def clear_overlay(page, tries=3):
    """X intermittently covers tweet pages with a login-wall / bot-check
    interstitial that intercepts every click. Wait it out, try Escape and a
    close control; return True when the page is clear."""
    for _ in range(tries):
        if not overlay_present(page):
            return True
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        try:
            close = page.locator('button[aria-label="Close"]').first
            if close.count() > 0:
                close.click(timeout=5000)
        except Exception:
            pass
        page.wait_for_timeout(5000)
    return not overlay_present(page)

def safe_click(page, loc, timeout=15000):
    """Click once; if an overlay intercepts it, clear the overlay and retry once."""
    try:
        loc.click(timeout=timeout)
    except Exception:
        page.wait_for_timeout(3000)
        clear_overlay(page)
        loc.click(timeout=timeout)

def like_within_5s(page, art, t_submit):
    """Like the post in `art` within 5 seconds of the submit at t_submit
    (a time.monotonic() reading). Returns (liked, ms_since_submit, error).
    Every step is budgeted against the 5 second window; a miss is reported
    with its reason instead of hanging past the window."""
    deadline = t_submit + 5.0
    def ms():
        return int((time.monotonic() - t_submit) * 1000)
    try:
        if art.locator('[data-testid="unlike"]').count() > 0:
            return True, ms(), ""
        like = art.locator('[data-testid="like"]').first
        if like.count() == 0:
            return False, ms(), "no like button on article"
        left = deadline - time.monotonic()
        if left > 0.3:
            like.scroll_into_view_if_needed(timeout=max(100, int(min(1500, left * 1000))))
        left = deadline - time.monotonic()
        if left <= 0:
            return False, ms(), "window expired before click"
        like.click(timeout=max(100, int(min(3000, left * 1000))))
        while time.monotonic() < deadline:
            if art.locator('[data-testid="unlike"]').count() > 0:
                return True, ms(), ""
            page.wait_for_timeout(100)
        return False, ms(), "unlike state not confirmed in window"
    except Exception as e:
        return False, ms(), f"{type(e).__name__}: {str(e)[:80]}"

ctx = Camoufox(headless=True, persistent_context=True, user_data_dir=PROFILE,
               proxy=PROXY, geoip=GEOIP, os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    page = ctx.new_page()

    if CMD == "foryou":
        page.goto("https://x.com/home", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(11000)
        tabs = page.locator('[role="tab"]')
        for i in range(tabs.count()):
            try:
                if "For you" in tabs.nth(i).inner_text():
                    if tabs.nth(i).get_attribute("aria-selected") != "true":
                        tabs.nth(i).click(timeout=8000)
                        page.wait_for_timeout(6000)
                    break
            except Exception:
                pass
        items = page.evaluate("""(own) => {
          const res = [];
          document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
            const tx = a.innerText || '';
            if (/Promoted|广告/.test(tx.slice(0, 400))) return;
            const links = [...a.querySelectorAll('a[href*="/status/"]')].map(x => x.getAttribute('href'));
            const userLink = a.querySelector('[data-testid="User-Name"] a');
            const handle = userLink ? userLink.getAttribute('href').slice(1) : '';
            if (!handle || handle.toLowerCase() === own.toLowerCase()) return;
            const tt = a.querySelector('[data-testid="tweetText"]');
            const likeBtn = a.querySelector('[data-testid="like"], [data-testid="unlike"]');
            const replyBtn = a.querySelector('[data-testid="reply"]');
            res.push({
              handle: handle,
              url: links.length ? 'https://x.com' + links[0] : '',
              text: tt ? tt.innerText.slice(0, 280) : tx.slice(0, 280),
              liked: !!a.querySelector('[data-testid="unlike"]'),
              like_label: likeBtn ? likeBtn.getAttribute('aria-label') : '',
              reply_label: replyBtn ? replyBtn.getAttribute('aria-label') : ''
            });
          });
          return res;
        }""", OWN)
        out({"candidates": items[:10]})

    elif CMD == "comment":
        page.goto(ARG, timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
        if not clear_overlay(page):
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(10000)
            if not clear_overlay(page):
                out({"ok": False, "error": "overlay blocks page"})
                raise SystemExit
        box = page.locator('[data-testid="tweetTextarea_0"]').first
        safe_click(page, box)
        page.wait_for_timeout(2000)
        page.keyboard.insert_text(TEXT)
        page.wait_for_timeout(1000)
        got = box.inner_text()
        if TEXT not in got:
            out({"ok": False, "error": "composer mismatch", "got": got[:80]})
            raise SystemExit
        # Inline reply composer uses tweetButtonInline; the main composer uses tweetButton.
        btn = page.locator('[data-testid="tweetButtonInline"]').first
        if btn.count() == 0:
            btn = page.locator('[data-testid="tweetButton"]').first
        safe_click(page, btn)
        # Hard rule (user, 2026-11-12): the like must land within 5 seconds
        # of the comment being submitted.
        t_submit = time.monotonic()
        page.wait_for_timeout(300)
        art = page.locator('article[data-testid="tweet"]').first
        liked, like_ms, like_error = like_within_5s(page, art, t_submit)
        page.screenshot(path=f"{CTL}/shot-engage-comment.png")
        out({"ok": True, "commented": ARG, "liked": liked, "like_ms": like_ms,
             "like_error": like_error, "like_within_5s": liked and like_ms <= 5000})

    elif CMD == "notifications":
        page.goto("https://x.com/notifications/mentions", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(12000)
        items = page.evaluate("""(own) => {
          const res = [];
          document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
            const userLink = a.querySelector('[data-testid="User-Name"] a');
            const handle = userLink ? userLink.getAttribute('href').slice(1) : '';
            if (!handle || handle.toLowerCase() === own.toLowerCase()) return;
            const links = [...a.querySelectorAll('a[href*="/status/"]')].map(x => x.getAttribute('href'));
            const mine = links.filter(h => h.toLowerCase().startsWith('/' + handle.toLowerCase() + '/status/'));
            const tt = a.querySelector('[data-testid="tweetText"]');
            res.push({
              handle: handle,
              url: mine.length ? 'https://x.com' + mine[0] : '',
              text: tt ? tt.innerText.slice(0, 280) : '',
              liked: !!a.querySelector('[data-testid="unlike"]')
            });
          });
          return res;
        }""", OWN)
        out({"items": [i for i in items if i["url"]][:12]})

    elif CMD == "reply_like":
        page.goto(ARG, timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
        if not clear_overlay(page):
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(10000)
            if not clear_overlay(page):
                out({"ok": False, "error": "overlay blocks page"})
                raise SystemExit
        box = page.locator('[data-testid="tweetTextarea_0"]').first
        safe_click(page, box)
        page.wait_for_timeout(2000)
        page.keyboard.insert_text(TEXT)
        page.wait_for_timeout(1000)
        got = box.inner_text()
        if TEXT not in got:
            out({"ok": False, "error": "composer mismatch", "got": got[:80]})
            raise SystemExit
        # Inline reply composer uses tweetButtonInline; the main composer uses tweetButton.
        btn = page.locator('[data-testid="tweetButtonInline"]').first
        if btn.count() == 0:
            btn = page.locator('[data-testid="tweetButton"]').first
        safe_click(page, btn)
        # Hard rule (user, 2026-11-12): the like must land within 5 seconds
        # of the reply being submitted.
        t_submit = time.monotonic()
        page.wait_for_timeout(300)
        art = page.locator('article[data-testid="tweet"]').first
        liked, like_ms, like_error = like_within_5s(page, art, t_submit)
        page.screenshot(path=f"{CTL}/shot-engage-reply.png")
        out({"ok": True, "replied": ARG, "liked": liked, "like_ms": like_ms,
             "like_error": like_error, "like_within_5s": liked and like_ms <= 5000})

    elif CMD == "firstfloor":
        page.goto(ARG, timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
        if not clear_overlay(page):
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(10000)
            if not clear_overlay(page):
                out({"ok": False, "error": "overlay blocks page"})
                raise SystemExit
        # Idempotency: never post the same first floor twice. If a reply
        # by the own account carrying the same text is already visible on
        # this post (the first article is the post itself, so skip it),
        # report success without sending.
        frag = TEXT[:20]
        already = page.evaluate("""(args) => {
          const own = args.own.toLowerCase();
          const frag = args.frag;
          let found = false;
          const arts = document.querySelectorAll('article[data-testid="tweet"]');
          arts.forEach((a, i) => {
            if (i === 0) return;
            const userLink = a.querySelector('[data-testid="User-Name"] a');
            const handle = userLink ? userLink.getAttribute('href').slice(1) : '';
            if (handle.toLowerCase() !== own) return;
            const tt = a.querySelector('[data-testid="tweetText"]');
            const tx = tt ? tt.innerText : (a.innerText || '');
            if (tx.includes(frag)) found = true;
          });
          return found;
        }""", {"own": OWN, "frag": frag})
        if already:
            out({"ok": True, "firstfloor": ARG, "already": True})
            raise SystemExit
        box = page.locator('[data-testid="tweetTextarea_0"]').first
        safe_click(page, box)
        page.wait_for_timeout(2000)
        page.keyboard.insert_text(TEXT)
        page.wait_for_timeout(1000)
        got = box.inner_text()
        if TEXT not in got:
            out({"ok": False, "error": "composer mismatch", "got": got[:80]})
            raise SystemExit
        # Dry run (FIRSTFLOOR_DRY_RUN=1): verify everything up to the
        # send click without publishing. Used to test the flow.
        if os.environ.get("FIRSTFLOOR_DRY_RUN") == "1":
            out({"ok": True, "firstfloor": ARG, "dry_run": True})
            raise SystemExit
        btn = page.locator('[data-testid="tweetButtonInline"]').first
        if btn.count() == 0:
            btn = page.locator('[data-testid="tweetButton"]').first
        safe_click(page, btn)
        page.wait_for_timeout(8000)
        page.screenshot(path=f"{CTL}/shot-engage-firstfloor.png")
        out({"ok": True, "firstfloor": ARG, "already": False})

    elif CMD == "followers":
        page.goto(f"https://x.com/{OWN}/followers", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(12000)
        cells = page.evaluate("""() => {
          const res = [];
          document.querySelectorAll('[data-testid="UserCell"]').forEach(c => {
            const links = [...c.querySelectorAll('a[href^="/"]')].map(x => x.getAttribute('href')).filter(h => h && h.split('/').length === 2);
            const handle = links.length ? links[0].slice(1) : '';
            if (!handle) return;
            const verified = !!c.querySelector('svg[data-testid="icon-verified"], [aria-label="Verified account"]');
            const fb = c.querySelector('[data-testid$="-follow"]');
            const ub = c.querySelector('[data-testid$="-unfollow"]');
            res.push({handle: handle, verified: verified, following: !!ub, can_follow: !!fb});
          });
          return res;
        }""")
        head = page.evaluate("() => document.body ? document.body.innerText.slice(0, 400) : ''")
        out({"followers": cells[:30], "head": head.replace("\n", " ")[:200]})

    elif CMD == "follow":
        page.goto(f"https://x.com/{ARG}", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
        if page.locator('[data-testid$="-unfollow"]').count() > 0:
            out({"ok": True, "already": True})
        else:
            page.locator('[data-testid$="-follow"]').first.click(timeout=15000)
            page.wait_for_timeout(4000)
            ok = page.locator('[data-testid$="-unfollow"]').count() > 0
            out({"ok": ok, "followed": ARG})

    elif CMD == "stats":
        page.goto(f"https://x.com/{OWN}", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(12000)
        data = page.evaluate("""(own) => {
          const res = {followers: null, following: null, posts: []};
          document.querySelectorAll('a[href$="/followers"], a[href$="/following"], a[href$="/verified_followers"]').forEach(a => {
            const t = a.innerText.replace(/,/g, '');
            const m = t.match(/([\\d.]+)([KM]?)\\s*(Followers|Following)/i);
            if (m) {
              let v = parseFloat(m[1]);
              if (m[2] === 'K') v *= 1000;
              if (m[2] === 'M') v *= 1000000;
              if (/follower/i.test(m[3])) res.followers = Math.round(v); else res.following = Math.round(v);
            }
          });
          document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
            const userLink = a.querySelector('[data-testid="User-Name"] a');
            const handle = userLink ? userLink.getAttribute('href').slice(1) : '';
            if (handle.toLowerCase() !== own.toLowerCase()) return;
            const time = a.querySelector('time');
            const an = a.querySelector('a[href$="/analytics"]');
            let views = null;
            if (an) {
              const t = an.innerText.replace(/,/g, '');
              const m = t.match(/([\\d.]+)([KM]?)/);
              if (m) { views = parseFloat(m[1]); if (m[2] === 'K') views *= 1000; if (m[2] === 'M') views *= 1000000; views = Math.round(views); }
            }
            const links = [...a.querySelectorAll('a[href*="/status/"]')].map(x => x.getAttribute('href'));
            res.posts.push({dt: time ? time.getAttribute('datetime') : '', views: views, url: links.length ? 'https://x.com' + links[0] : ''});
          });
          return res;
        }""", OWN)
        out(data)

    else:
        out({"ok": False, "error": f"unknown subcommand {CMD}"})
except Exception as e:
    # Never die silently: the orchestrator only sees a RESULT line.
    out({"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"})
finally:
    ctx.close()
print("ENGAGE DONE", flush=True)
