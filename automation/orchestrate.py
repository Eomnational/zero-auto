"""State machine for the X ops automation on @xunana1017.

One action per invocation, serialized. Cooldowns live in the state:
  post               next run in 15 to 30 minutes
  comment            next run in 0 to 10 minutes, traffic-weighted by
                     segment (evening peak 0-5, lunch peak 0-7, late
                     night 5-15); segment edges jitter +-15 min daily
  notification reply next run in 5 to 10 minutes
  follow back        next run in 3 to 5 minutes (random)
Active window 07:00-02:00 CST with a lunch break 11:00-12:00. The
operational day runs 07:00 -> 02:00 next day, so 00:00-02:00 counts
toward the day that started at 07:00.
Priority: post > comment > reply > follow back. An action that is cooling
down or has hit its daily cap is skipped and the next due one runs in that
same order; the run never idles waiting for the higher one. Replies have
no daily cap (user rule 2026-11-12): every queued notification gets a
reply; only the active window stops replies.
Modes:
  peek               decide what is due, fetching candidates when needed
  do post            --text T [--firstfloor F]
  do comment         --url U --text T   (also likes the post)
  do reply           --url U --text T   (also likes their tweet)
  do followback      --handle H
Every outcome prints one JSON line. A lock file prevents overlapping runs.
"""
import json, os, random, subprocess, sys, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BASE = os.path.expanduser("~/workspace/x-ops")
CAM = os.path.expanduser("~/workspace/camoufox")
STATE_F = os.path.join(BASE, "state.json")
LOCK_F = os.path.join(BASE, "lock")
VENV_PY = os.path.join(CAM, "venv/bin/python")
CST = ZoneInfo("Asia/Shanghai")
# Daily caps. reply is None = no cap: the user rule (2026-11-12) is that
# every notification gets a reply and only the active window stops replies.
CAPS = {"post": 20, "comment": 500, "reply": None, "followback": 15}
EXPECTED_IP = "<PROXY_IP>"

def under_cap(c, kind):
    cap = CAPS.get(kind)
    return cap is None or c.get(kind, 0) < cap

def now_ts():
    return time.time()

def today_cst():
    return datetime.now(CST).strftime("%Y-%m-%d")

def ops_day():
    # Operational day runs 07:00 -> 02:00 next day. The 00:00-02:00 stretch
    # belongs to the day that started at 07:00 the previous morning.
    return (datetime.now(CST) - timedelta(hours=7)).strftime("%Y-%m-%d")

def load_state():
    if os.path.exists(STATE_F):
        s = json.load(open(STATE_F))
    else:
        s = {}
    if s.get("date") != ops_day():
        s.update({"date": ops_day(),
                  "counts": {"post": 0, "comment": 0, "reply": 0, "like": 0, "followback": 0},
                  "notify_queue": [], "followback_queue": [], "log": []})
        s.setdefault("handled_notifications", [])
        s.setdefault("commented", [])
    s.setdefault("counts", {"post": 0, "comment": 0, "reply": 0, "like": 0, "followback": 0})
    for k in ("next_post_at", "next_comment_at", "next_reply_at", "next_followback_at",
              "next_notify_check_at", "next_stats_at", "quiet_until"):
        s.setdefault(k, 0)
    s.setdefault("notify_queue", [])
    s.setdefault("followback_queue", [])
    s.setdefault("handled_notifications", [])
    s.setdefault("commented", [])
    s.setdefault("followers", None)
    s.setdefault("today_views", 0)
    s.setdefault("exit_ip", EXPECTED_IP)
    s.setdefault("log", [])
    return s

def save_state(s):
    # Merge with whatever is on disk first: a run holds state in memory for
    # minutes while the browser works, and a blind write-back would clobber
    # counts or lists updated meanwhile (seen 2026-11-12: a follow-back run
    # overwrote a manual comment-count fix). Counters only ever grow, so
    # taking the max is safe; lists merge by union.
    try:
        disk = json.load(open(STATE_F))
        # Counters and the in-memory log belong to the operational day:
        # on a day rollover the on-disk values are yesterday's, and
        # max-merging them back resurrects yesterday's counts (seen
        # 2026-11-13: post 20/20 and followback 15/15 carried over, which
        # capped the new day before it started). Only merge them when the
        # disk state is from the same operational day.
        same_day = disk.get("date") == s.get("date")
        for k in ("commented", "handled_notifications"):
            merged = list(dict.fromkeys(s.get(k, []) + disk.get(k, [])))
            s[k] = merged
        if same_day:
            for k, v in disk.get("counts", {}).items():
                s.setdefault("counts", {})[k] = max(s["counts"].get(k, 0), v)
            if disk.get("log"):
                seen = {(e.get("type"), e.get("ts"), e.get("text", "")[:40]) for e in s.get("log", [])}
                s["log"] = s.get("log", []) + [e for e in disk["log"]
                                              if (e.get("type"), e.get("ts"), e.get("text", "")[:40]) not in seen]
    except Exception:
        pass
    os.makedirs(BASE, exist_ok=True)
    tmp = STATE_F + ".tmp"
    json.dump(s, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_F)

def _day_hours():
    # Hours on a 07:00-anchored clock: 07:00 -> 7.0, 00:00 -> 24.0,
    # 02:00 -> 26.0. Keeps the after-midnight stretch on the same scale.
    now = datetime.now(CST)
    h = now.hour + now.minute / 60.0
    return h + 24.0 if h < 7.0 else h

def in_window():
    # Active 07:00-02:00 CST, lunch break 11:00-12:00.
    h = _day_hours()
    if 11.0 <= h < 12.0:
        return False
    return 7.0 <= h < 26.0

# Traffic-weighted comment segments. BOUNDARIES are hours on the
# 07:00-anchored clock; SEG_RANGES holds the comment cooldown range
# (lo_s, hi_s) for each interval between consecutive boundaries, with
# None for the lunch break. Peak hours run denser, late night sparser.
# Boundary jitter (+-15 min, drawn per ops day from a seeded RNG so it
# is stable within the day) keeps the pattern from looking like a
# fixed grid.
BOUNDARIES = [7.0, 9.0, 11.0, 12.0, 14.0, 18.0, 19.0, 23.0, 26.0]
SEG_RANGES = [(0, 600), (0, 600), None, (0, 420), (0, 600), (120, 600),
              (0, 300), (300, 900)]

def segment_bounds(date_str):
    rng = random.Random("seg-" + date_str)
    return [b + (rng.uniform(-0.25, 0.25) if 0 < i < len(BOUNDARIES) - 1 else 0)
            for i, b in enumerate(BOUNDARIES)]

def comment_cooldown():
    h = _day_hours()
    bounds = segment_bounds(ops_day())
    for i, r in enumerate(SEG_RANGES):
        if r is not None and bounds[i] <= h < bounds[i + 1]:
            return random.uniform(*r)
    return random.uniform(0, 600)

# User-approved exit allowlist (2026-11-17): <PROXY_IP> is the static
# proxy she supplied that morning (Wave Broadband, Palo Alto CA). ip-api
# flags it proxy=true, but proxycheck says proxy=no, type Business, and
# she chose to use it as normal. Only this exact IP is exempt; every
# other proxy/hosting-flagged exit is still blocked.
ALLOWED_EXITS = {"<PROXY_IP>"}

def exit_is_dirty(ip):
    # IP-purity predicate: ip-api flags the exit as a proxy/VPN or as a
    # hosting/datacenter address. Either flag means the exit is dirty and
    # no X action may run on it (user rule) — unless the IP is allowlisted.
    if ip and ip.get("query") in ALLOWED_EXITS:
        return False
    return bool(ip and (ip.get("proxy") or ip.get("hosting")))

def check_relay_ip():
    try:
        r = subprocess.run(["curl", "-s", "-x", "http://127.0.0.1:18081", "--max-time", "20",
                            "http://ip-api.com/json/?fields=query,country,proxy,hosting"],
                           capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout)
        return d
    except Exception:
        return None

def run_browser(script, args, extra_env=None):
    env = dict(os.environ)
    env["GEOIP_IP"] = run_browser.exit_ip
    env["TMPDIR"] = os.path.join(CAM, "tmp")
    if extra_env:
        env.update(extra_env)
    r = subprocess.run([VENV_PY, os.path.join(CAM, script)] + args,
                       capture_output=True, text=True, timeout=420, env=env)
    for line in (r.stdout or "").splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):])
    return {"ok": False, "error": "no result", "raw": (r.stdout or "")[-400:], "stderr_tail": (r.stderr or "")[-300:]}

def log_action(s, rec):
    rec["ts"] = datetime.now(CST).strftime("%H:%M:%S")
    s["log"].append(rec)
    with open(os.path.join(BASE, f"log-{s['date']}.jsonl"), "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def publish_first_floor(s, post_url, post_text, ff_text):
    """Publish the first-floor follow-up (1楼承接) as a self-reply to the
    post just published. Returns a small result dict; on failure the
    follow-up is recorded pending (type first_floor_pending) for the main
    agent to top up, like a missed like. Never raises."""
    if not post_url:
        # x_ops.py could not read the URL back: resolve it from the
        # profile, accepting the latest post only when its first line
        # matches the post just published, so a stale profile can never
        # send the first floor to the wrong post.
        try:
            env = dict(os.environ)
            env["GEOIP_IP"] = run_browser.exit_ip
            env["TMPDIR"] = os.path.join(CAM, "tmp")
            r = subprocess.run([VENV_PY, os.path.join(CAM, "read_latest_post.py"), "xunana1017"],
                               capture_output=True, text=True, timeout=240, env=env)
            out = r.stdout or ""
            first_line = (post_text.split("\n")[0] if post_text else "")[:30]
            if "POST_URL: " in out and first_line and first_line in out:
                post_url = out.split("POST_URL: ", 1)[1].strip().splitlines()[0].strip()
        except Exception:
            post_url = ""
    if not post_url:
        log_action(s, {"type": "first_floor_pending", "url": "", "text": ff_text, "reason": "no post url"})
        return {"ok": False, "error": "no post url", "pending": True}
    # One attempt plus one retry (same discipline as the like top-up:
    # at most one retry per round). firstfloor is idempotent, so a retry
    # after an ambiguous failure cannot double-post.
    last = None
    for _ in (1, 2):
        last = run_browser("x_engage.py", ["firstfloor", post_url], {"TEXT": ff_text})
        if last.get("ok"):
            log_action(s, {"type": "first_floor", "url": post_url, "text": ff_text, "already": bool(last.get("already"))})
            return {"ok": True, "url": post_url, "already": bool(last.get("already"))}
    log_action(s, {"type": "first_floor_pending", "url": post_url, "text": ff_text, "reason": (last or {}).get("error", "unknown")})
    return {"ok": False, "url": post_url, "error": (last or {}).get("error", "unknown"), "pending": True}

def acquire_lock():
    try:
        fd = os.open(LOCK_F, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(int(now_ts())).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            age = now_ts() - int(open(LOCK_F).read().strip() or 0)
        except Exception:
            age = 9999
        if age > 900:
            os.remove(LOCK_F)
            return acquire_lock()
        return False

def release_lock():
    try:
        os.remove(LOCK_F)
    except Exception:
        pass

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "peek"
    args = {}
    it = iter(sys.argv[2:])
    for a in it:
        if a.startswith("--"):
            args[a[2:]] = next(it, "")
    if not acquire_lock():
        print(json.dumps({"busy": True}))
        return
    try:
        s = load_state()
        ip = check_relay_ip()
        if not ip or not ip.get("query"):
            print(json.dumps({"blocked": "relay_down", "hint": "restart the chain relay, see the x_account_cloud_login skill"}))
            return
        if ip.get("country") != "United States":
            print(json.dumps({"blocked": "ip_region_changed", "ip": ip}))
            return
        # IP-purity guard (hardened 2026-11-13: post #6 went out through a
        # dirty exit at 21:07 because only the country was checked and the
        # worker skipped the purity check). This sits above both peek and
        # do, so a dirty exit can never reach an action again, whatever
        # the worker does. Workers do not restart the relay for this
        # reason: a restart re-rolls nothing, the session exit stays dirty
        # until kookeey rotates it or a new config is supplied.
        if exit_is_dirty(ip):
            print(json.dumps({"blocked": "dirty_exit", "ip": ip}))
            return
        run_browser.exit_ip = ip["query"]
        if ip["query"] != s.get("exit_ip"):
            s["exit_ip"] = ip["query"]
            s["ip_rotated"] = ip["query"]
        t = now_ts()

        if mode == "peek":
            if not in_window():
                print(json.dumps({"due": "none", "reason": "outside active window 07:00-02:00 CST (break 11:00-12:00)"}))
                return
            if t < s["quiet_until"]:
                print(json.dumps({"due": "none", "reason": "quiet period", "until": s["quiet_until"]}))
                return
            c = s["counts"]
            # Priority (user rule, 2026-11-12): post > comment > reply >
            # follow back. A cooling-down or capped action is skipped and
            # the next due one runs in the same order.
            if t >= s["next_post_at"] and c["post"] < CAPS["post"]:
                print(json.dumps({"due": "post"}))
                return
            if t >= s["next_comment_at"] and c["comment"] < CAPS["comment"]:
                res = run_browser("x_engage.py", ["foryou"])
                cands = [x for x in res.get("candidates", []) if x.get("url")]
                print(json.dumps({"due": "comment", "candidates": cands[:6]}))
                return
            if s["notify_queue"] and t >= s["next_reply_at"] and under_cap(c, "reply"):
                print(json.dumps({"due": "reply", "item": s["notify_queue"][0], "queue": len(s["notify_queue"])}))
                return
            if t >= s["next_notify_check_at"]:
                res = run_browser("x_engage.py", ["notifications"])
                seen = set(s["handled_notifications"]) | {q["url"] for q in s["notify_queue"]}
                new = [i for i in res.get("items", []) if i.get("url") and i["url"] not in seen]
                s["notify_queue"].extend(new)
                s["next_notify_check_at"] = t + random.uniform(600, 1500)
                save_state(s)
                if s["notify_queue"] and under_cap(c, "reply"):
                    if t >= s["next_reply_at"]:
                        print(json.dumps({"due": "reply", "item": s["notify_queue"][0], "queue": len(s["notify_queue"]), "fresh": len(new)}))
                    else:
                        print(json.dumps({"due": "none", "reason": "replies queued, cooling down", "queue": len(s["notify_queue"])}))
                    return
                print(json.dumps({"due": "none", "reason": "notifications checked, nothing new", "fresh": len(new)}))
                return
            if t >= s["next_followback_at"] and c["followback"] < CAPS["followback"]:
                if s.get("followers") is not None and s["followers"] >= 5000:
                    print(json.dumps({"due": "none", "reason": "followers at or above 5000, follow back disabled"}))
                    return
                if not s["followback_queue"]:
                    res = run_browser("x_engage.py", ["followers"])
                    s["followback_queue"] = [f["handle"] for f in res.get("followers", [])
                                             if f.get("verified") and f.get("can_follow")]
                    save_state(s)
                if s["followback_queue"]:
                    print(json.dumps({"due": "followback", "handle": s["followback_queue"][0], "queue": len(s["followback_queue"])}))
                    return
            if t >= s["next_stats_at"]:
                res = run_browser("x_engage.py", ["stats"])
                if res.get("followers") is not None:
                    s["followers"] = res["followers"]
                if res.get("following") is not None:
                    s["following"] = res["following"]
                day = s["date"]
                views = 0
                for p in res.get("posts", []):
                    try:
                        # Attribute the post to its operational day (07:00-anchored).
                        d = (datetime.fromisoformat(p["dt"].replace("Z", "+00:00")).astimezone(CST)
                             - timedelta(hours=7)).strftime("%Y-%m-%d")
                    except Exception:
                        d = ""
                    if d == day and p.get("views"):
                        views += p["views"]
                s["today_views"] = views
                s["next_stats_at"] = t + 1800
                save_state(s)
                print(json.dumps({"due": "none", "reason": "stats refreshed", "followers": s["followers"], "today_views": views}))
                return
            print(json.dumps({"due": "none", "reason": "nothing due",
                              "next_post_in_min": round((s["next_post_at"] - t) / 60),
                              "next_comment_in_min": round((s["next_comment_at"] - t) / 60)}))
            return

        if mode == "do":
            action = args.get("action", "")
            text = args.get("text", "")
            url = args.get("url", "")
            handle = args.get("handle", "")
            c = s["counts"]
            # Random pre-action wait (user rule, 2026-11-12): the 2-minute
            # heartbeat is a fixed grid, so wait a random 0-120s before
            # executing, while holding the lock, so the action time itself
            # lands off the grid and no other run can start the same action.
            if action in ("post", "comment", "reply", "followback"):
                wait_s = random.uniform(0, 120)
                time.sleep(wait_s)
            else:
                wait_s = 0
            if action == "post":
                env = dict(os.environ)
                env["GEOIP_IP"] = run_browser.exit_ip
                env["TMPDIR"] = os.path.join(CAM, "tmp")
                env["TEXT"] = text
                r = subprocess.run([VENV_PY, os.path.expanduser("~/workspace/custom-skills/x_manual_ops/scripts/x_ops.py"), "post"],
                                   capture_output=True, text=True, timeout=420, env=env)
                res = {"raw": (r.stdout or "")[-400:], "stderr_tail": (r.stderr or "")[-300:]}
                if "POSTED" not in res.get("raw", ""):
                    print(json.dumps({"failed": "post", "res": res}))
                    return
                # New post URL, when x_ops.py captured it (it prints
                # "POSTED <url>"); used for the first-floor follow-up
                # and for the log so the Space link is no longer blank.
                post_url = ""
                for line in (r.stdout or "").splitlines():
                    if line.startswith("POSTED "):
                        post_url = line[len("POSTED "):].strip()
                        break
                # First-floor follow-up (user rule, 2026-11-16): part of
                # the post action, not a second action. A failed first
                # floor never fails the post — it is recorded pending,
                # like a missed like awaiting top-up.
                ff_text = args.get("firstfloor", "")
                ff_result = None
                if ff_text:
                    ff_result = publish_first_floor(s, post_url, text, ff_text)
                c["post"] += 1
                s["next_post_at"] = t + random.uniform(900, 1800)
                s["quiet_until"] = t + random.uniform(60, 300)
                s["next_stats_at"] = min(s["next_stats_at"], t + 180)
                log_action(s, {"type": "post", "text": text, "url": post_url, "firstfloor": ff_result})
                save_state(s)
                print(json.dumps({"done": "post", "url": post_url, "firstfloor": ff_result, "waited_s": round(wait_s), "next_post_in_min": round((s["next_post_at"] - t) / 60)}))
                return
            if action == "comment":
                res = run_browser("x_engage.py", ["comment", url], {"TEXT": text})
                if not res.get("ok"):
                    print(json.dumps({"failed": "comment", "res": res}))
                    return
                c["comment"] += 1
                if res.get("liked"):
                    c["like"] += 1
                s["commented"].append(url)
                s["next_comment_at"] = t + comment_cooldown()
                s["next_notify_check_at"] = t
                s["quiet_until"] = t + random.uniform(60, 300)
                log_action(s, {"type": "comment", "url": url, "text": text, "liked": res.get("liked"), "like_ms": res.get("like_ms"), "like_error": res.get("like_error")})
                save_state(s)
                print(json.dumps({"done": "comment", "waited_s": round(wait_s), "liked": res.get("liked"), "like_ms": res.get("like_ms")}))
                return
            if action == "reply":
                res = run_browser("x_engage.py", ["reply_like", url], {"TEXT": text})
                if not res.get("ok"):
                    print(json.dumps({"failed": "reply", "res": res}))
                    return
                c["reply"] += 1
                if res.get("liked"):
                    c["like"] += 1
                s["handled_notifications"].append(url)
                s["handled_notifications"] = s["handled_notifications"][-300:]
                s["notify_queue"] = [q for q in s["notify_queue"] if q["url"] != url]
                s["next_reply_at"] = t + random.uniform(0, 300)
                s["quiet_until"] = t + random.uniform(60, 240)
                log_action(s, {"type": "reply", "url": url, "text": text, "liked": res.get("liked"), "like_ms": res.get("like_ms"), "like_error": res.get("like_error")})
                save_state(s)
                print(json.dumps({"done": "reply", "waited_s": round(wait_s), "liked": res.get("liked"), "like_ms": res.get("like_ms"), "queue_left": len(s["notify_queue"])}))
                return
            if action == "followback":
                res = run_browser("x_engage.py", ["follow", handle])
                if not res.get("ok"):
                    print(json.dumps({"failed": "followback", "res": res}))
                    return
                c["followback"] += 1
                s["followback_queue"] = [h for h in s["followback_queue"] if h != handle]
                s["next_followback_at"] = t + random.uniform(180, 300)
                s["quiet_until"] = t + random.uniform(60, 240)
                log_action(s, {"type": "followback", "handle": handle})
                save_state(s)
                print(json.dumps({"done": "followback", "waited_s": round(wait_s), "handle": handle, "queue_left": len(s["followback_queue"])}))
                return
            print(json.dumps({"failed": "unknown action", "action": action}))
            return
        print(json.dumps({"failed": "unknown mode", "mode": mode}))
    finally:
        release_lock()

run_browser.exit_ip = EXPECTED_IP
if __name__ == "__main__":
    main()
