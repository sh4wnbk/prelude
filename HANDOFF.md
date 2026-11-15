# HANDOFF

The state of the repo, not its history. **Current state** is everything still
in force. **Next first action** is what to do first. **Last task** is the most
recent record in full. Every record before that one is in `docs/history/`,
unchanged, and `docs/history/README.md` says where each of its decisions now
lives.

A session orients by reading `CLAUDE.md`, then Current state, Next first action
and Last task here. `docs/history/` is for when the reasoning behind one
decision is needed, not for orientation.

Every number below came from a command that ran.

## Current state

### Before any Orchestrate test, demo recording or judging

**Standing, kept until submission.** The hosted API is at
<https://prelude-api.onrender.com>. Render spins the free service down after
fifteen minutes without traffic, and a cold wake took 82 seconds on the
keepalive run of 2026-11-07. A tool call that is the first traffic in a quarter
of an hour waits that long, and Orchestrate gives it less.

1. **Until the repository variable `PRELUDE_KEEPALIVE` reads `on`**, open
   <https://prelude-api.onrender.com/health> yourself and wait for
   `{"status": "ok"}` before testing a tool, recording the demo or handing the
   URL to a judge. The service is warm for fifteen minutes after that.
2. **Turn `PRELUDE_KEEPALIVE` on before judging**, under Settings, Secrets and
   variables, Actions, Variables. Do it after the repository goes public, where
   Actions minutes are not metered; on a private repository the schedule bills
   144 minutes a day. Then nothing has to be woken by hand.

### What exists

**The app is seven screens and a shell**, static files under `app/web/`,
deployed from `main` to <https://sh4wnbk.github.io/prelude/> by
`.github/workflows/pages.yml`, which stamps the commit into every `__V__`
placeholder. `index.html` holds each screen in an iframe and carries the
launch screen. The screens are the event list (`01`), Live (`02`), the moment
card (`03`), Moments (`04`), the scanner (`05`), the ticket (`06`) and Profile
(`07`). `app/web/match-content.js` is the renderer all of them share, with
`listener-card.js`, `manual-entry.js` and `narration-player.js` beside it, and
`matches.json`, `narrations.json` and `narrators.json` as its data.

**Nothing is loaded from anywhere else.** `tailwind.css` is compiled from the
config block the screens share, `fonts.css` and `assets/fonts/` are the four
families, `assets/vendor/jsQR.js` is the scanner's reader, `assets/brand/` is
the mark, `assets/icon/` is the icon set drawn from it and `assets/launch/` is
the eleven iPhone startup images drawn from the same layout, all committed and
all served from this repo.
`tests/browser/test_every_screen.py` asserts that no screen leaves its own
origin and that nothing 404s.

**Twenty-one modules in `app/`.** Standard library only, with one exception:
`app/api.py` takes FastAPI, and
`tests/test_api.py::TestWhatItDoesNotReach::test_the_only_module_in_app_that_takes_a_third_party_package`
is what keeps it the only one.

**Thirty-one scripts**, each runnable on its own: thirty directly under
`scripts/` and `scripts/brand/build_svg.py` beside the two fonts it reads.
Five are gates: `data_check.py`, `scan_copy.py`, `check_match_copy.py`,
`check_vocabulary.py` and `check_docs.py`. `docs/HARNESS.md` carries the table
of all thirty-one, what each writes and what each reaches, and a row for every
file in `tests/`.

**The hosted API** is `app/api.py` on Render at
<https://prelude-api.onrender.com>, three GET endpoints (`/health`,
`/moments`, `/buildup`), read only, holding no credentials and making no paid
call. Its whole job is to give watsonx Orchestrate a stable public URL.
`orchestrate/prelude_tools.yaml` is the OpenAPI file Orchestrate imports, and
`docs/orchestrate_agent.md` is the block pasted into the agent.

**The data** is StatsBomb open event data for two matches, 1986 Argentina vs
England (`3750191`) and the 2022 final (`3869685`). `data/raw/` is gitignored
and absent from a fresh clone, so `scripts/fetch_statsbomb.py` is the first
command in one.

**Six narrations and six recordings.** `app/web/narrations.json` holds the six
frozen narrations, one per match per listener slot (`buddy_scored`,
`buddy_conceded`, `storyteller_neutral`), and
`app/web/assets/audio/<match_id>_<slot>.mp3` holds the recording that reads
each one. The words on the card and the words the voice reads are one text,
resolved by one lookup.

**The test harness** is 42 files in `tests/` and seven in `tests/browser/`. The
unit suite is run by `pytest`, which leaves the browser suite out through
`norecursedirs`; the browser suite is run by naming it, `pytest tests/browser`,
and drives headless Chromium at 390 by 844 over a local server.

**The build** is four workflows. `ci.yml` runs on every push and pull request:
install, fetch the data, the unit suite, the five gates one step each, the
browser suite, and a step that fails if the run changed a tracked file.
`pages.yml` deploys on a push that touches `app/web/`. `smoke.yml` runs after
a Pages deploy succeeds and checks the deployed site and the hosted API.
`keepalive.yml` pings `/health` on a schedule, behind the `PRELUDE_KEEPALIVE`
switch. Render rebuilds the API only when `app/`, `pyproject.toml`, `uv.lock`
or `render.yaml` change, which is the build filter in `render.yaml`.

### The interfaces

Code is written against these rather than against each other. The first three
are the seams that let a module be replaced or be someone else's to build.

| Interface | Declared in | Satisfied by |
| --------- | ----------- | ------------ |
| `EventFeed`, `Moment`, `Buildup` | `app/event_feed.py` | `app/statsbomb_event_feed.py`, which is Bob's |
| the orchestrator: `transition`, `header`, `phase`, `score_state`, `outcome`, `default_persona` | `app/orchestrator_contract.py` | `app/orchestrator.py`, which is Bob's |
| `NarrationProvider` and `Transport` | `app/narration_provider.py` | `OllamaProvider` and `WatsonxProvider` |
| the grounding check | `app/grounding.py` | read by `app/narration.py` and by every script that writes a narration |
| the goal-call grammar | `app/narration_grammar.py` | read by `app/grounding.py` for a narration that cites nothing |
| the slot rule, as one table | `tests/slot_rows.json` | `Prelude.slotFor` in `app/web/match-content.js` and `slot_for` in `app/api.py` |
| the speech request | `app/tts.py` | Watson Text to Speech, with the delivery from `app/delivery.py` |
| the Orchestrate tool contract | `orchestrate/prelude_tools.yaml` | checked against `app.openapi()` by `tests/test_orchestrate_spec.py` |

**The EventFeed and moment-detection module is reserved for IBM Bob**, which
`CLAUDE.md` states as a rule. Code that needs moments is written against
`app/event_feed.py` and left waiting for it.

### Decisions still in force

Every one of these was settled in a task whose record is now in
`docs/history/`. The statement here is the decision; the record is the
evidence and the reasoning behind it. Changing one of them changes what the
app claims.

**The grounding check, and what may be said**

- The failure rule is whole-narration. A failing narration is not patched and
  not shown unlabelled: it fails together, is regenerated up to twice, and
  falls back to a narration assembled by code out of the facts. If even that
  failed, `narrate` raises rather than returning something unverified.
- A narration cites its facts, and each sentence is read against the facts it
  cited and nothing else. Pairing every name with every action inside one
  cited fact is what catches a true-sounding misdescription, and the cost is
  that some true sentences are refused, which is why the prompt asks for one
  action a sentence.
- Narration is past tense. A present-tense verb is refused rather than
  grounded.
- There is no closer. The last sentence cites the goal's own shot fact, and
  nothing follows it.
- The second person is refused everywhere. So are force words, editorial
  epithets, claims about the score or the result, and markup: the check
  refuses any narration holding `<` or `>` outright.
- "Won a foul" stays sayable because it is a `Foul Won` record; "won the
  match" is refused.
- A clock is checked against the cited fact's own clock, so a per-second
  clock is groundable.
- A persona is a register and changes nothing about what may be said. A check
  that loosened for one listener would make the label mean different things to
  different people.
- The partisan voice may say "we", "our" and "us" only in a sentence whose
  cited facts are recorded against the listener's own side. Nothing asks a
  model for the word any more, so the rule is a guard.
- A reaction is the second layer and is not a claim: at most `REACTION_WORDS`
  words, no digit, no player, team or pronoun, no claim about a recorded
  field, standing once at the goal after the finish has landed. Everything
  else still applies to it.
- "Under pressure" is a claim about the player on the ball, whoever is named
  beside it. "Under pressure from X" is a second claim, that X has a
  `Pressure` record in the passage.
- A place on the pitch is a claim, read off the attacking side's own record,
  and about the move it was said beside. A side is said only where the ball is
  clear of the middle.
- The pass rate counts first attempts only. Coverage is reported and never
  enforced, and is split by what wrote the narration, because a template
  fallback reaches every beat by construction.

**The narration, as it ships**

- One narration style for every persona. Three models were asked three ways
  for three registers and gave one register back each time, so the personas
  are separated by sound and not by text.
- `openai/gpt-oss-120b` is the active candidate, on the chat endpoint at
  `reasoning_effort` low. The endpoint and the effort travel with the
  candidate in `app/narration_config.py`, because a model id alone does not
  reach a model.
- The six narrations were written by the team and verified by the grounding
  check exactly as a model's would be. The authorship is disclosed beside each
  one and in `README.md`; the label is about whether the claims trace to the
  records, not about who put the words in that order.
- A telling opens on a name, and places the move at least `PLACES_WANTED`
  times. Both are acceptance rules in `scripts/narrator_candidates.py` and not
  in the check, because a narration that opens on "We" makes no false claim.
- A run against a paid model is capped in tokens and refuses to start without
  a cap, and the cap is tested before each call rather than after it.
- Copy the review file aside before any rerun. This is still not automated,
  and a run has already overwritten candidates it was meant to keep.
- What judges hear is recorded, never live. The six recordings are the
  fallback whether or not the API is up.

**The header, and the fan**

- The header says what the goal did to the score. It is the same line for a
  fan of either side and for a listener with none; allegiance picks the
  persona through `default_persona` and changes no word of the header.
- `ScoringMoment` carries the score before the moment as well as after it,
  passed by the caller and never derived, and a transition is read out of
  those two numbers and nothing earlier in the match.
- The header is never labelled. It is built from the kickoff time, the score
  and the listener's own answer, none of which is event data.
- The phase is a share of regulation time, so the rule outlives football.
  `tests/test_orchestrator.py::TestAnotherSport` is a sport that does not
  exist, and it fails if a 90 is ever written into the rule.
- A neutral listener has no score state and no outcome. Both raise rather than
  returning a third value.
- The name a fan types stays on the phone. It is added to the header after the
  narration has been generated, and is never sent to a model or a server.
- Prelude does not choose the match for the fan. There is no default match:
  the screens on `MATCH_REQUIRED` send a fan with no match to the list, and
  the header pill stays hidden until a match is chosen.
- The narrator outlives the tab, in `localStorage`. The allegiance and the
  name are answers about tonight and stay per session.

**The label**

- "Verified from play data" may appear only over narration whose claims trace
  back to the event data, exactly as written, with no partial credit and no
  softened variant. `CLAUDE.md` is where that rule lives.
- The narration is the one field on the moment card with no inline fallback
  copy, because it arrives under a label that says the data proves it. The
  paragraph and the label ship hidden and are revealed together by
  `showNarration`, and the block reserves its space so nothing moves.
- The play button ships disabled and is released by the same step that reveals
  the words.
- A data file records `"labelled": true`, the permission rather than the
  words. The label has one definition, `GROUNDING_LABEL` in
  `app/grounding.py`, which everything else imports, and the moment card's
  markup is the only other place the words are written as copy.
  `scripts/scan_copy.py` refuses them in a copy file.
- The claim count stands under the label and never apart from it. It is
  `check.claims_checked` out of `app/web/narrations.json`, which the freeze
  wrote and `tests/test_frozen_narrations.py` re-checks against `data/raw/`,
  so the number is the check's own. `showNarration` reveals the words, the
  label, the count and the play button in one step, and a slot with no usable
  count shows none of them.
- The agent's answer is the narration text exactly as `/buildup` returns it
  and nothing else: nothing before it, and after it no signature, no
  narrator's name, no label, no link and no closing sentence of its own. It
  never summarises, and if it cannot give the words in full it says so and
  gives none of them.

**The voice**

- `<prosody>` is ignored by Natural voices, pitch moves up and not down, and
  `<break>` works on one of the three voices. Those were measured, not
  inferred: an ignored control returns byte-identical audio.
- A delivery is per request, in `app/delivery.py`, keyed by persona and
  situation, because one voice does not read a goal for the listener's side
  and one against it the same way. The Buddy is never brighter or quicker when
  the other side scored, written as a comparison between its own two rows so
  it survives any pair of numbers picked by ear.
- The pronunciation table reaches the speech request and nothing else, and the
  guard is structural because neither failure announces itself.
- Vocabulary is looked up before it is heard. A spelling the dictionary gives
  more than one pronunciation for must be in `PRONUNCIATIONS` or on
  `CHECKED_NO_ENTRY_NEEDED`, so new words cannot reach a voice unreviewed.
- IBM bills the submitted length less its whitespace, which is
  `billed_characters`, and every budget is set on that count.
- The audio map is written from the files on disk rather than from the plan,
  so a run that stops part way leaves a map pointing only at real files.
- Each recording opens with half a second of silence, added by copying MP3
  frames rather than re-encoding, so the spoken samples are untouched.

**The ticket, the site and the type**

- The seats are settled: 1986 is Sec 108, Row 14, Seat 8, and 2022 is Sec 215,
  Row 9, Seat 6. They are demo fixture data, not play data, and carry no
  grounding obligation and no fourth input.
- A ticket code is a URL, `<site>/?ticket=<match>:<section>:<row>:<seat>`,
  built from the structured fields in `app/web/matches.json` so the code and
  the copy cannot drift, and each PNG is read back with a real decoder before
  it is written.
- A scanned code is a ticket only when the whole payload matches one this app
  holds. A typed seat is accepted as given, because where someone is sitting
  is theirs to state.
- There is one manual entry form, built in `app/web/manual-entry.js` and
  mounted by both screens. Reading a code does not start the match: Enter
  match on the ticket screen does.
- The camera needs a secure context, so the scanner works on the live site and
  on `localhost` and not off the filesystem.
- The label type scale is 13, 14 and 16 px, the manual entry fields are 16 px
  so iOS does not zoom on focus, and `user-scalable=no` and
  `maximum-scale=1.0` are gone from every screen because either one alone
  blocks pinch to zoom.
- The `<script id="tailwind-config">` block is one block and stays
  byte-identical across the screens; the design system rests on that. It
  carries `type="text/tailwind-config"`, so a browser parses it and does not
  run it, and `scripts/build_tailwind.py` compiles `app/web/tailwind.css` from
  it with Tailwind 3.4.17 and the forms and container queries plugins. The
  compiled file is committed, CI does not build it, and the step that fails on
  a dirty tree is what catches a stylesheet that no longer matches its config.
- Nothing a screen loads comes from another origin. The stylesheet, the four
  font families with every subset, jsQR and the icon set are committed, and
  `scripts/fetch_fonts.py` and `scripts/fetch_vendor.py` are the two scripts
  that reach outside to refresh them. jsQR's Subresource Integrity hash is
  checked at fetch time rather than at load time, because the script is same
  origin now.
- The mark is "Prelude." in Syne ExtraBold, white, with the "u" drawn as seven
  amber bars and the full stop amber. The icon is those seven bars alone, and
  they are outlines rather than text: an icon is rendered with no font
  loading. `scripts/brand/build_svg.py` draws every brand file from one set of
  numbers, with the two variable fonts committed beside it, and
  `scripts/make_icons.py` writes the icon set from two of them, reaching
  nothing. Both compare with `--check`, which `tests/test_the_mark.py` runs,
  and the two colours are read back out of the config block there. A PNG is
  compared pixel by pixel and not byte by byte, because Pillow encodes the
  same image a few bytes differently on Windows and on the Linux runner.
- The launch screen is the first frame of every load of the shell. The markup
  ships visible and the mark is inline, so it is up before any script has run
  and before any request of its own has been answered; it is one `role="img"`
  named "Prelude. Leave your seat. Stay in the game." that claims nothing, and
  the shell reads no storage at all. It is held 1.5 seconds on every full
  load, then fades over 300 ms once `data-matches-loaded` says matches.json
  was answered, and it is off the screen by 2.5 seconds whatever the list did:
  the cap bounds the screen rather than the start of the fade, so the fade
  begins at 2.2 seconds. Reduced motion gets the same hold and no fade.
- The launch screen is also eleven PNGs, one per iPhone screen in portrait,
  linked by the shell as `apple-touch-startup-image` behind a media query
  naming the screen's CSS size, its pixel ratio and portrait. iOS takes one
  only where the file is exactly that screen's own pixel size, and shows it
  while a web app opened from the home screen is starting. They are drawn by
  the brand script from `launch_layout`, which is the shell's own CSS rules as
  numbers, rather than from `prelude_launch.svg`: a screen that is not 390 by
  844 is not that file stretched, because the mark stays 300 CSS px wide and
  the CSS does not scale it. The two copies of those rules are held to each
  other by a screenshot: `tests/browser/test_the_launch_screen.py` measures
  the drawing the shell paints against `launch-1170x2532.png`.
- The shell says it is a web app, in `apple-mobile-web-app-capable` and
  `mobile-web-app-capable`, without which iOS opens the home-screen icon in
  Safari's chrome and shows no startup image at all. Its status bar is opaque
  black and not translucent: translucent puts the page under the bar, and the
  screens read their safe-area insets inside the shell's iframe, where `env()`
  is zero and nothing would move out of the way. The manifest's
  `background_color` is the colour the startup images are drawn on, so Android
  opens the same way.
- The desktop stadium backdrop applies only above 501 px, and `body` is
  transparent above that breakpoint or the shell's base layer paints over it.
- The repo is private and the site is public. Pages from a private repo is a
  paid-plan feature, so anything `README.md` offers as evidence has to be
  runnable from a clone rather than from a GitHub link.
- No screen claims a sensor, a feed or a connection the code does not have.
  Four lines did, and two pills said the play data was connected and
  synchronising; `scripts/scan_copy.py` holds a pattern for each so none can
  return, and `scripts/check_match_copy.py` fails on any screen carrying the
  GPS badge. Both pills read "PLAY-BY-PLAY DATA" now, which is the phrase the
  list card already used for what the app holds.
- The share button sends a link and a line of text, and says so. It offered a
  clip, and there is no clip in this repo and no code that cuts one; the old
  label is a banned string in `scripts/scan_copy.py`. With a share sheet the
  sheet is handed the title, the match's own line and the card's URL. Without
  one the link goes to the clipboard and the button says "LINK COPIED" only
  once that write has resolved: `navigator.clipboard` is undefined outside a
  secure context and `writeText` can be refused, and neither says anything.
- A Material Symbol span holds a ligature, not a word, so one inside a control
  whose name comes from its contents is read out before the label. The two
  buttons in the moment card's deck were named "ios_share SHARE" and
  "replay_10 REPLAY 10S"; both icons carry `aria-hidden` now. Every other
  icon in the app is still inside its control's name, which is under Open
  items.
- A line of match copy that describes the play carries a `grounding` block,
  and the block is a claim about those words rather than about the goal:
  every key in it is read against `data/raw/`, every key has to be said in the
  words beside it, and every claim in the words has to have a key.
  `scripts/check_match_copy.py` holds all three, and a line anywhere else in
  `app/web/matches.json` that makes one of those claims fails for having no
  block behind it. The moment card's broadcast quote was the copy this came
  out of: nothing read it out of the data, and the 2022 one said a pass went
  "back to Mac Allister" where the feed records it going 36 yards forward.

**Credentials, and what nothing may read**

- The live credentials are outside the repo, at `~/.prelude/.env` or wherever
  `PRELUDE_ENV_FILE` points, read by `app/credentials.py` and nothing else. A
  path inside the working directory is refused rather than read, nothing
  prints a value, and the process environment wins over the file. `CLAUDE.md`
  carries the rule.
- The `.env` entry in `.gitignore`, the one in `.bobignore` and the
  `Read(./.env)` deny rule in `.claude/settings.json` stay as a second layer,
  for a file created at the repo root by habit. None of them is the live
  location.
- The hosted service reads no credentials and no environment variable. The
  commit `/health` reports arrives as a file the build writes.
- The tests make no network call. `tests/conftest.py` replaces `urlopen` and
  `socket.connect` with functions that raise, and loopback is the one
  exception, recorded in `LOOPBACK_HOSTS` with the reason.

**How work is checked**

- A task is not done until CI is green on its last commit, and green CI is
  necessary and not sufficient. `CLAUDE.md`'s "Before you report" says which
  of its items CI runs and which are read by hand.
- The slot rule is written twice, so the seven rows live in
  `tests/slot_rows.json` and both copies are held to that one table. Any rule
  written twice is held to the first copy by a table or by a read.
- A test value is a literal written next to the check, never derived from
  another value. Derived test data once made a passing run read as a defect.
- `tests/browser/` writes down no expected words and no expected file: the
  slot comes from `app.api.slot_for`, the words from
  `app/web/narrations.json` and the file from `hero.audio`. Three rules are
  asked of every frame a `MutationObserver` recorded, not only of the state
  the card settled in.
- A path a doc names before it is written goes on `DELIBERATELY_ABSENT` in
  `scripts/check_docs.py`, and the check runs both ways: when the file
  appears, the gate fails until the plan entry is rewritten as built work.
  The same list carries the other direction, for a path a task record names
  because the file existed when the record was written and a later task
  removed, and `SINCE_REMOVED` does the same for a line of screen copy. A
  record is not edited as the code moves on, so the list moves instead.
- Four of the five gates have no test of their own: their evidence is the
  counts they print and their exit code, and `docs/VERIFICATION.md` says so.
  `scripts/check_match_copy.py` is the exception, because its three rules
  about the words are a reading of the feed rather than a string comparison:
  `tests/test_match_copy_claims.py` moves one value at a time off the feed
  and asserts the gate reports it.
- Shawn is asked whether to continue at the end of each task, after the exit
  commands have run.

**What is reserved or left alone**

- The EventFeed and moment-detection module is Bob's. Further work on moment
  detection is his, including the three orchestrator functions with no caller
  (`phase`, `score_state` and `outcome`), which stay where they are.
- 2022 defining moments are periods 1 to 4 only, because a shootout has no
  buildup to narrate. `Moment` carries no period field.
- A set piece is narrated from `buildup`, which reaches back a possession, not
  from a widened `event_window`. A penalty's own possession holds one event,
  the kick.
- Match and season ids are resolved at runtime from the data, never hardcoded
  from memory.

### Settled decisions: the session model

These are decided, not open. Changing any of them changes what the app claims.

#### The app is always live

No screen says "demo", "historical", "archive" or "replay". The app presents a
match in progress, and `scripts/scan_copy.py` keeps those words out of the
screens and `matches.json`.

**That framing covers the clock and the LIVE tag, which describe the match,
and it covers nothing else.** It did not cover a badge claiming a satellite
fix, a button offering to sync live audio, a status line claiming a connection
and a readiness, or a confirm button saying it had connected to a venue feed.
Those four are gone and are in `scan_copy.py`'s banned list.

#### Two stages, then a single event

**Stage 1 is a list of today's events.** Both matches appear as pre-match
cards: teams, stadium, kickoff time and 0-0. Nothing from after kickoff is on
it, so no clock, no GPS badge and no date. Kickoff times are read from the
match index, 19:00 for 1986 and 17:00 for 2022, and `check_match_copy.py`
verifies them and the 0-0 against it.

**Stage 2 is one event for the session.** Confirming a card, or scanning a
ticket, fixes the match for the rest of the session; Live, the moment card and
Moments then show only that match. The match travels in the query string, for
example `?match=3869685`, and with none in the URL the default is 1986. Scan
ticket opens the scanner rather than the list, because a scanned ticket names
its own event. A
small "Change event" link on Live goes back to the list.

**The seat belongs to the ticket screen and to Live.** It is the fan's own
ticket rather than a claim about the match, which is why it carries no data
obligation. The badge that read "AT VENUE, GPS" beside it is gone from every
screen: `CLAUDE.md` names GPS presence as one of the three inputs and no code
in this repo reads a position.

#### One session clock

Each match has a `session_clock` sitting at its hero moment: the 55th minute
goal for 1986, Di Maria's for 2022. It is the single "now" for the session, and
no screen shows anything after it.

#### Live has two states

| | Before heading out | After the moment |
| --- | --- | --- |
| 1986 | 2H 52', ARG 1-0 ENG (was 48', 0-0; Bob's Task 8) | 2H 55', ARG 2-0 ENG |
| 2022 | 1H 35', ARG 1-0 FRA | 1H 36', ARG 2-0 FRA |
| Prompt | READY FOR BUILDUP, HEADING OUT | BUILDUP READY, OPEN THE BUILDUP |

Heading out is what moves the clock: it marks the moment reached and opens the
moment card. Returning to Live keeps the advanced clock and score, and the
step-away prompt has become a way back into the buildup. The state lives in
`sessionStorage` keyed by match, so it survives navigation without riding in
the URL; blocked storage degrades to the pre-moment state rather than throwing.

Both scores are recomputed from the events rather than trusted: the after score
counts goals at or before the clock, the before score counts goals strictly
earlier.

#### Moments stops at the clock

Moments lists only what has happened by the session clock, chronologically,
with the count following the list and the subtitle "Tonight so far".

| Match | Shown | Left off |
| ----- | ----- | -------- |
| 1986 | 2H 51', 2H 55' | Lineker's 81' |
| 2022 | 1H 23', 1H 36' | 2H 80', 2H 81', ET 108', ET 118' |

Chronological order is deliberate. Leading with the hero would rank one goal
above the others, and that is a verdict the app does not get to make.
`check_match_copy.py` fails if any entry falls after the clock.

#### The repo is private, the site is not

`github.com/sh4wnbk/prelude` is private. GitHub Pages is still enabled and the
site is still public: `https://sh4wnbk.github.io/prelude/` serves 200 to an
unauthenticated request, and the Pages config reports `public: true`.

Two consequences worth knowing. Pages from a private repo is a paid-plan
feature, so losing that plan would take the site down without any commit
causing it. And the source is no longer browsable alongside the demo, so the
live URL is the only thing a reader can reach: anything the README promises as
evidence has to be runnable from a clone, not a GitHub link.

### Verifying the app in a browser

`tests/browser/` is the standing answer and is run by naming it. What follows
is what a hand run still needs to know, because none of it is derivable from
the screens.

**Serve it, do not open the files.** `match-content.js` fetches
`app/web/matches.json`, so a screen opened off the filesystem fails that fetch
and falls back to inline copy. The fallback is deliberate and quiet, which
means a filesystem run looks like a working app while confirming almost
nothing. Serve `app/web/` instead:

    ..\..\.venv-prelude\Scripts\python.exe -I -m http.server 8099 --bind 127.0.0.1

The `?v=__V__` placeholder stays literal when the app is served this way,
since CI substitutes it only on deploy. The server ignores query strings, so
every asset still resolves.

**`data-match-rendered` on `documentElement` is the signal** that a screen
rendered from `matches.json` rather than falling back. Wait for it before
reading any value. It is not enough on the moment card: the narration arrives
in a second fetch of `narrations.json` that lands after that attribute is set,
so wait for the narration to equal the served slot's text by value.

**The state keys.** The step-away state is `sessionStorage` under
`prelude.moment.<match_id>`, set to `"1"`; a typed seat is JSON under
`prelude.ticket.<match_id>`; the allegiance and the name are
`prelude.listener.<match_id>` and `prelude.name`, per session; and the
narrator is `prelude.narrator` in `localStorage`, which outlives the tab.

**A delay has to be the server's, not the driver's.** A `time.sleep` inside a
Playwright route handler blocks the driver's own event loop, so a check
written that way reports a state that has already moved on.
`tests/browser/server.py` is where a delay, a refusal or a silence is set per
file, and it answers byte ranges `206` the way GitHub Pages does.

**Driving the scanner.** A camera cannot be clicked, so a QR image becomes a
`.y4m` clip and Chromium is launched with
`--use-fake-device-for-media-stream` and `--use-file-for-fake-video-capture`.
Edge on Windows ships no usable `BarcodeDetector`, so a real browser here
always takes the jsQR path; that branch is covered by substituting a stub
detector, one that works and one that fails. A denied camera is simulated by
making `getUserMedia` reject with the error name the browser would use.

**Four measurements that look like defects and are not.** Each one produced a
false failure before being run down, and each will recur:

- **Decorative glows read as horizontal overflow.** Each card carries an
  absolutely positioned blur outside its own box and clips it with
  `overflow-x: hidden`, while `getBoundingClientRect()` reports the unclipped
  geometry. The claim that matters is whether the document scrolls at all.
- **The framed body measures 422 px, not 390.** Above the 501 px breakpoint
  `phone-frame.css` sets `box-sizing: content-box` with a 16 px bezel, so the
  border box is 390 plus 32 while the screen area is exactly 390. Read
  `body.clientWidth`, not the bounding rect.
- **An icon in a downscaled screenshot reads as a missing glyph.** At 390 px
  the Live icons are 13 and 14 px, and a review copy scaled down turns them
  into featureless boxes. Judge an icon from the rendered file at full
  resolution.
- **A `wait_for_function` predicate that throws fails the wait outright.** A
  predicate reaching through `document.documentElement` or `getElementById`
  runs while the page is still navigating, so it must answer false rather than
  throw. A faster machine hits a window a slower one never does.

One further non-defect: the Moments filter row clips its last chip at 390 px,
because that row scrolls. The browser's own `/favicon.ico` request used to be
the second; every screen declares the mark now, so the browser stops guessing
and nothing 404s.

### Open items

Nothing here is blocking, and each item says what it would take. Six groups:
the doc pass, Shawn's listening pass over the six recordings, the two narrow
readings a tuning pass would widen, where the fallback six and the candidate
runs are, and the two accessibility items from Phase 2. The headings say
whose each one is.

#### For Phase 7's doc pass

Found while clearing the register and deliberately not fixed, because the
sweep stops here. Each one is a sentence or two, and none of them is wrong
about anything a fan or a judge touches:

| Where | What to settle |
| ----- | -------------- |
| `docs/VOICE.md`, "The four prosody fields are empty and marked unconfirmed" | `Persona` no longer carries those four fields: the delivery moved to `app/delivery.py`, eight rows, and all three personas carry `prosody_confirmed` true |
| `docs/VOICE.md`, "the only thing that can be stated while the table is empty" | the delivery table is full, so the sentence should say that the comparison is the right shape now that it is, not that it is all that can be said |
| "holds no values" in four more places | `.env.example` line 1, `docs/bob_brief.md`, `docs/IBM_STACK.md` and `README.md` still say it; the two Shawn approved are changed and these four are not |

#### Still open from Phase 5: Shawn listens to the six

**The six recordings are in the repo and the moment card plays them.** No
prosody is tuned until they have been heard. What to listen for, which is the
last line of Task 15: Di María, Álvarez, MacAllister, Cuciuffo and Beardsley,
and the pacing.

| File | Voice | Who hears it |
| ---- | ----- | ------------ |
| `3750191_storyteller_neutral.mp3` | Emma | a listener with no side, 1986 |
| `3750191_buddy_scored.mp3` | Ethan | a fan of Argentina, 1986 |
| `3750191_buddy_conceded.mp3` | Ethan | a fan of England, 1986 |
| `3869685_storyteller_neutral.mp3` | Emma | a listener with no side, 2022 |
| `3869685_buddy_scored.mp3` | Ethan | a fan of Argentina, 2022 |
| `3869685_buddy_conceded.mp3` | Ethan | a fan of France, 2022 |

They are in `app/web/assets/audio/` and can be played from there, or in the
app: open the moment card, answer "Who are you with" to hear that listener's
own telling, and the text on the card is the words the voice reads.

**What a retake would cost.** The six are 2,403 billed characters, so a full
rerun of all six is that again against the monthly allowance, and one slot
alone is 324 to 485. `scripts/tts_hero.py --plan` prints the figure without
sending anything, and a rerun of one file is not built: the script sends all
six. Re-recording after a wording change means the words change first, which
is `scripts/authored_narrations.py` and then
`scripts/freeze_narrations.py --authored --confirm`.

**The pronunciation table is the first thing a listening pass reaches.** It
holds `lead`, `minute`, `close` and `di`, and "minute" has still never been
spoken: the header says no minute, so nothing in these six says that word.
`app/pronunciation.py` has the reasoning and `scripts/check_vocabulary.py`
collects the six, so a word added to a narration arrives for review before it
reaches a voice.

#### What the reading of the six left open, if a tuning pass follows

Two readings in `app/narration_grammar.py` are narrower than the words a
writer naturally reaches for, and both were found by the six rather than
argued about:

| Said | What happens | What it would take |
| ---- | ------------ | ------------------ |
| "past Beardsley, on into the final third" | the place is read as being about the dribble past Beardsley, which is thirty yards short of it | `_about` may look at the move after a place when the move before it does not hold |
| "beat Butcher on the right" | "beat" is not a dribble claim, so Butcher is a bare name and the place is read off England's record | "beat" joins `PAST_MARKERS`, which makes it a claim everywhere it is said |

Both are Shawn's call and neither is needed by the six as they stand: the two
1986 lines say "past Butcher in the final third on the right" instead, which
is the same claim about the same records in words the reading can pair. The
wordings that met those refusals are kept in
`tests/test_authored_narrations.py`, so a change to either reading fails there
first.

**Rule 18 and the eight references.** The opener rule asks the first word to
name a player, a team or a country the records hold, and four of the eight
references open elsewhere: the 1986 and 2022 Argentina Buddies on "We", the
1986 Caller on "It" and the 2022 France Buddy on "In". They are still the
standard for the writing and are still checked word for word. Whether rule 18
should reach them is open and nothing has changed them.

**The Caller has a style and no recording.** `hero.voice_for` sends no
listener to it, so there are six slots rather than eight. Its style is in
`app/goal_call_prompt.py` and its two reference narrations are in
`tests/test_reference_narrations.py`, so adding the recording later is a
change to `hero.voice_for`, one more narration per goal and two more calls,
and not to the writing.

#### The fallback six and the model runs, which are not these

`scripts/fallback_narrations.py` holds the six Shawn kept from the first run
of 2026-11-05 and `docs/narration_runs/fallback_2026-11-05.md` is their
re-check. All six of those ground and none of them places the move, which is
what Task 14 built the places rule for; they are the earlier answer to the
same question and are kept because a run is never the only copy of a
narration.

`docs/narration_runs/authored_2026-11-07.md` is the six that are frozen, read
against the records, and the per-goal narration `openai/gpt-oss-120b` wrote is
still in `app/web/narrations.json` beside them and still re-checked by
`tests/test_frozen_narrations.py`.

#### The candidate runs, and where they are

**No watsonx call was sent in Task 15.** The review files outside the repo are
as Task 14 left them:

| Where | What is in it |
| ----- | ------------- |
| `C:\Users\shawn\prelude-review\narrator_candidates_2026-11-05.md` | Task 14's one kept candidate (2022 `buddy_conceded`) and the carried 2022 Storyteller |
| `C:\Users\shawn\prelude-review\narrator_candidates_2026-11-05.before-task14-20261105T2027.md` | the zones run's eight, including the five 1986 ones Task 14's run replaced |

**Copy both aside before any rerun.** It is still not automated.

**The rerun command, if a slot is to be asked again.** A slot a run produces
replaces its older self and a slot it does not touch is carried across:

```
.\.venv-prelude\Scripts\python.exe -I scripts\narrator_candidates.py --confirm --match 3750191 --slot buddy_scored --reasoning-effort low --per-slot 3 --max-retries 2 --max-total-tokens 20000
```

`--plan` prints what it would spend and sends nothing; `--confirm` sends it.
A run now also refuses a grounded telling that does not open on a name, which
is rule 18 and `opener_missing`.

#### Phase 5 backlog
Items found during Phase 2 that belong with the wiring, not before it:

- **Every icon in the app is inside its control's accessible name.** A
  Material Symbol span holds a ligature, and Chromium reads it as a word:
  measured on 2026-11-15, the Live nav link is named "sensors LIVE" and the
  Moments one "auto_awesome_motion MOMENTS". Task 34 fixed the two buttons in
  the deck it was changing, by adding `aria-hidden="true"` to the icon span,
  and the same one attribute fixes every other one. It is a sweep over seven
  screens and the markup `app/web/match-content.js` builds, and it wants the
  browser suite to assert the names rather than the text, which
  `tests/browser/test_sharing.py` shows the shape of.
- **Keyboard focus states.** `docs/DESIGN.md` records that focus is defined only
  on the picker's text inputs. Every button in the system has no focus style,
  and the toggle at `prelude_04_moments.html:263` sets `focus:outline-none` with
  no replacement, so it has no visible keyboard focus. This is a real
  accessibility gap and a cheap win on the design and usability axis.
- **The empty placeholders, what is left of them.** The moment card's
  `#timerReadout` fills while the recording plays, and so does the Moments
  hero card's clock, since Task 32 gave both screens one player. The Moments
  meta badges are still present and empty, and so is the clock on a card with
  no recording, which is correct: there is no time to show.

#### Still open: what the build does not say

- **CI does not run on a schedule.** A push is the only thing that runs it, so
  a dependency that breaks under a new release is found by the next push
  rather than by a nightly run. That is a decision about Actions minutes on a
  repository that is still private.
- **The smoke workflow cannot be made to fail by a failing deploy.** It is
  skipped when the Pages job did not succeed, which is right, but that means a
  deploy that succeeded and published the wrong thing is the only case it
  catches. A Pages job that fails is already red on its own.
- **The smoke subset does not open the launch screen.** It checks the moment
  card, the label, the claim count, the play button and the three endpoints
  against the live site. The first frame of a visit is covered by
  `tests/browser/test_the_launch_screen.py` against the working tree and by
  nothing against the deployed one.

## Next first action

**The app is finished for the demo, it claims only what the code does, and the
build checks it.** The four overclaiming lines and the two pills beside them
are gone, every line that describes the play is held to the feed both ways,
the moment card says how many claims the check traced, the screens carry their
own stylesheet, fonts, icon and QR reader, the Moments hero card's waveform
follows the voice, the shell opens on the mark and the tagline and holds them
there, a home screen opens on the same screen drawn as a startup image, and
the API rebuilds only when something it serves changes. CI runs both suites
and the five gates on every push and the smoke workflow checks the deployed
site and the hosted API after every deploy.

**The first action is the Phase 7 README pass.** `README.md` is the document a
judge reads first and the one that has been edited least against the code.
Task 32 fixed only the lines it made false, which was the Profile line, the
moments waveform line and the paragraph about the hosted API, and Task 33 only
added the mark, the two scripts that draw it and the grounding rule to the
copy gate. What the pass still needs, in this order:

1. **Read it against the app as it is now.** The playback paragraph and the
   "what is not built" list were corrected in Task 30, three lines in Task 32,
   and the rest has not been read since Phase 5. `scripts/check_docs.py`
   checks the paths, the counts, the test citations and the dashes in it; the
   prose is not checked and that is where the drift is.
2. **Say what the build does.** Nothing in `README.md` mentions CI, the
   browser suite or the smoke workflow, and a judge reading it has no way to
   know the claims in it are checked on every push.
3. **Say what the app now shows.** The claim count under the label is the
   metric the audit asked for and `README.md` does not mention it; neither
   does it say that no screen loads anything from another origin. The mark,
   the launch screen and the tagline went in with Task 33 and the launch
   screen's timing and the home-screen startup images with Task 34, and those
   are the one part of this item that is done.
4. **The four "holds no values" passages** in `.env.example` line 1,
   `docs/bob_brief.md`, `docs/IBM_STACK.md` and `README.md`, which the open
   item above has been carrying since Phase 5.

**Then Phase 7's remaining bullets**, which `docs/history/the_plan_as_agreed.md`
carries in full: Shawn records the film and finishes the deck, exports
Bobalytics once at the end of the lab period, makes the repo public and
submits; Claude Code fills the judging-criteria-to-evidence table and does a
final recon from a fresh session. The Bobcoin figures for eleven of the
sixteen rows in `bob_sessions/README.md` come from that export.

## Last task: Task 34, the share button and the launch screen

**What Shawn asked for on 2026-11-15.** Four things, two about the moment
card's share button and two about the launch screen. The button said "SHARE
CLIP" (`removed`) and shared a link and a line of text; where the browser had
no share sheet it flashed a confirmation for 1.5 seconds and did nothing. The launch
screen had no hold, so a fast load painted the mark and took it away inside a
couple of hundred milliseconds. And a home-screen icon opened on a white
screen, because nothing told iOS the app was one.

**The share button** (`84dcbeb`). It reads "SHARE", which is what it does.
With a share sheet, `navigator.share` is handed the title, the match's own
line out of `hero.share_text` and the card's URL, unchanged. Without one the
link goes to the clipboard and the button says "LINK COPIED" only once that
write has resolved. There are two ways for nothing to have been copied, and
the old branch announced success in both: `navigator.clipboard` is undefined
outside a secure context, so reaching `writeText` throws, and `writeText`
itself can be refused, so it rejects. Neither says anything now. "SHARE CLIP"
is a banned string in `scripts/scan_copy.py`, which caught the comment that
explained the change and is why that comment does not quote it.

`tests/browser/test_sharing.py` drives both paths on both matches: the sheet
stubbed and recording what it was given, the sheet absent and the clipboard
read back with `readText`, the clipboard refusing, and the clipboard gone
altogether. The line is read out of `app/web/matches.json` rather than written
down. The confirmation is asked of every frame a `MutationObserver` recorded,
because a line that flashed for 80 ms is a line a fan can read.

**The accessible name, found while writing that test** (`84dcbeb`). A Material
Symbol span holds a ligature, not a word, and it was inside the button's name:
Chromium computed "ios_share SHARE" for this button and "replay_10 REPLAY 10S"
for the one beside it, measured through the role selector rather than read off
the markup. Both icons carry `aria-hidden="true"` now. Every other icon in the
app is still inside its control's name, which is one attribute each over seven
screens and is under Open items rather than done here.

**The launch screen's timing** (`84dcbeb`). Three numbers instead of two, in
`app/web/index.html` and in `docs/DESIGN.md`: a 1,500 ms hold on every full
load, a 300 ms fade, and 2,500 ms as the last moment a fan can see it. The cap
bounds the screen rather than the start of the fade, so the fade begins at
2,200 ms. The clock is `performance.now()`, which counts from the start of the
navigation, so both bounds are about the load the fan started rather than
about whenever the script ran. Reduced motion gets the same hold and no fade.
What is left of the hold is rounded up before it is asked for, because
`setTimeout` truncates a fractional delay: CI caught the fade starting at
1,499.7 ms against a 1,500 ms hold, which is the truncation and nothing else.

Measured in headless Chromium at 390 by 844, as the moment the fade began and
the moment the screen left the page: 1,507 and 1,809 ms with matches.json
answered at once, 1,589 and 1,891 ms with it delayed 1.5 s, 2,209 and 2,510 ms
with it refused, and no fade and 1,507 ms with reduced motion.

**The startup images** (`71dbc4c`). iOS shows an `apple-touch-startup-image`
while a web app opened from the home screen is starting, and it takes one only
where the file is exactly that screen's own pixel size. `IPHONES` in
`scripts/brand/build_svg.py` is eleven screens in portrait, read off Apple's
point sizes, covering every iPhone on a current iOS; the script draws one PNG
each into `app/web/assets/launch/`, 560 KB in all, and the shell links each
behind a media query naming the CSS size, the pixel ratio and portrait. The
ratio is in the query because two iPhones share 414 by 896 at two ratios and
the wrong one of those is a quarter of the pixels. The shell also carries
`apple-mobile-web-app-capable` and `mobile-web-app-capable`, without which iOS
opens the icon in Safari's chrome and shows no startup image, and an opaque
black status bar rather than a translucent one: translucent puts the page
under the bar, and the screens read their safe-area insets inside the shell's
iframe, where `env()` is zero. The manifest's `background_color` was already
`#101319`, which is the colour these are drawn on, and a test now reads the
corner pixel of one against it rather than taking both from the same constant.

**They are drawn from the layout, not from `prelude_launch.svg`.** A screen
that is not 390 by 844 is not that file stretched: the mark stays 300 CSS px
wide on every screen because the CSS does not scale it. `launch_layout` is
those rules as numbers and `app/web/index.html` is the same rules in CSS,
which is two copies of one thing, so
`tests/browser/test_the_launch_screen.py` screenshots the shell at 390 by 844
at three device pixels to the CSS pixel and measures the drawing in it against
`launch-1170x2532.png`.

**That comparison found the one real difference.** The block was being centred
on the tagline's 16 px type where the CSS centres its 20 px line box, which
put the mark 2 CSS px below where the shell paints it. `prelude_launch.svg`
moves by those 2 px and the three renderings are one layout now. Measured
after the fix: the white box agreed to within 1 device pixel and the amber box
to within 3, the amber being the tagline, whose outermost column and lowest
descender row the browser leaves fainter than the threshold.

**The glyphs are rasterised from their own outlines.** No font is loaded to
draw a startup image: `fontTools` gives the contours, a pen flattens the
curves, and Pillow fills each shape even-odd so a counter in a letter is a
hole, oversampled four times and reduced. The seven bars are capsules, as the
icon's are. `--check` compares a PNG pixel by pixel and not byte by byte, for
the reason `scripts/make_icons.py` measured in Task 33, and the Linux runner
agreed with this machine on all eleven.

**The evidence.** `pytest -q` reports `2085 passed`, up from `2067`; `pytest
tests/browser` reports `100 passed`, up from `88`; all five gates exit 0;
`git status` is clean after both. `scripts/brand/build_svg.py --check` reports
every committed brand file is what the numbers draw, the eleven startup images
included, and the Linux runner agreed with this machine on all eleven. CI is
green on the last commit of this task.

**Found, not fixed.**

- **Every icon in the app is still inside its control's accessible name.**
  Measured on 2026-11-15: the Live nav link is named "sensors LIVE" and the
  Moments one "auto_awesome_motion MOMENTS". The two in the deck Task 34
  changed are fixed and the rest are a sweep over seven screens plus the
  markup `app/web/match-content.js` builds. It is under Open items with what
  it would take.
- **The startup images are 560 KB.** Each is a flat background and a band of
  anti-aliased drawing, and it is the band that costs: measured on
  2026-11-15, quantising one to a 256-colour palette took it from 51,633
  bytes to 24,665, which would halve the set. It was not taken, because it
  puts a quantiser between the drawing and the check that says the committed
  file is what the numbers draw, and the whole set is reproducible to the
  pixel as it stands.
- **Nothing here has run on an iPhone.** Every claim about the startup images
  is about the files, the links and the media queries: that each file is the
  pixel size its query names, that the drawing in it is the drawing the shell
  paints, and that the shell says it is a web app. Whether iOS picks the
  right one of the eleven is a thing only a device shows, and no device was
  used. The eleven screens and the query form are read from Apple's point
  sizes rather than measured here.
- **The cap is 2,500 ms and the screen left the page at 2,510.** A
  `setTimeout` is a floor and not a ceiling, so 10 ms is what nothing in the
  page can take off; the browser suite allows the runner's own scheduling on
  top of that and the measurement is in `docs/DESIGN.md`.
- **A launch screen that is interrupted is not covered.** The suite drives a
  load, a reload, a new tab, a slow list, a refused list and a list that
  never answers. A fan who navigates away inside the hold, or whose tab is
  backgrounded so the timers are throttled, is not among them.
- **`prelude_launch.svg` is committed and nothing at runtime serves it**, and
  **the icon font is still 1.14 MB of the committed fonts**, and **the smoke
  subset does not open the launch screen**, and **the compiled stylesheet is
  not rebuilt by CI**, and **CI does not run on a schedule**, and **the smoke
  workflow cannot be made to fail by a failing deploy**. All six are Task
  33's, Task 32's and Task 30's, and all six still stand.

## History

`docs/history/` holds every task record before the one above, unchanged.
`docs/history/README.md` is the index and the ledger of where each archived
decision now lives.

| File | What is in it |
| ---- | ------------- |
| `docs/history/task_32_what_the_app_claims.md` | the four lines that claimed more than the code does, the claim count under the label, the compiled stylesheet and the committed fonts, one player for both screens, the first mark and the first launch screen |
| `docs/history/task_33_the_brand.md` | the brand given to the build, the icon set drawn from it, the launch screen, the broadcast quote removed and the six lines of match copy that were not held to the feed |
| `docs/history/phase1-3_scaffold_data_and_eventfeed.md` | the scaffold, the fetch, the data check, and Bob's EventFeed |
| `docs/history/phase4_narration_and_orchestrator.md` | the provider layer, the prompt, the grounding check, the personas, the model comparison and the orchestrator |
| `docs/history/phase5_voice_and_the_six.md` | the Text to Speech probe, the pronunciation table, the hero run that was refused, and the freeze |
| `docs/history/task_30_the_browser_suite_and_the_build.md` | the play button that waits for its words, the Moments hero card's recording, `tests/browser/`, CI on every push and the smoke workflow |
| `docs/history/data_check_and_screen_scan.md` | what the data said, and the copy claims that did not survive it |
| `docs/history/deviations.md` | where Phases 1 and 2 departed from the task list |
| `docs/history/the_ticket_flow_and_the_published_site.md` | the tickets, the scanner, the ticket screen, the deploy, the type scale and the backdrop |
| `docs/history/verifying_the_app_in_a_browser.md` | the hand-rolled browser method `tests/browser/` replaced |
| `docs/history/the_plan_as_agreed.md` | the Plan, task by task, and the Phase 5 to 7 outlines |
| `docs/history/tasks_11_to_29.md` | Task 29 back to the second Task 11 list |
| `docs/history/phase6_handover_and_the_doc_sweep.md` | the Orchestrate handover and the sweep that closed Phase 5 |
| `docs/history/tasks_7_to_10_and_bob_sessions.md` | the candidate runs later runs replaced, and every Bob session with its brief |
