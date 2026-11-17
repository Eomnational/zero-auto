# X Manual Ops

## What this skill owns

- Do one X action at a time by hand from a logged-in Camoufox profile: post, reply, like, follow, send a DM. Delete one of the account's own posts, and like several tweets in one browser session, are here too.
- Leave the environment, the proxy relay and the login itself to the skill x_account_cloud_login, because this skill assumes a profile that is already logged in.
- Draft a manual post with the creator method and the account voice profile before posting it (see Post below); the full method wording, the content red lines and the 法条 gate still live in the skill x_viral_ops.
- Leave scheduled and repeated operation to the skill x_ops_automation, because this skill runs one action when a human or a single task asks for it, never on a timer.

## Run one action

- Run `~/workspace/custom-skills/x_manual_ops/scripts/x_ops.py` with one action name, and pass the inputs as environment variables, never as command-line arguments, because the text can hold anything.
- Run it with the Camoufox venv python and `TMPDIR=~/workspace/camoufox/tmp`, because /tmp is a 512M tmpfs and the browser spills there.
- Set `GEOIP_IP` to the live exit IP first, because the script requires it and a stale IP logs the session in from the wrong place.

| Action | Command | Env in | What it prints |
| --- | --- | --- | --- |
| Post | `x_ops.py post` | `TEXT` | `POSTED` |
| Reply | `x_ops.py reply` | `TARGET_HANDLE`, `TEXT` | `REPLIED` |
| Like | `x_ops.py like` | `TARGET_HANDLE` | `LIKED` or `ALREADY LIKED` |
| Follow | `x_ops.py follow` | `TARGET_HANDLE` | `FOLLOWED` or `ALREADY FOLLOWING` |
| DM | `x_ops.py dm` | `TARGET_HANDLE`, `TEXT`, `CHAT_PIN` when asked | `DM SENT` |

- Shared env: `CAMOUFOX_PROFILE` (default `~/workspace/camoufox/profile-x`), `RELAY_URL` (default `http://127.0.0.1:18081`), `CTL_DIR` (screenshots, default `~/workspace/camoufox/ctl`).
- Run only one browser process per profile at a time, because a leftover process locks the profile and blocks the next launch.
- Kill helper scripts by exact process ID, and never put the script name in a `pkill -f` pattern inside the same shell command, because the pattern also matches the shell running the command and kills it.

## Post

- Draft the post before posting, with the creator method and the account voice profile (user rule, 2026-11-17 ~19:28 — the all-platform-creator skill and voice profile are merged into this operation):
  - Read the voice profile at `~/workspace/x-ops/voice-profile.md` first and draft in that voice: short lines separated by blank lines, ！！/？？ for emphasis, open with 兄弟们/好奇问问大家 or a direct scene, close with a question or an exclamation — never open with 吉伊我啊. The profile's few-shot samples are the 1:1 alignment baseline.
  - Fact first: every number, date and experience in the draft must come from something real (the user, the local log, a measured stat). No real views means no stats table; a missing number stays as `[填入实际数据]`; never invent a story.
  - Shape the post as one of the four high-conversion types (pain-point question, rule observation, self-deprecating contrast, progress check-in), inside the three pillars (Muse 相关话题， 日常小确幸， 轻提问）. The main post carries zero external links.
  - Run the de-AI pass before sending: no banned words, no translationese, no mechanical 三段论， no closing flourish — the full checklist lives in x_viral_ops.
  - Draft a first-floor follow-up only when the post has a link, a handout, or something readers will ask for (tool name, method, follow-up detail); never force one onto every post. Publish it after the post with `x_engage.py firstfloor <post URL>` (the same step the automation uses). The first floor is Simplified Chinese and 法条-checked, with no 25-character limit.
  - The full method wording lives in x_viral_ops (merged from the all-platform-creator skill on 2026-11-16); this section is the operative checklist for a manual post. When the two disagree, x_viral_ops wins.
- Post from the home composer (`tweetTextarea_0`, button `tweetButtonInline`), and verify from a second surface before reporting success, such as the profile post count going up or a search for the account's own posts.
- Post text must be Simplified Chinese — see the language rule below; the script refuses anything else before the browser opens.

## Reply and like

- Reply and like target the target account's latest non-pinned post, because profile timelines put an old pinned post first. The script scans the first six articles and takes the first one written by the target without "Pinned" in its text.
- Like first checks for the `unlike` state and reports `ALREADY LIKED` instead of clicking again, and asserts the button flipped to `unlike` after the click.
- Reply opens the reply composer from that post on the profile timeline, where the post button is `tweetButton`, and posts through it, then screenshots the result.

## Reply content rules (hard constraints)

- Every reply is at most 25 characters, counting every character including punctuation. Count before sending; if it is over, trim it to fit instead of sending a longer version. The script refuses a reply over 25 characters before opening the browser.
- Read the target post first and reply to something specific in it: a detail, a number, a word the author used. A reply that would fit any post is a failed reply — rewrite it or do not send it.
- Sound like a person texting a friend, not a bot: plain words, one idea, no buzzwords, no corporate phrasing, no em dash, no canned comfort, no defensive hedging ("能确认的是", "还不能确定", "不代表" and the like). Say it the way you would say it out loud.
- First sentence answers or reacts directly, then stop. No preamble, no summary of the post, no overexplaining.
- Punctuation stays minimal: no em dash, no trailing full stop unless the sentence needs it, no emoji unless the account's own style uses them.
- Before sending, check four things: (1) 25 characters or fewer? (2) does it name something from this post? (3) would a person say it out loud? (4) Simplified Chinese? Fail any one and rewrite.
- These rules are the user's own, adapted with two GitHub references cloned to `~/workspace/ref-skills/`: MistReplies (`0xmists/MistReplies` — X reply agent: short, casual, no robotic language) and chinese-natural-reply (`molang163/chinese-natural-reply` — plain spoken Chinese, no defensive hedging, no templates). The wording voice still lives in x_viral_ops; these rules are the hard gate on every reply this skill sends.

## Language rule (hard constraint, posts and replies)

- Post and reply text must be Simplified Chinese. This is a hard gate, enforced in `x_ops.py` before the browser opens: text containing Traditional-only characters, Japanese kana, or Korean hangul, text with no Chinese characters at all, or text where Latin letters outnumber Chinese characters is refused with `NOT_SIMPLIFIED_CHINESE` and never reaches X.
- English technical terms and brand names (AI, X, API), digits, @handles, URLs and emoji are fine inside Chinese text, as long as the Chinese characters dominate. An English sentence or a Traditional-Chinese sentence is not.
- The automation's posts go through `x_ops.py post`, so they are covered by the same gate. The automation's comments and replies run through `x_engage.py`, which enforces the same two gates (25-character limit and Simplified Chinese) before the browser opens — the same constraints, the same refusal codes (`REPLY_TOO_LONG`, `NOT_SIMPLIFIED_CHINESE`). The tone and specificity rules for automation comments and replies live in x_viral_ops, worded identically to the reply rules above.
- When a draft fails the gate, rewrite it in Simplified Chinese instead of working around the check.

## Follow

- Follow from the target profile page, and assert the button flipped to its unfollow state before reporting success, because the click can silently miss.

## Send a DM

- Open the DM from the target profile page with the `sendDMFromProfile` button, because going through the chat list first loses the target.
- Expect the X chat surface to hide its text from the page body text, because it renders inside shadow DOM, and locate its elements with Playwright selectors, which do reach inside.
- Ask the user for the four digit chat passcode when the chat asks to recover encryption keys, pass it to the script as the `CHAT_PIN` environment variable, and never write the passcode into any file. The chat stays unlocked in that profile afterwards, so later DMs do not ask again.
- Send with `dmComposerSendButton` when it exists, falling back to Enter, and confirm the message text is visible in the thread before reporting success.

## Delete one of the account's own posts

- Run `~/workspace/custom-skills/x_manual_ops/scripts/delete_tweet.py <status URL> <text fragment>` with the venv python and `TMPDIR=~/workspace/camoufox/tmp`.
- It opens the tweet, finds the article holding the text fragment, opens its caret menu, chooses Delete, confirms, then reloads the status URL and reports `deleted: true` only when the page says the post does not exist or the text is gone.
- Delete is the one action in this skill with no undo. Use it only when the user asked for that exact post to go, and report the verification, not just the click.

## Like several tweets in one session

- Run `~/workspace/custom-skills/x_manual_ops/scripts/like_many.py <url> <text fragment> [<url> <text fragment> ...]` when several likes are owed at once, for example the likes a reply or comment flow failed to finish.
- It opens each status page in the same browser session, finds the article holding the text fragment, skips it when it already shows `unlike`, and reports one `liked` result per URL.

## Hard rules from field experience

- Type into every X composer with `page.keyboard.insert_text`, never with sequential typing, because sequential typing moves the first Chinese character to the end of the text.
- Read the composer text back and send only when it matches the requested text exactly, and delete and redo any post that went out scrambled.
- Click modal and popup buttons with Playwright locators instead of coordinates, because coordinate clicks on X modal buttons silently miss while locator clicks fire the action.
- In the inline reply composer on a tweet page, the post button is `tweetButtonInline`, not `tweetButton` (the main composer on the home page uses `tweetButtonInline` too). Waiting for the wrong one times out every time, so try `tweetButtonInline` first and fall back to `tweetButton`.
- X intermittently covers tweet pages with a login-wall / bot-check interstitial ("Unlock more on X", "To make X great for everyone") that intercepts every click. Wait it out, dismiss it with Escape or its close control, reload once if it persists, and report a clean error instead of dying without a result.
- Verify every action from a second surface before reporting success, such as the profile post count, a search for the account own posts, the follow button flipping to its unfollow state, or the sent message bubble marked as sent.

## Stay inside the suite

- Use the skill x_account_cloud_login for the environment, the residential proxy relay and getting any account logged into its Camoufox profile.
- Use the skill x_viral_ops for every word that gets published, including post structure, comment voice, reply voice and the content red lines.
- Use the skill x_ops_automation for the running system on top of these actions, which is scheduling, action ordering, cooldowns, guards, measurement and bookkeeping.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [X](https://x.com/) for every account action. Carry in the account email, the target handles and the exact texts, and verify each result on the page before reporting it.
