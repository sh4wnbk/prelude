# The README's three claims, and the Bobalytics export

This is a record of what was true when this task closed. Present tense here
means that day. `HANDOFF.md` is the file that describes the repo now.

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
