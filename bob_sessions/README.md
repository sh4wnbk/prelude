# bob_sessions

Session exports from Bob's work on the EventFeed module, one per task.

**These are committed, not ignored.** The submission guide requires the exports
to be present in the final repo, so do not add this directory to `.gitignore`.

## Scrub before every commit

Exports are transcripts. They can pick up anything that passed through a
session, including credentials.

**Before each commit, scrub the export of anything secret:** API keys, tokens,
project ids, URLs carrying a key in the query string, and any value from `.env`.
`.env.example` lists the variable names to look for:

```
WATSONX_API_KEY  WATSONX_PROJECT_ID  WATSONX_URL
GRANITE_MODEL_ID  TTS_API_KEY  TTS_URL  TTS_VOICE
```

Replace a scrubbed value with a placeholder such as `<redacted>` rather than
deleting the line, so the export still reads as a record of what happened.

Check the diff before committing, not after. A key that reaches a public repo is
leaked even if the next commit removes it, because it stays in history; it has
to be rotated at that point, not just deleted.

`.bobignore` at the repo root lists files that must never be read into or
exported from a session.

## Naming

One file per task, named so the order is obvious:

```
phase3_task1_<short-description>.md
```

## Sessions

Phase 3, the EventFeed module, took two tasks. Each row is one session: the
export, the screenshot of its task summary, and the commit it produced.

| Task | Export | Screenshot | Commit | Bobcoins |
| ---- | ------ | ---------- | ------ | -------: |
| 1. Build `StatsBombEventFeed` | [`bob_sessions/phase3_task1_eventfeed.md`](phase3_task1_eventfeed.md) | [`bob_sessions/phase3_task1_eventfeed.png`](phase3_task1_eventfeed.png) | `3ce6bca` | 0.463 |
| 2. End event windows at the goal shot | [`bob_sessions/phase3_task2_window_fix.md`](phase3_task2_window_fix.md) | [`bob_sessions/phase3_task2_window_fix.png`](phase3_task2_window_fix.png) | `343c712` | 0.508 |

Task 1 built the module against `docs/bob_brief.md` and took all 14 acceptance
tests from failing to passing. Task 2 fixed `event_window`, which filtered by
clock time alone and so ran past the goal to the goalkeeper's event recorded in
the same second, and tightened the test that had missed it.

The Bobcoin figures are read from each session's task summary, which is what
the screenshots record.

The exports are transcripts and are kept verbatim, including the dashes Bob
typed. The repo's no-em-dash rule covers doc and UI copy written here, not a
record of what another tool said; `scripts/check_docs.py` checks this README
and leaves the exports alone.
