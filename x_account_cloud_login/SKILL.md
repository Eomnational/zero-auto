# X Account Cloud Login

## Prepare the environment

- Start every session by checking the chain relay at 127.0.0.1:18081, because Firefox and Camoufox cannot reach the proxy gate directly from this virtual machine and every browser session depends on the relay.

- Restart the relay from `~/workspace/camoufox/chain_relay.py` when it is down, passing the proxy credentials as the `KK_AUTH_B64` environment variable and the sandbox egress proxy as `UPSTREAM`, and expect the relay to die whenever the runtime service restarts.

- Current proxy (since 2026-11-17 09:36): <PROXY_IP>:<PROXY_PORT>, user <PROXY_USER> — the kookeey gate is superseded and must not be used. The relay script defaults KK_HOST/KK_PORT to the old kookeey gate, so every restart must set KK_HOST=<PROXY_IP> and KK_PORT=<PROXY_PORT> explicitly, with KK_AUTH_B64 = base64 of `<PROXY_USER>:<password>`; the password is supplied by the user at runtime, passed via environment variable, never written to any file.

- Verify the exit IP through the relay with a request to ip-api before opening any browser, and use that exact IP as the `geoip` argument, because the exit must be confirmed before any browser use.

- Give each X account its own Camoufox profile directory and its own Chromium profile directory, and run only one browser process per profile at a time, because a leftover process locks the profile and blocks the next launch.

- Launch Camoufox with a persistent context, the relay as proxy, `os` set to windows and `locale` set explicitly to en-US, because the geoip lookup alone once produced an es-US locale.

- Kill helper scripts by exact process ID, and never put the script name in a `pkill -f` pattern inside the same shell command, because the pattern also matches the shell running the command and kills it.

## Log in through Chromium, not Firefox

- Try the Chromium route first for an account that was created with Google sign-in, because on the account tested in November 2026 the three direct routes all failed in ways that look like account problems but are not.

- Treat the username and password form on X as a dead end for Google-created accounts, because it routes into a phone number signup flow and never shows a password field.

- Treat Google sign-in inside Firefox or Camoufox as a dead end, because Google completes its side and X then answers with an unexpected error and never sets the auth cookie, as proven by watching the cookie store during the flow.

- Try X phone verification at most once per attempt, because the request can return success while no SMS ever arrives on a mainland China number.

- Run `~/workspace/custom-skills/x_account_cloud_login/scripts/chrome_google_login.py` under `xvfb-run -a` with the email and password passed as environment variables, and keep the script alive until it writes the cookies file or reports a blocking step.

- Relay only the newest device prompt number to the user when Google asks for phone confirmation, because prompts queue up and rotate, and ask the user to dismiss the older ones.

- Stop and report when Google reports a wrong password, and ask the user to confirm the exact password variant instead of guessing variants.

## Transplant the session into Camoufox

- Run `~/workspace/custom-skills/x_account_cloud_login/scripts/transplant_cookies.py` after the Chromium login writes its cookies file, and set the `GEOIP_IP` environment variable to the live exit IP first.

- Confirm the transplant by loading the home timeline in Camoufox and checking that the account name appears, and send the user the proof screenshot.

- Delete the loose cookies file after a successful transplant, because the session then lives inside the Camoufox profile and the file is a stray credential.

## Check the account is not limited after login

- After the transplant is confirmed, run a shadowban check for the account on Shadowban Radar (https://shadowbanradar.com/zh), because a login that works says nothing about whether X is limiting the account's reach.
- Enter the handle without the @, run the free check, and record the overall verdict plus the four items: search suggestion ban （搜索建议封禁）, search ban （搜索封禁）, ghost ban （幽灵封禁）, reply deboosting （回复降权）, with each item's confidence and the time the X data was read.
- The check reads only public data and needs no login or password; never enter the account password there, and do not buy the paid Shadowban Recovery monitoring unless the user asks.
- Show the result in the X运营空间 with savenote for the current status and addlog for the check event, and tell the user at once if any item fails, because a limited account changes what the automation should do.
- Re-run the check when the account's reach suddenly drops or after any X warning, and compare the dated results to see whether a limit appeared or cleared.
- Treat the result as a measurement of today, not a verdict on the account forever, and do not infer a limit from low views alone when all four items pass.

## Run account actions

- Single manual actions live in the skill x_manual_ops now: one post, reply, like, follow or DM at a time from the logged-in profile, plus deleting one of the account's own posts and liking several tweets in one session. This skill stops at the login.
- Leave scheduled and repeated operation to the skill x_ops_automation and every publishable wording to the skill x_viral_ops.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [X](https://x.com/) for the login flow. Carry in the account email, and verify the result on the page before reporting it.

- [IP Net Coffee](https://ip.net.coffee/) for a human readable check of the proxy exit IP inside the browser. Compare its result with the ip-api answer before trusting a new session.
