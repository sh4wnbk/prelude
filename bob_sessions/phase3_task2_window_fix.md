# Fix a bug in app/statsbomb_event_feed.py, then tighten the test that missed it.

The bug: docs/bob_brief.md says an event window ends with the event the moment was built from (the goal shot). event_window filters by clock time only, so when StatsBomb records the goalkeeper's reaction at the same second as the shot, that later event is included and the window ends on it. This happens for 6 of the 9 goals across the two matches.

Fix: in event_window, find the goal shot's source event (you already locate it to get the period), and exclude any event whose "index" is greater than that shot's index. Keep everything else the same: raw records unchanged, same period only, feed order.

Also remove the module-level assert at the bottom of the file; checking the protocol is the tests' job, not something to run on import.

Then strengthen test_window_ends_at_the_moment in tests/test_event_feed.py so it checks the last event is the goal shot itself: its type name is "Shot", its shot outcome name is "Goal", and its minute and second match the moment. Change only that test.

Rules: do not open the raw JSON files in data/raw/ or .env. Standard library only.

Run:
.\.venv-prelude\Scripts\python.exe -m pytest tests/test_event_feed.py -q
and show the real output. Commit both files with the message "fix: end event windows at the goal shot (built with IBM Bob)".

When the task is complete, print this reminder as your final line:
"REMINDER: Screenshot this task summary and export the task markdown to bob_sessions/phase3_task2_window_fix.md. Scrub credentials before committing."

---

**Status:** active  **Date:** 2026-10-24

---

### 👤 User

Fix a bug in app/statsbomb_event_feed.py, then tighten the test that missed it.

The bug: docs/bob_brief.md says an event window ends with the event the moment was built from (the goal shot). event_window filters by clock time only, so when StatsBomb records the goalkeeper's reaction at the same second as the shot, that later event is included and the window ends on it. This happens for 6 of the 9 goals across the two matches.

Fix: in event_window, find the goal shot's source event (you already locate it to get the period), and exclude any event whose "index" is greater than that shot's index. Keep everything else the same: raw records unchanged, same period only, feed order.

Also remove the module-level assert at the bottom of the file; checking the protocol is the tests' job, not something to run on import.

Then strengthen test_window_ends_at_the_moment in tests/test_event_feed.py so it checks the last event is the goal shot itself: its type name is "Shot", its shot outcome name is "Goal", and its minute and second match the moment. Change only that test.

Rules: do not open the raw JSON files in data/raw/ or .env. Standard library only.

Run:
.\.venv-prelude\Scripts\python.exe -m pytest tests/test_event_feed.py -q
and show the real output. Commit both files with the message "fix: end event windows at the goal shot (built with IBM Bob)".

When the task is complete, print this reminder as your final line:
"REMINDER: Screenshot this task summary and export the task markdown to bob_sessions/phase3_task2_window_fix.md. Scrub credentials before committing."

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Read and understand the current code in app/statsbomb_event_feed.py
[ ] Read the current test in tests/test_event_feed.py
[ ] Fix the event_window bug (exclude events with index > shot's index)
[ ] Remove the module-level assert
[ ] Strengthen the test_window_ends_at_the_moment test
[ ] Run pytest and verify all tests pass
[ ] Commit both files with the specified message


### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — tests/test_event_feed.py

> 🔧 **read_file** — app/statsbomb_event_feed.py

### 🤖 Assistant

> 🔧 called: update_todo_list

Now I have a clear picture of both files. Let me make the changes:

1. **Bug fix**: In `event_window`, capture the source event's `index` and filter out events with a higher index
2. **Remove module-level assert**
3. **Strengthen the test** to verify the last event is actually the Shot/Goal

> 🔧 **update_todo_list** — 
[x] Read and understand the current code in app/statsbomb_event_feed.py
[x] Read the current test in tests/test_event_feed.py
[-] Fix the event_window bug (exclude events with index > shot's index)
[ ] Remove the module-level assert
[ ] Strengthen the test_window_ends_at_the_moment test
[ ] Run pytest and verify all tests pass
[ ] Commit both files with the specified message


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — app/statsbomb_event_feed.py

### 🤖 Assistant

> 🔧 called: update_todo_list

Now strengthen the test:

> 🔧 **update_todo_list** — 
[x] Read and understand the current code in app/statsbomb_event_feed.py
[x] Read the current test in tests/test_event_feed.py
[x] Fix the event_window bug (exclude events with index > shot's index)
[x] Remove the module-level assert
[-] Strengthen the test_window_ends_at_the_moment test
[ ] Run pytest and verify all tests pass
[ ] Commit both files with the specified message


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — tests/test_event_feed.py

### 🤖 Assistant

> 🔧 called: update_todo_list

Now run the tests:

> 🔧 **update_todo_list** — 
[x] Read and understand the current code in app/statsbomb_event_feed.py
[x] Read the current test in tests/test_event_feed.py
[x] Fix the event_window bug (exclude events with index > shot's index)
[x] Remove the module-level assert
[x] Strengthen the test_window_ends_at_the_moment test
[-] Run pytest and verify all tests pass
[ ] Commit both files with the specified message


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe -m pytest tests/test_event_feed.py -q

### 🤖 Assistant

> 🔧 called: update_todo_list

All 14 tests pass. Now commit:

> 🔧 **update_todo_list** — 
[x] Read and understand the current code in app/statsbomb_event_feed.py
[x] Read the current test in tests/test_event_feed.py
[x] Fix the event_window bug (exclude events with index > shot's index)
[x] Remove the module-level assert
[x] Strengthen the test_window_ends_at_the_moment test
[x] Run pytest and verify all tests pass
[-] Commit both files with the specified message


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — git add app/statsbomb_event_feed.py tests/test_event_feed.py; git commit -m "fix: end event windows at the goal shot (built with IBM Bob)"

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Read and understand the current code in app/statsbomb_event_feed.py
[x] Read the current test in tests/test_event_feed.py
[x] Fix the event_window bug (exclude events with index > shot's index)
[x] Remove the module-level assert
[x] Strengthen the test_window_ends_at_the_moment test
[x] Run pytest and verify all tests pass
[x] Commit both files with the specified message


### 🤖 Assistant

All done. Here's a summary of every change made:

---

### [`app/statsbomb_event_feed.py`](app/statsbomb_event_feed.py)

**Bug fix — `event_window`**: Instead of extracting only `event["period"]` from the source shot, the code now captures the whole `source_event` and reads both `source_event["period"]` and `source_event["index"]`. The window filter gains a third condition `and event["index"] <= shot_index`, which excludes any event (like a goalkeeper reaction logged at the same clock second) that follows the goal shot in feed order.

**Removed**: The module-level `assert isinstance(StatsBombEventFeed(), EventFeed)` — that check is the tests' responsibility, not something that should run on every import.

---

### [`tests/test_event_feed.py`](tests/test_event_feed.py)

**`test_window_ends_at_the_moment`**: Added two new assertions on `last` before the clock check:
- `last["type"]["name"] == "Shot"` — the final event is a shot
- `last["shot"]["outcome"]["name"] == "Goal"` — it's the goal itself

This is the assertion that would have caught the original bug (a goalkeeper-reaction event at the same second would fail the `type["name"] == "Shot"` check).

---

**Test output:**
```
..............
14 passed in 1.04s
```

REMINDER: Screenshot this task summary and export the task markdown to bob_sessions/phase3_task2_window_fix.md. Scrub credentials before committing.