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

## Nothing here yet

Phase 3 has not started. The first export lands when Bob builds the module
against `docs/bob_brief.md`.
