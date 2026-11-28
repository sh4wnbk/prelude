# Tasks 1 and 1b: the play segments

This is a record of what was true when Task 1b closed. Present tense here
means that day. `HANDOFF.md` is the file that describes the repo now.

**What Shawn asked for on 2026-11-28.** Task 1: a module that says which
words of a frozen narration stand on which records, with its tests. Task 1b:
the script that writes those segments for the six slots into a file, a
`records` map beside them, a `draw_from` table per slot, the "under pressure
from X" overlap folded, and this handoff.

**What changed.** `app/grounding.py` builds the goal-call reader in a public
`goal_call_reader(facts, side)`, which `_goal_call` calls, with no change in
behaviour. `app/play_segments.py` is new, and so are
`scripts/write_play_segments.py`, `app/web/play_segments.json` and
`tests/test_play_segments.py`. Current state carries the rules under The play
segments.

**Three deviations from Task 1's spec, each agreed with Shawn before it was
built.**

1. `app/narration_grammar.py` was edited, which the spec did not list. A
   chain and "under pressure from X" carry `receiver_said` in their detail,
   and a merged long ball carries `long_said` and `chain_at`. These are
   `SPAN_KEYS`, position data only. The grammar, grounding and frozen
   narration tests gave `272 passed` before the edit and `272 passed` after
   it, and all six `claims_checked` values are unchanged.
2. The chain rule. The spec put every claim at the sentence's offset plus
   `move.at`, but the reader builds a chain as its marker and the receiver's
   name at the name's position, so "found Maradona" has its `at` on
   "Maradona". The span is `end = at + len(receiver_said)`,
   `start = end - len(said)`, with the exact match asserted. "Under pressure
   from X" is built the same way and takes the same rule.
3. The long-ball rule. The spec asserted that every span reads as its move's
   `said`, but `_merge_long` joins "long ball" and "to MacAllister" while the
   text has "forward" between them. That one move, recognised as a chain whose
   detail says `long`, spans from the long ball to the end of the chain's
   name, and its segment's `said` is the text there: "long ball forward to
   MacAllister", on the one long pass. Every other move still matches
   exactly, and any other mismatch raises.

**Task 1b's two decisions.** The segments are in a separate file,
`app/web/play_segments.json`, and not added to `app/web/narrations.json`,
which `scripts/freeze_narrations.py` writes. And `draw_from` follows the rule
under The play segments in Current state: in 1986 `buddy_conceded` the shot,
index 1971, is held by "picked it up" as well, and is drawn at "scored"; in
1986 `storyteller_neutral` carry 1970 is drawn at "Shilton". The rule
was read as the earliest claiming segment that is not earlier than the
floor, because the literal reading, the later of the earliest claim and the
floor, puts that shot at "Shilton", a segment that does not claim it. The
two readings differ on that one record in the six slots and nowhere else.

**The evidence.** At the start of Task 1, on a clean tree: `pytest -q`
reported `2106 passed` and the five gates printed their passing lines.
`scripts/write_play_segments.py` prints 8, 8 and 9 segments for the 1986
slots (`buddy_conceded`, `buddy_scored`, `storyteller_neutral`) and 9, 10 and
9 for 2022, and `--check` exits 0. The end-of-task figures and the CI run are
in the report for this commit.

**Found, not fixed.**

- "Under pressure from Beardsley and Reid" names two pressers, and the reader
  gives the second the said "under pressure from Reid", which is not one run
  of the text. `segments` raises on such a narration rather than place it.
  None of the six says it.
- In 1986 `storyteller_neutral`, carry 1955 is claimed only by "carried",
  which comes after "Beardsley" in the text, so the rule draws Beardsley's two
  records at "carried" and nothing at "Beardsley". That is the rule working
  as written; whether a later screen wants it is for that screen's task.
- `docs/HARNESS.md` lists the standard library modules `app/` imports, and the
  list already left out `datetime`, `base64`, `textwrap` and `time` before
  this task. `app/play_segments.py` adds no new one.
