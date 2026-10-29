# Read CLAUDE.md and docs/bob_brief.md, section "Task 9: the 'Who are you with' card". Build exactly the three changes it lists and nothing else: no tests, no docs, no Python, no other screen, no persona choice, no Profile tab. Copy every piece of wording exactly as given. Run .\.venv-prelude\Scripts\python.exe -m pytest -q and report the real output; the target is 0 failed. Run the four gate scripts and report each exit code; check_docs failing on app/web/listener-card.js being listed as absent is expected. If anything does not fit the brief, stop and report it. Commit and push. When done, print the reminder in the brief's "When you are done".

---

**Status:** active  **Date:** 2026-10-29

---

### 👤 User

Read CLAUDE.md and docs/bob_brief.md, section "Task 9: the 'Who are you with' card". Build exactly the three changes it lists and nothing else: no tests, no docs, no Python, no other screen, no persona choice, no Profile tab. Copy every piece of wording exactly as given. Run .\.venv-prelude\Scripts\python.exe -m pytest -q and report the real output; the target is 0 failed. Run the four gate scripts and report each exit code; check_docs failing on app/web/listener-card.js being listed as absent is expected. If anything does not fit the brief, stop and report it. Commit and push. When done, print the reminder in the brief's "When you are done".

---

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\CLAUDE.md

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\docs\bob_brief.md

### 🤖 Assistant

> 🔧 called: grep

The brief file is large. Let me read the Task 9 section specifically.

> 🔧 **grep** — Task 9

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\docs\bob_brief.md

### 🤖 Assistant

> 🔧 called: list_files, glob

Now let me explore the existing codebase to understand the structure:

> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude\app\web

> 🔧 **glob** — tests/test_listener_card.py

### 🤖 Assistant

> 🔧 called: read_file, read_file

The test file doesn't exist yet. Let me read the existing files I need to understand:

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\app\web\match-content.js

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\app\web\manual-entry.js

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — state_badge, script loading, listener-card, match-content.js loading

### 🤖 Assistant

> 🔧 called: list_files, list_files

Now let me look at the tests directory to understand what tests already exist, and look for the test file spec:

> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude\tests

> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — all test cases and assertions for listener card

### 🤖 Assistant

> 🔧 called: glob

Now I have a clear picture. Let me also check the gate scripts:

> 🔧 **glob** — c:\Users\shawn\Documents\src\prelude\scripts

### 🤖 Assistant

> 🔧 called: glob



> 🔧 **glob** — c:\Users\shawn\Documents\src\prelude\scripts

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — gate scripts, four gate scripts

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — four gate scripts, gate commands to run

### 🤖 Assistant

> 🔧 called: read_file

Let me look at previous task gates to understand what "four gates" means:

> 🔧 **read_file** — four gate scripts, commands to run them

### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — c:\Users\shawn\Documents\src\prelude\docs\bob_brief.md

### 🤖 Assistant

> 🔧 called: update_todo_list

The four gates are: `scripts/data_check.py`, `scripts/scan_copy.py`, `scripts/check_match_copy.py`, `scripts/check_docs.py`.

Now I have a complete picture. Let me set up the todo list and start implementing:

> 🔧 **update_todo_list** — 
[-] 1. Add storage helpers and headerWithName to match-content.js (listenerFor, setListener, nameFor, setName, headerWithName, update renderHero, add to window.Prelude)
[ ] 2. Create app/web/listener-card.js (new file)
[ ] 3. Update prelude_02_live_seated.html (add script tag, add whitespace-nowrap to state_badge)
[ ] 4. Run pytest and report output
[ ] 5. Run four gate scripts and report exit codes
[ ] 6. Commit and push


### 🤖 Assistant

> 🔧 called: apply_diff

Now let me implement Change 1 — the storage helpers in `match-content.js`:

> 🔧 **apply_diff** — c:\Users\shawn\Documents\src\prelude\app\web\match-content.js

### 🤖 Assistant

> 🔧 called: apply_diff

Now update `renderHero` and `window.Prelude` in the same file:

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:261
-------
  function renderHero(match) {
    if (!field("hero_caption")) return;
    setText("hero_caption", match.hero.caption);
    if (match.hero.opening) {
      setText("hero_header", match.hero.opening.header);
    }
=======
  function renderHero(match) {
    if (!field("hero_caption")) return;
    setText("hero_caption", match.hero.caption);
    if (match.hero.opening) {
      setText("hero_header", headerWithName(match.hero.opening.header, nameFor()));
    }
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:186
-------
  window.Prelude = {
    matchId: MATCH_ID, url: url, defaultMatch: DEFAULT_MATCH,
    momentSeen: momentSeen, markMomentSeen: markMomentSeen,
    resetMoment: resetMoment, ticketFor: ticketFor, setTicket: setTicket,
    ticketLine: ticketLine, whenMatches: whenMatches, matches: null
  };
=======
  window.Prelude = {
    matchId: MATCH_ID, url: url, defaultMatch: DEFAULT_MATCH,
    momentSeen: momentSeen, markMomentSeen: markMomentSeen,
    resetMoment: resetMoment, ticketFor: ticketFor, setTicket: setTicket,
    ticketLine: ticketLine, whenMatches: whenMatches, matches: null,
    listenerFor: listenerFor, setListener: setListener,
    nameFor: nameFor, setName: setName, headerWithName: headerWithName
  };
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] 1. Add storage helpers and headerWithName to match-content.js (listenerFor, setListener, nameFor, setName, headerWithName, update renderHero, add to window.Prelude)
[-] 2. Create app/web/listener-card.js (new file)
[ ] 3. Update prelude_02_live_seated.html (add script tag, add whitespace-nowrap to state_badge)
[ ] 4. Run pytest and report output
[ ] 5. Run four gate scripts and report exit codes
[ ] 6. Commit and push


### 🤖 Assistant

> 🔧 called: write_file

Now let me create `app/web/listener-card.js`. Key requirements from the brief:
- Uses `Prelude.whenMatches`, finds the match by `match_id === Prelude.matchId`
- Does nothing if no match or fetch failed
- Shows overlay if `Prelude.listenerFor(Prelude.matchId)` is `null`
- Question: `"Who are you with " + match.hero.opening.greeting + "?"`
- Three choice buttons: home_team (team_a), away_team (team_b), "Just here for the game" (neutral)
- Choosing marks with `aria-pressed="true"`, clears others
- Text field labelled `What should we call you?`, `placeholder="Optional"`, prefilled with `Prelude.nameFor() || ""`
- `Continue` button, disabled until a choice is made
- Markup style: like `manual-entry.js`, string assigned once with `innerHTML`, uses `FIELD` and `LABEL` class strings, Continue button classes
- Only classes already used in `app/web/`
- Choice buttons: `bg-surface-container` (unselected) and `bg-primary-container` (selected)
- Name never goes into `innerHTML` string
- Field named `listener-call` (not "name")
- Single `container.innerHTML = markup(match);`

> 🔧 **write_file** — c:\Users\shawn\Documents\src\prelude\app\web\listener-card.js

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] 1. Add storage helpers and headerWithName to match-content.js (listenerFor, setListener, nameFor, setName, headerWithName, update renderHero, add to window.Prelude)
[x] 2. Create app/web/listener-card.js (new file)
[-] 3. Update prelude_02_live_seated.html (add script tag, add whitespace-nowrap to state_badge)
[ ] 4. Run pytest and report output
[ ] 5. Run four gate scripts and report exit codes
[ ] 6. Commit and push


### 🤖 Assistant

> 🔧 called: apply_diff

Now Change 3 — update `prelude_02_live_seated.html`. I need to:
1. Add `<script src="listener-card.js?v=__V__"></script>` after `match-content.js`
2. Add `whitespace-nowrap` to the `state_badge` span's classes

> 🔧 **apply_diff** — c:\Users\shawn\Documents\src\prelude\app\web\prelude_02_live_seated.html

### 🤖 Assistant

> 🔧 called: update_todo_list

Now let me run the tests:

> 🔧 **update_todo_list** — 
[x] 1. Add storage helpers and headerWithName to match-content.js (listenerFor, setListener, nameFor, setName, headerWithName, update renderHero, add to window.Prelude)
[x] 2. Create app/web/listener-card.js (new file)
[x] 3. Update prelude_02_live_seated.html (add script tag, add whitespace-nowrap to state_badge)
[-] 4. Run pytest and report output
[ ] 5. Run four gate scripts and report exit codes
[ ] 6. Commit and push


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe -m pytest -q 2>&1

### 🤖 Assistant

> 🔧 called: update_todo_list

475 passed, 0 failed. Now run the four gate scripts:

> 🔧 **update_todo_list** — 
[x] 1. Add storage helpers and headerWithName to match-content.js (listenerFor, setListener, nameFor, setName, headerWithName, update renderHero, add to window.Prelude)
[x] 2. Create app/web/listener-card.js (new file)
[x] 3. Update prelude_02_live_seated.html (add script tag, add whitespace-nowrap to state_badge)
[x] 4. Run pytest and report output
[-] 5. Run four gate scripts and report exit codes
[ ] 6. Commit and push


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts/data_check.py; Write-Host "data_check exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts/scan_copy.py; Write-Host "scan_copy exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts/check_match_copy.py; Write-Host "check_match_copy exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts/check_docs.py; Write-Host "check_docs exit: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: execute_command

Both `check_docs.py` failures are exactly as predicted in the brief:
1. The quoted pytest result in the brief no longer matches (expected)
2. `app/web/listener-card.js` now exists but is listed as absent (expected — the brief says this is the follow-up's work)

Exit code timed out before reporting — let me check it directly:

> 🔧 **execute_command** — .\.venv-prelude\Scripts\python.exe scripts/check_docs.py 2>&1; $ec = $LASTEXITCODE; Write-Host "exit: $ec"

### 🤖 Assistant

> 🔧 called: update_todo_list

`check_docs.py` exits 1 for exactly the two expected reasons. Both are the follow-up's work per the brief. No other gate failures.

Now commit and push:

> 🔧 **update_todo_list** — 
[x] 1. Add storage helpers and headerWithName to match-content.js (listenerFor, setListener, nameFor, setName, headerWithName, update renderHero, add to window.Prelude)
[x] 2. Create app/web/listener-card.js (new file)
[x] 3. Update prelude_02_live_seated.html (add script tag, add whitespace-nowrap to state_badge)
[x] 4. Run pytest and report output
[x] 5. Run four gate scripts and report exit codes
[-] 6. Commit and push


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — git add app/web/listener-card.js app/web/match-content.js app/web/prelude_02_live_seated.html; git commit -m "Task 9: the \"Who are you with\" card

- match-content.js: add listenerFor, setListener, nameFor, setName,
  headerWithName; update renderHero to use headerWithName; expose all
  five on window.Prelude
- listener-card.js: new file; full-screen overlay on the Live screen
  asking the fan who they are with and what to call them; answer kept
  in sessionStorage only
- prelude_02_live_seated.html: load listener-card.js after
  match-content.js; add whitespace-nowrap to state_badge"

### 🤖 Assistant

> 🔧 called: execute_command

Multi-line commit message needs a different approach in PowerShell:

> 🔧 **execute_command** — git add app/web/listener-card.js app/web/match-content.js app/web/prelude_02_live_seated.html

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — $msg = @"
Task 9: the "Who are you with" card

- match-content.js: add listenerFor, setListener, nameFor, setName,
  headerWithName; update renderHero to use headerWithName; expose all
  five on window.Prelude
- listener-card.js: new file; full-screen overlay on the Live screen
  asking the fan who they are with and what to call them; answer kept
  in sessionStorage only
- prelude_02_live_seated.html: load listener-card.js after
  match-content.js; add whitespace-nowrap to state_badge
"@
git commit -m $msg

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — $msg = 'Task 9: the Who are you with card'; git commit -m $msg

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — git push

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] 1. Add storage helpers and headerWithName to match-content.js (listenerFor, setListener, nameFor, setName, headerWithName, update renderHero, add to window.Prelude)
[x] 2. Create app/web/listener-card.js (new file)
[x] 3. Update prelude_02_live_seated.html (add script tag, add whitespace-nowrap to state_badge)
[x] 4. Run pytest and report output
[x] 5. Run four gate scripts and report exit codes
[x] 6. Commit and push


### 🤖 Assistant

Done. Here's the summary:

**Three changes built:**

1. **[`app/web/match-content.js`](app/web/match-content.js)** — Added `listenerFor`, `setListener`, `nameFor`, `setName`, `headerWithName` (all with `try`/`catch`); updated `renderHero` to call `setText("hero_header", headerWithName(..., nameFor()))`; exposed all five on `window.Prelude`.

2. **[`app/web/listener-card.js`](app/web/listener-card.js)** *(new)* — Full-screen overlay using `Prelude.whenMatches`; shows the question `"Who are you with " + greeting + "?"`, three choice buttons (home/away/neutral), an optional name field labelled `What should we call you?`, and a disabled-until-chosen `Continue` button. Name is set via `.value` only, never via `innerHTML`. Sends nothing anywhere.

3. **[`app/web/prelude_02_live_seated.html`](app/web/prelude_02_live_seated.html)** — Added `<script src="listener-card.js?v=__V__"></script>` after `match-content.js`; added `whitespace-nowrap` to the `state_badge` span.

**Test results:**
```
475 passed in 30.02s
```

**Gate script exit codes:**
- `data_check.py` → **0**
- `scan_copy.py` → **0**
- `check_match_copy.py` → **0**
- `check_docs.py` → **1** (two expected failures only: the quoted pytest result in the brief, and `listener-card.js` listed as absent — both are the follow-up's work per the brief)

---

> Export this session to `bob_sessions/phase4_task9_listener_card.md` and `.png`, scrub it against the list in `bob_sessions/README.md` before committing, and check the diff rather than the commit.