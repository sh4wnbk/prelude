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

**Thirty-two scripts**, each runnable on its own: thirty-one directly under
`scripts/` and `scripts/brand/build_svg.py` beside the two fonts it reads.
Five are gates: `data_check.py`, `scan_copy.py`, `check_match_copy.py`,
`check_vocabulary.py` and `check_docs.py`. `docs/HARNESS.md` carries the table
of all thirty-two, what each writes and what each reaches, and a row for every
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

**The test harness** is 43 files of tests in `tests/` and eight in `tests/browser/`. The
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
- The tagline is one constant, `TAG` in `scripts/brand/build_svg.py`, and
  every file that carries it is drawn from there: the wordmark, the eleven
  startup images and `prelude_launch.svg`'s title. The shell's visible line
  and its `aria-label` are the two places it exists as text, and they are
  changed together. The retired phrase is a banned pattern in
  `scripts/scan_copy.py`, so it cannot come back to a screen.
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
  named "Prelude. Leave your seat. Not the game." that claims nothing, and
  the shell reads no storage at all. It is held 1.5 seconds on every full
  load, and it is off the screen by 2.5 seconds whatever the list did: the cap
  bounds the screen rather than the start of the fade, so the fade begins at
  2.2 seconds.
- Then the mark and the event list cross: the mark fades out over 300 ms while
  the list fades in over the same 300 ms, opacity and nothing else, and the
  list is revealed in the step that starts the fade rather than before it. A
  list already up behind a fading mark is a fade and not a crossfade.
- Ready is two things and the fade waits for both. `data-matches-loaded` is
  the renderer saying matches.json was answered; `data-painted` is the framed
  screen's own, set two animation frames after its `DOMContentLoaded`, and
  says one frame has been drawn with the app background and its stylesheet
  applied. The second is what keeps the list from being revealed white.
- A request for less motion keeps the fade. An opacity fade is not motion:
  nothing on either screen moves, scales, slides or spins, so the preference
  has nothing here to be about, and what it got instead was a hard cut from
  the mark to the list, which is the one thing in the sequence that reads as a
  jolt. There is no `prefers-reduced-motion` rule in the shell and no
  `matchMedia` branch in its script; anything added later that moves belongs
  behind that query. Task 34 specified no fade under `reduce` and that was
  wrong.
- Every Material Symbols span in `app/web/` is `aria-hidden="true"`, so a
  control's accessible name is the label a fan reads and never the glyph's
  own name. The rule is asked of the browser rather than of the markup:
  `tests/browser/test_the_accessible_names.py` reads the ligatures off the
  live DOM and the names out of `aria_snapshot`, on every screen, both
  matches, three listeners and three narrator states.
- No frame of a load is white, and the three things that make it so are in
  markup rather than in script, because the frames before any script has run
  are a state a fan can see. Every page sets the app background on `html` and
  `body` in its own head in front of every `<link>` it carries, the same bytes
  in all eight. The shell's iframe carries the same colour on the element,
  because the element is painted by the shell and the head by the screen. And
  the iframe is invisible until that screen says it has painted. The top of
  the screen is sampled across the launch in five states, the worst near-white
  share measured being the light text in the list's own header, and the
  sampler is itself checked against the defect forced on purpose.
- The launch screen is also eleven PNGs, one per iPhone screen in portrait,
  linked by the shell as `apple-touch-startup-image` behind a media query
  naming the screen's CSS size, its pixel ratio and portrait. iOS takes one
  only where the file is exactly that screen's own pixel size, and shows it
  while a web app opened from the home screen is starting. They are drawn by
  the brand script from `launch_layout`, which is the shell's own CSS rules as
  numbers, rather than from `prelude_launch.svg`: a screen that is not 390 by
  844 is not that file stretched, because the mark stays 300 CSS px wide and
  the CSS does not scale it. The two copies of those rules are held to each
  other by eleven screenshots: `tests/browser/test_the_launch_screen.py`
  renders the shell at each screen's own CSS size and pixel ratio and measures
  the drawing in it against that screen's own image. The eleven rather than
  one, because the layout is not a share of the screen, so one screen agreeing
  says nothing about the arithmetic on the other ten.
- The shell says it is a web app, in `apple-mobile-web-app-capable` and
  `mobile-web-app-capable`, without which iOS opens the home-screen icon in
  Safari's chrome and shows no startup image at all. Its status bar is
  `black-translucent` and its viewport carries `viewport-fit=cover`, so the
  page is the whole screen. That is what makes the startup image and the
  screen behind it one drawing: an opaque bar gives the page the area below it
  and leaves iOS to fit the full-screen image into that smaller area, so the
  mark comes up smaller in the image than the page draws it and then moves as
  the app takes over.
- The safe-area insets are the shell's to apply. iOS reports them to the shell
  and not to the screens, which are inside its iframe where `env()` is zero,
  so the shell reads the four into `--safe-top`, `--safe-right`,
  `--safe-bottom` and `--safe-left` and pads `#frame` by them: all seven
  screens clear the clock and the home indicator at once, and the desktop
  frame takes none. The launch screen is deliberately not inset, because it is
  the drawing the startup image has to match and that image is drawn for the
  whole screen; what is asked of it instead is that the mark and the tagline
  clear insets forced to 64 px at the top and 48 px at the bottom, measured on
  all eleven screens and at an Android viewport.
- Android opens the same way, and it is Chrome that draws the first screen
  there: the icon centred on the manifest's `background_color` with the name
  under it, for a `standalone` display. All three fields are asserted and so
  is the absence of white, both icon PNGs being drawn on `#101319` and holding
  no white pixel. The browser suite runs the launch at 412 by 915 as well as
  at the eleven iPhone sizes.
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
  "replay_10 REPLAY 10S"; both icons carry `aria-hidden` now, and since
  Task 37 every other icon span in the app does too.
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
- `README.md` is the page a judge reads: pictures first, short sentences and
  a link wherever depth belongs, at most 150 lines and no sentence over 25
  words. Everything longer lives in `docs/` with one link from the README,
  and `docs/DOCUMENTS.md` is the index of all of it. A section moved out of
  the README goes into `scripts/check_docs.py`'s `DOCS` list in the same
  commit, so it keeps every check it had while it was in the README.
- The pictures in `README.md` are drawn by `scripts/make_docs_images.py` from
  the running app, not taken by hand. It serves `app/web/` itself and reaches
  each screen by tapping, so a state that cannot be reached by tapping cannot
  be photographed, and `--check` says whether the committed files are still
  what the app draws. It needs a browser, so it is not one of the five gates
  and CI does not run it.
- Shawn is asked whether to continue at the end of each task, after the exit
  commands have run.

**What is reserved or left alone**

- The EventFeed and moment-detection module is Bob's. Further work on moment
  detection is his, including the three orchestrator functions with no caller
  (`phase`, `score_state` and `outcome`), which stay where they are.
- The fan is the user and the venue operator is the customer, and
  `README.md` says so under "Who it's for". The operator's benefit is stated
  as a mechanism with no figure: spreading the rush on concessions and
  restrooms is for a pilot to measure. Nothing in the repo is built for an
  operator.
- Bob's part of Prelude is closed. Shawn took the Bobalytics export on
  2026-11-19, and one read-only session ran after it, a score against the lab
  rubric, whose 1.02 Bobcoins come from its screenshot. No further Bob session
  is planned. The module stays Bob's, and nothing replaces it.
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

- **`scripts/make_docs_images.py` is not run by CI.** A screen that changes
  leaves the README's pictures stale until someone runs `--check` by hand. It
  needs a browser, which is why it is not one of the gates.
- **The README's top row is three 780-pixel screenshots** in a three-column
  table, so GitHub shows them small. A narrower render, or two rows, would
  read better on a phone.
- **CI does not run on a schedule.** A push is the only thing that runs it, so
  a dependency that breaks under a new release is found by the next push
  rather than by a nightly run. That is a decision about Actions minutes on a
  repository that is still private.
- **The smoke workflow cannot be made to fail by a failing deploy.** It is
  skipped when the Pages job did not succeed, which is right, but that means a
  deploy that succeeded and published the wrong thing is the only case it
  catches. A Pages job that fails is already red on its own.
- **The smoke subset now opens the launch screen.** Task 35 added the mark,
  the web-app meta tags, the eleven startup images, the white sampling and the
  list up once the mark is gone, and the run after `061e2ee` held all eight
  against <https://sh4wnbk.github.io/prelude/>. What it still cannot say is
  anything about iOS: it drives headless Chromium, the same as the suite.

## Next first action

**The app is finished for the demo, it claims only what the code does, the
build checks it, and `README.md` is now the page a judge reads.** Every
overclaiming line is gone, every line that describes the play is held to the
feed both ways, the moment card says how many claims the check traced, the
screens carry their own stylesheet, fonts, icon and QR reader, the shell opens
on the mark and crossfades into the event list with no white frame, and every
icon is hidden from a screen reader so a control is named by its label. CI
runs both suites and the five gates on every push, and the smoke workflow
checks the deployed site and the hosted API after every deploy.

**The first action is item 2 of the submission checklist below.** Item 1 is
done. Nothing in the app is waiting on a change; what is left is the four
things only Shawn can do, in the order they have to happen.

**Then the rest of Phase 7**, which `docs/history/the_plan_as_agreed.md`
carries in full: Shawn records the film and finishes the deck, and Claude Code
does a final recon from a fresh session.

**Still open from Phase 5**, and unchanged by the README pass: Shawn listens
to the six recordings, and the tuning pass that would follow if one of them is
wrong. The open items above carry what each one would need.

## The submission checklist

**Kept here until Prelude is submitted, then deleted in the same commit.**
Five things, in this order, and the first two have to happen before the last
three mean anything.

| # | What | Who | Done when |
| - | ---- | --- | --------- |
| 1 | Export Bobalytics once, from User scope over the full lab period, and commit the CSV | Shawn | done on 2026-11-19: both CSVs are in `bob_sessions/`, and every row of its table has a figure; the export totals by day, so ten of them are day totals |
| 2 | Make the repository public | Shawn | <https://github.com/sh4wnbk/prelude> opens signed out |
| 3 | Turn `PRELUDE_KEEPALIVE` on, under Settings, Secrets and variables, Actions, Variables | Shawn | the variable reads `on`, and the keepalive workflow has a green run after it |
| 4 | Check the live API and the Orchestrate agent after the flip | Shawn | `/health` answers without a cold wait, and the agent answers on both matches |
| 5 | Add the demo video link to `README.md` | Shawn, or Claude Code given the link | the link is in `README.md` and opens |

**Why that order.** The keepalive is metered on a private repository, 144
minutes a day, which is why item 3 waits for item 2. The agent check in item 4
is what proves the keepalive works, so it comes after the flip rather than
before it. The Bobalytics export is first because it is the one item whose
timing is not Shawn's: it is taken once, at the end of the lab period.

**Until item 3 is done**, the standing note at the top of Current state still
applies: open `/health` by hand and wait for the ok before testing a tool,
recording the demo or handing the URL to a judge.

## Last task: the README's three claims, and the Bobalytics export

**What Shawn asked for on 2026-11-18 and 2026-11-19.** Two small changes made
outside Bob, after a Bob session on the first stopped at its 20-coin cost
limit with nothing committed.

**`d7337b4` corrected three claims in `README.md`.** The six demo narrations
were drafted with an AI assistant and edited by Shawn, so the flow now shows
them entering the grounding check beside the narration pipeline rather than
coming out of it; `scripts/make_docs_images.py` draws the same two sources and
`docs/images/architecture.png` was redrawn from it. The Bob row lists what Bob
built over eighteen sessions. The Caller is described as listed on Profile as
coming soon with no recording. `bob_sessions/README.md` gained the row for the
stopped session, and `docs/IBM_STACK.md` the same.

**This commit closes Bob's part.** Shawn took the Bobalytics export on
2026-11-19 and it is committed as `bob_sessions/bobalytics_activity_pattern.csv`
and `bob_sessions/bobalytics_days_active.csv`. It totals by day, not by
session, so of the eleven figures that waited for it, one could be read
directly: the read-only review, 2.22, which had its day to itself. The other
ten rows give their day's total and the sessions it covers. Days are UTC, and
placing each session on the UTC day of its commit makes every day's task count
match the export, 17 completed in all.

**One Bob session ran after the export**: a read-only score of the app
against the lab rubric, `00c3110`, 1.02 Bobcoins from its screenshot. It
scored 17 of 20 and suggested four changes. Recording the Caller was declined:
no Caller narration exists, so it is a build, not a recording. A keyboard
focus style is under Open items already. Keepalive is checklist item 3. Its
one wording catch was right: the README said Bob built its part "over
eighteen sessions", and two of those built nothing, so the line now reads
"in sixteen of its nineteen sessions".

**Two disagreements are recorded, not resolved.** The README-claims session
read 20.12 in Bob and the export shows 8.94 for its day, which had not ended
when the export was taken. The first four sessions' task summaries differ
slightly from their day totals. `bob_sessions/README.md` lists both.

**The evidence.** At the start, on a clean tree: `pytest -q` reported
`2106 passed` and all five gates exited 0. The end-of-task figures and the CI
run are in the report for this commit.

**Found, not fixed.**

- The Nov 19 row of the export was taken while that UTC day was in progress.
  A later export could show a different figure for it; nothing here retakes it.
- Everything under Open items, unchanged by this task.

## History

`docs/history/` holds every task record before the one above, unchanged.
`docs/history/README.md` is the index and the ledger of where each archived
decision now lives.

| File | What is in it |
| ---- | ------------- |
| `docs/history/task_37_the_readme.md` | the README cut to a page a judge skims, six sections moved into `docs/`, the pictures drawn from the running app, and every icon hidden from a screen reader |
| `docs/history/task_36_the_tagline.md` | the tagline changed in one constant, every brand file redrawn from it, and the old phrase made banned copy |
| `docs/history/task_35_the_launch_on_a_phone.md` | the status bar, the safe-area insets, all eleven startup images checked, the no-white guarantee and the crossfade |
| `docs/history/task_34_the_share_button_and_the_launch_screen.md` | the share button that offered a clip, the accessible name a Material Symbol was inside, the launch screen's hold, fade and cap, and the eleven startup images |
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
