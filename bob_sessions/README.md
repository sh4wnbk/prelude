# bob_sessions

Session exports from Bob's work on the EventFeed module, one per task.

**These are committed, not ignored.** The submission guide requires the exports
to be present in the final repo, so do not add this directory to `.gitignore`.

## Scrub before every commit

Exports are transcripts. They can pick up anything that passed through a
session, including credentials.

**Before each commit, scrub the export of anything secret:** API keys, tokens,
project ids, URLs carrying a key in the query string, and any credential value.
The live credentials live outside the repo (see `app/credentials.py`), so an
export should not contain one at all; scrub anyway, because a session can be
told a value by hand. `.env.example` lists the variable names to look for:

```
WATSONX_API_KEY  WATSONX_PROJECT_ID  WATSONX_URL
TTS_API_KEY  TTS_URL  TTS_VOICE
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
phase<phase>_task<task>_<short-description>.md
```

The task number is the one in the brief Bob worked to, not a count of sessions
in the phase: the buildup task is Task 3 of `docs/bob_brief.md` and the first
Bob session of Phase 4, so it is `phase4_task3_buildup.md`.

## Sessions

Each row is one session: the export, the screenshot of its task summary, and
the commit it produced.

| Phase | Task | Export | Screenshot | Commit | Bobcoins |
| ----: | ---- | ------ | ---------- | ------ | -------: |
| 3 | 1. Build `StatsBombEventFeed` | [`bob_sessions/phase3_task1_eventfeed.md`](phase3_task1_eventfeed.md) | [`bob_sessions/phase3_task1_eventfeed.png`](phase3_task1_eventfeed.png) | `3ce6bca` | 0.463 |
| 3 | 2. End event windows at the goal shot | [`bob_sessions/phase3_task2_window_fix.md`](phase3_task2_window_fix.md) | [`bob_sessions/phase3_task2_window_fix.png`](phase3_task2_window_fix.png) | `343c712` | 0.508 |
| 4 | 3. Add `buildup` | [`bob_sessions/phase4_task3_buildup.md`](phase4_task3_buildup.md) | [`bob_sessions/phase4_task3_buildup.png`](phase4_task3_buildup.png) | `24e1a8d` | 1.22 |
| 4 | 4. Build the orchestrator | [`bob_sessions/phase4_task4_orchestrator.md`](phase4_task4_orchestrator.md) | [`bob_sessions/phase4_task4_orchestrator.png`](phase4_task4_orchestrator.png) | `1c4063a` | 4.02 |

Task 1 built the module against `docs/bob_brief.md` and took all 14 acceptance
tests from failing to passing. Task 2 fixed `event_window`, which filtered by
clock time alone and so ran past the goal to the goalkeeper's event recorded in
the same second, and tightened the test that had missed it. Task 3 added
`buildup`, which reaches back a possession for a set piece so the foul that won
a penalty is in the run-up, and merged `BuildupFeed` into `EventFeed` as the
brief asked, leaving `BuildupFeed` behind as an alias so the tests needed no
change.

Task 4 built `app/orchestrator.py` against the contract and fixed the period
gap in `buildup`, which turned out to be in the goal's own possession rather
than in the set-piece reach back the brief had pointed at.

Nothing was scrubbed from the Task 3 export: a scan for the variable names in
`.env.example`, for bearer tokens, keys, project ids and URLs carrying a query
string found none. Its two mentions of `.env` are the rule text telling Bob not
to open it, not a value read out of it.

Nothing was scrubbed from the Task 4 export either. The same scan found none of
the six variable names, no `.env` mention, no bearer token, no key-shaped
string and no URL carrying a query string. Its only long opaque strings are a
file path and two test names. The screenshot shows a task id and a Bobcoin
figure, which identify the session rather than authorising anything.

The Bobcoin figures are read from each session's task summary, which is what
the screenshots record.

The exports are transcripts and are kept verbatim, including the dashes Bob
typed. The repo's no-em-dash rule covers doc and UI copy written here, not a
record of what another tool said; `scripts/check_docs.py` checks this README
and leaves the exports alone.
