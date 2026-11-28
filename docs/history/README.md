# The task records, archived

`HANDOFF.md` grew by a full record every task, and every session read all of
it. The records moved here, unchanged, so that file could become a running
snapshot plus the latest detail. **Nothing was deleted**, and every line that
left `HANDOFF.md` is in one of the files below, byte for byte.

**These files are records, not descriptions of the repo today.** Present tense
in one of them means the day its task closed. `HANDOFF.md` is the only file
that describes the repo now.

## The files

| File | What is in it |
| ---- | ------------- |
| `docs/history/tasks_1_and_1b_the_play_segments.md` | Tasks 1 and 1b on `birds-eye`: `app/play_segments.py`, the three deviations from its spec, `scripts/write_play_segments.py`, the records map and `draw_from` |
| `docs/history/the_readme_claims_and_the_bobalytics_export.md` | the README's three corrected claims, the Bobalytics export committed, and the rubric session that ran after it |
| `docs/history/task_37_the_readme.md` | the README cut to 127 lines, the six long sections moved into `docs/`, the pictures drawn by `scripts/make_docs_images.py`, and every Material Symbols span hidden from a screen reader |
| `docs/history/task_36_the_tagline.md` | the tagline as one constant in the brand script, the fifteen files redrawn from it, the shell's visible line and accessible name, and the retired phrase made banned copy |
| `docs/history/task_35_the_launch_on_a_phone.md` | the status bar, the safe-area insets, all eleven startup images checked, the no-white guarantee and the crossfade |
| `docs/history/phase1-3_scaffold_data_and_eventfeed.md` | the scaffold, the fetch, the first data check, and Bob's EventFeed in two sessions |
| `docs/history/phase4_narration_and_orchestrator.md` | the provider layer, the prompt, the grounding check, the personas, the paid model comparison, and the orchestrator in two Bob sessions |
| `docs/history/phase5_voice_and_the_six.md` | the Text to Speech facts and probe, the pronunciation table, the hero run the service refused, and the freeze |
| `docs/history/data_check_and_screen_scan.md` | what the data said, and the copy claims that did not survive it |
| `docs/history/deviations.md` | where Phases 1 and 2 departed from the task list |
| `docs/history/the_ticket_flow_and_the_published_site.md` | the demo tickets, the scanner, the ticket screen, the Pages deploy, the readable type and the desktop backdrop |
| `docs/history/verifying_the_app_in_a_browser.md` | the hand-rolled browser method `tests/browser/` replaced in Task 30 |
| `docs/history/the_plan_as_agreed.md` | the Plan, task by task, and the Phase 5, 6 and 7 outlines |
| `docs/history/tasks_11_to_29.md` | Task 29 back to the second Task 11 list, newest first |
| `docs/history/phase6_handover_and_the_doc_sweep.md` | the Orchestrate handover, and the sweep that emptied the register of stale passages |
| `docs/history/task_30_the_browser_suite_and_the_build.md` | the play button that waits for its words, the Moments hero card's recording, `tests/browser/`, CI on every push and the smoke workflow after a deploy |
| `docs/history/tasks_7_to_10_and_bob_sessions.md` | the candidate runs later runs replaced, every Bob session from task 7 to task 13 with its brief, and what tasks 4b, 6 and 6d settled |
| `docs/history/task_32_what_the_app_claims.md` | the four lines that claimed more than the code does, the claim count under the label, the compiled stylesheet and the fonts, jsQR and the icon brought into the repo, one player for both screens, and the first mark and launch screen |
| `docs/history/task_34_the_share_button_and_the_launch_screen.md` | the share button that offered a clip and the two ways nothing was copied, the accessible name a Material Symbol was inside, the launch screen's hold, fade and cap, and the eleven startup images |
| `docs/history/task_33_the_brand.md` | the brand given to the build: the mark, the icon set drawn from it, the launch screen, the broadcast quote removed, the six lines of match copy that described the play and were not held to the feed, and the two pills |

## Where each archived decision now lives

Read against the archive, section by section. The right-hand column is where a
session finds the decision now, and "settled and closed" means the decision
was about work that is finished and constrains nothing further.

### From Phases 1 to 3

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| Raw StatsBomb data is never committed; `data/raw/` is gitignored and rebuilt | `CLAUDE.md`, and Current state under What exists |
| Season and match ids are resolved at runtime, never hardcoded | Current state, What is reserved or left alone |
| The EventFeed and moment-detection module is reserved for IBM Bob | `CLAUDE.md`, and Current state under The interfaces |
| 2022 defining moments are periods 1 to 4 only; a shootout has no buildup | Current state, What is reserved or left alone |
| `Moment` carries no period field; Bob may add one with its tests | Current state, What is reserved or left alone |
| A set piece is narrated from `buildup`, not from a widened `event_window` | Current state, What is reserved or left alone |
| A penalty's own possession holds one event, the kick | Current state, What is reserved or left alone |
| The window fix, and the 6 of 9 goals it affected | settled and closed |
| `.gitkeep` files, and the CRLF normalization warning | settled and closed |

### From Phase 4

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| A model id is not a credential | Current state, Credentials |
| The tests make no network call, with loopback the one recorded exception | Current state, Credentials |
| The watsonx golden file is a schema fixture and says so about itself | settled and closed; the test still holds it |
| The failure rule is whole-narration | Current state, The grounding check |
| The pass rate counts first attempts only | Current state, The grounding check |
| A narration cites its facts, checked sentence by sentence | Current state, The grounding check |
| Pairing is blunt, and the prompt asks for one action a sentence because of it | Current state, The grounding check |
| Per-second clocks are groundable against the cited fact's own clock | Current state, The grounding check |
| Narration is past tense; present tense is refused | Current state, The grounding check |
| There is no closer; the last sentence cites the goal's shot | Current state, The grounding check |
| The second person is refused everywhere | Current state, The grounding check |
| "Won a foul" allowed, "won the match" refused | Current state, The grounding check |
| Coverage is reported and never enforced, and is split by what wrote it | Current state, The grounding check |
| A persona is a register and changes nothing about what may be said | Current state, The grounding check |
| The partisan voice's "we" needs a cited fact recorded against that side | Current state, The grounding check |
| One narration style for every persona; personas separated by sound | Current state, The narration as it ships |
| `openai/gpt-oss-120b` is active, chat endpoint, `reasoning_effort` low | Current state, The narration as it ships |
| The settings travel with the candidate, not with the call site | Current state, The narration as it ships |
| The header says what the goal did to the score | Current state, The header and the fan |
| The header is the same line for every listener; allegiance picks the persona | Current state, The header and the fan |
| The header is never labelled | Current state, The label |
| `ScoringMoment` carries the score before as well as after, never derived | Current state, The header and the fan |
| A transition is read out of those two scores and nothing earlier | Current state, The header and the fan |
| The phase is a share of regulation time, guarded by `TestAnotherSport` | Current state, The header and the fan |
| A neutral listener has no score state and no outcome; both raise | Current state, The header and the fan |
| `phase`, `score_state` and `outcome` have no caller and stay | Current state, What is reserved or left alone |
| The credentials live outside the repo, and nothing prints a value | `CLAUDE.md`, and Current state under Credentials |
| The `.env` deny rule and the two ignore entries stay as a second layer | Current state, Credentials |
| The four evidence documents carry a file and a test per statement | Current state, How work is checked |
| Nothing tests the gates themselves | Current state, How work is checked |
| The three measured persona runs, and that none separated the voices | settled and closed; the reports stay in `docs/narration_eval.md` |
| The 13 of 15 shot claim is refuted | settled and closed; `scripts/data_check.py` is the gate |

### From Phase 5

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| `<prosody>` is ignored, pitch moves up only, `<break>` works on one voice | Current state, The voice |
| A delivery is per request, in `app/delivery.py`, keyed by persona and situation | Current state, The voice |
| The Buddy is never brighter or quicker when the other side scored | Current state, The voice |
| The pronunciation table reaches the speech request and nothing else | Current state, The voice |
| The check refuses markup outright; the structural test is the second layer | Current state, The grounding check |
| Vocabulary is looked up before it is heard | Current state, The voice |
| IBM bills submitted length less whitespace; budgets are set on it | Current state, The voice |
| The audio map is written from the files on disk, not from the plan | Current state, The voice |
| What judges hear is recorded, never live | Current state, The narration as it ships |
| The six recordings are the fallback if the API is down | Current state, The narration as it ships |
| Half a second of silence in front of each recording, by frame copy | Current state, The voice |
| The six were written by the team and verified by the check; disclosed | Current state, The narration as it ships |
| A telling opens on a name and places the move at least twice | Current state, The narration as it ships |
| Force words refused; the neutral finishes stay sayable | Current state, The grounding check |
| A reaction is the second layer and claims nothing | Current state, The grounding check |
| A run is capped in tokens and refuses to start without a cap | Current state, The narration as it ships |
| Copy the review file aside before any rerun; not automated | Current state, The narration as it ships, and Open items |
| "Under pressure" belongs to the player on the ball | Current state, The grounding check |
| A side is said only where the ball is clear of the middle | Current state, The grounding check |
| A place is read off the attacking side's own record | Current state, The grounding check |
| No yard figures in the beats; consecutive dribbles grouped | settled and closed; `app/story_beats.py` holds it |
| The near-copy filter, on shape and on words, at 0.8 | settled and closed; `scripts/narrator_candidates.py` holds it |
| The hyphen reads as the space it stands in for | settled and closed; `app/narration_grammar.py` holds it |
| The 403, and that the instance was above its Lite cap | settled and closed; the recordings exist |
| Shawn's listening pass over the six | Open items, Still open from Phase 5 |
| The two narrow readings in `app/narration_grammar.py` | Open items, What the reading of the six left open |
| Rule 18 against the four references that open elsewhere | Open items, What the reading of the six left open |
| The Caller has a style and no recording | Open items, What the reading of the six left open |
| Where the candidate runs are, and the rerun command | Open items, The candidate runs and where they are |
| Keyboard focus states, and the empty placeholders | Open items, Phase 5 backlog |

### From the ticket flow and the published site

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| The two seats, as demo fixture data carrying no grounding obligation | Current state, The ticket the site and the type |
| The ticket payload is a URL, built from the structured fields | Current state, The ticket the site and the type |
| Each ticket PNG is read back with a real decoder before it is written | Current state, The ticket the site and the type |
| The scanner reads both the URL and the older `prelude:` form | Current state, The ticket the site and the type |
| A scanned code must match a whole payload; a typed seat is accepted as given | Current state, The ticket the site and the type |
| One manual entry form, mounted by both screens | Current state, The ticket the site and the type |
| Reading a code does not start the match | Current state, The ticket the site and the type |
| The camera needs a secure context | Current state, The ticket the site and the type |
| The label scale is 13, 14 and 16 px, and zoom is unblocked | Current state, The ticket the site and the type |
| The Tailwind config block stays byte-identical across the screens | Current state, The ticket the site and the type |
| The desktop backdrop applies above 501 px, with `body` transparent | Current state, The ticket the site and the type |
| The repo is private and the site is public, with both consequences | Current state, The ticket the site and the type, and the session model |
| What was stripped from each Stitch mockup, and why | settled and closed |

### From the pre-`tests/browser/` method

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| Serve the directory, do not open the files | Current state, Verifying the app in a browser |
| `data-match-rendered` is the signal, and is not enough on the moment card | Current state, Verifying the app in a browser |
| The session and local storage keys | Current state, Verifying the app in a browser |
| A delay has to be the server's, not the driver's | Current state, Verifying the app in a browser |
| Driving the scanner with a fake capture device | Current state, Verifying the app in a browser |
| The measurements that look like defects and are not | Current state, Verifying the app in a browser, with a fourth added |
| Test values are literals, not derived from each other | Current state, How work is checked |
| "No browser automation is installed" | **superseded**: Task 30 added Playwright to the dev group and `tests/browser/`, and Current state says so |

### From the Plan, and from Tasks 7 to 29

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| Shawn is asked whether to continue at the end of each task | Current state, How work is checked |
| `DELIBERATELY_ABSENT`, and that the check runs both ways | Current state, How work is checked |
| The hosted service holds no keys, writes nothing, makes no paid call | Current state, What exists, and Credentials |
| Hosting adds no input; the three real inputs are unchanged | `CLAUDE.md` |
| `GROUNDING_LABEL` lives in `app/grounding.py` | Current state, The label |
| The commit `/health` reports arrives as a file, not an environment variable | Current state, Credentials |
| The keepalive is behind `PRELUDE_KEEPALIVE`, and what it costs | Current state, the standing section |
| The slot rule is written twice and held to one table | Current state, How work is checked, and The interfaces |
| `match` is a string of digits on both endpoints | settled and closed; `tests/test_api.py::TestTheMatchParameter` holds it |
| The agent is told which matches it serves, from a generated list | settled and closed; `scripts/write_served_matches.py --check` is the gate |
| The agent's answer is the narration and nothing else | Current state, The label |
| The agent never summarises, and never writes the label | Current state, The label |
| Prelude does not choose the match for the fan | Current state, The header and the fan |
| The narrator outlives the tab; allegiance and name stay per session | Current state, The header and the fan |
| The narration has no inline fallback copy, and is revealed with its label | Current state, The label |
| The play button ships disabled and is released by the reveal | Current state, The label |
| The Moments hero card plays the fan's own recording | settled and closed; `tests/test_narration_player.py` holds it |
| The seated caption promises the buildup, not everything | settled and closed; `tests/test_screen_copy.py` holds it |
| `tests/browser/` writes down no expected words or files | Current state, How work is checked |
| Three rules are asked of every recorded frame | Current state, How work is checked |
| CI runs the suite, the gates, the browser suite and a clean-tree check | `CLAUDE.md`, and Current state under What exists |
| A task is not done until CI is green on its last commit | `CLAUDE.md` |
| The three CDNs the browser suite needs | **closed by Task 32**: the screens carry their own stylesheet, fonts and QR reader, and `tests/browser/test_every_screen.py` asserts no screen leaves its origin |
| The Moments waveform is still fixed bars | **closed by Task 32**: one player, and the hero card's bars follow the voice and scrub |
| `tests/browser/` is not in the `docs/HARNESS.md` table | **partly closed by Task 32**: every file in `tests/` has a row; `tests/browser/` keeps a section of its own, because the table is the unit suite `scripts/check_docs.py` counts |
| CI does not run on a schedule | Current state, Still open: what the build does not say |
| The smoke workflow cannot be failed by a failing deploy | Current state, Still open: what the build does not say |
| Task 30's record in full | `docs/history/task_30_the_browser_suite_and_the_build.md` |
| The reservation is short below 390 px | `docs/history/tasks_11_to_29.md`, Task 29's Found, not fixed; a layout judgement that is Shawn's |
| Nothing in the suite can re-measure 16.75rem | `docs/history/tasks_11_to_29.md`, Task 29's Found, not fixed |
| `scripts/scan_copy.py` would pass the label over an empty paragraph | `docs/history/tasks_11_to_29.md`, Task 29's Found, not fixed |
| Eight test files are missing from the `docs/HARNESS.md` table | `docs/history/tasks_11_to_29.md`, Task 29's Found, not fixed |
| The card on Shawn's iPhone, and the pitch film | `HANDOFF.md`, Next first action |
| Every candidate run that a later run replaced | settled and closed |
| Every Bob session brief, and what each session built | settled and closed; `docs/bob_brief.md` is the live brief |

### From Task 32

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| The four lines that claimed a sensor, a feed or a connection | Current state, under the app's decisions; `scripts/scan_copy.py` holds a pattern for each |
| The claim count under the grounding label | Current state, The label |
| Nothing a screen loads comes from another origin | Current state, What exists, and the same bullet under the app |
| One player for the moment card and the Moments hero card | settled and closed; `tests/test_narration_player.py` holds it |
| The mark is "P." in Syne Bold, drawn by `scripts/make_mark.py` | **superseded by Task 33**: the mark is the brand's, drawn by `scripts/brand/build_svg.py`, and `scripts/make_mark.py` is on `DELIBERATELY_ABSENT` |
| The launch screen paints once per tab, out of `sessionStorage` | **superseded by Task 33**: every full load paints it and the shell reads no storage |
| The API rebuilds only when something it serves changes | Current state, What exists, the `render.yaml` build filter |
| The two pills that said the play data was connected and synchronising | **closed by Task 33**: both read "PLAY-BY-PLAY DATA" and both old phrases are banned copy |
| The icon font is 1.14 MB of the committed fonts | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| `scripts/fetch_statsbomb.py` is not in the Render build filter | settled and closed; the four paths are the ones Shawn named |
| A screen-only push still rebuilds the API | settled and closed; `app/web/` holds three files the service answers from |
| The smoke subset does not open the launch screen | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| The compiled stylesheet is not rebuilt by CI | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |

### From Task 33

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| The mark, the icon and the tagline, drawn by `scripts/brand/build_svg.py` | Current state, under the ticket, the site and the type |
| The launch screen paints on every full load and the shell reads no storage | Current state, same section |
| The launch screen never outlives two seconds | **superseded by Task 34**: it is held 1.5 seconds, fades over 300 ms and is off the screen by 2.5 |
| `prelude_launch.svg` is the layout the CSS was measured against | **superseded by Task 34**: `launch_layout` in the brand script is the layout, and a screenshot holds it to the CSS |
| A committed PNG is compared pixel by pixel and not byte by byte | Current state, same section; `scripts/brand/build_svg.py` compares the startup images the same way |
| The broadcast quote, its two openings and the guillemet are banned copy | Current state, The label, and `scripts/scan_copy.py` |
| A line of match copy that describes the play carries a `grounding` block | Current state, under the ticket, the site and the type |
| The two pills now read "PLAY-BY-PLAY DATA" | Current state, same section |
| At 32 px the seven bars come back as three runs of amber | settled and closed; `tests/test_the_mark.py` records the measurement |
| `prelude_launch.svg` is committed and nothing at runtime serves it | still true, and `docs/DESIGN.md` says so; the startup images are drawn from its layout rather than from the file |
| A claim phrase in `CLAIMS` is a phrase and not a reading of the sentence | `docs/history/task_33_the_brand.md`, Found, not fixed |
| Nothing holds the Moments cards' `aria-label` to the title it repeats | `docs/history/task_33_the_brand.md`, Found, not fixed |
| The icon font is 1.14 MB of the committed fonts | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| The smoke subset does not open the launch screen | Current state, Still open: what the build does not say |

### From Task 34

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| The share button says what it does, and says "LINK COPIED" only once the write resolved | Current state, under the ticket, the site and the type |
| An icon span inside a control's accessible name carries `aria-hidden` | Current state, same section; the sweep over the rest is under Open items |
| The launch screen is held 1.5 s, and is off the screen by 2.5 s | Current state, under the ticket, the site and the type |
| What is left of the hold is rounded up, because `setTimeout` truncates | Current state, same bullet; `app/web/index.html` carries the reasoning |
| Reduced motion gets the same hold and no fade | **superseded by Task 35**: the fade is kept, because an opacity fade is not motion |
| The status bar is opaque black, because `env()` is zero inside the iframe | **superseded by Task 35**: it is `black-translucent`, and the insets are the shell's to apply |
| The startup images are held to the CSS by a screenshot at 390 by 844 | **widened by Task 35**: all eleven are rendered at their own size and ratio and measured against their own file |
| The eleven iPhone screens, and the pixel ratio in each media query | Current state, same section |
| The glyphs are rasterised from their own outlines, no font loaded | Current state, same section |
| The manifest's `background_color` is the colour the images are drawn on | Current state, same section, and Android's own splash beside it |
| Nothing has run on an iPhone | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| The startup images are 560 KB, and a quantiser would halve them | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| A launch screen that is interrupted is not covered | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| The cap is 2,500 ms and the screen left the page at 2,510 | settled and closed; the measurement is `docs/DESIGN.md`'s and the slack is the browser's |
| The smoke subset does not open the launch screen | **closed by Task 35**: `scripts/smoke_live.py` opens it, and the checks run after the next deploy |

### From Task 35

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| The status bar is `black-translucent` and the page is the whole screen | Current state, under the ticket, the site and the type |
| The safe-area insets are the shell's to apply, via CSS variables on `#frame` | Current state, same section |
| All eleven startup images are checked at their own size and pixel ratio | Current state, same section |
| The tagline comparison is split into two bands at the tagline's line box | `docs/history/task_35_the_launch_on_a_phone.md`, What it is |
| The fade is kept under reduced motion, because an opacity fade is not motion | Current state, same section |
| No frame of a load is white, and three things in markup make it so | Current state, same section |
| `data-painted` is what keeps the list from being revealed white | Current state, same section |
| `scripts/check_docs.py` collects `tests/browser` in a second pass | Current state, How work is checked |
| `scripts/smoke_live.py` opens the launch screen on the deployed site | settled and closed; the check runs after every deploy |
| Nothing has run on an iPhone | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| The startup images are 560 KB | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |
| A launch screen that is interrupted is not covered | `HANDOFF.md`, Last task's Found, not fixed, where it still stands |

### From Task 36

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| The tagline is "Leave your seat. Not the game." | Current state, under the ticket, the site and the type, via `scripts/brand/build_svg.py` |
| `prelude_launch.svg`'s title uses `TAG` rather than a string literal | `scripts/brand/build_svg.py`, in `drawn()` |
| "Stay in the game" is banned copy in `scripts/scan_copy.py` | `scripts/scan_copy.py`, `BANNED` |

### From Task 37

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| `README.md` is the page a judge reads, and a section moved out goes into `scripts/check_docs.py`'s `DOCS` list | Current state, Decisions still in force |
| The README's pictures are drawn by `scripts/make_docs_images.py` from the running app | Current state, Decisions still in force |
| Every Material Symbols span is `aria-hidden="true"`, asked by `tests/browser/test_the_accessible_names.py` | Current state, Decisions still in force |
| `docs/IBM_STACK.md` lists watsonx Orchestrate as built | settled and closed |
| `scripts/make_docs_images.py` is not run by CI | Current state, Open items, under what the build does not say |
| The README's top-row screenshots read small on a phone | Current state, Open items, under what the build does not say |
| The Task 36 carry-forwards | Current state, Open items |

### From the README's three claims and the Bobalytics export

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| The six narrations are shown entering the check beside the pipeline, not coming out of it | `README.md` and `scripts/make_docs_images.py`; settled and closed |
| Bob's part is closed, and the module stays Bob's | Current state, Decisions still in force |
| The export totals by day, so ten rows give their day's total | `bob_sessions/README.md` |
| The two recorded disagreements between Bob and the export | `bob_sessions/README.md` |
| The Nov 19 row was taken while that UTC day was in progress | Current state, Decisions still in force, beside Bob's part |
| Everything under Open items | Current state, Open items, unchanged |

### From Tasks 1 and 1b, the play segments

| Decision, rule or open item | Now lives |
| --------------------------- | --------- |
| What a segment is, and what is left out | Current state, The play segments |
| Spans are computed from `SPAN_KEYS`, never searched for | Current state, The play segments |
| The chain rule and the long-ball rule | Current state, The play segments; the reasoning in the archived record |
| "Under pressure from X" is one segment | Current state, The play segments |
| The `draw_from` rule, and the reading that puts the 1986 shot at "scored" | Current state, The play segments; the reading in the archived record |
| The segments are in their own file, not in `narrations.json` | Current state, The play segments |
| Two pressers make `segments` raise | the archived record's Found, not fixed, where it still stands |
| "Beardsley" draws nothing in 1986 `storyteller_neutral` | the archived record's Found, not fixed, where it still stands |
| `docs/HARNESS.md`'s import list was already incomplete | the archived record's Found, not fixed, where it still stands |
