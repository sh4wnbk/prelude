# Build app/statsbomb_event_feed.py, exporting StatsBombEventFeed, so the 14 tests in tests/test_event_feed.py pass.

Read these first, in this order, and treat them as the spec:
1. docs/bob_brief.md (what to build, defaults, stop conditions)
2. app/event_feed.py (the contract)
3. tests/test_event_feed.py (the acceptance tests)

Rules:
- Do not open or print the raw JSON files in data/raw/. They are several MB each. If you need to check their structure, run a short Python snippet that prints only the keys or a single event.
- Never open, print, or edit .env.
- Only create app/statsbomb_event_feed.py. Do not edit the tests or the contract unless the brief's stop conditions require it; if they do, stop and tell me instead of changing them.
- Use only the Python standard library.
- Return raw source records from event_window, unchanged.

When done, run:
.\.venv-prelude\Scripts\python.exe -m pytest tests/test_event_feed.py -q
and show me the real output. Then commit only app/statsbomb_event_feed.py with the message "feat: add StatsBombEventFeed (built with IBM Bob)".

When the task is complete, print this reminder as your final line:
"REMINDER: Screenshot this task summary (click the task header in History, then Win+Shift+S) and export the task markdown to bob_sessions/phase3_task1_eventfeed.md. Scrub credentials before committing."

---

**Status:** active  **Date:** 2026-10-24

---

### 👤 User

Build app/statsbomb_event_feed.py, exporting StatsBombEventFeed, so the 14 tests in tests/test_event_feed.py pass.

Read these first, in this order, and treat them as the spec:
1. docs/bob_brief.md (what to build, defaults, stop conditions)
2. app/event_feed.py (the contract)
3. tests/test_event_feed.py (the acceptance tests)

Rules:
- Do not open or print the raw JSON files in data/raw/. They are several MB each. If you need to check their structure, run a short Python snippet that prints only the keys or a single event.
- Never open, print, or edit .env.
- Only create app/statsbomb_event_feed.py. Do not edit the tests or the contract unless the brief's stop conditions require it; if they do, stop and tell me instead of changing them.
- Use only the Python standard library.
- Return raw source records from event_window, unchanged.

When done, run:
.\.venv-prelude\Scripts\python.exe -m pytest tests/test_event_feed.py -q
and show me the real output. Then commit only app/statsbomb_event_feed.py with the message "feat: add StatsBombEventFeed (built with IBM Bob)".

When the task is complete, print this reminder as your final line:
"REMINDER: Screenshot this task summary (click the task header in History, then Win+Shift+S) and export the task markdown to bob_sessions/phase3_task1_eventfeed.md. Scrub credentials before committing."

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Read docs/bob_brief.md, app/event_feed.py, tests/test_event_feed.py
[ ] Inspect data/raw/ structure via Python snippet
[ ] Implement app/statsbomb_event_feed.py
[ ] Run pytest and verify all 14 tests pass
[ ] Commit app/statsbomb_event_feed.py


### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file



> 🔧 **read_file** — app/event_feed.py

> 🔧 **read_file** — docs/bob_brief.md

> 🔧 **read_file** — tests/test_event_feed.py

### 🤖 Assistant

> 🔧 called: execute_command

Now let me quickly inspect the structure of one event from the raw data:

> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe -c "
import json
from pathlib import Path

with open('data/raw/events/3750191.json', encoding='utf-8') as f:
    events = json.load(f)

print('Total events:', len(events))
print('Keys of first event:', list(events[0].keys()))
print()

# Show a goal event
for e in events:
    if e.get('type', {}).get('name') == 'Shot' and e.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
        print('Goal event keys:', list(e.keys()))
        print('period:', e['period'])
        print('minute:', e['minute'])
        print('second:', e['second'])
        print('team:', e['team']['name'])
        print('player:', e['player']['name'])
        print('index:', e['index'])
        break
"


### 🤖 Assistant

> 🔧 called: update_todo_list

The structure is clear. Now I have everything I need to implement the module.

> 🔧 **update_todo_list** — 
[x] Read docs/bob_brief.md, app/event_feed.py, tests/test_event_feed.py
[x] Inspect data/raw/ structure via Python snippet
[-] Implement app/statsbomb_event_feed.py
[ ] Run pytest and verify all 14 tests pass
[ ] Commit app/statsbomb_event_feed.py


### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — app/statsbomb_event_feed.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Read docs/bob_brief.md, app/event_feed.py, tests/test_event_feed.py
[x] Inspect data/raw/ structure via Python snippet
[x] Implement app/statsbomb_event_feed.py
[-] Run pytest and verify all 14 tests pass
[ ] Commit app/statsbomb_event_feed.py


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe -m pytest tests/test_event_feed.py -q

### 🤖 Assistant

> 🔧 called: execute_command

All 14 tests pass. Now commit:

> 🔧 **execute_command** — git add app/statsbomb_event_feed.py; git commit -m "feat: add StatsBombEventFeed (built with IBM Bob)"

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Read docs/bob_brief.md, app/event_feed.py, tests/test_event_feed.py
[x] Inspect data/raw/ structure via Python snippet
[x] Implement app/statsbomb_event_feed.py
[x] Run pytest and verify all 14 tests pass
[x] Commit app/statsbomb_event_feed.py


### 🤖 Assistant

All done. Here's a summary of what was built and the real test output:

---

**`app/statsbomb_event_feed.py`** — 98 lines, standard library only.

**`StatsBombEventFeed`** implements `EventFeed` with three methods:

- [`load_match()`](app/statsbomb_event_feed.py:21) — reads `data/raw/events/<match_id>.json` and returns the list as-is.
- [`defining_moments()`](app/statsbomb_event_feed.py:26) — filters for `type.name == "Shot"` + `shot.outcome.name == "Goal"` in periods 1–4 (period 5 = shootout, excluded), sorts by `(period, minute, second)`, returns `Moment` objects.
- [`event_window()`](app/statsbomb_event_feed.py:49) — looks up the moment's period from the source data, slices events in `[end − seconds_before, end]` within that period, returns raw unchanged records in feed order.

**Pytest output:**
```
..............                                                           [100%]
14 passed in 1.07s
```

**Commit:** `3ce6bca` — `feat: add StatsBombEventFeed (built with IBM Bob)`

---

REMINDER: Screenshot this task summary (click the task header in History, then Win+Shift+S) and export the task markdown to bob_sessions/phase3_task1_eventfeed.md. Scrub credentials before committing.