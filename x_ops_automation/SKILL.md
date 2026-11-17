# X Ops Automation

## Split the work across four skills

- Use the skill x_account_cloud_login for the environment, the residential proxy relay and getting any account logged into its Camoufox profile.

- Use the skill x_manual_ops for one action at a time by hand from that profile: post, reply, like, follow and DM. The automation's post step calls its `x_ops.py` script.

- Use the skill x_viral_ops for every word that gets published, including post structure, comment voice, reply voice and the content red lines.

- Use this skill for the running system on top of them, which is scheduling, action ordering, cooldowns, guards, measurement and bookkeeping.

## Keep the architecture split into three layers

- Let a deterministic state machine script own all timing, queues, counters and cooldowns, because an agent improvising timing drifts into fixed intervals and double actions.

- Let the agent only decide what is due by reading the state machine output and only write the copy for the one action that is due, because copy is the part that needs judgment.

- Let small browser scripts only click and report structured results, because mixing page mechanics into the scheduler makes every X layout change break the whole system.

- Wake the system on a short heartbeat cron and let the state machine answer that nothing is due most of the time, because the heartbeat is transport and the randomized deadlines inside the state are the real schedule.

## Enforce serial actions and random cooldowns

- Run at most one action per wake and add a short random quiet period after it, because posting, commenting, replying and liking at the same moment is the clearest automation fingerprint there is.

- Before executing any due action, wait a random 0 to 120 seconds while holding the state-machine lock, because the 2-minute heartbeat is a fixed grid and the wait puts the action's own timestamp off the grid; the wait is reported as `waited_s` in the run result. The lock is held during the wait so no other wake can start the same action meanwhile. (User rule, 2026-11-12.)

- Draw the next post deadline as a random 15 to 30 minutes after each success, and draw the next comment deadline from the traffic-weighted segment the run lands in: 0 to 10 minutes in most segments, 0 to 5 in the 19:00–23:00 evening peak, 0 to 7 at the 12:00–14:00 lunch peak, 5 to 15 late at night (23:00–02:00). Segment edges jitter by up to 15 minutes each day so the pattern never sits on a fixed grid.

- Draw the next notification reply deadline as a random 0 to 5 minutes when more replies are queued, and draw the next follow back deadline as a random 3 to 5 minutes after each success.

- Recompute every deadline from the moment of success and never from a fixed grid, because grids are what the user banned when asking for random 1 to 30 minute refresh behaviour.

## Priority queue (hard constraint)

- This priority is a hard constraint set by the user, and it lives here in the automation skill — never in x_manual_ops, which has no queue, no cooldowns and no scheduling to constrain. The order is fixed: post first, comment second, reply to a notification third, follow back last.
- When one or more actions are cooling down or have hit their daily cap, run the next due one in the same order — never idle waiting for the higher one, and never reorder the queue to favour whatever happens to be ready.

- Scan notifications right after each comment, because the user flow is comment, then check who answered, then reply to them one by one. The scan feeds the reply queue; serving a queued reply still waits its turn behind posts and comments.

- Run follow backs after engagement actions, and refresh profile stats last and at most every half hour, because stats never block a conversation.

- Like as part of the parent action and never as a standalone task, liking the post right after commenting on it and liking the person tweet right after replying to it. The like must land within 5 seconds of the comment or reply being submitted; the attempt is timed (like_ms) and a miss is reported with its reason, never silently skipped.

- Top up a missed like after the round ends (补赞 — user rule, 2026-11-12): when the 5-second like fails after a comment or reply, the round is not finished until the like is topped up. Once the parent action has completed, top up the like in the same run: take the x-ops lock, reopen the original post with `like_many.py` (from x_manual_ops, handle fragment as the match), like it, verify it flips to unlike, then release the lock. A successful top-up is logged as a like (state like count +1, a `补赞` entry in the daily log, and a 点赞 record in the X运营空间 with liked=true). If the lock is held by another run, or the top-up itself fails, record the pending miss (URL + comment + reason) in the run result and the daily log — the main agent tops it up automatically afterwards. Never ask the user for approval to top up a like: top-ups are always automatic (user rule, 2026-11-12 ~19:15). Never silently drop a miss; a single miss is retried at most once per round. The top-up completes the parent action's like step; it is not a second action and does not change the one-action-per-run discipline or the priority queue.

- Publish the first-floor follow-up as part of the post action (1 楼承接 — user rule, 2026-11-16): when the worker drafts a first-floor follow-up with the post (links, handouts, or a follow-up detail readers will ask for), it passes the text to `do post` via `--firstfloor` and the state machine publishes it as a self-reply to the new post in the same run, holding the lock. The first floor is part of the post action, not a second action, and it does not change the one-action-per-run discipline or the priority queue. It is published only when the worker drafted one — a post with nothing to add gets no first floor. A failed first floor never fails the post: the state machine retries once in the same run (firstfloor is idempotent, so a retry cannot double-post) and records a still-failing one as `first_floor_pending` (post URL + text + reason) in the daily log, for the main agent to top up afterwards — the same discipline as a missed like. Never ask the user for approval to top up a first floor. The first-floor text follows the post's rules: Simplified Chinese, judged against the 法条 before publishing; no 25-character limit.

## Guard every run

- Check the relay and the live exit IP before any browser opens, follow the new exit when the sticky session rotates inside the same country, and stop and report when the exit leaves the expected country.

- Follow back only followers with a verified badge, and disable follow backs for good once the follower count reaches 5000.

- Keep an active window and daily caps on posts, comments and follow backs as risk rails, and change them only when the user asks. Current caps (set by the user 2026-11-12): posts 20, comments 500, follow-backs 15 per day. Replies have no daily cap (user rule 2026-11-12): every notification gets a reply, and only the active window stops replies. Active window 07:00–02:00 CST with a lunch break 11:00–12:00; the operational day runs 07:00 -> 02:00 next day, so 00:00–02:00 counts toward the day that started at 07:00.
- The heartbeat is 2 minutes (set by the user 2026-11-12, was 5 minutes). At 2 minutes the realistic output is roughly 250–350 comments a day even with the 500 cap, because runs collide on the single-browser lock and the quiet period blocks the next wake or two. Batching several comments per run is the remaining way to reach 500 — it changes the one-action-per-run discipline, so do not make it without the user's explicit say-so.

- Before any post, comment or notification reply is published, the worker judges the draft against the 法条 compliance check in x_viral_ops (X审判者法条， baseline 2026-11-11, full text at `~/workspace/ref-skills/x-judge/references/法条-公开版.md`). A draft judged 中危 or worse is rewritten once; if it still fails, the action is skipped, the skip is logged with the failed provision and one-line reason, and the run ends — the next run proceeds normally. Never publish a draft that failed the check.
- Record the 法条 verdict (合规 or 低危 — a published item is always one of the two) with every published comment and notification reply when syncing it into the X运营空间 (the `verdict` field on the addengagement action), so the user can see the AI 审判 result on each item. Skipped drafts are logged locally only, with the failed provision and reason.
- Automation comments and notification replies follow exactly the same hard content constraints as manual replies in x_manual_ops (user rule, 2026-11-12): at most 25 characters counting every character including punctuation, Simplified Chinese, reply to something specific in the target post, and sound like a person texting a friend. The worker writes the draft within these limits — see x_viral_ops "Comment and reply with the same voice" for the full wording — and `x_engage.py` enforces the two checkable gates before the browser opens, printing `REPLY_TOO_LONG` or `NOT_SIMPLIFIED_CHINESE` and exiting, exactly as `x_ops.py` does for manual replies. A refused draft published nothing and counts as no action: the worker trims or rewrites it and retries once in the same run.
- Known accepted risk (user decided 2026-11-12 ~16:39, after being told the conflict): the 法条's automation rules (§2.4: auto-like prohibited, auto-reply requires opt-in, AI reply bots need X written approval) and monetization rules (§3.4: content created or published by automated means does not count as qualified original content) conflict with this automation's own mechanism — automatic liking after comments/replies, automatic replies to notifications, and automated posting. She chose to keep the full automation running and accept that risk. The mechanism stays as-is; do not re-raise it unless the situation changes (a new X warning, limit or suspension). The content check above still judges every draft.
- Refresh the 法条 baseline periodically against its sources (github.com/xai-org/x-algorithm for algorithm parameters; help.x.com Authenticity, Original Content Rewards and Creator Monetization Standards pages for rules and monetization), and note the baseline date in any judgment made from it.

- Refuse to send when the composer text read back differs from the intended text, because a scrambled first character already shipped once and had to be deleted.

- In the inline reply composer on a tweet page, the post button is `tweetButtonInline`, not `tweetButton` (the main composer uses `tweetButton`). Waiting for `tweetButton` there times out every time, so the comment and reply flows must try `tweetButtonInline` first and fall back to `tweetButton`. Diagnosed and fixed 2026-11-12 after two consecutive comment timeouts.

- X intermittently covers tweet pages with a login-wall / bot-check interstitial ("Unlock more on X", "To make X great for everyone") that intercepts every click. The comment and reply flows must detect it, wait it out or dismiss it with Escape/close, reload once if it persists, and report a clean "overlay blocks page" error instead of dying without a result line. Hardened 2026-11-12 after three consecutive overlay-blocked comments.

## Measure IP purity with two sources

- Query ip-api for the proxy, hosting and mobile flags and query proxycheck for the risk score and connection type, because each source alone mislabels real addresses.

- Call an address clean only when it reads as residential with a risk score near zero and no proxy or hosting flag, and call it dirty when either source flags it as a VPN, a proxy or a datacenter range.

- Never run account work on a dirty address, and recheck after every restart, because sticky residential sessions rotate after about a day and the cloud computer egress drifts inside its range.

- `orchestrate.py` enforces the rule in code (hardened 2026-11-13, after post #6 went out through a dirty exit at 21:07 because only the country was checked): before peek or do runs, it blocks with `dirty_exit` when ip-api flags the exit as proxy or hosting, so a dirty exit can never reach an action whatever the worker does. Never restart the relay for a dirty exit — a restart re-rolls nothing, the session exit stays dirty until the provider rotates it or a new config is supplied.
- User-approved exception (2026-11-17): `ALLOWED_EXITS = {"<PROXY_IP>"}` in `orchestrate.py`. That static proxy (supplied by the user) is flagged proxy=true by ip-api but proxy=no, type Business by proxycheck, and she chose to use it as normal. The exemption is per-IP only — every other proxy/hosting-flagged exit is still blocked. Never add another IP to the allowlist without her explicit say-so.

## Keep the books in two places

- Append every successful action with its time, type, target and text to a local daily log file, because the local log survives even when the dashboard is unreachable. The post log entry carries the new post's status URL (captured by x_ops.py after publishing, falling back to a profile read) — use it as the Space post link instead of leaving it blank. A published first floor is logged as its own `first_floor` entry (post URL + text); a failed one is logged as `first_floor_pending` for top-up.

- Mirror posts, engagements, follow backs and metrics into the X运营空间 through its published actions addpost, addengagement, addfollowback, setfollowbackstatus, updatemetrics and updatepoststats, and read the live action list before assuming a name still exists.

- Fill the dashboard only with measured numbers and leave a metric empty when it was not measured, because an invented view count destroys trust in the whole panel.

- Treat the daily impressions progress bar as a simple sum of the view counts on that day posts against the target the user set, and say plainly which posts were counted.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [X](https://x.com/) for the For You feed, the mentions page, the followers page and the own profile stats that feed the state machine.

- [proxycheck](https://proxycheck.io/) for the risk score and connection type half of the IP purity verdict.

- [ip-api](https://ip-api.com/) for the flag half of the IP purity verdict and the live exit check through the relay.
