# Task 36: the tagline

This is a record of what was true when Task 36 closed. Present tense here
means that day. `HANDOFF.md` is the file that describes the repo now.

**What Shawn asked for on 2026-11-15.** Change the tagline from "Leave your
seat. Stay in the game." to "Leave your seat. Not the game." and ensure the
old phrase cannot come back.

**The change is in one constant** (`TAG` in `scripts/brand/build_svg.py`), and
everything follows from it. The brand script draws every brand file from one
set of numbers: the SVG layout, the eleven startup images, and the title and
`aria-label` of `prelude_launch.svg`. Before this task, the SVG's title was a
hardcoded string literal rather than a reference to `TAG`, so the script could
not update it; that literal is now `f"Prelude. {TAG}"`. Running the script with
`--confirm` regenerated all fifteen files. The brand check (`--check`) confirms
every committed file is what the script now draws.

**The visible copy and the accessible name in `app/web/index.html` are updated
together.** The `<p id="launch-line">` text and the `aria-label` on
`<div id="launch" role="img">` are the two places the tagline exists as text in
the shell; the mark itself is outlines.

**The docs updated: `README.md`, `HANDOFF.md`, `docs/DESIGN.md` and
`scripts/brand/README.md`.** Each carried the old tagline in a present-tense
description; each is now the new one. `docs/history/task_33_the_brand.md` and
`bob_sessions/phase6_review_app.md` are records of what was true when they were
written and are left as they are.

**The tests updated: `tests/browser/test_the_launch_screen.py` and
`tests/test_screen_copy.py`.** Both define `TAGLINE` as a constant and both
expected the old phrase; both are now the new one.

**"Stay in the game" is now banned copy.** A new entry in
`scripts/scan_copy.py`'s `BANNED` list labelled `"retired tagline"` matches the
pattern `r"Stay in the game"` and prevents the old phrase from returning to any
web screen.

**The evidence.** `pytest -q` reports `2106 passed`; all five gates exit 0;
the brand check exits 0 with every file marked `same`. "Stay in the game"
appears only in `docs/history/task_33_the_brand.md`,
`bob_sessions/phase6_review_app.md` and the `BANNED` pattern in
`scripts/scan_copy.py`. CI is green on the last commit of this task.

**Found, not fixed.**

- The same carry-forwards as Task 35: every icon in the app is still inside
  its control's accessible name, the startup images are 560 KB, a launch screen
  that is interrupted is not covered, `prelude_launch.svg` is committed and
  nothing at runtime serves it, the icon font is still 1.14 MB of the committed
  fonts, the compiled stylesheet is not rebuilt by CI, CI does not run on a
  schedule, and the smoke workflow cannot be made to fail by a failing deploy.
