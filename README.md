# zero-auto

X operations toolkit: four Muse skills plus the automation scripts that run them.

## Skills

- **x_account_cloud_login** — Log an X account into a cloud Camoufox profile behind a residential proxy: Google sign-in in Chromium, then transplant the session.
- **x_manual_ops** — Do one X action at a time by hand: post, reply, like, follow, DM, delete one post, batch likes.
- **x_ops_automation** — Run serialized, randomly cooled-down X operations (post, comment, reply, like, Blue-V follow-back) from a state machine with IP purity guards and dual bookkeeping.
- **x_viral_ops** — Viral post method and engagement voice: fact-first drafting, hit breakdown, de-AI pass, and the content red lines.

## Automation

- `automation/orchestrate.py` — the deterministic state machine: timing, queues, counters, cooldowns, guards.
- `automation/x_engage.py` — browser primitives for the For You feed, comments, notifications, replies, follows, stats, first-floor follow-ups.
- `automation/chain_relay.py` — local HTTP relay that chains the sandbox egress proxy to the upstream residential proxy.
- `automation/read_latest_post.py`, `read_recent_posts.py`, `verify_login.py`, `check_post_replies.py`, `check_comment.py` — read-only helpers for verification.
- `automation/voice-profile.md` — the account voice profile used when drafting manual posts.

## Setup

Proxy details are placeholders (`<PROXY_IP>`, `<PROXY_PORT>`, `<PROXY_USER>`): fill in your own proxy and pass its password only via the `KK_AUTH_B64` environment variable. Never commit credentials.
