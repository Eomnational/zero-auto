"""Read-only check: open a tweet in the logged-in Camoufox profile and report
whether @xunana1017's comment text appears among the replies, plus whether the
original post shows as liked. No clicks, no typing, no writes to X.
Usage: check_comment.py <tweet_url> <needle_text>
Prints one JSON line.
"""
import json, os, sys
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
PROFILE = os.environ.get("CAMOUFOX_PROFILE", f"{HOME}/workspace/camoufox/profile-x")
PROXY = {"server": os.environ.get("RELAY_URL", "http://127.0.0.1:18081")}
GEOIP = os.environ["GEOIP_IP"]
URL = sys.argv[1]
NEEDLE = sys.argv[2] if len(sys.argv) > 2 else ""
OWN = "xunana1017"

def out(obj):
    print("RESULT " + json.dumps(obj, ensure_ascii=False), flush=True)

ctx = Camoufox(headless=True, persistent_context=True, user_data_dir=PROFILE,
               proxy=PROXY, geoip=GEOIP, os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    page = ctx.new_page()
    page.goto(URL, timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    # Scroll to load more replies.
    for _ in range(4):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
    data = page.evaluate("""(p) => {
      const own = p.own, needle = p.needle;
      const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
      const replies = arts.map(a => {
        const userLink = a.querySelector('[data-testid="User-Name"] a');
        const handle = userLink ? userLink.getAttribute('href').slice(1) : '';
        const tt = a.querySelector('[data-testid="tweetText"]');
        return {handle: handle, text: tt ? tt.innerText.slice(0, 200) : ''};
      });
      const first = arts[0];
      const liked = first ? !!first.querySelector('[data-testid="unlike"]') : null;
      const mine = replies.filter(r => r.handle.toLowerCase() === own.toLowerCase());
      return {
        total_articles: arts.length,
        original_liked: liked,
        my_replies: mine,
        needle_found: needle ? replies.some(r => r.text.includes(needle)) : false,
        reply_handles: replies.map(r => r.handle)
      };
    }""", {"own": OWN, "needle": NEEDLE})
    out({"ok": True, **data})
except Exception as e:
    out({"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"})
finally:
    ctx.close()
print("CHECK DONE", flush=True)
