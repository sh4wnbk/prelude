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
placeholder. `index.html` holds each screen in an iframe. The screens are the
event list (`01`), Live (`02`), the moment card (`03`), Moments (`04`), the
scanner (`05`), the ticket (`06`) and Profile (`07`).
`app/web/match-content.js` is the renderer all of them share, with
`listener-card.js`, `manual-entry.js` and `narration-player.js` beside it, and
`matches.json`, `narrations.json` and `narrators.json` as its data.

**Twenty-one modules in `app/`.** Standard library only, with one exception:
`app/api.py` takes FastAPI, and
`tests/test_api.py::TestWhatItDoesNotReach::test_the_only_module_in_app_that_takes_a_third_party_package`
is what keeps it the only one.

**Twenty-six scripts in `scripts/`**, each runnable on its own. Five are
gates: `data_check.py`, `scan_copy.py`, `check_match_copy.py`,
`check_vocabulary.py` and `check_docs.py`. `docs/HARNESS.md` carries the table
of all twenty-six, what each writes and what each reaches.

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

**The test harness** is 38 files in `tests/` and five in `tests/browser/`. The
unit suite is run by `pytest`, which leaves the browser suite out through
`norecursedirs`; the browser suite is run by naming it, `pytest tests/browser`,
and drives headless Chromium at 390 by 844 over a local server.

**The build** is four workflows. `ci.yml` runs on every push and pull request:
install, fetch the data, the unit suite, the five gates one step each, the
browser suite, and a step that fails if the run changed a tracked file.
`pages.yml` deploys on a push that touches `app/web/`. `smoke.yml` runs after
a Pages deploy succeeds and checks the deployed site and the hosted API.
`keepalive.yml` pings `/health` on a schedule, behind the `PRELUDE_KEEPALIVE`
switch.

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
  byte-identical across the screens; the design system rests on that.
- The desktop stadium backdrop applies only above 501 px, and `body` is
  transparent above that breakpoint or the shell's base layer paints over it.
- The repo is private and the site is public. Pages from a private repo is a
  paid-plan feature, so anything `README.md` offers as evidence has to be
  runnable from a clone rather than from a GitHub link.

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
- Nothing tests the gates themselves. Their evidence is the counts they print
  and their exit code, and `docs/VERIFICATION.md` says so.
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

**"At venue, GPS" belongs to Live.** It appears only after selection, never on
the list. Both matches are at the venue with a seat; the seat is the fan's own
ticket, not a claim about the match, which is why it carries no data
obligation.

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

Two further non-defects: the browser requests `/favicon.ico` on its own and
gets a 404, which nothing in the app references, and the Moments filter row
clips its last chip at 390 px because that row scrolls.

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

- **Keyboard focus states.** `docs/DESIGN.md` records that focus is defined only
  on the picker's text inputs. Every button in the system has no focus style,
  and the toggle at `prelude_04_moments.html:263` sets `focus:outline-none` with
  no replacement, so it has no visible keyboard focus. This is a real
  accessibility gap and a cheap win on the design and usability axis.
- **The empty placeholders.** The Moments meta badges, the three Moments player
  timers, and the moment card's `#timerReadout` are all present and empty,
  waiting for real values from the fixture.

## Next first action

**The app is finished for the demo and the build checks it.** Both gaps Shawn
named on 2026-11-12 are closed, `tests/browser/` keeps the browser checks that
used to be thrown away, CI runs both suites and the five gates on every push,
and the smoke workflow checks the deployed site and the hosted API after every
deploy. `CLAUDE.md` records which of its pre-report items that automates.

**The first action is the Phase 7 README pass.** `README.md` is the document a
judge reads first and the one that has been edited least against the code.
What it needs, in this order:

1. **Read it against the app as it is now.** The playback paragraph and the
   "what is not built" list were corrected in Task 30 and the rest has not
   been read since Phase 5. `scripts/check_docs.py` checks the paths, the
   counts, the test citations and the dashes in it; the prose is not checked
   and that is where the drift is.
2. **Say what the build does.** Nothing in `README.md` mentions CI, the
   browser suite or the smoke workflow, and a judge reading it has no way to
   know the claims in it are checked on every push.
3. **The four "holds no values" passages** in `.env.example` line 1,
   `docs/bob_brief.md`, `docs/IBM_STACK.md` and `README.md`, which the open
   item above has been carrying since Phase 5.
4. **The Bobcoin figures and the missing session row.**
   `bob_sessions/README.md` says nine of its figures come from the Bobalytics
   export at submission. Its table also lists fourteen sessions while fifteen
   exports are committed: `bob_sessions/phase6_task15_orchestrate_spec.md` has
   no row, and adding one needs the commit the work landed in, the commit that
   added the export and the figure, so it belongs with this pass rather than
   before it.

**Then Phase 7's remaining bullets**, which `docs/history/the_plan_as_agreed.md`
carries in full: Shawn records the film and finishes the deck, exports
Bobalytics once at the end of the lab period, makes the repo public and
submits; Claude Code fills the judging-criteria-to-evidence table and does a
final recon from a fresh session.

## Last task: Task 30, the two gaps closed, and the browser checks kept

**What Shawn asked for on 2026-11-12.** Two gaps in the app, and then a build
that catches this class of miss by itself: every browser check until now was a
script written for one task and thrown away, so a miss was found by hand or
not at all.

**The play button waits for the words it reads** (`c914857`). The recording
lands with `matches.json` and the words land with a second fetch of
`narrations.json`, so with the second one slow the card showed a blank
paragraph, no label and an enabled play button. Task 29 recorded that under
"Found, not fixed". The button now ships disabled and `whenNarrationShown` in
`app/web/match-content.js` releases it in the same step that reveals the
narration and the label; `showNarration` is the one thing that fires it, so a
`narrations.json` that fails, that holds no entry for this match or that holds
no text for this listener's slot leaves it as the markup ships it. Seven tests
in `tests/test_narration_player.py`, each run against the broken code:

| Mutation | Refused by |
| -------- | ---------- |
| the button enabled as soon as the file is known | `test_the_player_subscribes_to_it`, `test_the_player_releases_the_button_nowhere_else` |
| the reveal announcing nothing | `test_the_renderer_fires_it_from_the_reveal`, `test_nothing_else_in_the_renderer_fires_it` |
| the catch arm revealing words | `test_a_failing_fetch_leaves_the_button_disabled` |
| the subscription dropping an early caller | `test_the_subscription_survives_either_order` |

**The Moments hero card plays the fan's own recording** (`195747e`). Both play
buttons on that screen were markup that swapped an icon and promised audio
neither had. The hero goal has a recording, the one the moment card plays this
fan, so that card's button plays it and the other card's button is disabled.
`match-content.js` builds those cards, so it asks the one slot lookup which
file this fan hears and hands that button to `narration-player.js`, which the
Moments screen now loads too: the player owns the playing, the renderer owns
the markup, and a button nothing takes stays disabled, which is how both now
ship. Nine mutations, every one refused.

**The accessible names were the 1986 templates' on every card**, so the 2022
screen named Maradona over Messi and Di Maria. The renderer writes each card's
own title into its label and says no narration is recorded where there is
none. Found while wiring the buttons, not asked for.

**`tests/test_narration_waveform.py` and `tests/test_narration_scrubber.py`
now read `start()` rather than the whole player file.** The file holds two
players since the Moments button went into it, and a whole-file search answers
about whichever comes first in it. Three tests failed on exactly that and are
the reason the scope is written down.

**`tests/browser/`, seventy one tests** (`a443243`). Headless Chromium at 390 by 844
over a local server, run by naming it and left out of the default run by
`norecursedirs`. Nothing in it writes down which words or which file a fan
should get: the slot comes from `app.api.slot_for`, the Python copy of
`Prelude.slotFor`, the words from `app/web/narrations.json` and the file from
`hero.audio`.

| File | What it drives |
| ---- | -------------- |
| `tests/browser/server.py` | byte ranges answered `206` the way GitHub Pages does, and a delay, a refusal or a silence set per file |
| `tests/browser/test_the_fan_hears_their_own.py` | both matches by three listeners by three narrator states: the card's words, the player's file and the Moments hero card's file are one slot |
| `tests/browser/test_the_label_waits.py` | `narrations.json` slow, refused and never answered, `matches.json` slow and refused, a refresh and a reopened tab |
| `tests/browser/test_the_first_load.py` | nothing stored: no match chosen, the pill hidden, the five match screens sending the fan to the list, the narrator outliving the tab |
| `tests/browser/test_the_player_works.py` | the clock, the fill, the bars moving with the voice, the scrubber, the arrow keys, Replay 10s, and the server's own range answer |
| `tests/browser/test_every_screen.py` | every screen by both matches by four listener states, 56 loads |

Three rules are asked of every frame a `MutationObserver` recorded, not only
of the state the card settled in: the paragraph holds nothing or exactly the
served slot's text, the paragraph and the label are both hidden or both shown,
and the play button is disabled in every frame where the words are hidden. The
delay is the server's rather than the driver's, for the reason Task 29
recorded.

**The suite found two things on its first runs.**

- **The moment card's play button was enabled in the markup**, disabled only
  by the player, so the frames before any script had run offered a press that
  did nothing. It ships `disabled` now, with the same `disabled:opacity-40`
  treatment the rest of the app uses.
- **`tests/test_authored_narrations.py` ran the report writer**, which stamps
  the date it was rechecked, so the suite rewrote
  `docs/narration_runs/authored_2026-11-07.*` on any day but the one the
  committed report was written. It had been invisible because the committed
  copy was written the day before. `main` takes an `out_dir` now and the test
  passes pytest's temporary directory; a hand run still writes the real
  report, which was checked by running it.

**`.github/workflows/ci.yml`, on every push and pull request** (`e10a0be`):
install with uv, fetch the StatsBomb data, the unit suite, the five gates one
step each, the browser suite, and a step that fails if the run changed a
tracked file. The last step prints the wall clock time and the minutes it
bills as.

**It was red twice before it was green, and both were real.**

- **38 browser checks failed on the first run.** A `wait_for_function`
  predicate that reaches through `document.documentElement` or
  `getElementById` runs while the page is still navigating, and a predicate
  that throws fails the wait outright rather than being tried again. The
  runner is faster than the machine they were written on, so it hit a window
  that machine never did. Every predicate answers false now instead.
- **`uv.lock` was rewritten by `uv sync`**, because the dev group gained
  Playwright without re-locking. The lock is updated and both workflows
  install with `--frozen`, so a dependency added to `pyproject.toml` without
  re-locking fails the install rather than being resolved differently on every
  machine.

**What a run costs.** The three green runs took 218, 212 and 213 seconds of
wall clock, each billed as 4 Actions minutes on a Linux runner at the 1x
multiplier. The two red ones were 166 and 254: the first stopped early on the
browser suite, and the second ran everything and failed at the end. Of the 218
on `c8a884d`, the unit suite is 36 seconds and the browser suite 123, and the
install and the Chromium download are most of the rest. Minutes are not
metered on a public repository, which this one will be; on a private one four
minutes a push is the figure, so the 3,000 GitHub Pro includes is 750 pushes a
month.

**`.github/workflows/smoke.yml`, after a Pages deploy succeeds** (`d9bc232`).
CI checks the working tree; it cannot say that what a judge opens is the same
app, because the deploy stamps a version into every asset URL, Pages serves
from its own cache and the API runs somewhere else. `scripts/smoke_live.py` is
the short subset: both matches with one listener each, the frozen words under
the label, the recording the player loads, the deployed version stamped into
the assets, the same card under two seconds of latency showing no words and
offering no voice, and then `/health`, `/moments` and `/buildup`. The checkout
is the deployed commit, so the narrations it compares against are the ones the
site serves, and `/health` is given ninety seconds for a cold Render wake. The
latency is set through the DevTools protocol, because there is no server of
ours to slow.

**Its first run printed two FAIL lines and passed** (`5bd5482`). A `run` step
gets bash with `-e` and not `-o pipefail` unless the shell is named, so the
pipe into `tee` answered with `tee`'s exit code. The step names `shell: bash`
now, and the script was given a wrong version by hand to watch it exit 1. Both
failures it printed were real: the same null predicate as in the browser
suite, and a hand run comparing the site against the tip of `main`, which a
push that touches nothing under `app/web/` never deploys. A hand run reports
the version the site is serving now; a run after a deploy still holds the site
to that deploy's commit.

**`CLAUDE.md`'s "Before you report" says which of its items CI runs.**
Items 1, 2, 3, 4 and 8 and most of 6 are automated; item 5 beyond the smoke
subset, item 7 and the judgement half of item 6 are still read by hand. A task
is not done until CI is green on its last commit, and green CI is necessary
and not sufficient: a check nobody wrote still passes.

**The evidence.** `pytest -q` reports `1906 passed`, up from `1884`; the
browser suite reports `71 passed`; all five gates exit 0; `git status` is
clean after both. In CI on `52dbea7` the same numbers came back in 213
seconds, and the smoke workflow passed on its own trigger after the Pages job
for that commit: the site served version `52dbea7`, both matches showed the
frozen words under the label with the play button offered and the right
recording loaded, both showed nothing and offered nothing under two seconds of
latency, and `/health`, `/moments` and `/buildup` answered on
<https://prelude-api.onrender.com>, which reported the same commit.

**Found, not fixed.**

- **The browser suite needs three CDNs to be reachable.** The screens load
  Tailwind from `cdn.tailwindcss.com` and their fonts from Google, which is
  how they are deployed, so a blocked or slow CDN breaks the layout and with
  it the 268 px measurement. Failures from those hosts are no longer counted
  against the screens, which keeps the message honest, but a run without them
  still fails. Pinning a copy of Tailwind into `app/web/` would change what
  the deployed site loads and is a bigger decision than this task.
- **The Moments card's waveform is still fixed bars.** The hero card plays,
  and nothing on that card follows the voice: there is no clock, no playhead
  and no scrubber in its markup. The bars sit at the heights the markup gives
  them while the recording plays, which is not false, but a fan who has seen
  the moment card may expect them to move.
- **`tests/browser/` is not in the test table in `docs/HARNESS.md`.** It has
  a section of its own instead, because the table is about the unit suite and
  `scripts/check_docs.py` counts that suite. The seven test files Task 29
  listed as missing from the table are still missing.
- **CI does not run on a schedule.** A push is the only thing that runs it, so
  a dependency that breaks under a new release is found by the next push
  rather than by a nightly run. That is a decision about Actions minutes on a
  repository that is still private.
- **The smoke workflow cannot be made to fail by a failing deploy.** It is
  skipped when the Pages job did not succeed, which is right, but that means a
  deploy that succeeded and published the wrong thing is the only case it
  catches. A Pages job that fails is already red on its own.

## History

`docs/history/` holds every task record before the one above, unchanged.
`docs/history/README.md` is the index and the ledger of where each archived
decision now lives.

| File | What is in it |
| ---- | ------------- |
| `docs/history/phase1-3_scaffold_data_and_eventfeed.md` | the scaffold, the fetch, the data check, and Bob's EventFeed |
| `docs/history/phase4_narration_and_orchestrator.md` | the provider layer, the prompt, the grounding check, the personas, the model comparison and the orchestrator |
| `docs/history/phase5_voice_and_the_six.md` | the Text to Speech probe, the pronunciation table, the hero run that was refused, and the freeze |
| `docs/history/data_check_and_screen_scan.md` | what the data said, and the copy claims that did not survive it |
| `docs/history/deviations.md` | where Phases 1 and 2 departed from the task list |
| `docs/history/the_ticket_flow_and_the_published_site.md` | the tickets, the scanner, the ticket screen, the deploy, the type scale and the backdrop |
| `docs/history/verifying_the_app_in_a_browser.md` | the hand-rolled browser method `tests/browser/` replaced |
| `docs/history/the_plan_as_agreed.md` | the Plan, task by task, and the Phase 5 to 7 outlines |
| `docs/history/tasks_11_to_29.md` | Task 29 back to the second Task 11 list |
| `docs/history/phase6_handover_and_the_doc_sweep.md` | the Orchestrate handover and the sweep that closed Phase 5 |
| `docs/history/tasks_7_to_10_and_bob_sessions.md` | the candidate runs later runs replaced, and every Bob session with its brief |
