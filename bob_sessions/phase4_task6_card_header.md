# Read CLAUDE.md and docs/bob_brief.md, section "Task 6: the header on the moment card". Build exactly the three changes it lists and nothing else. Do not edit any test, any doc, app/orchestrator.py, app/orchestrator_contract.py or app/statsbomb_event_feed.py. Run the script once to write the openings. Run .\.venv-prelude\Scripts\python.exe -m pytest -q and report the real output; the target is 0 failed. Run the four gate scripts and report each exit code; check_docs failing on scripts/write_headers.py being listed as absent is expected. If anything does not fit the brief, stop and report it. Commit and push. When done, print the reminder in the brief's "When you are done".

---

**Status:** active  **Date:** 2026-10-29

---

### 👤 User

Read CLAUDE.md and docs/bob_brief.md, section "Task 6: the header on the moment card". Build exactly the three changes it lists and nothing else. Do not edit any test, any doc, app/orchestrator.py, app/orchestrator_contract.py or app/statsbomb_event_feed.py. Run the script once to write the openings. Run .\.venv-prelude\Scripts\python.exe -m pytest -q and report the real output; the target is 0 failed. Run the four gate scripts and report each exit code; check_docs failing on scripts/write_headers.py being listed as absent is expected. If anything does not fit the brief, stop and report it. Commit and push. When done, print the reminder in the brief's "When you are done".

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

Let me start by reading the required documents.

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\CLAUDE.md

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\docs\bob_brief.md

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\docs\bob_brief.md

### 🤖 Assistant

> 🔧 called: read_file, read_file

Now let me explore the existing codebase to understand what's there:

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\app\web\matches.json

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\tests\test_moment_card_header.py

### 🤖 Assistant

> 🔧 called: read_file, read_file

Now let me read the orchestrator to understand `greeting_word` and `header`:

> 🔧 **read_file** — greeting_word and header functions, ScoringMoment, Event, parameters they take

> 🔧 **read_file** — h1 heading, hero_header, You stepped away buildup, classes around it

### 🤖 Assistant

> 🔧 called: read_file, read_file

Now let me read the orchestrator contract to understand the `Event` and `ScoringMoment` structures, and the `match-content.js` for the `renderHero` function:

> 🔧 **read_file** — Event, ScoringMoment dataclass fields, kickoff, team_a, team_b, scoring_side, score_a, score_b, score_before_a, score_before_b, minute, second, regulation_minutes

> 🔧 **read_file** — renderHero function, hero_caption, how data fields are set

### 🤖 Assistant

> 🔧 called: read_file

Now let me look at the StatsBomb event feed interface:

> 🔧 **read_file** — defining_moments method signature, what it returns, DefiningMoment structure, event fields

### 🤖 Assistant

> 🔧 called: read_file

Now I have everything I need. Let me understand what the script needs to do:

1. `defining_moments(match_id)` returns `Moment` objects with `team`, `player`, `minute`, `second`, `type` fields
2. The hero event in `matches.json` has `period`, `minute`, `second`, `player`, `team`, `shot_type`
3. Match the hero event to a `Moment` from `defining_moments()` by `minute`, `second`, `player`, `team`
4. Count goals before the hero to get `score_before`, then after = `score_before + 1`
5. Build `Event` with kickoff from `picker.kickoff`, `team_a=home_team`, `team_b=away_team`, `sport="football"`
6. Build `ScoringMoment` with scoring_side, scores, minute, second, `regulation_minutes=90`

Let me also check the `Moment` dataclass:

> 🔧 **read_file** — Moment dataclass fields

### 🤖 Assistant

> 🔧 called: update_todo_list

Now I have a complete picture. Let me set up the todo list and build the three changes:

> 🔧 **update_todo_list** — 
[-] Create scripts/write_headers.py
[ ] Edit app/web/prelude_03_moment_card.html (add data-field="hero_header", update inline text)
[ ] Edit app/web/match-content.js (set hero_header in renderHero from opening.header)
[ ] Run script to write openings to matches.json
[ ] Run pytest and report output
[ ] Run four gate scripts and report exit codes
[ ] Commit and push


### 🤖 Assistant

> 🔧 called: write_file

Now I'll create `scripts/write_headers.py`. The key logic:
- For each match in `matches.json`, find the hero goal among `defining_moments(match_id)` by matching `minute`, `second`, `player`, `team`
- Count goals before the hero to determine `score_before_a` / `score_before_b`
- Build `Event` with `kickoff` as a `datetime` from `picker.kickoff`, `team_a=home_team`, `team_b=away_team`, `sport="football"`, `regulation_minutes=90`
- Call `greeting_word(event)` and `header(event, moment)` from `app/orchestrator.py`

> 🔧 **write_file** — c:\Users\shawn\Documents\src\prelude\scripts\write_headers.py

### 🤖 Assistant

> 🔧 called: search_and_replace

Now edit the HTML to add `data-field="hero_header"` to the `<h1>` and update its inline text. The brief says to set the text to the 1986 header exactly as the script writes it: `"Argentina extend the lead. Argentina 2, England 0. Here's the buildup."`:

> 🔧 **search_and_replace** — c:\Users\shawn\Documents\src\prelude\app\web\prelude_03_moment_card.html

### 🤖 Assistant

> 🔧 called: read_file

The file has all its content on a few lines. Let me check the exact content around the h1:

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\app\web\prelude_03_moment_card.html

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — c:\Users\shawn\Documents\src\prelude\app\web\prelude_03_moment_card.html

### 🤖 Assistant

> 🔧 called: apply_diff

Now edit [`match-content.js`](app/web/match-content.js) to set `hero_header` from `match.hero.opening.header` in `renderHero`:

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:206
-------
  function renderHero(match) {
    if (!field("hero_caption")) return;
    setText("hero_caption", match.hero.caption);
    setText("hero_quote", match.hero.quote);
=======
  function renderHero(match) {
    if (!field("hero_caption")) return;
    setText("hero_caption", match.hero.caption);
    if (match.hero.opening) {
      setText("hero_header", match.hero.opening.header);
    }
    setText("hero_quote", match.hero.quote);
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Create scripts/write_headers.py
[x] Edit app/web/prelude_03_moment_card.html (add data-field="hero_header", update inline text)
[x] Edit app/web/match-content.js (set hero_header in renderHero from opening.header)
[-] Run script to write openings to matches.json
[ ] Run pytest and report output
[ ] Run four gate scripts and report exit codes
[ ] Commit and push


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts\write_headers.py

### 🤖 Assistant

> 🔧 called: read_file

Good. Let me verify what was written:

> 🔧 **read_file** — hero.opening field for both matches

### 🤖 Assistant

> 🔧 called: update_todo_list

Both openings match the expected values exactly. Now run pytest:

> 🔧 **update_todo_list** — 
[x] Create scripts/write_headers.py
[x] Edit app/web/prelude_03_moment_card.html (add data-field="hero_header", update inline text)
[x] Edit app/web/match-content.js (set hero_header in renderHero from opening.header)
[x] Run script to write openings to matches.json
[-] Run pytest and report output
[ ] Run four gate scripts and report exit codes
[ ] Commit and push


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe -m pytest -q 2>&1

### 🤖 Assistant

> 🔧 called: update_todo_list

442 passed, 0 failed. Now run the four gate scripts:

> 🔧 **update_todo_list** — 
[x] Create scripts/write_headers.py
[x] Edit app/web/prelude_03_moment_card.html (add data-field="hero_header", update inline text)
[x] Edit app/web/match-content.js (set hero_header in renderHero from opening.header)
[x] Run script to write openings to matches.json
[x] Run pytest and report output
[-] Run four gate scripts and report exit codes
[ ] Commit and push


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts\data_check.py; Write-Host "data_check exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts\scan_copy.py; Write-Host "scan_copy exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts\check_match_copy.py; Write-Host "check_match_copy exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts\check_docs.py; Write-Host "check_docs exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command

`check_docs` failed with exit code 1. The brief says:

> `check_docs.py` will fail on this brief naming `scripts/write_headers.py` as unbuilt and on test counts; that is expected and is Claude Code's follow-up. Any other gate failure is yours to report.

All four failures are exactly the ones the brief says are expected: the `write_headers.py` being listed as absent (in 3 docs) and the test count mismatch. No unexpected failures. Exit code from `check_docs` was not captured (timed out) — let me get that:

> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts\check_docs.py 2>&1; $ec = $LASTEXITCODE; Write-Host "check_docs exit: $ec"

### 🤖 Assistant

> 🔧 called: update_todo_list

All four stale claims are exactly what the brief predicts. Now commit and push:

> 🔧 **update_todo_list** — 
[x] Create scripts/write_headers.py
[x] Edit app/web/prelude_03_moment_card.html (add data-field="hero_header", update inline text)
[x] Edit app/web/match-content.js (set hero_header in renderHero from opening.header)
[x] Run script to write openings to matches.json
[x] Run pytest and report output
[x] Run four gate scripts and report exit codes
[-] Commit and push


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — git add scripts/write_headers.py app/web/matches.json app/web/prelude_03_moment_card.html app/web/match-content.js; git status

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — git commit -m "Task 6: put orchestrator header on the moment card

- scripts/write_headers.py: computes greeting_word + header from
  StatsBombEventFeed().defining_moments() and writes hero.opening into
  app/web/matches.json; --check mode exits 1 on drift, --path for alt files
- app/web/matches.json: hero.opening written by the script for both matches
- app/web/prelude_03_moment_card.html: h1 gets data-field=\"hero_header\";
  inline text is the 1986 header (Argentina extend the lead. Argentina 2,
  England 0. Here's the buildup.)
- app/web/match-content.js: renderHero sets hero_header from
  match.hero.opening.header when opening is present

442 passed, 0 failed"

### 🤖 Assistant

> 🔧 called: execute_command

Need to use a file for the commit message to avoid quoting issues in PowerShell:

> 🔧 **execute_command** — $msg = @"
Task 6: put orchestrator header on the moment card

- scripts/write_headers.py: computes greeting_word + header from
  StatsBombEventFeed().defining_moments() and writes hero.opening into
  app/web/matches.json; --check mode exits 1 on drift, --path for alt files
- app/web/matches.json: hero.opening written by the script for both matches
- app/web/prelude_03_moment_card.html: h1 gets data-field=hero_header;
  inline text is the 1986 header
- app/web/match-content.js: renderHero sets hero_header from
  match.hero.opening.header when opening is present

442 passed, 0 failed
"@
$msg | git commit -F -

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — git push

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Create scripts/write_headers.py
[x] Edit app/web/prelude_03_moment_card.html (add data-field="hero_header", update inline text)
[x] Edit app/web/match-content.js (set hero_header in renderHero from opening.header)
[x] Run script to write openings to matches.json
[x] Run pytest and report output
[x] Run four gate scripts and report exit codes
[x] Commit and push


### 🤖 Assistant

Done. Here's the summary:

---

**Three changes built:**

1. **[`scripts/write_headers.py`](scripts/write_headers.py)** — New script. For each match in `app/web/matches.json`, locates the hero goal in `StatsBombEventFeed().defining_moments()`, counts preceding goals to derive `score_before_*`, builds `Event` and `ScoringMoment`, calls `greeting_word` and `header` from `app/orchestrator.py`, and writes `hero.opening = {"greeting": ..., "header": ...}`. Exposes `openings()`, supports `--check` (exit 1 on drift, writes nothing) and `--path`.

2. **[`app/web/prelude_03_moment_card.html`](app/web/prelude_03_moment_card.html)** — The `<h1>` now carries `data-field="hero_header"` and its inline text is the 1986 header: `"Argentina extend the lead. Argentina 2, England 0. Here's the buildup."` The old "You stepped away..." text is gone.

3. **[`app/web/match-content.js`](app/web/match-content.js)** — `renderHero` now sets `hero_header` from `match.hero.opening.header` when `opening` is present, the same way `hero_caption` is set.

**Results:**
- Script wrote both openings: matches expected values exactly
- `pytest -q`: **442 passed, 0 failed**
- `data_check.py`: exit 0
- `scan_copy.py`: exit 0
- `check_match_copy.py`: exit 0
- `check_docs.py`: exit 1 — 4 stale claims (3× `write_headers.py` listed as absent, 1× test count `10 failed, 432 passed` vs current `442 passed`) — all expected per the brief

Commit: `aab7093` pushed to `main`.

---

> Export this session to `bob_sessions/phase4_task6_card_header.md` and `.png`, scrub it against the list in `bob_sessions/README.md` before committing, and check the diff rather than the commit.