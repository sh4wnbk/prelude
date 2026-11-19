# The hosted API

**Live URL: <https://prelude-api.onrender.com>.** Deployed on 2026-11-07 and
answering; `/health` reports the commit Render built. The free service sleeps
after fifteen minutes without traffic and a cold wake took 82 seconds, so open
`/health` and wait for `{"status": "ok"}` before the first real call. `HANDOFF.md`
has the standing note.

`app/api.py` is a read-only FastAPI service, GET only, with CORS open for GET.
It exists so watsonx Orchestrate has a stable public URL to call: GitHub Pages
serves files, and a tool needs an answer. It serves what this repo already
holds and computes nothing a screen does not already show.

| Endpoint | What it answers |
| -------- | --------------- |
| `GET /health` | `{"status": "ok"}`, plus the commit the build came from when the build wrote one |
| `GET /moments?match=<id>` | every goal of the match from the EventFeed module: scorer, team, the minute the app captions, the score after it, and whether the app narrates it |
| `GET /buildup?match=<id>&listener=team_a\|team_b\|neutral&narrator=<id>` | that listener's slot, the narrator's name, the frozen narration and its authorship, the recording's URL on the Pages site, and the grounding label |

`narrator` is optional and takes a persona id from
[`app/web/narrators.json`](../app/web/narrators.json). With none given, the
listener's side decides, which is what the app does. An unknown match is a
404; a listener that is not one of the three is a 422.

Run it:

```
.\.venv-prelude\Scripts\python.exe -I -m pytest tests/test_api.py
.\.venv-prelude\Scripts\python.exe -m uvicorn app.api:app --port 8099
curl "http://127.0.0.1:8099/buildup?match=3869685&listener=team_b"
```

**It holds no key and spends nothing.** It reads no environment variable, makes
no paid call, and imports neither `app/tts.py` nor the watsonx backend;
`tests/test_api.py::TestWhatItDoesNotReach` reads the module's whole import
closure and holds that. The narration it serves was frozen once and the
recordings were made once, so a thousand calls cost what one does.

**It holds no state and writes nothing.** [`render.yaml`](../render.yaml) is a
Blueprint for one free web service, where a spin-down rebuilds the filesystem
from the build, so there is nowhere for state to live and nothing here tries.
[`.github/workflows/keepalive.yml`](../.github/workflows/keepalive.yml) pings
`/health` so a cold start does not land on a visitor.

**The slot rule is written twice and tested once.** `Prelude.slotFor` in
[`app/web/match-content.js`](../app/web/match-content.js) picks what the moment
card shows and plays; `slot_for` in `app/api.py` picks the same slot for a
caller. The seven rows they answer are in
[`tests/slot_rows.json`](../tests/slot_rows.json), which both test files read.
