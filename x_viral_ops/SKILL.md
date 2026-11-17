# X Viral Ops

## Provenance

- Adapt the method in this skill from the open source xiaohongshu-ops-skill at `~/workspace/ref-skills/xiaohongshu-ops-skill/SKILL.md` and the trend scouting idea behind Agent-Reach, both linked from a post by @3three_AI, and read the original file when a detail here is unclear.

- Merged 2026-11-16 from the user-supplied all-platform-creator skill (`~/workspace/user/files/skill_md.md` plus its voice-profile template `~/workspace/user/files/voice_profile_md.md`): the fact-first iron rule, Traffic Lift attribution, the khazix hv-analysis five-dimension breakdown, khazix-writer, the leader seven questions (trimmed to what drafting needs), and the humanizer-zh 24-item de-AI checklist. The voice-profile mechanism was deliberately NOT adopted on 2026-11-16 — the user said so ("不配置voice那个"). Reversed 2026-11-17 ~19:28: she re-uploaded the same two files and asked to merge them into x_manual_ops's posting operations — a filled voice profile now exists at `~/workspace/x-ops/voice-profile.md` (from the account's real published posts) and manual posts draft against it. This skill's voice baseline stays the three pillars plus the account's real published posts in the local log; the automation does not read the profile unless she asks. Read the source file when a detail here is unclear.

- Apply the method to X only, because the original targets Xiaohongshu and its browser flows, cover cards and note formats do not transfer. The source skill's other-platform tracks (小红书图文、公众号/知乎长文、视频口播稿） are preserved in the source file for future use and are NOT active in this account's automation.

- The source skill's local scraping modules (MCP / CDP / browser extensions) assume a local agent with a local logged-in browser. This account runs in the cloud through Camoufox behind the residential relay, so those modules do not apply here: all post data and view counts come from the existing stack (x_engage.py stats, the local daily log, the X运营空间 records). Never claim a live scrape when the session or relay is down.

## First iron rule: everything must be based on fact (highest priority, above every other rule)

- Never invent a statistic, a number, a personal experience, or a story that did not happen. Every time, amount, follower count, view count, price, or mishap detail in a draft must come from something the user actually provided or from a measured record (the local log, the Space, a live stats read).
- No real view numbers means no stats table: compute Traffic Lift and write a quantified attribution table ONLY when real views exist for the posts being compared. With text only, skip the table and go straight to drafting.
- A missing concrete number is written as the placeholder `[填入实际数据]`, never filled in by guessing.
- Never pass off an old record as a fresh live fetch. If the session is down or no live data is available, say so plainly and draft from the account's recent real posts and the three pillars instead.
- Trade-off order when rules collide: 事实准确性 > 个人真实语感 > 篇幅长度.

## Voice baseline: the account's own published posts

- A filled voice profile now exists at `~/workspace/x-ops/voice-profile.md` for the manual post flow (x_manual_ops, user rule 2026-11-17 ~19:28). This skill's voice baseline stays the three pillars plus the account's real published posts in the local log; do not read the profile for automation drafts unless she asks.
- The voice baseline is the three pillars plus the account's real published posts: the local log holds every post text. Skim the recent ones before drafting so the new post sounds like the same person — same punctuation habits, same line-break rhythm, same openers （吉伊我啊， AI 现在会…, 今天让 AI 帮我…), same plain first-person chat, same one light question at the end.

## Set the account position first

- Fix four variables before writing anything, which are the target reader, the value each post gives, the angle bigger accounts do not take, and the tone rules with a red line list.

- Write in the voice of the account 吉伊大王 (@xunana1017): playful and cute on the surface, with real curiosity about Muse underneath. The account voice is exactly these three pillars, in the user's own words:
  - Muse 相关话题： share Muse finds and things you actually did with Muse — a trick, a discovery, an everyday use — never a spec dump, never an ad.
  - 日常小确幸： small daily moments of happiness, light and cute, with a picture the reader can see.
  - 轻提问： close with one light question a reader can answer in a line — easy, specific, never heavy.
- Every post, comment and reply stays inside these three pillars; if a draft fits none of them, it is the wrong draft.
- (2026-11-16, at the user's request: pillar 1 was AI 工具/科技发现 and is now Muse 相关话题. Drafts written before the change stay in the log as history; new drafts use the new pillar.)
- The concrete voice fingerprint (punctuation, line breaks, openers, pet phrases) lives in the account's real published posts, not here — skim the recent ones in the local log before every draft.

## Scout signals before writing

- Read the For You feed and X search results for the pillar topics, and collect posts whose likes, reposts and replies run far above the recent average.

- Record each strong post with its hook line, its angle, its structure tags, the question it asks the reader, and its topic tags.

- Read the replies under two or three strong posts and extract where readers disagree, because a controlled disagreement is the raw material for a post people answer.

- Before drafting, run the leader zero question: check the real inputs first (recent real posts skimmed, facts verified, environment bounds known) — never draft behind closed doors.

## Attribute with real views: Traffic Lift × hv-analysis five dimensions

- When real view counts exist for the account's posts, score each post by Traffic Lift = single post views / account recent median views, and weight the next draft by tier:
  - Tier S (super hit, Lift ≥ 5.0x): 50% of the draft's structure weight — decides the hook and the angle.
  - Tier A (breakout, 2.0x–5.0x): 35% — decides sentence rhythm, line breaks, and the interaction hook.
  - Tier B (baseline, 0.8x–2.0x): 15% — keep only the base persona voice.
  - Tier C (flop blacklist, Lift < 0.8x): 0% — extract its cause of death (external link in the main post, long unbroken sentences, pure self-talk with no hook) into the draft's avoid list.
- With no measured views, skip the tiers entirely — never estimate views. (As of 2026-11-16 the account's per-post views are mostly unmeasured, so this section usually stays dormant; it activates the moment real stats exist.)
- For a Tier S/A hit (or a long-form outline), break it down on the five hv-analysis dimensions before reusing its structure:
  1. Angle — narrow the topic to a specific group + specific scene + a counter-intuitive number or real conflict.
  2. Hook — the first line shows the result, a warning, or a cost contrast; cut all grand background.
  3. Granularity — concrete parameters, real errors, saved amounts, personal action details nobody else gave.
  4. Pacing — one or two sentences per paragraph, blank lines for air, long and short sentences alternating.
  5. Engagement trigger — a low-barrier take-a-side question, a dilemma, or a first-floor follow-up to pull replies and bookmarks.
- Reuse the structure of a proven hit and never copy its wording, because copying text invites reports and kills the account voice.

## Shape every post as a viral unit

- Open with one hook line that takes a side, asks a pointed question, or states a contrast, and keep it under one short sentence.

- Follow the three part body, which is a clear view first, one concrete piece of evidence or a lived detail second, and the other side or a twist third.

- Close with exactly one question that a reader can answer in one line, because that question is the reply engine of the post.

- Keep the whole post short enough to read at a glance, use at most three topic tags, and produce at least two variants before choosing one.

- Prefer the four high-conversion post types, each still inside the three pillars and still closing with one light question:
  1. Low-barrier pain-point / tool question — a concrete tool doubt or a real either-or from daily life, with your own stance stated first so passers-by can jump in (the reply magnet).
  2. Platform-rule / trend observation — a fresh platform change, tool update, or information gap, with a rhetorical question that pulls reposts and discussion.
  3. Doing-the-account / self-deprecating contrast — an honest account of the grind, the mishaps, or the input/output gap; draws peers in.
  4. Progress check-in / dry value straight up — real staged numbers, a tested bill, or a pit-avoidance checklist, with steady interaction to convert passers-by into followers.

- For longer drafts, write as khazix-writer's 有见识的普通人： not a mentor, expert, or marketing account, but a normal friend who tinkers, has tripped, and talks eye to eye. Four-step method: (1) dig granularity and body temperature — concrete time, concrete action, mishap numbers, the real reaction at the time （说实话我当时看到报错就懵了）; (2) build a natural breathing skeleton — open with a concrete scene or self-deprecation, one or two sentences per paragraph, blank lines for air; (3) first de-AI pass — zero out all official phrasing and abstract big words; (4) second pass inject living-person roughness — natural spoken connectors （说实话、最坑的是、直接抄作业、我老觉得）, parenthetical asides for inner complaints （真的，看到那一刻我人都麻了）.
- Khazix-writer four no's: (1) never preach from above — no 你应该/你必须/你要明白， use 我自己试下来 / 我当时是怎么踩坑的； (2) no empty hype — replace 极其震撼/性价比拉满/颠覆想象 with concrete numbers and physical feeling; (3) never sacrifice realness for neatness — break tidy three-line parallelisms and four-character idiom piles, keep the pauses and short-sentence rhythm of real speech; (4) never fence-sit for safety — good is good, a pit is a pit, give a clear verdict, never 一方面...另一方面...各有千秋.

- First-floor follow-up （评论区 1 楼承接）: the main post carries ZERO external links — a link in the main post triggers downranking. Every external link, repo address, or file handout goes into a first-floor self-reply written alongside the post, plus a warm-up reply line for readers. Draft the 1 楼文案 with every post that has something to link or hand out — and also when the post references something readers will ask for (a tool name, a method, a follow-up detail worth adding). If there is genuinely nothing to add, there is no first floor: never force one onto every post. The 1 楼文案 is published automatically as a self-reply right after the post (wired 2026-11-16, user approved): the worker passes it to `do post` via `--firstfloor`, and the state machine publishes it in the same run, retries once on failure, and records a still-failing one as pending for top-up. A first floor is part of the post action, not a second action. It follows the same rules as a post: Simplified Chinese (enforced by the `x_engage.py` firstfloor gate — no 25-character limit, a first floor is a follow-up post, not an engagement reply), judged against the 法条 before publishing, and never an engagement solicitation (§3.4).

## De-AI pass (humanizer-zh): run twice before any draft goes out

- Pass 1: zero out the 24 AI tells below. Pass 2: calibrate line breaks, punctuation, blank lines, and sentence-final particles against the account's recent real published posts in the local log.
- Banned high-frequency AI words — never appear: 总而言之、综上所述、值得注意的是、不可否认、毋庸置疑、在当今快节奏的时代、随着...的不断发展、宛如、恰似、不仅...更...、双刃剑、赋能、闭环、抓手、底层逻辑、顶层设计、降维打击、生态位、心智、沉淀、组合拳、情绪价值、编织出、奏响了.
- Cut translationese and 的-word disease: no 进行…的构建/分析/实施/探讨 verb structures — replace with crisp one- or two-syllable concrete verbs; break up any attributive chain with three or more 的.
- Break mechanical three-part structure and subheading-colon disease: no 首先/其次/再次/最后 mechanical listing; no 四字词语 + 冒号 + 抽象大词 subheadings （破局之道：构建流量闭环）; do not overuse double quotes to emphasize ordinary nouns, do not overuse em dashes for stiff explanations.
- Never end with a flourish or a slogan: after the concrete value or the interaction question, stop writing — never 让我们拭目以待 / 未来可期 / 时间会给出答案 / 唯有坚持方能致远.

## Enforce the red lines

- Never touch topics about Chinese politics, and drop a candidate topic the moment it drifts toward them.

- Never write mutual follow or follow for follow content, and never promise follows, likes or reposts in exchange for engagement.

- Never publish posts about Muse operating or running this account: no meta content revealing that Muse writes the posts, drafts the replies, or runs the account's operations (user rule, 2026-11-17 ~19:19; the 2026-11-17 09:50 post — "它每天帮我写帖子、跑这个号的运营" — is the banned pattern, do not repeat it). This is not a ban on pillar 1: posts about using Muse — a trick, a discovery, an everyday use, something you actually did with Muse — are still the pillar. The line is operator vs. tool: Muse as a tool you use is fine; Muse as the one running this account is never mentioned.

- Never attack a person, never promise results the post cannot prove, and mark any candidate that risks a fight beyond a friendly disagreement as do not publish.

## Check every draft against the 法条 before publishing

- Judge every post, first-floor follow-up, comment and notification reply against the X审判者法条 (baseline 2026-11-11, full text at `~/workspace/ref-skills/x-judge/references/法条-公开版.md`, from the public repo Rick-newbit/x-judge linked by @HoneyBiu) before it is published. The 法条 is the sole authority; the checklist below is its application to this account's content, not a replacement for it.
- Run this check on the draft text, in order, and publish only when every item passes:
  - No coordinated engagement exchange (§2.1): no mutual-follow / follow-for-follow content, no promises of follows, likes, reposts or replies in exchange for engagement, no recruiting people into an exchange (already a red line above).
  - No abuse of reporting (§2.1): never call on people to report or mass-report an account.
  - No content spam (§2.2): never repeat the same or near-identical text across posts (copypasta); never send bulk unsolicited replies, @s or DMs; never stack unrelated hashtags (at most three topic tags, already the rule); never make pure-link posts the account's main activity; never reply to a post with unrelated promotion.
  - No fake persona or impersonation (§2.3); no deceptive synthetic media — non-deceptive AI content is allowed and needs no AI label.
  - No hate toward a protected group, no gambling promotion, no guaranteed-return financial claims, no one else's private information, no adult media in the post or the profile.
  - No repeated engagement solicitation (§3.4): never instruct readers to like, repost, follow or bookmark, especially not as a repeated routine. One substantive question that invites a reply with content is not solicitation — that is the post's reply engine, not an interaction instruction.
  - No tutorial that teaches coordinated exchange or automated manipulation (§2.7 教程帖三段论）.
- Judge context and behavior, never keywords (§2.7): mentioning a banned word while asking about it, reporting on it, or warning others about it is not a violation; a short greeting or catchphrase reply is not spam; a single short reply or a single pure-link post is not a violation. Never block a draft for a word alone — read what the draft is doing.
- Verdicts for the forward gate: 合规 → publish. 低危 → publish, and clean it up only if the fix is trivial. 中危 or worse → rewrite once; if the rewrite still fails, do not publish and log the skip with the failed provision and one-line reason. The automation skill owns the skip discipline.

## Final self-check before output (four standing orders)

- [ ] No fabricated stats table or personal experience that never happened? (If yes, delete and rewrite at once.)
- [ ] Do the layout, punctuation, line width, and line breaks reproduce the real-post habits of the account's recent published posts?
- [ ] Are all AI clichés, official phrasing, and preachy condescension fully cleared?
- [ ] Is there a copy-ready first-floor follow-up draft and an interaction warm-up line, when the post has a link or handout to carry?

## Comment and reply with the same voice

- Every comment and notification reply follows exactly the same hard constraints as a manual reply in x_manual_ops (user rule, 2026-11-12): at most 25 characters counting every character including punctuation; Simplified Chinese; read the target post first and reply to something specific in it — a detail, a number, a word the author used — a comment that would fit any post is a failed comment, rewrite it or do not send it; sound like a person texting a friend — plain words, one idea, no buzzwords, no corporate phrasing, no em dash, no canned comfort, no defensive hedging ("能确认的是", "还不能确定", "不代表" and the like); first sentence answers or reacts directly, then stop; minimal punctuation, no trailing full stop unless the sentence needs it, no emoji unless the account's own style uses them. The browser script refuses anything over 25 characters or not Simplified Chinese before it opens, so count before calling it and trim to fit.
- Before sending, check four things: (1) 25 characters or fewer? (2) does it name something from this post? (3) would a person say it out loud? (4) Simplified Chinese? Fail any one and rewrite.
- Read the whole post before commenting, and answer its actual point with one specific observation; add at most one question only when it still fits inside 25 characters.
- Reply to people who engaged with the account by answering their words first, thanking or teasing lightly second, and never pasting a template.
- Keep every comment and reply short, human and varied, because repeated phrasing is the fastest way to look automated.

## Stay inside the suite

- Leave timing, ordering and cooldowns to the skill x_ops_automation, single hand-run actions to the skill x_manual_ops, and the environment, login and browser mechanics to the skill x_account_cloud_login, because this skill owns only the words.

## Record and review

- Log every published post with its time, text, link and later view count, and log every comment, reply, like and follow back with the target account and post.

- Review the log daily, name the best performing hook and the weakest post, and feed both back into the next round of topics. When real view counts exist, review by Traffic Lift tiers: Tier S/A structures get reused, Tier C causes of death go on the avoid list; with no measured views, review by reply counts and fit with the account's recent posts instead — never by invented numbers.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [X](https://x.com/) for signal scouting in the For You feed and search, and for every publish and engagement action. Verify each result on the page before logging it.
