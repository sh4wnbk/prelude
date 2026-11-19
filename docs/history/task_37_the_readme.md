# Task 37: the README

This is a record of what was true when Task 37 closed. Present tense here
means that day. `HANDOFF.md` is the file that describes the repo now.

**What Shawn asked for on 2026-11-18.** `README.md` was 649 lines of prose,
one image, four empty placeholder sections and a 400-line capability list. It
had to read like a product page a judge skims in two minutes: pictures first,
short sentences, links for depth. Five steps, with a commit between each.

**Every Material Symbols icon is hidden from a screen reader.** A Material
Symbols span's text is the glyph's name, so the word was inside its control's
accessible name: the bottom nav read "sensors LIVE" and the moment card's
second button read "replay_10 REPLAY 10S". All 58 spans in `app/web/` carry
`aria-hidden="true"` now, the 56 that did not plus the two Task 34 hid, and
that includes the one the picker's own script builds on a tap, which is why
`CHECK_GLYPH` in `tests/test_match_choice.py` changed with them. This was a
carry-forward in every Found, not fixed since Task 34.

**`tests/browser/test_the_accessible_names.py` asks the browser rather than
the markup.** Every screen, both matches, three listeners and three narrator
states: every icon span hidden from the tree, no glyph name inside any
accessible name, the bottom nav named by its three labels and the moment
card's four buttons by theirs. The ligatures are read off the live DOM, so
nothing is written down twice, and the names come from `aria_snapshot`, which
is the computation a reader does. It fails 9 of 9 on the tree before this
task.

**`docs/images/` holds the seven pictures `README.md` shows**, drawn by
`scripts/make_docs_images.py`. Five are the running app at 390 by 844 with a
device scale factor of 2, taken through the app's own controls: the script
serves `app/web/` on a port the operating system picks, opens `index.html`,
and taps the 2022 card, Confirm event, Argentina, Continue, Profile, the
Buddy, Live, Heading out and Moments. Nothing writes `sessionStorage`, so a
screen that cannot be reached by tapping cannot be photographed. The sixth is
the flow diagram, drawn as one SVG in the app's palette with the app's own
fonts. The seventh is the committed mark on the app's own background: the mark
is white letters on nothing, which is right in the app and wrong in a README,
where GitHub draws it on whichever background the reader's theme sets.

**`README.md` is 127 lines and no sentence in it is over 25 words.** In
order: the mark, one sentence on what Prelude does, the tagline, the live
link, three screenshots side by side, the demo tickets, the flow as a Mermaid
block GitHub renders, the two Orchestrate screenshots with one line each, what
is verified, what is built with IBM, the judging criteria, what runs where,
the limits, and the StatsBomb attribution with its logo.

**The six long sections moved into `docs/` intact**, each with one link from
the README: `docs/CAPABILITIES.md`, which also takes "What the demo is,
precisely"; `docs/THE_LABEL.md`; `docs/HOSTED_API.md`; `docs/DOCUMENTS.md`;
`docs/CREDENTIALS.md`; and `docs/DATA.md`. Markdown link targets were
rewritten one level down; backtick paths, which `scripts/check_docs.py`
resolves against the repo root, were not. All six are in that script's `DOCS`
list and `docs/CAPABILITIES.md` is in its test-count list, so every check the
text had inside `README.md` it still has.

**The four empty placeholder sections are gone**: "The problem", "What makes
it different", "How it works" with its two empty subheads, and the judging
table with an empty evidence column. The judging table is back with four rows,
each a line and a link to evidence that exists.

**`docs/IBM_STACK.md` called watsonx Orchestrate planned** while the agent was
live, its OpenAPI file was committed and its two screenshots were in
`docs/evidence/`. It is a Built section now, with the file, seven tests and
the two screenshots behind it, and Planned is empty and says so.

**`bob_sessions/README.md` has the Phase 7 row**: the tagline session,
`e1b4d6a` for the work, `f40af46` for the export, and 11.18 Bobcoins read off
the task summary in the screenshot. It carries no task number, for the same
reason the read-only review carries none: `docs/bob_brief.md` ends at Task 15
and both were run to a brief written elsewhere. The scrub scan found nothing.
`docs/IBM_STACK.md`'s session table stopped at fourteen and holds all
seventeen now.

**The evidence.** At the start, on a clean tree: `pytest -q` reported
`2106 passed`, all five gates exited 0, and `pytest tests/browser` reported
`146 passed`. At the end: `2106 passed`, all five gates 0, and `155 passed`
in the browser suite, which is the nine the new file adds.
`scripts/make_docs_images.py --check` reports every image as what the app
draws. CI is green on the last commit of this task.

**Found, not fixed.**

- The three screenshots in the README's top row are 780 pixels wide each and
  GitHub scales them into a three-column table, so a judge sees them small. A
  narrower render, or two rows, would read better on a phone.
- `scripts/make_docs_images.py` is not run by CI, so a screen that changes
  leaves the committed pictures stale until someone runs `--check` by hand. It
  needs a browser, which is why it is not in the gate list.
- The carry-forwards from Task 36, less the icons, which this task fixed: the
  startup images are 560 KB, a launch screen that is interrupted is not
  covered, `prelude_launch.svg` is committed and nothing at runtime serves it,
  the icon font is still 1.14 MB of the committed fonts, the compiled
  stylesheet is not rebuilt by CI, CI does not run on a schedule, and the
  smoke workflow cannot be made to fail by a failing deploy.
- Nothing in this repo has run on an iPhone. Task 35 is still waiting on that,
  and this task's pictures are headless Chromium at 390 by 844.
