# Task 30: the two gaps closed, and the browser checks kept

**This is a record of what was true when Task 30 closed, on 2026-11-12.** It
is not a description of the repo today; `HANDOFF.md` is the only file that is.
It moved here from `HANDOFF.md`'s "Last task" when Task 32 closed, unchanged
below the heading.

Three of the five items under "Found, not fixed" were closed by Task 32: the
browser suite no longer needs the three CDNs, because the screens carry their
own stylesheet and their own fonts; the Moments hero card's waveform follows
the voice and scrubs; and every file in `tests/` has a row in the
`docs/HARNESS.md` table, which is the seven this record counts and the three
written since. `tests/browser/` still has a section of its own rather than
rows in that table, which is deliberate: the table is the unit suite, and
`scripts/check_docs.py` counts that suite. The other two, CI not running on a
schedule and the smoke workflow not being failable by a failing deploy, are
carried in `HANDOFF.md`.

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
