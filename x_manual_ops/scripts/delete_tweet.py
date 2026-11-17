"""One-off: delete one of our own tweets by status URL.
Opens the tweet, uses its caret menu -> Delete -> confirm, then verifies it's gone."""
import json, os, sys
from camoufox.sync_api import Camoufox

HOME = os.path.expanduser("~")
URL = sys.argv[1]
TEXT_FRAG = sys.argv[2] if len(sys.argv) > 2 else ""
ctx = Camoufox(headless=True, persistent_context=True,
               user_data_dir=f"{HOME}/workspace/camoufox/profile-x",
               proxy={"server": "http://127.0.0.1:18081"},
               geoip=os.environ["GEOIP_IP"], os="windows", locale="en-US",
               i_know_what_im_doing=True).__enter__()
try:
    page = ctx.new_page()
    page.goto(URL, timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    # Find our tweet's article by text fragment, then its caret (more) button.
    art = None
    for a in page.locator('article[data-testid="tweet"]').all():
        try:
            if TEXT_FRAG and TEXT_FRAG in (a.inner_text() or ""):
                art = a
                break
        except Exception:
            pass
    if art is None:
        art = page.locator('article[data-testid="tweet"]').first
    caret = art.locator('[data-testid="caret"]').first
    caret.click(timeout=15000)
    page.wait_for_timeout(2500)
    # Menu item "Delete"
    menu = page.locator('[role="menuitem"]', has_text="Delete").first
    menu.click(timeout=15000)
    page.wait_for_timeout(2500)
    # Confirm dialog
    confirm = page.locator('[data-testid="confirmationSheetConfirm"]').first
    if confirm.count() == 0:
        confirm = page.locator('button:has-text("Delete")').last
    confirm.click(timeout=15000)
    page.wait_for_timeout(5000)
    # Verify: reload the status URL; a deleted tweet shows the missing-page notice.
    page.goto(URL, timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    body = page.locator("body").inner_text(timeout=5000)
    gone = ("doesn't exist" in body) or ("Hmm" in body) or (TEXT_FRAG not in body)
    print("DELETE_RESULT " + json.dumps({"deleted": gone, "url": URL}, ensure_ascii=False), flush=True)
    page.screenshot(path=f"{HOME}/workspace/camoufox/ctl/shot-delete.png")
finally:
    ctx.__exit__(None, None, None)
