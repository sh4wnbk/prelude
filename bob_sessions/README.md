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

Each row is one session: the export, the screenshot of its task summary, the
commit the work landed in and the commit that added the export. The two differ
because an export is committed after the work it records, and sometimes
alongside another session's.

| Phase | Task | Export | Screenshot | Work | Export | Bobcoins |
| ----: | ---- | ------ | ---------- | ---- | ------ | -------- |
| 3 | 1. Build `StatsBombEventFeed` | [`bob_sessions/phase3_task1_eventfeed.md`](phase3_task1_eventfeed.md) | [`bob_sessions/phase3_task1_eventfeed.png`](phase3_task1_eventfeed.png) | `3ce6bca` | `7970216` | 0.463 |
| 3 | 2. End event windows at the goal shot | [`bob_sessions/phase3_task2_window_fix.md`](phase3_task2_window_fix.md) | [`bob_sessions/phase3_task2_window_fix.png`](phase3_task2_window_fix.png) | `343c712` | `7970216` | 0.508 |
| 4 | 3. Add `buildup` | [`bob_sessions/phase4_task3_buildup.md`](phase4_task3_buildup.md) | [`bob_sessions/phase4_task3_buildup.png`](phase4_task3_buildup.png) | `24e1a8d` | `e0bbbdd` | 1.22 |
| 4 | 4. Build the orchestrator | [`bob_sessions/phase4_task4_orchestrator.md`](phase4_task4_orchestrator.md) | [`bob_sessions/phase4_task4_orchestrator.png`](phase4_task4_orchestrator.png) | `1c4063a` | `be0426f` | 4.02 |
| 4 | 5. The game-focused header | [`bob_sessions/phase4_task5_header.md`](phase4_task5_header.md) | [`bob_sessions/phase4_task5_header.png`](phase4_task5_header.png) | `7f1b21e` | `4826671` | 3.16 |
| 4 | 6. The header on the moment card | [`bob_sessions/phase4_task6_card_header.md`](phase4_task6_card_header.md) | [`bob_sessions/phase4_task6_card_header.png`](phase4_task6_card_header.png) | `aab7093` | `95341d1` | from the Bobalytics export at submission |
| 4 | 7. The screen copy | [`bob_sessions/phase4_task7_screen_copy.md`](phase4_task7_screen_copy.md) | [`bob_sessions/phase4_task7_screen_copy.png`](phase4_task7_screen_copy.png) | `8215108` | `76e0d15` | from the Bobalytics export at submission |
| 4 | 8. Where the 1986 fan steps away | [`bob_sessions/phase4_task8_step_away.md`](phase4_task8_step_away.md) | [`bob_sessions/phase4_task8_step_away.png`](phase4_task8_step_away.png) | `30116a2` | `3380bf3` | from the Bobalytics export at submission |
| 4 | 9. The "Who are you with" card | [`bob_sessions/phase4_task9_listener_card.md`](phase4_task9_listener_card.md) | [`bob_sessions/phase4_task9_listener_card.png`](phase4_task9_listener_card.png) | `c6fc1ad` | `4f12bea` | from the Bobalytics export at submission |
| 4 | 10. The Profile screen | [`bob_sessions/phase4_task10_profile.md`](phase4_task10_profile.md) | [`bob_sessions/phase4_task10_profile.png`](phase4_task10_profile.png) | `4ef3aa0` | `b2d29a2` | from the Bobalytics export at submission |
| 5 | 11. Audio playback on the moment card | [`bob_sessions/phase5_task11_player.md`](phase5_task11_player.md) | [`bob_sessions/phase5_task11_player.png`](phase5_task11_player.png) | `35708cd` | `076e914` | from the Bobalytics export at submission |
| 5 | 12. "Your narrator" on Profile | [`bob_sessions/phase5_task12_narrators.md`](phase5_task12_narrators.md) | [`bob_sessions/phase5_task12_narrators.png`](phase5_task12_narrators.png) | `35c91b6` | `d0837ac` | from the Bobalytics export at submission |
| 5 | 13. Rename the persona id from mate to buddy | [`bob_sessions/phase5_task13_buddy_rename.md`](phase5_task13_buddy_rename.md) | [`bob_sessions/phase5_task13_buddy_rename.png`](phase5_task13_buddy_rename.png) | `4e61a10` | `473b98e` | from the Bobalytics export at submission |
| 5 | 14. The narrator picker | [`bob_sessions/phase5_task14_narrator_picker.md`](phase5_task14_narrator_picker.md) | [`bob_sessions/phase5_task14_narrator_picker.png`](phase5_task14_narrator_picker.png) | `d5dc9c2` | `9f98e91` | from the Bobalytics export at submission |
| 6 | 15. The OpenAPI file watsonx Orchestrate imports | [`bob_sessions/phase6_task15_orchestrate_spec.md`](phase6_task15_orchestrate_spec.md) | [`bob_sessions/phase6_task15_orchestrate_spec.png`](phase6_task15_orchestrate_spec.png) | `39856bd` | `39856bd` | from the Bobalytics export at submission |
| 6 | A read-only review of the app | [`bob_sessions/phase6_review_app.md`](phase6_review_app.md) | [`bob_sessions/phase6_review_app.png`](phase6_review_app.png) | none | `927ad9e` | from the Bobalytics export at submission |
| 7 | The tagline | [`bob_sessions/phase7_tagline.md`](phase7_tagline.md) | [`bob_sessions/phase7_tagline.png`](phase7_tagline.png) | `e1b4d6a` | `f40af46` | 11.18 |
| 7 | Three README claims: stopped at the 20-coin cost limit, nothing committed, its local changes discarded; the edits were made outside Bob | [`bob_sessions/phase7_readme_claims.md`](phase7_readme_claims.md) | [`bob_sessions/phase7_readme_claims.png`](phase7_readme_claims.png) | none | `788b5a4` | 20.12 |

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

Task 5 built `transition` and `header` in `app/orchestrator.py` and pointed
`PreludeOrchestrator.opening` at the new header. It also found two tests in
`TestAnotherSport` built with the wrong scoring side; Shawn approved the fix
and only `side=TEAM_B` was added, with every expectation left as written.

Nothing was scrubbed from the Task 3 export: a scan for the variable names in
`.env.example`, for bearer tokens, keys, project ids and URLs carrying a query
string found none. Its two mentions of `.env` are the rule text telling Bob not
to open it, not a value read out of it.

Nothing was scrubbed from the Task 5 export. The same scan found none of the
six variable names, no `.env` mention, no bearer token, no key-shaped string
and no URL of any kind. Its only long opaque strings are a module name and six
test names. The screenshot shows the workspace, a context gauge and a Bobcoin
figure, none of which authorises anything.

Nothing was scrubbed from the Task 4 export either. The same scan found none of
the six variable names, no `.env` mention, no bearer token, no key-shaped
string and no URL carrying a query string. Its only long opaque strings are a
file path and two test names. The screenshot shows a task id and a Bobcoin
figure, which identify the session rather than authorising anything.

Task 15 wrote `orchestrate/prelude_tools.yaml`, the OpenAPI file watsonx
Orchestrate imports. Its work and its export landed in one commit, `39856bd`,
so the two commit columns hold the same id: the export was committed beside
the work rather than after it.

**The read-only review has no work commit, because it changed no file.** It
was run in Ask mode against the brief at the top of
`bob_sessions/phase6_review_app.md`, which tells the session to create, edit
and delete nothing and to answer in the chat. So there is nothing for a Work
column to point at, and the commit that added the export, `927ad9e`, is the
only commit the session produced. Its findings were read against the repo
afterwards: four lines in the screens claim more than the code does, one
metric the app already records is not shown anywhere a fan or a judge can
see it, and one `README.md` line is stale. Task 32's steps 1, 2 and 8 are
what answers them.

Nothing was scrubbed from either Phase 6 export. The same scan found none of
the six variable names, no bearer token, no key-shaped string and no URL
carrying a query string in either file; the review's two mentions of `.env`
are the rule text telling the session not to open one, not a value read out
of it. Both screenshots show a workspace, a context gauge and a Bobcoin
figure, none of which authorises anything.

**The tagline session has no number**, for the same reason the read-only
review has none: it was run to a brief written in `HANDOFF.md` and the
session rather than to a numbered task in `docs/bob_brief.md`, which ends at
Task 15. It changed the tagline from "Leave your seat. Stay in the game." to
"Leave your seat. Not the game." The change is one constant in
`scripts/brand/build_svg.py`, and everything else follows from it: the
wordmark, the eleven startup images, the shell's visible line and its
accessible name, four docs and two tests. The old phrase is banned copy now,
so it cannot come back to a screen. Its work landed in `e1b4d6a` as Task 36
and its export in `f40af46`.

Nothing was scrubbed from the tagline export. The same scan found none of the
six variable names, no `.env` mention, no bearer token, no key-shaped string
and no URL carrying a key; its one URL with a query string is an unauthenticated
call to the public GitHub Actions API. The screenshot shows a workspace, a
context gauge, a todo list and a Bobcoin figure, none of which authorises
anything.

The Bobcoin figures are read from each session's task summary, which is what
the screenshots record. Six were read that way as the sessions ran. The other
eleven are not guessed and not left blank: Phase 7 exports Bobalytics once, from
User scope over the full lab period, and the figures for those rows come from
that export.

The exports are transcripts and are kept verbatim, including the dashes Bob
typed. The repo's no-em-dash rule covers doc and UI copy written here, not a
record of what another tool said; `scripts/check_docs.py` checks this README
and leaves the exports alone.
