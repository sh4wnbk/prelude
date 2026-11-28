# Task 2: when each segment is spoken

This is a record of what was true when Task 2 closed. Present tense here
means that day. `HANDOFF.md` is the file that describes the repo now.

**What Shawn asked for on 2026-11-28.** For each of the six recordings, the
moment each play segment starts, found by transcribing the recording with
word timestamps and matching the recognised words to the slot's text, with no
segment timed by a guess. A CI test that needs no audio tools, a cue sheet per
slot, and a stop for Shawn to listen.

**What changed.** `faster-whisper` is in the dev dependency group.
`scripts/align_segments.py` is new and offline: it transcribes each MP3,
aligns the words with `difflib`, takes each segment's `start_ms` from the word
at its `start_char`, prints a cue sheet per slot and writes
`app/web/segment_timings.json`, with each recording's sha256 and duration.
`tests/test_segment_timings.py` holds the file to `app/web/play_segments.json`
and to the committed MP3s. Current state carries the rules under The play
segments.

**Deviations from the spec, each agreed with Shawn before it was committed.**

1. The audio is decoded by the script with PyAV, not by `faster-whisper`.
   `faster_whisper.audio.decode_audio` in 1.2.1 passes `metadata_errors` to
   `av.open`, which PyAV 19 no longer accepts. The script does the same decode
   without that argument, 16 kHz mono with nothing trimmed, so times are still
   positions in the file. No version pin was added.
2. The model is `small.en`, downloaded once from huggingface.co as
   `Systran/faster-whisper-small.en`. It is a build tool and not an input to
   the app.
3. The first run left two segments unmatched, which was a stop: in both 2022
   Buddy recordings "on to MacAllister" was heard as "onto macalester". The
   fix is the one split in Current state, a recognised "onto" against the
   text's "on to", and nothing wider. Both splits are printed by the script,
   at 0:09.860 in 2022 `buddy_conceded` and at 0:08.360 in 2022
   `buddy_scored`.

**The evidence.** At the start, on a clean tree: `pytest -q` reported
`2158 passed` and all five gates exited 0. The script timed all 52 segments
by a matched word and exited 0. The end-of-task figures, the cue sheets and
the CI run are in the report for this commit.

**Found, not fixed.**

- The recogniser heard "MacAllister" as "macalester" and "mcallister" and
  "Cuciuffo" as "cusiuffo". No segment starts on either name, so no time
  depends on it, but a segment that did would fail rather than match.
- `docs/HARNESS.md` and `CLAUDE.md` name `.venv-prelude` as the virtualenv;
  this worktree runs its own `.venv`, made by `uv sync`. The docs describe the
  main checkout and were left as they are.
