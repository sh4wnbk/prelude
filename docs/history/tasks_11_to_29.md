# Tasks 11 to 29

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

Every task record from Task 29 back to the second Task 11 list, in the order the file held them, which is newest first.

---

### Task 29: the label waits for the words it is about (done)

**What Shawn saw on 2026-11-12.** On the moment card the inline fallback
narration, the 1986 text, showed under a 2022 header and under "Verified from
play data" until `narrations.json` arrived. A fan on a slow connection can read
the wrong match's narration under the label. Task 28's harness note above had
already caught the same screen and read it as a harness problem.

**It reproduces, and the two trees say so side by side.** Both `app/web/` at
`375e3b5` and the working tree were served by a server that sleeps two seconds
before answering `narrations.json`, and the 2022 card was read one second in:

| Served tree | Header | Narration shown | Label shown | The words |
| ----------- | ------ | --------------- | ----------- | --------- |
| `375e3b5` | Argentina 2, France 0 | yes | yes | the 1986 narration |
| the fix | Argentina 2, France 0 | no | no | none |

Both then settle on the 2022 narration with the label when the fetch lands.
The delay has to be the server's: a `time.sleep` inside a Playwright route
handler blocks the driver's own event loop, so the first attempt at this
reported a state that had already moved on. That mistake is worth not
repeating.

**The narration is now the one field on this card with no inline copy**, and so
the one with no fallback. Every other field carries the default match's copy,
which leaves a correct screen when a fetch fails; this one cannot take that
bargain, because it arrives under a label that says the data proves it, and the
1986 words prove nothing about 2022. The paragraph ships empty, it and the
label ship with `style="display:none"`, and `showNarration` in
`app/web/match-content.js` sets the text and then clears the `display` on both.
There is no path that shows one without the other, and `.catch` leaves both as
they shipped. A match `narrations.json` does not hold, and a slot with no text,
both return before the reveal.

**The space is kept rather than collapsed**, so the player below does not move
when the words appear. The block carries `min-height:16.75rem`, which is 268 px
at 390 px wide: the six frozen narrations measured 216, 242, 242, 216, 242 and
268 px with the label, so the reservation is the tallest of them. Across every
state checked below the block measured 268 px in every recorded frame.

**`scripts/check_match_copy.py`'s hold moved with the copy.** It no longer
holds the markup to the neutral narration, because the markup carries none:
`check_card_carries_no_narration` refuses any of the six frozen narrations
inline on the card, which is the text the card can show. The per-slot checks
the old `frozen_narration` also did are unchanged under the name
`check_frozen_narrations`, and the `storyteller_neutral` check it made is now
about the renderer's fallback key rather than about the markup.

**`TestTheNarrationAndTheLabelAppearTogether` in
`tests/test_frozen_narrations.py` is seven tests**, and the state before the
fetch resolves is the shipped markup, which is what lets them read it: both
elements hidden, the paragraph empty, the block keeping its space, then that
`showNarration` shows the two together and in that order, that nothing else in
the renderer reaches either of them, that the words are the served slot's, that
the catch arm reveals nothing, and that a match with no frozen narration
returns first. Two helpers lift one brace-matched function out of
`match-content.js`, because a test searching the whole file could not tell the
one reveal from a second one elsewhere. `TestTheNarrationOnTheMomentCard` lost
the two tests that held the inline copy in place and gained two that hold its
absence, so that class is still nine tests and the file is 37, up from thirty.

**Each of the seven was run against the broken code.** Seven mutations were
applied to the working tree in turn, the file was run, and the tree restored:

| Mutation | Refused by |
| -------- | ---------- |
| the paragraph ships shown | `test_the_paragraph_ships_empty`, `test_before_the_fetch_resolves_neither_is_shown` |
| the label ships shown | `test_before_the_fetch_resolves_neither_is_shown` |
| the block keeps no space | `test_the_block_keeps_the_space_while_they_are_hidden` |
| the 1986 narration back inline | `test_no_narration_is_in_the_markup_at_all`, two more, and `check_match_copy.py` |
| the reveal moved out of `showNarration` | `test_showNarration_shows_the_two_together`, `test_nothing_else_in_the_renderer_shows_either_of_them` |
| the catch arm showing words | `test_a_failing_fetch_leaves_both_hidden`, `test_nothing_else_in_the_renderer_shows_either_of_them` |
| the paragraph written by `setText` again | three tests |

**Driven in headless Chromium at 390 by 844**, against the working tree served
over HTTP. Two matches by four narrator states (unset, the Storyteller, the
Buddy, and the Caller, which the picker refuses but which storage could still
hold) by four listener states (unanswered, `team_a`, `team_b`, `neutral`), so
32 combinations, each in six load states: a first load with storage cleared, a
refresh, the tab closed and a new one opened, a slow load with `matches.json`
and `narrations.json` each delayed two seconds by the server, `narrations.json`
answered `503`, and `narrations.json` never answered at all.

A `MutationObserver` was installed before any of the page's own scripts ran, so
every state the block passed through was recorded rather than sampled. Three
rules were asked of every recorded frame, not only of the end state:

| Rule | Result |
| ---- | ------ |
| the paragraph holds nothing, or exactly the served slot text for the match and slot on screen | held in every frame |
| the paragraph and the label are both hidden or both shown | held in every frame |
| the label is never shown over an empty paragraph | held in every frame |
| the slot the page resolved is the slot the side and narrator rules name | 32 of 32 |
| the block's height | 268 px in every frame of every state |

**And the card was reached by tapping, with nothing written into storage by the
harness**, once per match: the match picked off the list and confirmed, the
allegiance and the name entered on the listener card, the narrator chosen on
Profile, and the buildup reached by tapping Heading out. 1986 with England and
the name Olivia resolved `buddy_conceded`; 2022 with Argentina, the name Sam
and the Storyteller chosen resolved `storyteller_neutral`. Both showed the
served words with the label, in a 268 px block.

**One thing that reads as a defect and is not.** Tapping the narrator who is
already current stores nothing, because `renderNarrators` attaches no click
handler to the current card. In the 1986 tap run the Buddy was already current
for a fan of England, so `prelude.narrator` stayed empty while the slot was
`buddy_conceded` all the same. That is the picker's existing behaviour and not
this change.

**Every screen was loaded as well**, because `match-content.js` is shared: the
seven screens by two matches by four listener states, 56 loads, no console
error and no page error on any of them beyond the `/favicon.ico` 404 the
browser asks for on its own.

`pytest -q` reports `1884 passed`, up from `1877`, and all five gates exit 0.
`git status` is clean after the suite.

**Five docs described the code as it was** and were corrected in the same
commits: `docs/HARNESS.md` said the gate holds the markup's inline copy to the
neutral narration, `docs/bob_brief.md` told Bob a missing key leaves the inline
copy and that every screen keeps its inline copy off the filesystem,
`docs/GOVERNANCE.md` listed three things holding the label rule where there are
now four, and `docs/DESIGN.md` described the verified marker without saying it
ships hidden.

**And the deployed site serves the fix**, <https://sh4wnbk.github.io/prelude/>,
once the Pages job for `8f5d21d` had run (success). The served
`prelude_03_moment_card.html` carries an empty `hero_narration` with
`display:none`, a `hero_label` with `display:none` and the block's
`min-height:16.75rem`, and none of the six narrations in the served
`narrations.json` appears in it. The served `match-content.js?v=8f5d21d`
carries `showNarration` and both reveals. Twelve of the 32 combinations were
then driven against the site itself in three states each, the throttled one
with two seconds of latency set through the DevTools protocol rather than in
the driver: the paragraph was empty with no label in every throttled reading,
every frame obeyed the three rules, and the block measured 268 px throughout.
`app/api.py` was not touched, so <https://prelude-api.onrender.com> needed no
check.

**Found, not fixed.**

- **Below 390 px the reservation is short, and the player still moves.** The
  block is 268 px hidden; with the longest of the six narrations in it the
  block measures 294 px at 375 px and at 360 px wide, and 364 px at 320 px, so
  a fan on a 375 px phone sees the card below the narration shift down one
  line, 26 px, when the words land. At 390 px and wider it is 268 px either
  way and nothing moves. Reserving enough for 320 px would mean 364 px, which
  is about 96 px of empty card under the label on every 390 px phone for the
  four shorter narrations, so it trades a one-line shift on one phone size for
  dead space on all of them. That is a layout judgement rather than a
  correctness one, and it is Shawn's.
- **Nothing in the suite can re-measure 16.75rem.** It is a measured constant
  held by a test as a string. A narration reworded longer, or a reader's larger
  base font, would make it short again and the suite would still pass. Checking
  the fit needs a browser, and `CLAUDE.md` keeps browser packages out of
  `.venv-prelude`, which is the venv the gates run in.
- **The play button is enabled while the words are still blank.** It is wired
  from `hero.audio` in `matches.json`, which lands with the first fetch, so
  with `narrations.json` delayed three seconds the card showed no narration and
  no label and an enabled play button, which would play the right recording for
  the slot. Nothing false is said, since the label is about the words and the
  words are absent, but the card and the voice are meant to be one piece of
  writing and for that moment only one of them is there. Pairing them was not
  in the task.
- **`scripts/scan_copy.py` would still pass the label over an empty
  paragraph.** Its tree walk asks whether the label shares a card with a field
  it knows holds narration, not whether that field has words in it, which is
  the right question for a markup gate and the wrong one for this state. The
  new tests hold the shipped hidden state instead, so a regression is caught,
  but by the suite rather than by the gate. Changing what the gate asks would
  change a rule the other screens rest on.
- **`tests/test_frozen_narrations.py` is not in the test table in
  `docs/HARNESS.md`.** Nor are seven other test files: the table lists 30 of
  the 38. It claims no completeness, so nothing in it is stale, and
  `scripts/check_docs.py` passes. It predates this task and was left alone.

**Still Shawn's to do:** the card on his iPhone on a real slow connection, and
the pitch film, whose five frames were rendered before this change. None of the
five shows the narration mid-load, so none of them is wrong; a sixth frame
showing the empty block would be a new frame rather than a correction.

### Task 28: the narrator outlives the tab, and the Moments tagline goes (done)

**What Shawn said on 2026-11-13.** A narrator is chosen before a match, at
home or in transit, not during one. It was held for the session, so it was
gone the moment the tab was. And the Moments footer still carried a line that
belongs in marketing.

**`prelude.narrator` moved from `sessionStorage` to `localStorage`,** in
`app/web/match-content.js`. Every read and write stays inside the same `try`,
so blocked storage still costs the preference and not the screen, and the key
is still removed when the id is empty. "Who are you with" and the name are
answers about tonight rather than standing preferences, so `listenerFor`,
`setListener`, `nameFor` and `setName` are untouched and still per session.

**The old key is carried over once.** `carryNarratorOver` runs on the first
read of a page: if `localStorage` holds nothing it adopts whatever the session
key holds and clears it, so a fan who had already chosen one does not lose it.
Two guards keep a stale value from outranking a later choice: it returns early
once `localStorage` holds anything, and `setNarrator` marks the carry done, so
a choice made now wins. A fan with no old value never notices it.

**`TestTheChoice` in `tests/test_narrator_picker.py` held the old decision,**
so it is five tests for the new one: the reader and writer use `localStorage`
inside a `try`, the session key no longer holds the choice, the carry over
reads the old key and clears it, the carry over runs once and cannot outrank a
later choice, and the allegiance and the name did not move. That file is now
43 tests, up from thirty nine.

**Driven in Chromium against a local server**, serving the working tree from
`app/web/` on port 8099, in one persistent profile so `localStorage` survived
between tabs and `sessionStorage` did not. Every check passed:

| Checked | Result |
| ------- | ------ |
| current narrator before any choice | The Buddy |
| `localStorage` after tapping The Storyteller | `storyteller` |
| `sessionStorage` after that tap | empty |
| `localStorage` in a new tab, the first closed | `storyteller` |
| what `narratorFor` reads in the new tab | `storyteller` |
| the narrator Profile marks there | The Storyteller |
| the allegiance in the new tab | empty, so it did not follow |
| an old session value, `localStorage` cleared | carried over, old key cleared |
| a choice made after a stale session value | the later choice held |

**The tagline is out of the Moments footer.** "The moment you missed deserves
an encore!" told the fan they had missed something on a screen they can reach
without ever having stepped away, and "deserves an encore" is a judgement
rather than a description of the data. Only the sentence was removed: the
"ENCORE FEED READY" label above it and the rest of the footer are untouched, so
that callout is now the label alone beside its icon.
`TestTheMomentsFooterCarriesNoTagline` in `tests/test_screen_copy.py` holds its
absence from the Moments screen, from every `.html` and `.js` file in
`app/web`, and from `matches.json`, and holds the phrase "deserves an encore"
out on its own so a reworded version cannot return.

`pytest -q` reports `1877 passed` and all five gates exit 0.

**Two docs described the code as it was** and were corrected in the same
commits: `docs/bob_brief.md` specified `window.sessionStorage` for the narrator
and listed the tagline among the four lines Shawn chose to keep.

**And the deployed site serves both changes**, <https://sh4wnbk.github.io/prelude/>,
once the Pages job for `401d56f` had run (success). The served
`prelude_04_moments.html` carries no "deserves an encore", and the served
`match-content.js?v=401d56f` carries `NARRATOR_KEY`, `carryNarratorOver` and
the `localStorage` reads and writes.

**A fifth film frame**, rendered from that deployed site the way Task 27
rendered the other four, into `C:\Users\shawn\prelude-review\film\`, which is
outside the repo and not committed. 390 by 844 at device scale 3, so 1170 by
2532.

| File | Bytes | What it shows |
| ---- | ----: | ------------- |
| `moment_2022_buddy.png` | 318,143 | the moment card, 2022, with Argentina and the name Olivia and no narrator chosen, so the lookup falls to the side's own voice and the Buddy tells it |

The match was picked off the list and confirmed, the allegiance and the name
went in through the listener card, and the buildup was reached by tapping
Heading out. Nothing was written into storage from the harness. On the card
`localStorage` and `sessionStorage` both held no narrator, `narratorFor` read
nothing, and the slot resolved to `buddy_scored`.

**The four frames from Task 27 were not re-rendered and did not need to be.**
Neither change touches a pixel on them: the tagline was on the Moments screen,
which none of them shows, and where the narrator is kept does not change how
anything draws.

**A third measurement that looks like a defect and is not.**
`data-match-rendered` says a screen rendered from `matches.json`, and it was
not enough on the moment card. `hero_narration` is filled by a second fetch of
`narrations.json` that lands after that attribute is set, so at this commit a
reader taken on the attribute alone could catch the inline 1986 copy still
sitting under the 2022 header. It did here, and the words looked like a bug in
the lookup when the lookup was right. The render now waits for the narration to
equal the served slot text by value, and asserts it before the shutter. The
frame itself was never wrong, because the screenshot came later than the read.

It turned out not to be only a harness problem. A fan on a slow connection
reads the same screen the harness read, and the label is over it, which is
Task 29 below.

**Still Shawn's to do:** the narrator choice on his iPhone, closing the tab and
reopening it, and the pitch film re-rendered from the five frames.

### Task 27: the seated caption promises the buildup, not everything (done)

**What Shawn said on 2026-11-12.** The Live screen's caption read "You're in
your seat. We'll catch anything you miss." The demo narrates one goal per
match, so the line promised a great deal more than the app does.

**The new line, in all three places the old one lived.** It is
"You're in your seat. We'll catch the buildup if you step away.", and it
replaced the old text in `app/web/matches.json` for both matches and in the
Live screen's inline fallback copy. `scripts/check_match_copy.py` holds that
inline copy to the default match's entry in `matches.json`, so the two had to
move together.

**Four tests in `tests/test_screen_copy.py`,** as
`TestTheSeatedCaptionPromisesOnlyTheBuildup`: the caption literal for each
match, the inline copy on the Live screen, and a sweep of every
`app/web/*.html` and `matches.json` for the phrase "anything you miss", which
is now absent. That file went from ten tests to fourteen, so the counts in
`docs/bob_brief.md` and `docs/HARNESS.md` moved with it; `check_docs.py` failed
on exactly those three claims until they did.

`pytest -q` reports `1870 passed` and all five gates exit 0.

**The two other promises in `app/web`, reported rather than changed.** Neither
is this task's to settle:

| Where | The line | Why it is in this list |
| ----- | -------- | ---------------------- |
| `prelude_04_moments.html` | "The moment you missed deserves an encore!" | Tells the fan they missed something on a screen they can reach without ever having stepped away, and "deserves an encore" is editorial rather than descriptive |
| `matches.json` and the Live inline copy | "Tap as you leave your seat. Prelude keeps track while you're away." | "Keeps track" is the same unbounded promise in weaker form. `tests/test_screen_copy.py` records it as deliberately kept, so it was settled once already |

**And the deployed site serves it**, <https://sh4wnbk.github.io/prelude/>, once
the Pages job for `efba61e` had run (`43340966555`, success). The served
`matches.json` carries the new caption on both entries and the phrase "anything
you miss" appears nowhere in it; the served Live screen carries
`data-field="caption">You're in your seat. We'll catch the buildup if you step
away.<` and loads `match-content.js?v=efba61e`.

**The four film frames, rendered from that deployed site** into
`C:\Users\shawn\prelude-review\film\`, which is outside the repo and not
committed. Each is 390 by 844 at device scale 3, so each PNG is 1170 by 2532.

| File | Bytes | What it shows |
| ---- | ----: | ------------- |
| `live_2022.png` | 188,441 | Live, 2022, before Heading out, carrying the new caption |
| `profile_2022_buddy.png` | 114,631 | Profile, name Olivia, with Argentina, no narrator chosen, the Buddy marked current |
| `profile_2022_storyteller.png` | 114,630 | the same after tapping The Storyteller, which is then marked current |
| `moment_2022_storyteller.png` | 332,687 | the moment card, Di Maria at 1H 36', the Storyteller's narration, the header ending ", Olivia." |

**Every value was set by a tap, not written into storage from the harness.**
The match was picked off the list and confirmed; the allegiance and the name
went in through the listener card that mounts itself on Live; the narrator was
chosen by tapping it on Profile; and the buildup was reached by tapping Heading
out. At the end of the run `sessionStorage` held `prelude.name` as `Olivia`,
`prelude.listener.3869685` as `team_a`, `prelude.narrator` as `storyteller` and
`prelude.moment.3869685` as `1`, all of them put there by the app. That is
where the narrator sat on this commit; Task 28 moved it to `localStorage`.

**The fourth frame is the Storyteller's, and was checked rather than assumed.**
With the listener on `team_a` the app resolved the slot to
`storyteller_neutral`, and the narration on the card is byte for byte the
`storyteller_neutral` text in the served `narrations.json`. This is what
`slotFor` is for: `voice_for.team_a` is `buddy_scored`, which is why the Buddy
is current before a choice is made, and the Storyteller is choosable because
`voice_for.neutral` is `storyteller_neutral`. The Caller renders disabled on
both Profile frames, because 2022 has no `caller_` slot.

**No browser automation was added to `.venv-prelude`.** Playwright went into a
scratch venv outside the repo and drove the bundled Chromium 158.0.8127.18 from
the existing `ms-playwright` cache, so nothing was downloaded. The method is the
one under "Driving it" above, except that the bundled Chromium was enough here
and Edge was not needed.

**One measurement that looks like a defect and is not,** to add to the two
already recorded above. At 390 px the stadium and ticket icons on Live are 14 px
and 13 px, and a screenshot scaled down for review turns them into featureless
boxes that read exactly like missing glyphs. They are not missing: both
ligatures form in Chromium and in Edge, measuring one 48 px advance against 185
px and 501 px for the same strings in a font without them, and a full resolution
crop of the delivered PNG shows a stadium and an amber ticket. Judge an icon
from the rendered file, never from a downscaled copy of it.

**Still Shawn's to do:** re-render the pitch film from the four frames.

### Task 26: Prelude does not choose the match for the fan (done)

**What Shawn saw on 2026-11-10.** After a hard refresh the event list showed
Argentina vs England already selected, with the amber ring, the amber accent
bar and the check in its radio, and the header pill read "ARG vs ENG . LIVE".
Nothing had been chosen. Two separate causes: card 1's markup carried the
selected style, and `DEFAULT_MATCH` in `app/web/match-content.js` stood in for
a fan's choice wherever a screen needed a match and the URL named none.

**Every place `DEFAULT_MATCH` was used, and what each one does now.** All five
are gone from that file; the constant itself is removed.

| Where it was used | What it did | What happens now |
| ----------------- | ----------- | ---------------- |
| `var DEFAULT_MATCH = 3750191` | the id every fallback reached for | removed; `scripts/check_match_copy.py` keeps its own, which is what holds the inline copy to `matches.json` |
| `MATCH_ID = Number(queryValue("match")) \|\| DEFAULT_MATCH` | every screen had a match whether or not one was chosen | `CHOSEN_MATCH`, the match in the query string, and `null` when there is none |
| `url(path, matchId)` appended `match=MATCH_ID` | the nav on the list handed Live, Moments and Profile the default, and Scan ticket too | the match is appended only when there is one, so those links leave the list bare |
| `start()` fell back to `DEFAULT_MATCH` | a `?match=` id this app does not hold opened 1986 instead | a screen that is about one match goes to the list; the list and the scanner render no match |
| `Prelude.matchId` was `MATCH_ID` | `listener-card.js`, `narration-player.js`, `manual-entry.js` and the ticket screen read a default | it is the chosen match, and each of those runs on a screen that requires one |
| `seenKey()` and `ticketKey()` fell back to `MATCH_ID` | session keys were written under the default | they fall back to the chosen match |
| `Prelude.defaultMatch` | exported the constant | removed; nothing read it |

**The list.** Both cards ship in the unselected style, the same class string
and the same radio mark on each. Card 1's play-data strip was brighter than
card 2's and had a different inner structure, which read as a second selection
cue, so it is card 2's strip with card 1's values. A card takes the selected
style in one place, `selectEvent()`, which a tap reaches and which runs on
load for a match named in the query string: that is the return from Edit
details at `?match=<id>&manual=1`, and a ticket that opens a match. An id the
list does not carry is dropped rather than confirmed for the fan. Confirm
event ships disabled and follows the selection. The cards gained `role="radio"`
and `aria-checked`, which `selectEvent()` keeps, because the list was already
a `role="radiogroup"` with no radios in it.

**The pill is hidden on the list rather than reworded, and the reason is the
pill.** Its caption is a match label joined to the word LIVE, so before a
choice both halves are untrue: there is no match to name, and nothing of the
fan's is live. Neutral wording would still sit beside the pulsing amber dot,
which asserts a live feed on its own. A header with no pill is a shape the app
already carries, because `app/web/prelude_05_scan.html` has one. So the list
ships the pill with `style="display:none"` and an empty caption, and
`renderChip` fills the caption and clears that display once a match is chosen.
The list names a match in its header only when the session is already on that
match; a tap is shown on the card, because the list is a pre-match screen.

**Which screens send the fan back.** `MATCH_REQUIRED` in
`app/web/match-content.js` lists `prelude_02_live_seated.html`,
`prelude_03_moment_card.html`, `prelude_04_moments.html`,
`prelude_06_ticket.html` and `prelude_07_profile.html`. The list and the
scanner are not on it: neither is about a match yet. The check is read in the
head, before the markup is parsed, so the inline copy never paints on the way
past, and it is `location.replace()` so a screen the fan never chose a match
for is not a step Back returns to.

**Driven in headless Chromium 158.0.8127.18**, 390 by 844 with touch, with
`app/web/` served on port 8099 by `http.server`. Playwright 1.65.1 in a scratch
venv outside the repo, on the already installed `chromium-1254`. Every row is a
separate browser context, so each one starts with nothing in session storage,
and the first group reloads after clearing it.

| Opened at | Lands on | `data-match-rendered` |
| --------- | -------- | --------------------- |
| `01` list, no match | `01` list | none |
| `02` Live, no match | `01` list | none |
| `03` moment card, no match | `01` list | none |
| `04` Moments, no match | `01` list | none |
| `05` scanner, no match | `05` scanner | none |
| `06` ticket, no match | `01` list | none |
| `07` Profile, no match | `01` list | none |

Every one of the seven opened at `?match=3869685` stays where it was asked for
and renders 3869685, and the same seven at `?match=3750191` render 3750191.
At `?match=999999` the five match screens land on the list with neither card
selected, and the list and the scanner stay put.

| On the list, with nothing chosen | Read |
| -------------------------------- | ---- |
| cards carrying a selected mark | 0 of 2 |
| the two cards' class strings | identical |
| the two radio marks | identical |
| `aria-checked` on each | `false`, `false` |
| Confirm event | disabled |
| header pill | caption empty, computed display `none` |
| nav hrefs | `prelude_02_live_seated.html?v=__V__`, `prelude_04_moments.html?v=__V__`, `prelude_07_profile.html?v=__V__` |
| tapping LIVE | lands on the list |

Tapping Argentina vs France puts the selected style on that card alone, leaves
the other unselected, and enables Confirm event; confirming lands on
`prelude_02_live_seated.html?v=__V__&match=3869685`, which renders 3869685 and
whose nav then carries `match=3869685` on all three items. Opening the list at
`?match=3869685` selects that card and the pill reads `ARG vs FRA . LIVE`.

**The three ways in, both matches, unchanged.** A ticket code is a link, so
the camera path and the link path end in the same screen.

| Way in | 1986, Sec 108 Row 14 Seat 8 | 2022, Sec 215 Row 9 Seat 6 |
| ------ | --------------------------- | -------------------------- |
| `/?ticket=<match>:<sec>:<row>:<seat>` | ticket screen renders 3750191 | ticket screen renders 3869685 |
| code held to a fake camera on `05` | ticket screen renders 3750191 | ticket screen renders 3869685 |
| manual entry on the list | ticket screen renders 3750191 | ticket screen renders 3869685 |
| Enter match from there | Live at `&match=3750191`, ARGENTINA vs ENGLAND | Live at `&match=3869685`, ARGENTINA vs FRANCE |
| Edit details back to the list | `?v=__V__&match=3750191&manual=1`, that card selected, panel filled 108/14/8 | `?v=__V__&match=3869685&manual=1`, that card selected, panel filled 215/9/6 |

The scanner is now opened from the list with no match in its URL rather than
with the default, and it still reads both codes. Profile's Change still lands
on `prelude_02_live_seated.html?v=__V__&match=3869685&ask=1` with the listener
card on screen. The camera was a `.y4m` clip built from the committed ticket
PNGs with ffmpeg, given to Chromium through
`--use-file-for-fake-video-capture`, which is the method recorded under
"Driving the scanner" above.

**`tests/test_match_choice.py`, 51 tests.** Run against `70e117d`, the commit
before step 1, 34 of the 51 fail. The 17 that pass there are the ticket flow
and the deep links, which this task had to leave working.

`pytest -q` reports `1866 passed` and all five gates exit 0.
`docs/bob_brief.md` and `docs/HARNESS.md` quote that count and were updated
with it.

**And the deployed site serves it**, <https://sh4wnbk.github.io/prelude/>,
once the Pages job for `9628e83` had run (`43290931746`, success). The served
`match-content.js?v=9628e83` carries no `DEFAULT_MATCH` at all, and the served
list carries both cards in the unselected class string with
`aria-checked="false"` and the pill at `style="display:none"`. Driven there in
the same headless Chromium: the five match screens opened with no match land
on the list and the scanner stays put; the list after a hard refresh with
session storage cleared has 0 cards with the ring, `false` on both, Confirm
event disabled and an empty pill whose computed display is `none`; tapping
Argentina vs France and confirming lands on
`prelude_02_live_seated.html?v=9628e83&match=3869685`, rendering 3869685 with
the pill reading `ARG vs FRA . LIVE`; both ticket links open the ticket screen
on their own match and Enter match reaches ARGENTINA vs ENGLAND and ARGENTINA
vs FRANCE; and Moments at each of the two ids renders that id.

**Still Shawn's to do:** the list on his iPhone, after a hard refresh. Neither
card selected and no pill in the header before a tap, and then the whole way
in on both matches.

### Task 25: half a second of silence in front of every recording (done)

**Task 24 fixed one of the two causes and the word was still cut.** With the
Web Audio resume awaited inside the tap, the 2022 Storyteller still began at
"tina" rather than at "Argentina" on Shawn's iPhone. The remaining cause is
below the page: the audio output wakes a moment after `play()` starts, and the
opening of the file was landing inside that wake. Task 24 said what the next
step would be if the order was not enough, and this is it, at 500 ms rather
than the 300 ms guessed there.

**Nothing was re-encoded, and that was a decision with a measurement behind
it.** An MP3 is a sequence of frames, so a lead-in can go in front of the
spoken frames instead of being mixed into them: `scripts/pad_hero_audio.py`
builds half a second of silence as its own MP3 and concatenates it with the
original through ffmpeg's concat demuxer with `-c copy`, which hands the
original's frames through untouched. The re-encode was tried first on
`3750191_storyteller_neutral.mp3`, against a signal of -28.8 dBFS: libmp3lame
at 80 kbps CBR left an error 20.9 dB below it at 253,005 bytes, VBR quality 2
left 27.7 dB at 218,637 bytes, and the frame copy left no error to measure at
222,885 bytes. So the copy is what shipped, and the recordings keep 24000 Hz,
one channel and their own bitrates because they keep their own frames.

**The six, measured by `--check` against `9da1a30` with both sides decoded to
PCM.** Every lead-in is 12,143 samples and every duration grew by the same
0.506 s, so those two columns are one figure each rather than six.

| What was read | Every one of the six |
| ------------- | -------------------- |
| lead-in | 506.0 ms, 12,143 samples |
| samples after the lead-in | identical to the original's, every one |
| worst sample difference | 0 |
| frames copied rather than re-encoded | yes |
| decoded duration added | +0.506 s |
| opening 400 ms, peak | -inf dBFS, digital silence |
| sample rate, channels | 24000 Hz, 1, both unchanged |

| Recording | bytes | bitrate, bps | decoded duration, s | samples held identical |
| --------- | ----: | -----------: | ------------------: | ---------------------: |
| `3750191_buddy_conceded.mp3` | 186,452 to 192,213 | 71,850 to 72,308 | 20.760 to 21.266 | 498,240 |
| `3750191_buddy_scored.mp3` | 192,812 to 198,573 | 70,241 to 70,711 | 21.960 to 22.466 | 527,040 |
| `3750191_storyteller_neutral.mp3` | 217,124 to 222,885 | 70,267 to 70,684 | 24.720 to 25.226 | 593,280 |
| `3869685_buddy_conceded.mp3` | 223,868 to 229,629 | 69,159 to 69,579 | 25.896 to 26.402 | 621,504 |
| `3869685_buddy_scored.mp3` | 205,724 to 211,485 | 69,337 to 69,791 | 23.736 to 24.242 | 569,664 |
| `3869685_storyteller_neutral.mp3` | 225,188 to 230,949 | 72,176 to 72,551 | 24.960 to 25.466 | 599,040 |

**Both numbers in that table are measured rather than quoted.** The durations
are decoded sample counts divided by the sample rate, and the bitrates are
bytes over those durations. ffprobe's own figures are off because it divides by
the header's estimate of the duration, which on these files is wrong: it
reported 22.716 s and 76,450 bps for a file that decodes to 24.720 s and
carries 70,267.

**The lead-in lands at 506 ms and not 500 ms because an MP3 frame is not
divisible.** A frame at 24000 Hz carries 576 samples, which is 24 ms, so half a
second is 20.8 of them. ffmpeg wrote 24 silent frames, 576 ms encoded, and the
decoder takes the encoder's delay off the front of that, leaving 506.0 ms. One
frame is the tolerance `--check` allows, and 6.0 ms is inside it.

**The file names did not change, so nothing that finds a recording changed.**
`hero.audio` in `app/web/matches.json`, `Prelude.slotFor`, the side rule and
every path the player fetches are as they were, and no TTS call was made: the
paid path is `scripts/tts_hero.py` and it was not run.

**One thing improved on the way past, unasked.** The concat demuxer wrote an
accurate Xing header, so each file's header duration is now within 22 ms of its
decoded length where the originals were up to 2.0 s short of it. Task 23
recorded that gap as an estimate being corrected once the file was fully
decoded, and Task 24's table recorded `aria-valuemax` taking the short figure
at `loadedmetadata`. The scrubber's range is now right from the first metadata
event instead: the headers read 21.288, 22.488, 25.248, 26.424, 24.264 and
25.488 s, against decoded lengths of 21.266, 22.466, 25.226, 26.402, 24.242 and
25.466.

**`tests/test_narration_scrubber.py` is 61 tests now.** The six SHA-256 digests
it pins are the padded files, which is the deliberate change that list was put
there to force, and the comment above them says why they moved and that the
spoken samples behind the lead-in are untouched. `TestTheLeadInIsThere` is the
18 new ones, three per recording: the file opens with at least 400 ms of
silence, the narration still follows it, and the lead-in is the longest run of
silence in the file. All eighteen fail against the recordings at `9da1a30`.

**Those tests decode nothing, so the suite still needs no ffmpeg.** Each frame
carries `part2_3_length` and `big_values` in its side information, and both
zero means the frame describes no sound, so silence is read off the format
rather than compared against a level. The six open with 24 such frames every
time. The third test holds the lead-in to being the longest silence rather than
the only one because the narrations have pauses in them and the longest of
those reaches 408 ms.

**`scripts/pad_hero_audio.py` is what did it, and it is re-runnable.**
`--plan` probes the six and writes nothing, `--confirm` pads and then prints
the same comparison `--check` prints, and `--check --against <ref>` reads the
unpadded originals out of git so the evidence can be produced again later. A
second `--confirm` reports all six as already padded and writes nothing, which
is what keeps a re-run from stacking a second half second on the first. It
reaches no service and needs a local ffmpeg, on `PATH` or named by
`PRELUDE_FFMPEG`; this run used the BtbN GPL static build
`n8.1.3-27-g8dca1586f4-20261031`, installed with winget, because the machine
had none and the only copy on it was Playwright's, built with
`--disable-everything` and carrying no MP3 codec at all.

**And the deployed site serves them**, <https://sh4wnbk.github.io/prelude/>,
once the Pages job for `81f12a6` had run (`42721414300`, success). Each of the
six was fetched from `assets/audio/` and came back `200` with
`Accept-Ranges: bytes` and a body SHA-256 identical to the committed file:
192,213, 198,573, 222,885, 229,629, 211,485 and 230,949 bytes, in the order
the table above lists them. Seeking still has what it needs on the rewritten
files: `Range: bytes=1000-1999` on
`assets/audio/3869685_storyteller_neutral.mp3` returned `206 Partial Content`
with `Content-Range: bytes 1000-1999/230949`, and those 1,000 bytes are the
committed file's bytes 1000 to 1999.

`pytest -q` reports `1815 passed` and all five gates exit 0.

**Still Shawn's to do:** the card on his iPhone, on the speaker and on
earbuds, on both matches. Listen for whether "Argentina" is whole from the
first tap, and whether half a second of silence before the voice is too long a
wait on a tap that is already waiting for the context to resume. 500 ms is the
figure asked for, not a measured minimum: if the word is whole and the gap
drags, the lead-in can be rebuilt shorter by changing `LEAD_IN_SECONDS` in
`scripts/pad_hero_audio.py` and re-running it over the recordings restored from
`9da1a30`.

### Task 24: the waveform is a scrubber, and the opening word is not cut (done)

**The first word was cut on an iPhone.** The 2022 Storyteller started at
"tina" rather than at "Argentina". Since Task 23 the element is routed through
a Web Audio graph, and iOS starts every `AudioContext` suspended: `play()`
called before the context is running starts the element's clock into a graph
that renders nothing, and whatever plays in that gap is gone.

**So the order changed, and nothing else did.** The resume moved out of
`openAnalyser` into `resumeContext`, which answers with a promise on every
path, including the two that have nothing to do and the one that throws. The
play handler is `async`: it opens the graph, asks for the resume inside the
tap, waits for it, and then plays. The first play starts at `currentTime` 0
unless the fan has already moved the playhead themselves, in which case it
starts where they left it. A refused `play()` puts the icon back rather than
leaving a pause icon over silence.

**No audio file was re-encoded, so the lead-in of silence was not needed to
get this far.** The six MP3s are byte for byte what they were, and
`tests/test_narration_scrubber.py` carries their SHA-256 digests so that
adding a lead-in would have to be a deliberate change made with that list.
**Whether it is needed at all is Shawn's iPhone to answer**, because headless
Chromium does not reproduce the clipping: suspending the context there stops
the element rather than letting it play into a stopped graph. Measured on both
matches, the clock stood still at 16.936 s (1986) and 16.737 s (2022) across
500 ms of a suspended context, so 0.000 s of audio was lost where iOS loses
the opening word. Chromium can show that the new order runs; only the phone
can show that it was enough.

**The waveform is a scrubber now.** It could show a position and not set one:
a `click` handler read `e.clientX`, which a tap gives too, so there was no
drag and no keyboard. It is `pointerdown`, `pointermove` and `pointerup` with
pointer capture, which is one path for touch and for mouse, and the capture is
what keeps a drag alive once the finger has left the bars. The position under
the finger, as a fraction of the track's width, is the position in the
recording, clamped to the start and the end. A cancelled gesture leaves the
playhead where it reached rather than seeking again.

**The amber fill follows the finger immediately, playing or paused.** It used
to be painted in the `timeupdate` handler, and a paused recording sends none,
so the fill and the playhead are painted from the fraction in `paintProgress`
and the clock's handler calls the same function. Playing stays playing and
paused stays paused: nothing in the scrub path calls `play()` or `pause()`.
Task 23's bars carry on untouched, because the scrub paints classes and `left`
while the analyser sets inline heights.

**The waveform is a slider for a keyboard too.** The track carries
`role="slider"`, `aria-label="Narration position in seconds"`,
`aria-valuemin="0"`, `tabindex="0"`, the recording's length as
`aria-valuemax` from `loadedmetadata` and `durationchange`, and the position
in seconds as `aria-valuenow`, kept current by the same function that writes
the timer. The left and right arrows move five seconds and any other key is
left to the page. It has no focus style yet, which is the keyboard focus item
already in the Phase 5 backlog below rather than something this task added.

**`touch-action: none` is on the waveform alone**, so a drag scrubs instead of
scrolling the page, and nothing else on the card stops a scroll. A test counts
the occurrences in the card, because a page that cannot be scrolled would be a
worse fault than a scrubber that is hard to grab.

**Nothing that decides which recording plays was touched.** The audio files,
the narration text, `hero.audio`, `Prelude.slotFor` and the side rule are as
they were; with no recording for the fan's key the player still returns before
it builds the element, so there is no scrub handler to fire; and the player
still sends and parses nothing.

**`tests/test_narration_scrubber.py`, 61 tests**, of which this task wrote the
first forty three and Task 25 below added eighteen. They read the player's own
handler bodies, with the line comments stripped first, and 32 of them fail
against the player at `455939f`. The 11 that pass are the seven about the
recordings being untouched, the three about what did not change, and the one
that counts a single `play()` in the tap.

That is the helper and the reason from `tests/test_narration_waveform.py`,
where two of the existing tests were rewritten rather than deleted, because
the code they read moved: the resume is now in `resumeContext`, and the fill
is now in `paintProgress`.

**Driven in headless Chromium on both matches**, 390 by 844 with touch, with
`app/web/` served on port 8099 by a server that answers Range requests.
`http.server` answers 200 with the whole file whatever Range asks for, so a
forward seek into an unbuffered part of an MP3 cannot be checked against it.

| What was read | 1986, `3750191_storyteller_neutral.mp3` | 2022, `3869685_storyteller_neutral.mp3` |
| ------------- | --------------------------------------- | --------------------------------------- |
| duration at metadata, s | 22.72 | 22.42 |
| aria-valuemax once metadata was in | 22.7 | 22.4 |
| tap at a quarter of the width, s | 5.68, of an expected 5.68 | 5.61, of an expected 5.61 |
| the fraction it landed on | 0.2500 | 0.2500 |
| playhead, and aria-valuenow, after it | 25%, and 5.7 | 25%, and 5.6 |
| mouse drag to 0.85, s | 19.31, of an expected 19.31 | 19.06, of an expected 19.06 |
| mouse drag back to 0.10, s | 2.27, of an expected 2.27 | 2.24, of an expected 2.24 |
| touch drag to 0.60, s | 13.63, of an expected 13.63 | 13.45, of an expected 13.45 |
| paused throughout those three | yes | yes |
| scrollable page, and scrollY across a drag carrying 140 px of vertical | 241 px, 120 then 120 | 290 px, 120 then 120 |
| arrows from 10 s: right, then two lefts | 15.0, then 5.0 | 15.0, then 5.0 |
| focus after a pointerdown | `scrubTrack` | `scrubTrack` |
| scrub to 0.70 while playing, s | 16.22, and still playing | 16.01, and still playing |
| frames after that scrub unlike resting, distinct | 6 of 6, 6 | 6 of 6, 6 |
| scrub to 0.30 while paused, s | 6.81, and still paused | 6.73, and still paused |
| heights after the pause | back to resting, 0 inline | back to resting, 0 inline |
| seek to three seconds from the end, then play | played on from 20.92 | played on from 20.63 |
| a Range request from the page | 206, `Accept-Ranges: bytes`, 1,000 bytes | 206, `Accept-Ranges: bytes`, 1,000 bytes |
| page errors | none | none |

The scrub to 0.70 lands a little past the expected 15.90 and 15.70 because the
recording went on playing while the drag was being made, which is the point of
that row: the drag did not stop it.

**And a second pass on a page nothing had scrubbed**, because the busier page
above has moved the playhead by then and the player is right to leave it
alone, so the reset cannot be seen there. With the element's clock set to
7.0 s before the first tap, the first play started at 0.013 s (1986) and
0.014 s (2022), and the clock then ran on normally. With the context suspended
by hand before a second tap, it read `running` by the time the recording
played and the clock advanced 0.413 s and 0.409 s over 400 ms, which is the
new order doing its work.

**Then against the deployed site**, <https://sh4wnbk.github.io/prelude/>, once
the Pages job for `5344427` had run. Both cards load
`narration-player.js?v=5344427`, which is MD5 identical to the committed
file (`9e2f6128cf147cda0219f349825b5b3e` both sides). Every row above read the same
there, within the timing of a recording that keeps playing: the quarter tap,
both drags, the touch drag, the arrows, the two scrubs and the resting heights
were identical, 0 page errors on either card, and the fresh pass started the
first play at 0.014 s and 0.015 s.

**GitHub Pages answers audio requests with ranges, which is what seeking
needs.** A plain GET of `assets/audio/3869685_storyteller_neutral.mp3` returns
`200` with `Accept-Ranges: bytes` and `Content-Length: 225188`, and
`Range: bytes=1000-1999` returns `206 Partial Content` with
`Content-Range: bytes 1000-1999/225188` and `Accept-Ranges: bytes`.

`pytest -q` reports `1797 passed` and all five gates exit 0.

**One thing to know about running the suite.**
`tests/test_authored_narrations.py::TestWhatTheCheckSays::test_the_script_says_so_and_exits_zero`
runs `scripts/authored_narrations.py`, which rewrites
`docs/narration_runs/authored_2026-11-07.md` and `.json` with the date it ran
on. So a clean tree comes back dirty on those two files after any `pytest`,
with the body saying 2026-11-09 under a filename saying 2026-11-07. It was
there before this task, nothing was committed from it, and tidying it is its
own small job.

**Still Shawn's to do:** the card on his iPhone. Tap, drag forward, drag back,
on both matches, playing and paused, and listen for whether "Argentina" is
whole. If it is still cut, the next step is the one this task did not need: a
lead-in of about 300 ms of silence at the start of each of the six MP3s,
re-encoded locally with ffmpeg and no TTS call, with the spoken audio
unchanged and `hero.audio` keeping the same paths.

### Task 23: the waveform bars follow the voice (done)

**The waveform was a progress bar.** The bar heights were fixed in the card's
markup and the amber fill ran left to right with the clock, so a fan watching
it learned how far through the recording they were and nothing about the
sound. The film's listening shot shows bars that move with the voice, and the
condition was that the app ships the same thing.

**`app/web/narration-player.js` now puts the element through a Web Audio
analyser.** The first play tap opens one `AudioContext` and resumes it inside
the tap, because iOS starts every context suspended and resumes one only on a
user gesture. The Audio element goes through a `MediaElementAudioSourceNode`
into an `AnalyserNode` and on to the context's destination, which is the
connect that keeps the sound reaching the speakers. While it plays,
`requestAnimationFrame` sets each bar's inline height from the analyser's
levels, reading the bottom half of the spectrum where a voice puts its energy;
on pause and at the end the loop is cancelled and the inline heights are
cleared, which hands every bar back to the height its class sets. The amber
fill is untouched: it is classes and the heights are inline styles, so
progress and voice do not meet.

**Three things about that were worth getting right, and the tests hold each.**
The context is created in the tap rather than at load, or iOS would leave it
suspended and the bars would be dead while the narration played. The source
node is created once per element, because a second
`createMediaElementSource` on the same element throws, which a fan would meet
on the second tap and not the first. And where `navigator.audioSession`
exists its type is set to `"playback"`, so the silent switch does not mute the
narration.

**Every bit of Web Audio is optional.** With no `AudioContext`, or if any of
the wiring throws, the analyser stays null and the player keeps exactly what
it did before: fixed bars, the amber fill as progress, and the recording
playing. If the element was already captured when the failure came, its source
node is connected straight to the destination, so a failure costs the bars and
not the sound.

**`tests/test_narration_waveform.py`, 25 tests.** They read the player's own
handler bodies rather than searching the file, because "the context is created
inside the tap" cannot be told from "the context is created somewhere in this
file" by searching for a string: `block_after` walks the braces from a marker
and returns that block. They also strip the line comments first, since the
comments say what the code does in the same words and a test that counted the
prose would pass on a file that only talked about connecting to the
destination. 21 of the 25 fail against the player at `c2bac5c`; the 4 that do
not are the ones about what did not change, which are the resting heights in
the card, `slotFor` and `hero.audio`, and the element never being repointed.

**Driven in headless Chromium on both matches**, 390 by 844, with `app/web/`
served on port 8099 and the recording played to its end. A forward seek is
dropped here, because `http.server` answers no Range request, so the end was
reached by letting it run rather than by seeking.

| What was read | 1986, `3750191_storyteller_neutral.mp3` | 2022, `3869685_storyteller_neutral.mp3` |
| ------------- | --------------------------------------- | --------------------------------------- |
| audio plays | yes, to 24.70 s | yes, to 24.94 s |
| frames sampled while playing | 14 | 14 |
| frames unlike the resting heights | 14 | 14 |
| distinct frames among them | 14 | 14 |
| lowest and highest bar, px | 6.0 and 35.3 | 6.0 and 33.2 |
| bars with an inline height while playing | 24 | 24 |
| heights after pause | back to resting, 0 inline | back to resting, 0 inline |
| replay tap: frames unlike resting, distinct | 8 of 8, 8 | 8 of 8, 8 |
| heights after the end | back to resting, 0 inline | back to resting, 0 inline |
| amber bars at 3 s, and at the end | 3, then 24 | 3, then 24 |
| page errors | none | none |

The resting heights read the same on both, `[14, 20, 28, 32, 20, 14, 24, 36,
28, 20, 32, 36, 24, 32, 36, 28, 24, 32, 20, 28, 16, 24, 12, 8]`, which is the
markup with the Tailwind CDN loaded. The replay row is the part a source test
cannot reach: it is the second `openAnalyser` call, against a context and a
source node that already exist, and the bars still move with no error.

**And then against the deployed site**, <https://sh4wnbk.github.io/prelude/>,
once the Pages job for `6c22238` had run. Both cards load
`narration-player.js?v=6c22238`, which is the stamped copy of the committed
file, and both play the Storyteller's neutral recording. Ten of ten sampled
frames were unlike the resting heights and all ten were distinct, the bars
ran 6.0 to 33.8 px on the 1986 recording and 6.0 to 33.3 on the 2022 one, the
heights came back to the resting list on pause, and neither page reported an
error.

**Two things the run showed that are not defects.** The element is
`new Audio(file)` and is never attached to the document, so the harness wraps
`window.Audio` to keep a reference to it; the wrapper returns a real
`HTMLAudioElement` and the page cannot tell. And the reported duration moves
from 22.72 s to 24.70 s on the 1986 recording once the file is fully decoded,
which is an MP3 estimate being corrected, not the clock drifting.

**Nothing that decides which recording plays was touched.** The audio files,
the narration text, `hero.audio`, `Prelude.slotFor` and the side rule are as
they were, and the player still sends and parses nothing. `docs/DESIGN.md` no
longer calls the waveform static, and `README.md` says what the bars follow.

`pytest -q` reports `1754 passed` and all five gates exit 0.

**Still Shawn's to do:** the card on his iPhone, with the silent switch off
and then on, before the film clip is re-recorded.

### Task 22: rule 4 refuses a summary outright, and the two-digit rules line up (done)

**Rule 4 had a clause that no longer led anywhere.** It read: if you cannot
quote the words in full, say so plainly, say that you are summarising, and do
not show the label. Both halves were dead by Task 20. The agent shows no label
at all now, so "do not show the label" forbade something already impossible,
and the permission to summarise was a second way to answer a narration
question, which is a second thing to get right in instructions whose whole
point is that there is one way.

**Shawn's wording, and it is now rule 4**: never summarise or shorten a
narration; if you cannot give the words in full, say that you cannot, and give
none of them. A refusal is a safe answer and a summary is not, because a
summary is narration this repo has not checked sitting in the place a fan
expects checked narration.

**The label prohibition did not move out, it moved up.** The old rule 4 ended
"there is no shorter version of the label and no softer one", which is
`CLAUDE.md`'s no-partial-credit rule. Rule 2 already carries it: the phrase is
never the agent's to write, "not with a letter of it in a different case, not
shortened, not softened, not inside brackets or parentheses, not after a
name". So the rule is in one place now instead of two, which is the same
reason the slot rule has one table.

**The label tests written in Task 18 were held to the old wording, and now
hold the new.** The one that said a summary says so and drops the label is
gone, because the thing it held is gone. In its place:
`test_there_is_no_summarised_narration_at_all` reads rule 4;
`test_the_summarising_clause_is_gone_from_the_rules` fails if either removed
phrase comes back into the block, so the clause cannot return by accident; and
`test_there_is_no_softened_variant_of_the_label` now reads rule 2, which is
where that prohibition lives. The rest of `TestTheLabelRule` was untouched and
still passes, because rule 2 and rule 5 did not change.

**Rules 10 and 11 line up now.** Their markers are two characters wider than a
one-digit rule's, so their continuation lines were a space short and the list
read ragged in the block a judge sees pasted. The text is unchanged apart from
the rewrap.

### Task 21: all of the narration, in one run (done)

**The live result, Shawn, 2026-11-07.** The agent was asked the 1986 question
as a fan of neither side. It chose the right match, asked the right question
about sides, and reached the right narration, the Storyteller's neutral
telling. Then it handed over part of it. The answer stopped at "then took it
into the box", closed with an ellipsis, and broke one of its sentences across
two lines. The 2022 answer in the same session was complete, so this is a
narration given in part, not a rule the agent never read.

**What was missing**, read off `app/web/narrations.json`:

| The field | 65 words, 330 characters, in one run with no line break |
| --------- | ------------------------------------------------------- |
| what the answer carried | 53 words, 262 characters, ending part way through a sentence |
| what it dropped | 13 words, 68 characters: ", slipped past Shilton and scored with his left foot. What a moment." |

**The thirteen words are the goal.** What the answer dropped is the ball going
past the goalkeeper and in, and the sentence after it. A telling cut before
the finish is the telling of a goal that never goes in, which is the one thing
a goal call cannot leave out. It is also narration nothing has checked:
`app/grounding.py` read all 65 of those words when it passed them, and the
label the response carries was earned by the field as a whole, so four fifths
of it is new writing with an old guarantee standing behind it.

**Rule 3 now says it in the terms the failure took.** Rule 1 already said
never to shorten the text, and that was not enough, because nothing said what
shortening looks like from the inside. Two paragraphs were added to rule 3:
all of the field, from its first word to its last full stop, never stopping
part way through, never leaving its last sentence unfinished, and never closed
with an ellipsis, three dots, "and so on" or any other mark standing in for
words left out. And one run of text: the field arrives with no line break in
it, so the answer has none, is not wrapped, is not split into lines or
paragraphs, and does not break a sentence across two lines.

**One line of rule 3 may have invited part of this, and it is fixed.** The
rule's list of what may not follow the narration ended "no closing sentence,
no offer of more", which meant no closing sentence of the agent's own. The
1986 narration's last sentence is "What a moment.", which is exactly the kind
of sentence that list reads as forbidding. It now says "no closing sentence of
your own", and the paragraph above it says in as many words that the field's
own final sentence is part of the field. That is a rule written here in Task
20 and read back by a model two hours later, which is the only way an
ambiguity in instructions this short gets found.

**Five tests in
`tests/test_orchestrate_agent.py::TestTheAnswerIsTheNarration`.** Four read
the block: all of the field to its last full stop, the refusal of a cut and an
ellipsis, the field's last sentence not being a closing sentence of the
agent's, and the refusal of an added line break. The fifth reads
`app/web/narrations.json` instead, and holds the premise the rule rests on:
each of the six frozen narrations is one run of single-spaced text with no
line break, no ellipsis and no ellipsis character. So every break in an answer
is the agent's own, and a frozen narration that grew one would fail here
rather than leaving the rule quietly wrong.

**What a test cannot do here.** The same limit as Tasks 18, 19 and 20. Nothing
in this environment has a watsonx Orchestrate account, so these tests hold the
instructions and not the agent. Step 5 of the setup list in
`docs/orchestrate_agent.md` is the check, and both live failures so far were
found by running it.

### Task 20: the answer is the narration, and nothing else (done)

**The live result, Shawn, 2026-11-07.** The agent was asked for the 2022
narration and it quoted the Buddy's telling word for word. The quoting was
right: rules 1 and 2 of `docs/orchestrate_agent.md` did their job, and the
words a fan read were the words the grounding check passed and the recording
reads. Then the agent added a line of its own under them, and that line was
wrong in three ways at once:

| What it put there | Why it is a breach |
| ----------------- | ------------------ |
| an em dash to open the line | `CLAUDE.md` takes no em dash in any doc or UI copy, and this is UI copy a fan reads |
| the narrator's name as a signature | the telling is not signed anywhere else in the product, and a signature makes the words read as a personality's rather than as a checked record |
| the label behind the name in parentheses, its first letter lower-cased | `CLAUDE.md` allows "Verified from play data" only exactly as written, with no partial credit and no softened variant. A lower-cased copy in brackets is not the label |

**None of the three came from a rule given badly.** The old rule 2 said to
show the label with the words it belongs to and said nothing about where on
the answer it goes or what may sit around it. An instruction to show
something is an instruction to place and style it, and placing and styling is
what a model does with a free hand.

**Shawn's decision: the answer is the narration text exactly as `/buildup`
returns it, and nothing else.** Not a shape for the extra material; no extra
material. The narration was written to be read on its own, and
`app/grounding.py` read it on its own when it earned the label, so handing it
over on its own is the only form in which nothing has been added to it. It
also removes the whole class of failure rather than this instance of it: there
is no styling decision left to make.

**Rule 3 in `docs/orchestrate_agent.md` is that decision**, and the old rules
3 to 10 are 4 to 11. It says the whole answer is the `text` field exactly as
returned, then refuses by name each thing the live answer added: nothing
before it, and after it no signature, no byline, no narrator's name, no label,
no link, no authorship line, no closing sentence, and no dash of any kind
anywhere in the answer. Rule 2 no longer tells the agent to show the label; it
says the label field is the response's and never the agent's to write, in any
case, shortened, softened, bracketed or placed after a name. Rule 11 keeps the
`narrator` and `audio_url` fields out of the answer in the same way, instead
of placing them in it.

**What the decision costs, recorded rather than left to be discovered.** The
agent no longer shows the label, the narrator's name, the recording link or
the authorship line. The authorship line is the one worth naming twice: it is
what told a fan the words were drafted with an AI assistant and edited by a
person, and the old rule 2 asked for it. A fan reads the label and hears the
recording in the app, where
`app/web/prelude_03_moment_card.html` sets the label as its own element with
no punctuation around it. Every one of those fields is still in the buildup
response, so bringing one back is a change to rule 3 and Shawn's to make.

**`tests/test_orchestrate_agent.py::TestTheAnswerIsTheNarration`, 14 tests**,
nine of them this task's and five Task 21's.
The rule itself, the nothing before and the nothing after with each refused
item named, the no dash clause, the label as never the agent's to write, and
two that read the block against the failure rather than against the rule:
every occurrence of the label in the block has to be the spelling
`app/grounding.py` writes, which is what the live answer got wrong, and no
label line or audio line may be left in the block to stand beside rule 3 as a
softer version of it. The four label tests written in Task 18 still pass
unchanged, because the label rules became prohibitions rather than going away.

**What a test cannot do here.** The same limit as Task 18 and Task 19: nothing
in this environment has a watsonx Orchestrate account, so these tests hold the
instructions and not the agent. Step 5 of the setup list in
`docs/orchestrate_agent.md` is the check, and it now reads that the answer
should be the telling word for word and nothing else, which is the thing that
failed.

### Task 19: the match parameter Orchestrate can send, and the matches the agent is told about (done)

**Two things the first live test of the agent found**, Shawn, 2026-11-07, with
Bob's Task 15 spec imported into watsonx Orchestrate and attached to the
prelude agent. Neither is a fault in the spec and neither was findable from
here: the suite has no network and nothing in this environment has an
Orchestrate account, which Task 18 says in the same words.

1. **Orchestrate called `/buildup` with `match=3.869685e+06`.** It serialises
   an integer tool argument as a float. The service answered 422, which was
   correct: the parameter was an integer and that is not one. The 422 was also
   no use, because the agent could not send the value it had and had nothing
   to read the right form off.
2. **The agent asked the fan for a StatsBomb match id.** Nothing in its
   instructions said which matches exist, so the one number it could not get
   from a fan is the one it asked for.

**`match` is a string of digits now**, on both endpoints, with the pattern
`^[0-9]+$` in the schema and the conversion to an integer inside `app/api.py`.
Orchestrate passes a string through unchanged, so the agent can send what it
has. The 422 that a bad value gets now names the pattern and echoes what was
sent, which is the whole of what a caller needs for its next attempt:

```
{"detail": [{"type": "string_pattern_mismatch", "loc": ["query", "match"],
"msg": "String should match pattern '^[0-9]+$'", "input": "3.869685e+06",
"ctx": {"pattern": "^[0-9]+$"}}]}
```

`MATCH_PATTERN` in `app/api.py` carries the reason, and
`tests/test_api.py::TestTheMatchParameter`, 30 tests, holds it over both
endpoints: digits answer 200 and report the id as an integer, a float in
either spelling, a signed number and a word are 422 with the pattern and the
value in the body, well formed digits the service does not serve are still
404, and `app.openapi()` carries the pattern so the spec has one thing to
copy.

**`orchestrate/prelude_tools.yaml` follows**, with `type: string`, the same
pattern, and the example quoted so an agent copies digits rather than a
number. It was Bob's file and this is a change to it after the task, which
`docs/bob_brief.md` Task 15 records along with why.
`tests/test_orchestrate_spec.py::TestTheParameters` is what caught the drift
when `app/api.py` changed: it reads the types out of `app.openapi()`, which is
exactly the job Task 18 wrote it for, and it failed before the file was
touched. One test in that file changed with it, the one reading the `match`
example, which now compares against the served ids as strings.

**The agent is told which matches it serves.** The pasteable block in
`docs/orchestrate_agent.md` carries them, and a new rule 5 tells the agent to
choose the match from that list, pass the id as digits, never ask a fan for a
StatsBomb match id, and ask which match is meant when a fan's words fit more
than one or none. The old rules 5 to 9 are 6 to 10; rule 1 is still the
verbatim rule, which is what the grounding label rests on.

**The list is generated.** `scripts/write_served_matches.py` writes it and,
with `--check`, fails on a stale one. The id and the two team names come from
`app/web/matches.json`, which is the service's own list of what it serves.
That file records no competition and no stage, so the competition, the season,
the stage and the date are read from the StatsBomb match files under
`data/raw/matches/`, which is where both match ids were resolved from in the
first place and which `scripts/fetch_statsbomb.py` downloads. What it wrote:

```
- 3750191: Argentina vs England, FIFA World Cup 1986, Quarter-finals, 1986-06-22
- 3869685: Argentina vs France, FIFA World Cup 2022, Final, 2022-12-18
```

`tests/test_orchestrate_agent.py::TestTheMatchesItServes`, 9 tests, holds
every line to both sources and to the ids `app/api.py` serves, holds the list
inside the pasteable block rather than in the prose around it, and holds the
three things the rule says. A third match in the app fails the suite here
until the list is written again.

**Task 15 is verified and `scripts/check_docs.py` is clear.** The brief's
Task 15 carries the table of what was run against Bob's commit `39856bd`:
1675 passed with the spec's 64 among them, the file valid as OpenAPI 3.0.3
under `openapi-spec-validator`, one server, two GET operations, no security
block, and the live service answering. The two claims the gate was holding
open are closed: the quoted `pytest -q` result is the current run and
`bob_sessions/phase6_task15_orchestrate_spec.md` is off `DELIBERATELY_ABSENT`,
which is empty again. `docs/HARNESS.md` loses the exception the suite no
longer has, and its `tests/test_narrator_picker.py` row no longer claims
seventeen failures.

**Checked against the deployed service**, 2026-11-07, after Render reported
`9e3d67d` on `/health`, which is this task's own commit. The two calls are the
value Orchestrate should send now and the value it actually sent in the failed
live test.

`GET /buildup?match=3869685&listener=team_b&narrator=buddy` answered **200 in
0.18s**: `match_id` 3869685 as a number, slot `buddy_conceded`, narrator "The
Buddy", the authorship line, the recording at
`https://sh4wnbk.github.io/prelude/assets/audio/3869685_buddy_conceded.mp3`,
and the grounding label present, which is the slot's own record and not
attached by the endpoint.

`GET /buildup?match=3.869685e+06&listener=team_b&narrator=buddy` answered
**422 in 0.17s**, with the form and the value in the body:

```
{"detail":[{"type":"string_pattern_mismatch","loc":["query","match"],
"msg":"String should match pattern '^[0-9]+$'","input":"3.869685e+06",
"ctx":{"pattern":"^[0-9]+$"}}]}
```

That second one is still a refusal, and it is meant to be: the service serves
integer match ids and `3.869685e+06` is not one of them. What changed is that
the parameter no longer asks Orchestrate for the type it cannot send, so the
agent has a value it can pass, and a refusal it can read if it passes
something else.

**Cold wake, measured again.** `/health` answered in 31.5 seconds from asleep
on 2026-11-07, in line with the 32 seconds Task 18 measured twice and well
under the 82 the keepalive run recorded. The standing section at the top of
this file still plans on the 82, which is the safe number to plan on.

**What was not verified, and cannot be here.** The same thing Task 18 says:
nothing in this environment has a watsonx Orchestrate account, so the fix for
a symptom Orchestrate produced is checked against the service and against the
suite, and the agent's behaviour under rule 5 is checked by asking it. Step 5
of the setup list in `docs/orchestrate_agent.md` is how.

### Task 18: the Orchestrate tool contract, the agent instructions, and the dry run (done, the spec is Bob's)

**The API is deployed and answering.** <https://prelude-api.onrender.com>
reports `833dbed` from `/health`, which is the commit Render built, and the
standing section at the top of this file is what a cold wake costs. Everything
below was checked against that service rather than against a local uvicorn.

**What Bob gets, and what he does not.** The OpenAPI file Orchestrate imports,
`orchestrate/prelude_tools.yaml`, is Task 15 in `docs/bob_brief.md`. It is not
in the repo: this task wrote the brief, the acceptance tests and the agent's
instructions, and the file itself is the session Shawn runs.

**`tests/test_orchestrate_spec.py`, 64 tests, all failing.** They are the
contract for that one file: OpenAPI 3.0 because IBM requires it, one server
and that server the deployed URL, exactly two operations and `/health` not
among them, an operationId and a description an agent can choose by, the
parameters and enums the service takes, a JSON 200 per operation, and no
authentication block because the service takes none.

**Almost nothing in those tests is spelled twice.** The parameter names, the
required flags, the types, the listener enum and the response types are read
out of `app.api`'s own `app.openapi()` inside the tests and compared with the
file, so a change to `app/api.py` fails the spec here rather than in
Orchestrate, where the symptom is an agent calling with an argument the
service drops. The status codes the file may declare are demonstrated against
the application in process, 200, 404 and 422, before the file is allowed to
name one. That is the same answer Task 17 gave the slot rule: when a rule is
written twice, the second copy is held to the first by a table or by a read.

**Three things the tests do assert on their own**, because the code does not
hold them: the 3.0 version, which is the one place the file may not match
`app.openapi()`; the narrator enum, which is the persona ids that have a
recording, read off `hero.audio` in `app/web/matches.json` and so two of the
three; and a description on every operation and parameter plus an example on
every parameter, none of which FastAPI writes.

**`docs/orchestrate_agent.md` is the agent, as far as this repo can hold it.**
The agent is created in Orchestrate's UI and its model is fixed by the lab
admins, so what is here is the block Shawn pastes into it. Its first rule is
the verbatim rule: quote the narration the tool returned word for word, never
paraphrase, shorten or add to it. Its second is the label rule: "Verified from
play data" goes over those words and nothing else, and the phrase is never the
agent's to write. `CLAUDE.md` allows no partial credit and no softened
variant, and an agent is the one writer in this system that nobody here
reviews, so the rule is written where it will be read. Task 20 is where that
rule stopped being about showing the label and became about never writing it,
and Task 22 is where rule 4 stopped allowing a summary to be offered instead.
`tests/test_orchestrate_agent.py`, 40 tests, holds both rules, reads the label
from `app/grounding.py` and the three listener values from `app.openapi()`,
and refuses a verdict nickname in the file at all.

**The dry run, on a scratch branch that was deleted.** The spec was written
once to the brief, 197 lines in one file and nothing else changed, and all 64
tests in `tests/test_orchestrate_spec.py` passed on the first run of it, so the
contract is satisfiable as written. The suite then came out at 1675 passed and the five gates were at
exit 0 except `check_docs.py`, which failed on exactly the claim the brief
predicts: the quoted `pytest -q` result in `docs/bob_brief.md`. The file also
validated as OpenAPI 3.0.3 under `openapi-spec-validator`, run outside the
project with `uv run --no-project`, so nothing was added to `pyproject.toml`
for it. `docs/bob_brief.md` carries the seven things the run taught; the
longest of them is that describing the 200 body is worth doing and that every
field named has to be read off the live body, including the fields inside
`goals`.

**What the live service answered during the dry run**, 2026-11-07, which is
the half of the check a test cannot do:

| Call | Answer |
| ---- | ------ |
| `/health` | 200 with the deployed commit, after a 32 second cold wake |
| `/moments?match=3750191` | 200 in 0.56s, Argentina 2 England 1, the second goal narrated |
| `/buildup?match=3750191&listener=team_b&narrator=buddy` | 200 in 0.18s, the `buddy_conceded` slot with its text, authorship, recording and label |
| `/moments?match=1` | 404 |
| `/buildup?match=3750191&listener=nope` | 422 |
| `/buildup?match=3750191&listener=team_a&narrator=caller` | 200, fallen back to `buddy_scored` |

A cold wake measured 32 seconds twice that day, against the 82 seconds the
keepalive run recorded. The standing section plans on the 82.

**`pyyaml` joins the dev group.** The suite had no way to parse YAML, which is
why the two YAML files in Task 17 were read by eye. It is dev only, so the
deployed service still installs `fastapi`, `uvicorn` and `segno` and nothing
else, and `docs/HARNESS.md`'s dependency table says so.

**What was not verified, and cannot be here.** Nothing has been imported into
watsonx Orchestrate: there is no account in this environment, the import is
Toolset, Add tool, Import, Import from file in the lab's UI, and the agent and
its instructions go in beside it. So "Orchestrate accepts this file" is
checked by IBM's published conditions and by an OpenAPI validator, and not by
Orchestrate. The agent's behaviour under the two rules is checked by asking
it, which is step 5 of the setup list in `docs/orchestrate_agent.md`.

### Task 17: the hosted read-only API, and the slot rule in one table (done, and deployed since)

**Shawn, 2026-11-07: the hosted service holds no keys.** The Plan's Phase 6
below was written for a backend holding the IBM keys with rate limiting, so
judges would get live, varied narration. That is not what was built. The app
stays on GitHub Pages, which is static and always on, and the hosted part is a
small read-only API whose only job is to give watsonx Orchestrate a stable
public URL to call. Render spins a free service down after fifteen minutes
without traffic, takes about a minute to wake, and rebuilds its filesystem
from the build when it does, so the service holds no state, writes nothing,
needs no credentials and makes no paid call: it serves what the repo already
holds. The six recordings stay the fallback, as the Phase 6 note already says,
and hosting still adds no input.

**`app/api.py`, three endpoints, GET only, CORS open for GET.**

| Endpoint | What it answers |
| -------- | --------------- |
| `/health` | `{"status": "ok"}`, and the commit when the build wrote one |
| `/moments?match=<id>` | every goal from Bob's `app/statsbomb_event_feed.py`: scorer, team, the minute the app captions, the score after it, and `narrated` true for the hero goal alone |
| `/buildup?match=<id>&listener=...&narrator=...` | the slot, the narrator's name, the frozen narration and its authorship, the recording's URL on the Pages site, and the grounding label |

An unknown match is a 404 and a listener that is not one of the three is a
422, which is FastAPI validating a `Literal` rather than a hand-written check.

**The slot rule is now written twice, so the table is a file.** The rule picks
the narration a listener hears and the recording that reads it, and it had one
home, `Prelude.slotFor` in `app/web/match-content.js`. `slot_for` in
`app/api.py` is the second. Two copies of a rule drift, so the seven rows
moved into `tests/slot_rows.json` and the `slot_rows` fixture in
`tests/conftest.py` hands them to both suites.

`tests/test_api.py`, 98 tests, runs each row through the Python copy and
through `/buildup`, so the rule the service answers with is the rule in the
table. It was 92 when this record was written; the count is kept current
because `scripts/check_docs.py` reads every count in `docs/history/` against
the suite, which is the one thing in these records that does move.

`tests/test_narrator_picker.py`, 43 tests, reads each row against
`hero.voice_for` and `hero.audio`, which is what the browser's copy indexes:
every row names a match the app serves, a key that match carries and a
recording in the repo, and each row is the branch of the rule it claims to be.
The nine new ones are `TestTheSevenRows`.

The seven rows, which are the ones Shawn named:

| Row | Slot |
| --- | ---- |
| 2022, Argentina, nothing chosen | `buddy_scored` |
| 2022, Argentina, the Storyteller | `storyteller_neutral` |
| 2022, Argentina, the Buddy | `buddy_scored` |
| 2022, France, the Storyteller | `storyteller_neutral` |
| 2022, no side, the Buddy | `storyteller_neutral` |
| 2022, no side, nothing chosen | `storyteller_neutral` |
| 1986, England, the Buddy | `buddy_conceded` |

**Three decisions inside the build, each of which changed something else.**

- **`GROUNDING_LABEL` moved from `app/narration.py` to `app/grounding.py`.**
  Importing one string from `app/narration.py` would have put the watsonx
  backend in the deployed process, because that module imports
  `app/narration_provider.py`. The label now sits with the check that earns
  it, `app/narration.py` imports it from there so
  `from app.narration import GROUNDING_LABEL` still reads, and
  `tests/test_api.py::TestWhatItDoesNotReach::test_it_imports_no_paid_backend_through_anything_else`
  reads the whole import closure rather than the first line.
  `docs/GOVERNANCE.md` and `docs/VERIFICATION.md` say where it lives now.
- **The commit `/health` reports arrives as a file.** Render publishes the
  deployed commit to the build, and `render.yaml` writes it to
  `build/commit.txt`, which `.gitignore` ignores. Reading `RENDER_GIT_COMMIT`
  in the service would have made it an environment reader, and
  `tests/test_api.py::TestWhatItDoesNotReach::test_it_reads_no_environment_variable`
  is what says it is not one. A build that wrote no stamp answers without a
  commit rather than guessing one.
- **The network guard now lets loopback through.** Running the application in
  process starts an asyncio event loop, and on Windows the loop wakes itself
  by connecting a socket pair on `127.0.0.1`, so the old guard failed 36 of
  the new tests before one of them reached the API. `LOOPBACK_HOSTS` in
  `tests/conftest.py` records why it is not a hole: nothing in this repo
  serves on a port, and watsonx, Watson Text to Speech and StatsBomb are all
  somewhere else. Every other address still refuses, which
  `tests/test_api.py::TestTheNetworkGuardStillHolds::test_a_remote_connection_still_refuses`
  holds, and `docs/GOVERNANCE.md` no longer says no test can open a socket at
  all.

**`app/` takes a third-party package now, and the documents say so.** FastAPI
is in `app/api.py` and in no other module of `app/`, which
`tests/test_api.py::TestWhatItDoesNotReach::test_the_only_module_in_app_that_takes_a_third_party_package`
holds. `docs/HARNESS.md` and `docs/GOVERNANCE.md` said `app/` imported nothing
outside the standard library, and thirteen module docstrings said "like the
rest of `app/`"; all of them now name the one exception. The dependency table
in `docs/HARNESS.md` names `fastapi`, `uvicorn` and `httpx`.

**Steps 1 and 2 landed in one commit, `29dd7a5`.** The doc corrections the
service forced cite the new tests, so committing the service without them
would have committed a failing `scripts/check_docs.py`. `render.yaml` is
`ba32216` and the keepalive is `a5d0d0a`.

**`render.yaml`: one free web service, in Python, with `/health` as the health
check path.** uv is enabled by `uv.lock` being in the repo root, which is how
Render documents turning it on, and the build command then uses uv in place of
pip, which is what Render documents for a uv project. It is
`uv sync --locked --no-dev`, then `scripts/fetch_statsbomb.py` (`data/raw/`
stays gitignored and is downloaded by the build), then the commit stamp. The
start command is `uv run --no-sync uvicorn app.api:app` with Render's own host
and port. Nothing sets `PYTHON_VERSION`: `.python-version` says 3.13 and
Render reads it. The locked production sync was run into a throwaway
environment and installed `fastapi`, `uvicorn` and `segno` and nothing from
the dev group, and uvicorn from that environment is what answered the curl
runs below.

**What the keepalive costs, and the switch that decides it.**
`.github/workflows/keepalive.yml` pings `/health` every ten minutes and on
manual dispatch. The URL is the repository variable `PRELUDE_API_URL`, not a
line in the file. By GitHub's billing rule that each job is rounded up to the
whole minute, six runs an hour is 144 a day, so 144 Actions minutes a day and
4,320 in a 30 day month, or 4,464 in a 31 day one, against the 3,000 a month
this account's GitHub Pro plan includes on a private repository: about three
weeks of allowance. (Corrected 2026-11-07: this paragraph and the comment in
`.github/workflows/keepalive.yml` first said 2,000 and GitHub Free.) Minutes
are not metered on a public repository. So the schedule is behind a
second variable, `PRELUDE_KEEPALIVE`: unless it reads `on` the scheduled job
is skipped before a runner starts and bills nothing, while a hand run goes
either way.

**Verified, Claude, 2026-11-07.** The suite printed `1595 passed` and the five
gates exited 0. uvicorn served the three endpoints locally on port 8099, out
of the production-only environment:

```
{"status":"ok"}
```

```
{"match_id":3750191,"home_team":"Argentina","away_team":"England","goals":[{"scorer":"Diego Armando Maradona","team":"Argentina","display_minute":51,"score_after":{"home":1,"away":0},"narrated":false},{"scorer":"Diego Armando Maradona","team":"Argentina","display_minute":55,"score_after":{"home":2,"away":0},"narrated":true},{"scorer":"Gary Lineker","team":"England","display_minute":81,"score_after":{"home":2,"away":1},"narrated":false}]}
```

The 2022 final's six goals came back the same way, ending 3 to 3, because the
shootout is not a goal of the match. One `/buildup`, for a fan of England in
1986 with nothing chosen:

```
{"match_id":3750191,"listener":"team_b","slot":"buddy_conceded","narrator":"The Buddy","text":"Maradona picked it up just inside his own half, and though Beardsley and Reid pressed him, he went past Beardsley there, past Butcher in the final third on the right and past Fenwick on the edge of the box, then got past Shilton in the box and scored with his left foot.","authorship":"drafted with an AI assistant, edited by Shawn, verified by the grounding check","audio_url":"https://sh4wnbk.github.io/prelude/assets/audio/3750191_buddy_conceded.mp3","label":"Verified from play data"}
```

`/moments?match=1` answered 404 and `/buildup?match=3869685&listener=nope`
answered 422. With `build/commit.txt` written by hand, `/health` answered
`{"status":"ok","commit":"29dd7a5c0ffee"}`, and the file was removed again. A
GET carrying `Origin: https://sh4wnbk.github.io` came back with
`access-control-allow-origin: *`, and a POST to each of the three paths
answered 405.

**What was not verified when this was written, and was afterwards.** Nothing
was deployed at the time: no Render service existed, so no public URL had been
called, the keepalive had never run, and `/health` had never reported a real
commit. Shawn deployed it the same day, the keepalive ran by hand and passed,
and Task 18 above is where the live service is checked. The two YAML files were not
parsed by a YAML library, because the repo has none and `npx` was refused;
they are read by eye, and GitHub validates the workflow when it is listed. The
warning in the suite output is starlette asking for `httpx2` instead of
`httpx`; `uv add --dev httpx2` was refused by the sandbox, so the suite
reports one warning beside `1595 passed`.

### The deploy checklist, for Shawn

**Done on 2026-11-07**, except for turning `PRELUDE_KEEPALIVE` on in step 4,
which the standing section at the top of this file covers. Kept as the record
of how the service was created and what to do if it has to be created again.

1. **Create the service from the Blueprint.** Render dashboard, New, then
   Blueprint, and point it at `sh4wnbk/prelude` on `main`. Render's GitHub app
   needs access to the repository, which it will ask for; the repository is
   private, so the grant has to name it.
2. **Watch the first build.** It runs `uv sync --locked --no-dev`, then
   `scripts/fetch_statsbomb.py`, which downloads about six megabytes from
   `github.com/hudl/open-data`, then writes `build/commit.txt`. If uv turns
   out not to be on the path for the start command, the fallback is
   `.venv/bin/uvicorn` with the same arguments, because `uv sync` puts the
   environment in `.venv`.
3. **Copy the URL** Render gives the service, with no trailing slash, and open
   `<url>/health`. The first call after a build is warm; a later one may take
   about a minute while the service wakes.
4. **Set the repository variables.** GitHub, Settings, Secrets and variables,
   Actions, Variables: `PRELUDE_API_URL` to that URL, and `PRELUDE_KEEPALIVE`
   to `on` when the Actions minutes above are acceptable, which on a private
   repository they are not for long. The standing section at the top of this
   file says when to turn it on and what to do until then.
5. **Run the keepalive by hand once.** Actions tab, "Keep the API awake", Run
   workflow. A hand run goes whatever the switch says, and its log prints the
   body it got back. This is also what proves the file is valid YAML.
6. **Hand the URL back**, so the "Live URL: added after deploy" line in
   `README.md` becomes the real one and the OpenAPI spec Bob writes has an
   endpoint to be checked against.

### Task 16: the narrator picker (done, built by Bob and verified)

**Shawn, 2026-11-07: the narrator picker goes live.** Until this task the side
decided the recording and Profile's narrator cards only said "coming soon". A
fan may now choose, and the side rule stays the default until they do. Bob
built it against Task 14 in `docs/bob_brief.md`, in `d5dc9c2`, and the session
export is in `9f98e91`.

**What the build came out as.** 73 lines added and 26 removed across
`app/web/match-content.js` and `app/web/narration-player.js`, which is the two
files the dry run predicted and no more: Profile's markup and the moment card's
inline script needed nothing. The suite is at 1524 passed and all five gates
are at exit 0.

**Verified, Claude, 2026-11-07.** The suite printed `1524 passed`, and the
seven rows of the lookup table below were checked again in a headless browser
against `app/web/` served over HTTP: in each one the words the moment card
showed and the file the player loaded were the same slot, which is the thing
this task could have broken and did not.

**The README says who wrote the six, and so does the frozen field.** The
authorship line said they were written by the team. It now says what that was:
drafted with an AI assistant, edited by Shawn, and verified by Prelude's
grounding check against StatsBomb play data. The watsonx pipeline and its runs
stay named under it. The field frozen beside each narration said the old
sentence for one commit; `AUTHORSHIP` in `scripts/authored_narrations.py` now
carries the README's wording, and the six were refrozen with it, so the one
string the review file, the JSON and `app/web/narrations.json` all read from
says what the README says.

**One lookup is the whole of the design.** `Prelude.slotFor(match)` becomes the
only reader of `hero.voice_for`. The words the moment card shows, the recording
its player plays and the card Profile marks are three answers to one question,
and Task 15 put the first two on one key so the words under the grounding label
are the words the voice reads. A slot belongs to the narrator whose id starts
it, so the lookup also answers which narrators a fan can choose: one with no
slot for any answer has no recording (the Caller), and one with a slot for some
other answer is waiting on a side (the Buddy). No list of persona ids is
spelled in the browser and no rule is written twice.

**The tests that were failing on `main` are the state Bob was handed, and
they pass now.** `tests/test_narrator_picker.py` holds 30, seventeen of which
failed until the picker existed: where the lookup lives, who calls it, what is
stored and the copy a fan reads. Thirteen passed all along and are what the
picker had to leave alone: the keys in
`app/web/matches.json`, the six recordings, the list in
`app/web/narrators.json`, the side rule in `app/orchestrator.py`, and the
Caller having no recording to choose. Three more failed with them, one each in
`tests/test_narrators.py`, `tests/test_narration_player.py` and
`tests/test_frozen_narrations.py`: the note is a tail joined to the name with
nothing after the period, and the two tests that held the shared-lookup
invariant by naming `voice_for` ask for `Prelude.slotFor` instead.

**The lookup's behaviour is checked in a browser, not in the suite**, which has
no JavaScript runtime. The brief and the test module both carry the table and
say so. Task 11 is the precedent: a player that read `whenMatches`'s document
as the list of matches passed every file-reading test and played nothing.

**The dry run.** The brief was implemented on a scratch branch, checked in
headless Edge against `app/web` served over HTTP, and the branch deleted, so
what landed on `main` first was only the README change, the failing tests and
the brief. The diff was 112 lines added and 29 removed across
`app/web/match-content.js` and `app/web/narration-player.js`; Profile's markup
and the moment card's inline script needed nothing. The suite came out at 1524
passed and the five gates at exit 0, except `check_docs.py` failing on the one
claim the brief predicts: the quoted pytest result, which then quoted the
failing run and was the follow-up's.

Every row the browser showed, with the words read off the moment card and the
file read off the player, on Argentina vs England:

| Answer and choice | The card's words | The player's file |
| ----------------- | ---------------- | ----------------- |
| Argentina, nothing chosen | `buddy_scored` | `3750191_buddy_scored.mp3` |
| Argentina, the Storyteller | `storyteller_neutral` | `3750191_storyteller_neutral.mp3` |
| Argentina, the Buddy | `buddy_scored` | `3750191_buddy_scored.mp3` |
| Argentina, the Caller stored | `buddy_scored` | `3750191_buddy_scored.mp3` |
| Just here for the game, nothing chosen | `storyteller_neutral` | `3750191_storyteller_neutral.mp3` |
| Just here for the game, the Buddy stored | `storyteller_neutral` | `3750191_storyteller_neutral.mp3` |
| no answer at all | `storyteller_neutral` | `3750191_storyteller_neutral.mp3` |

The words and the file are the same slot in every row. On Profile, a fan saw
The Buddy marked and The Caller disabled with "The Caller is coming soon.";
tapping The Storyteller marked it and stored `storyteller`, tapping The Buddy
marked it and stored `buddy`. A listener with no side saw The Storyteller
marked, both others disabled, and "The Buddy needs a team. Choose a team under
'Who are you with.'". A tap on a disabled card stored nothing. With the Buddy
stored and the side then dropped, Profile marked The Storyteller and left The
Buddy disabled, which is the lookup's own fallback showing through rather than
anything clearing the stored id.

**What the dry run taught, and the brief now carries it**: serve the screens
over HTTP or every screen keeps its inline copy; the player never puts its
audio element in the document, so reading the file it chose means replacing
`window.Audio` in the page before the screens' scripts run; and emptying the
narrator list with `innerHTML` is refused by the tests, so it is emptied a
child at a time.

**Bob's session is in.** `docs/bob_brief.md` Task 14 is the brief and
`bob_sessions/phase5_task14_narrator_picker.md` is the export, committed in
`9f98e91`, so the entry came off the deliberately absent list in
`scripts/check_docs.py` and that list is empty again.

### Task 15: the six written by the team, verified, frozen and recorded (done)

The record is above. Listed here so the plan reads in order: a half said with
a possessive resolved from the listener's side, a telling required to open on
a name, the six hero narrations the team wrote put in the repo and read
against the records, two of them refused for a place and reported rather than
reworded, both written again by Shawn, the six frozen per listener with their
authorship, the moment card showing the one the fan is about to hear, the
disclosure in `README.md`, and the six recordings in the repo for 2,403
billed characters.

### Task 14: the fallback back in the repo, the side rule, and places required (done, the run kept one)

The record is above. Listed here so the plan reads in order: the six fallback
narrations written verbatim into `scripts/fallback_narrations.py` and
re-checked into `docs/narration_runs/`, a side said only where the ball is
clear of the middle, a candidate refused for places in the run and not in the
check, the review file copied aside with a timestamp before anything was
sent, and a run of all six slots that kept one candidate of the fourteen it
reached.

### Task 13: the move placed on the pitch (done, the six fallback candidates lost)

The record is above. Listed here so the plan reads in order: a zone
vocabulary of eight bands up the pitch and three across it, the beats
carrying a place where the move starts, turns and ends, a wrong place
refused, rule 17 asking every narrator for two or three of them, and a run
of all six slots that kept eight of eighteen and overwrote the six
candidates it was told to keep as the fallback.

### Task 12: the hyphen, the Storyteller's full sentences and the two-slot rerun (done)

The record is above. Listed here so the plan reads in order: a hyphen reading
as the space it stands in for, so "first-time" and "left-foot" are checked
rather than read as prose; the Storyteller told to write no pass as "X to Y";
and one rerun of the two 2022 slots that had something to gain from both.

### Task 11, the second list: the pressure rule, the beats as phrases, two rules and the near copies (done)

The record is above. Listed here so the plan reads in order: "under pressure"
attributed to the player on the ball with "from X" checked against X's own
pressure, every beat rendered as a phrase instead of a line with its fields
labelled, rules 15 and 16 about the long ball and the first-time finish, a
near-copy filter on the words as well as on the shape, and one rerun of the
three 2022 slots.

### Task 11: the three check and prompt fixes, and the rerun (done)

The record is above, under "Task 11". Listed here so the plan reads in order:
`is_a_reaction` against the match's own names, attribution read off the
subject of the sentence rather than off the ball, the yard figures out of the
beats with the consecutive dribbles grouped, and one rerun of the six slots
with no retries.

### Task 10: a token cap, curated beats and rule 14 (done, the run short of eighteen)

**The diagnosis, from Shawn on 2026-10-31: the candidates echo the fact
list.** Every one of the eighteen said "received, carried and passed",
because the prompt handed over every recorded event of the passage. Eight of
the twenty-four 1986 records are a `Ball Receipt*` and seven more are a carry
of under a yard. Nothing in `app/grounding.py` was wrong about any of it: a
receipt is a real record and a touch on the spot is a real record, and
neither is a beat. High effort cost about 817,000 tokens and bought nothing,
and the fix was never the model: it is curating what the model is given,
which is Prelude's job whatever narrates.

**Step 1, `11b357d`: a run is capped in tokens and refuses to start without
one.** `WatsonxProvider` takes `token_cap` and raises `TokenCapReached`
before a call whose worst case would pass it: the tally it already reads off
watsonx's `usage` object, plus the prompt at `CHARACTERS_A_TOKEN`, plus the
whole of `max_new_tokens`, because a reasoning model writes its reasoning
into that budget. Before the call rather than after it, since a call already
sent is already billed. `scripts/narrator_candidates.py` takes
`--max-total-tokens`, there is no default, and `--confirm` refuses without
one. When the cap is reached the run keeps every candidate already written:
the slot it stopped in with what it had, the goal with the slots it had, and
the review file saying it is short of what it asked for.

**Step 2, `62c7d6b`: `app/story_beats.py`, and the records block is gone.**
The prompt now shows the beats a goal call tells: the recovery, each pass
(who it reached, "forward" or "back" off the change in x, "long" at
`LONG_PASS_YARDS`, the assist, the box), each carry of `RUN_YARDS` or more
(its distance in whole yards and whether it ended in the box), each dribble
past an opponent as one beat for the two records naming both players, the
pressure on the player with the ball, and the finish with the body part and
the first-time flag. Receipts go because the pass beat already names who the
ball reached; a carry under `RUN_YARDS` goes because a touch on the spot is
not a turn in the story.

`StoryBeat` carries no minute, no second and no timestamp, and
`NO_CLOCK_FIELDS` is read off the dataclass by a test, so a clock added to it
fails a test rather than reaching a prompt. The goal's minute is in the
report header and the model never sees it. `play_pattern` and the own half
are said once above the list rather than on every line, which was two facts
printed twenty-four times.

**The beat lists, from `scripts/story_beats_report.py`:**

| Goal | Records | Beats | What they are |
| ---- | ------: | ----: | ------------- |
| 1986 54:18 | 24 | 14 | 1 recovery, 2 passes, 3 pressure, 4 dribbles past, 3 runs, the finish |
| 2022 35:22 | 13 | 6 | 5 passes, the finish |

The 1986 list in order: Cuciuffo recovered; Cuciuffo to Enrique, forward;
Enrique to Maradona, the assist, forward; Beardsley pressed; past Beardsley;
a run of 35 yards forward; Reid pressed; past Butcher; 17 yards forward; past
Fenwick; 17 yards forward, ending in the box; Butcher pressed; past Shilton;
the shot, from inside the box, with his left foot. The 2022 list: Molina to
MacAllister, MacAllister to Messi, Messi to Álvarez, Álvarez to MacAllister
long, MacAllister to Di María the assist into the box, and the shot first
time with his left foot.

**Butcher's third pressure is matched on feed order and not on the clock.**
It is recorded at 54:17 against the carry at 54:15 it overlapped, because the
clock fields floor and a pressure lasts longer than the touch that began
under it. Matching on the second dropped it; `_pressed_the_carrier` looks at
the possession team's nearest record in feed order instead, and all three
pressures are kept. Reid's only record in the passage is a pressure, so
without them "Beardsley and Reid closed him down" cannot be written at all.

**The check is unchanged and still reads every record.** The curation can
only narrow what a narration may say: a line about a ball receipt would still
pass the check and will not be written, because the model was never shown
one. The block no longer says "nothing happened that is not here", which a
curated list makes untrue; it says the narration may not reach outside the
list, which is true.

**Step 3, `c938a87` and `185563e`: rule 14.** "Use the word 'who' at most
once in the narration. Join the play with other connections: a comma chain,
'and', 'on to', or a new clause." Added as rule 14 rather than inserted, so
the numbers rules 11, 12 and 13 are referred to by elsewhere do not move. The
cadence rules are untouched: rule 12 still asks for one or two sentences of
play with the clauses joined, nothing bans a long sentence and nothing asks
for a full stop after each pass. Nothing in `app/grounding.py` answers to it
because it is cadence and not a claim, so `said_who` counts the word, the
review table has a "who" column, and a candidate saying it more than once is
flagged in bold and kept.

**The run, and the cap stopped it at ten of eighteen.** Six slots, three
candidates each, `openai/gpt-oss-120b` at `reasoning_effort` low,
`--max-total-tokens 80000`. The candidates are in
`C:\Users\shawn\prelude-review\narrator_candidates_2026-11-05.md`, with the
same data beside it as JSON.

| What | Figure |
| ---- | -----: |
| billed by watsonx, off the `usage` object | 76,542 |
| of it prompt | 62,766 |
| of it completion | 13,776 |
| the cap | 80,000 |
| unspent | 3,458 |
| the plan's expected figure | 78,622 |
| calls sent | 26 |
| candidates kept | 10 of 18 |
| slots reached | 5 of 6 |

**Where it stopped.** In the 2022 `buddy_scored` slot, on candidate 2: 76,542
billed and the next call's worst case 80,731. So 2022 `buddy_scored` has
nothing and 2022 `storyteller_neutral` was never generated. Everything
written before that point is in the files.

**The prompt is the expensive half, and the retries are why the run ran out.**
62,766 of the 76,542 is prompt, over 26 calls, which is about 2,414 a call.
Nine of the 26 were failed attempts. Eighteen calls at that rate is about
43,000 and the cap would not have been reached; the nine retries spent the
difference.

**Eight of the nine failures are one failure.** The model wrote the reaction
as a second sentence opening on a capitalised adjective, "Incredible!",
"Pure magic!", "Unbelievable!", and the check refused all three the same way:
`is_a_reaction` wants a sentence that names nobody, and a capitalised word
that is not in `NOT_A_NAME` reads as a name. "What a finish!" passes because
"What" is in that set. The same attempts were also refused for the
exclamation mark and for ending the play and then carrying on. This is the
check working as specified on an edge the prompt does not warn about, and it
cost nine calls of twenty-six. Whether the fix belongs in `NOT_A_NAME`, in
`is_a_reaction` or in rule 3 is the next thing to decide, and nothing was
changed here.

**The distances are being read out loud, and that is new.** Every 1986
candidate spells the yards: "carried forward thirty-five yards, evaded Reid,
beat Butcher, ran forward seventeen yards, beat Fenwick, ran forward
seventeen yards into the box". It is grounded, because the beats carry the
distance and the grammar holds a yards claim against the record, and the two
seventeens read as a stumble rather than as a build. The three
`storyteller_neutral` candidates say "ran forward" with no figure and are the
better cadence for it. Whether a beat should carry the distance at all, or
say "a run" and nothing more, is Shawn's call after reading them aloud.

**Rule 14 held on all ten.** Seven say "who" once and three say it not at
all, against eighteen of eighteen hanging the move off it on 2026-10-31.

**Every candidate fits the budget.** `scripts/tts_hero.py --budget` is 3,500
for the six recordings, so 583 a recording, and the ten run 297 to 369
billed. The 1986 candidates are 343 to 369 and the 2022 ones 297 to 339.

### Task 11: the three check and prompt fixes Shawn read off the run (done)

**Shawn read the ten candidates of 2026-11-05 aloud and none was ready to
record.** The curation had done its job: the "received" echo was gone and the
event order was right in every 1986 candidate. What was left was one hole in
the check and three things the pipeline was doing to the output.

**The hole, and it matters more than the cap.** Buddy for Argentina candidate
1 said "We won it back through Cuciuffo, who passed to Enrique and set up
Maradona". The records put `goal_assist` on Enrique. The check passed it on
twenty-one claims.

`support` was never the problem: a `chain` grounds only against a record
whose `pass.player` is the actor and whose `pass.recipient` is the target, and
"set up" only against the pass carrying `goal_assist`. The problem was which
actor reached it. `Reader` advanced `tracked` to the recipient after a chain,
and the next chain marker in the same clause took `tracked` as its source, so
the ball moving on to Enrique made Enrique the subject of "set up" although
"and" joins a second verb to the same subject.

**Fix 2, `f6cb030`: `_chain_source` answers in three steps.** A name or
pronoun in the marker's own clause; failing that the subject a chain in that
clause already established; failing that the player with the ball. A bare
marker is exempt because it carries no verb of its own, so "Molina to
MacAllister on to Messi" is the ball continuing, which rule 14 offers as a
join. All eight references still pass, including "played it to Enrique who
found Maradona", where the pronoun moves the subject on and the second chain
really is Enrique's.

**Fix 1, `bdecc28`: a reaction names nobody by the match's names, not by
capitals.** The reader emits an unknown name for any capitalised word it
cannot resolve, `is_a_reaction` refused a sentence holding one, and "What a
finish!" passed only because "What" is in `NOT_A_NAME`. So every neutral
candidate of that run ended "What a moment", "What a finish" or "What a
strike", every England one on a stapled-on "Ah, no.", eight of the nine
retries went on the refusal and the 2022 `buddy_scored` slot lost all three
attempts to it. `name`, `team` and `ambiguous_name` resolve against this match
and still make a sentence play; `unknown_name` points at no record and no
longer rules a reaction out.

One capital is still not allowed through. "Pure Pelé, that!" names a
footballer who is not in this match, which is both an invention and the
verdict about history `CLAUDE.md` forbids, so an unresolved capital is read as
a reaction only where it is the sentence's own first word. A proper noun
introduced mid-sentence keeps the sentence in the play.

**Two of the three words the model reached for stay refused anyway**, as the
editorial epithets they are: "incredible", "unbelievable" and "stunning" are
in `BANNED_PATTERNS`. What the fix widens is the rest, and the rerun used it:
"Pure magic." was written and accepted as a reaction.

**Fix 3, `ed20c8f`: no yard figures, and consecutive dribbles grouped.** The
beats carried a carry's distance in whole yards and every 1986 candidate read
it out. `yards` is `long_carry` now, a flag, and the beat says "a long carry";
the beat list is bulleted rather than numbered for the same reason, so the
block holds no digit at all. And consecutive dribbles past one player are one
beat naming the defenders in order, with the carries between them absorbed,
because a list of beats is read out as a list of beats. A pressure between
them keeps its own beat and the group sits where it ends, so a pressure inside
its span is said before it. A carry that ended in the box ends the group,
which is why Shilton is beaten in a beat of his own.

**The 1986 beat list, from `scripts/story_beats_report.py`: 24 records to 10
beats, from 14.**

```
- Cuciuffo recovered the ball
- Cuciuffo passed to Enrique, forward
- Enrique passed to Maradona, the assist, forward
- Beardsley pressed the player on the ball
- Reid pressed the player on the ball
- Maradona dribbled past Beardsley, Butcher and Fenwick, carrying the ball
  forward between them, under pressure
- Maradona carried the ball, a long carry, forward, ending in the box, under
  pressure
- Butcher pressed the player on the ball
- Maradona dribbled past Shilton, under pressure
- Maradona shot, from inside the box, with his left foot
```

The 2022 list is unchanged at six: it holds no dribble and no carry over ten
yards.

**Fix 4, the rerun: all six slots, one attempt a candidate, and it cost two
thirds of what the retried run did.** `--max-retries` is a flag now, and 0 is
one attempt with no regeneration.

| | 2026-11-05, three attempts | the rerun, one attempt |
| --- | ---: | ---: |
| calls sent | 26 | 18 |
| billed by watsonx | 76,542 | 51,496 |
| of it prompt | 62,766 | 43,691 |
| of it completion | 13,776 | 7,805 |
| the cap | 80,000 | 80,000 |
| unspent | 3,458 | 28,504 |
| candidates kept | 10 of 18 | 10 of 18 |
| slots reached | 5 of 6 | 6 of 6 |

**The grouping is in the output.** "Maradona dribbled past Beardsley, Butcher
and Fenwick, carried it forward into the box, slipped past Shilton and struck
with his left foot" is every 1986 candidate's shape now, against "beat
Butcher, ran forward seventeen yards, beat Fenwick, ran forward seventeen
yards" before it. No candidate carries a yard figure, and none says "evaded
Reid": where Reid is named it is as "pressed by Beardsley and Reid", which the
records hold.

**Five of the eight drops are the model being wrong, which is the check
working.** "Álvarez back to MacAllister" over a ball 36 yards up the pitch,
twice; "MacAllister set up Di María forward" with the "forward" landing on Di
María, whose only record with two ends is the shot; "a long pass to Di María"
over a pass of 26 yards; "Ah, no." written in front of the play; and
"Incredible!".

**Three of the eight are one false refusal, and it is new.** "Under pressure
from Beardsley and Reid" is refused with `'under pressure': no record of Peter
Beardsley is marked under pressure`. The claim is true: Beardsley and Reid are
the players who pressed. The `pressured` move resolves its actor by the
framework's action before name, so it lands on Beardsley, and `support` then
asks whether Beardsley's own record carries `under_pressure`, which is
Maradona's flag and not his. "Pressed by Beardsley and Reid" passes, which is
why half the kept 1986 candidates say it that way. The beat line "X pressed
the player on the ball" is what invites the other phrasing, so this is partly
the curation's own doing and nothing was changed for it here. The fix is a
rule about who "under pressure" is about, in `app/narration_grammar.py`, and
it is one line of `support` plus a test.

**"Glided past Shilton" still passes, and "glided" is a manner word.** "Past
Shilton" is grounded, because the records hold a dribble past him; the manner
is unsaid in the data and uncheckable, like "smashed" before it was banned
outright. No candidate of the rerun used one, and nothing was changed for it.

### Task 15: the writing moved to the team, and the six recorded (done)

**Shawn, 2026-11-05: at effort low the model would not place the move, so the
six hero narrations are written by the team and verified by Prelude's
grounding check like any model output.** "Verified from play data" still means
every claim traces to the records; the check is what proves it. The authorship
is disclosed rather than implied, and the model runs stay in
`docs/narration_runs/` as the evidence of the pipeline.

**Step 1, `35db706`: whose half "our half" is.** A half said with a possessive
names a side, and the band is read in that side's own frame.
`from_the_other_end` in `app/pitch_zones.py` is the arithmetic, `PITCH_X` less
the recorded `x`, and `_reads_from_the_other_end` in
`app/narration_grammar.py` is the resolution: "our" is the listening side,
"their" is the side they are not on, and with no listener in hand the phrase
is read as the vocabulary spells it, so a Storyteller's "their own half" is
still the half the side on the ball defends.

| Said | For a fan of Argentina | For a fan of France |
| ---- | ---------------------- | ------------------- |
| "deep in our own half" | where Molina played it, `x` 25.9 | France's own half, refused |
| "deep in their own half" | France's own half, refused | where Molina played it |
| "just inside our half" | `x` 50 to 60 | where the long ball was struck, 63.2, which is 56.8 from France's end |

Three more things came with it. A half with no band word in front of it ("we
started from our own half") is the broad position claim it always was and
places nothing, so the old 2022 `buddy_scored` fallback still places the move
nowhere. "Our half" is the one first person that stands on itself: every
record in "Álvarez, just inside our half on the right" is Argentina's, so
asking the play for a France listener's own side refused a true line. And a
curly apostrophe is written as a straight one before anything is read, which
is what the kept candidate of Task 14 carried.

**Step 2, `26a461a`: a telling opens on a name.** The first word is a player,
a team or a country the records hold. `opener_missing` in
`scripts/narrator_candidates.py` is the acceptance rule, beside
`places_missing` and not in the check, because a narration opening on "We"
makes no false claim and a check that refused one would be refusing cadence.
Rule 18 of the goal-call prompt asks every narrator for it and the rule
numbers before it do not move.

**Four of the eight references open elsewhere, and the rule is newer than they
are.** The 1986 Argentina Buddy and the 2022 Argentina Buddy open on "We", the
1986 Caller on "It" and the 2022 France Buddy on "In". They are still the
standard for the writing and are still checked word for word; `docs/VOICE.md`
records the tension beside the rule. Whether rule 18 should reach them is
Shawn's call and nothing here changed them. Two recorded test fixtures did
change, because both are candidates their tests mean the run to keep: the
near-copy pair opens on Molina now and the cap test's answer on Argentina.

**Step 3, `776b4a1`: the six are in the repo and read against the records.**
`scripts/authored_narrations.py` holds them verbatim with straight
apostrophes, carries `AUTHOR` ("the team") and `AUTHORSHIP` ("written by the
team, verified by the grounding check") beside every one of them, and reads
each through the three rules a candidate meets. It calls no model, freezes
nothing, writes `docs/narration_runs/authored_2026-11-07.md` and the same
answers as JSON, and exits 1.

| Slot | Check | Claims | Places | Opener | Billed |
| ---- | ----- | -----: | -----: | ------ | -----: |
| 1986 `storyteller_neutral` | **refused** | 18 | 5 | Cuciuffo | 367 |
| 1986 `buddy_scored` | **refused** | 18 | 5 | Cuciuffo | 351 |
| 1986 `buddy_conceded` | grounded | 17 | 4 | Maradona | 324 |
| 2022 `storyteller_neutral` | grounded | 23 | 5 | Argentina | 485 |
| 2022 `buddy_scored` | grounded | 23 | 4 | Molina | 449 |
| 2022 `buddy_conceded` | grounded | 22 | 4 | Molina | 428 |

All six open on a name, all six place the move four or five times, not one of
them says "who", and the six together are 2,404 billed characters of the 3,500
the budget allows. **The three 2022 slots and the 1986 `buddy_conceded` slot
are grounded. The other two 1986 slots are refused, and both refusals are the
reading pairing a place with the wrong action.**

**The first: "on into the final third" is read as being about Beardsley.** The
1986 `buddy_scored` line says "past Beardsley, on into the final third, past
Butcher on the right". `_about` in `app/narration_grammar.py` points a place at
the move before it, which is the dribble past Beardsley at (54.4, 56.4), and
that is just inside his own half. The carry the words mean ends at (87.1,
68.6), which is the final third, and "on into" is not a move the grammar
reads, so there is nothing between the place and Beardsley. The claim is true
of the records and the pairing cannot see it. Reading a place as being about
the move after it when the move before it refuses is a change to `_about` and
a judgement about which of the two is meant.

**The second: "beat Butcher on the right" leaves Butcher a bare name.**
`PAST_MARKERS` is "past", "around" and "round", so "beat" is not read as a
dribble past anybody: Butcher and Fenwick become name moves, and the zone
branch reads a place off the attacking side's own records, which a defender's
name holds none of. The 1986 `storyteller_neutral` line is refused twice over
for it, on "on the right" and on "on the edge of the box". Both places are
true: Maradona's dribbles past Butcher and Fenwick are at (87.1, 68.6) and
(97.1, 55.1). Adding "beat" to `PAST_MARKERS` would read the line as written
and would also make "beat" a claim everywhere else it is said, which is the
decision.

**Neither was reworded by the session that found them**, which is what that
task asked: the words were Shawn's, the refusals are the check's, and a
narration bent to fit a reading is not the thing that was written. The two
refusals were reported instead, and Shawn wrote both lines again himself.

**The two 1986 lines were written again, by Shawn, and nothing in the check
moved.** Both refusals above were the pairing and not the words, and the
answer was to say the place beside the dribble itself in both tellings: "past
Butcher in the final third on the right, past Fenwick on the edge of the box".
"On into the final third" and "beat Butcher on the right" are gone. The two
wordings they replaced are in `tests/test_authored_narrations.py` with the
refusal each one met, so the day either reading changes, that is where it
shows. `_about` still points a place at the move before it and "beat" is
still not in `PAST_MARKERS`.

**Step 1 of the resumed task, `11dfdaf`: all six ground.** The six together
are 2,403 billed characters of the 3,500 the budget allows, none of them says
"who", every one opens on a name, and every one places the move four or five
times.

| Slot | Check | Claims | Places | Opener | Billed |
| ---- | ----- | -----: | -----: | ------ | -----: |
| 1986 `storyteller_neutral` | grounded | 18 | 5 | Cuciuffo | 371 |
| 1986 `buddy_scored` | grounded | 18 | 5 | Cuciuffo | 346 |
| 1986 `buddy_conceded` | grounded | 17 | 4 | Maradona | 324 |
| 2022 `storyteller_neutral` | grounded | 23 | 5 | Argentina | 485 |
| 2022 `buddy_scored` | grounded | 23 | 4 | Molina | 449 |
| 2022 `buddy_conceded` | grounded | 22 | 4 | Molina | 428 |

**Step 2, `eadd988`: the card shows what the fan hears.**
`app/web/narrations.json` holds the six under `slots`, one per
`hero.voice_for` key, beside the per-goal narration the model wrote, which is
untouched and stays as the pipeline's own evidence. Each slot carries the
narrator, the listening side, the author, the authorship, the check's verdict,
the places it says and what the recording costs.

`scripts/freeze_narrations.py --authored` writes them with no model call and
refuses to write one the check, the places rule or the opener rule turns
down. The moment card picks its text by `voice_for[listenerFor(match)]`,
which is the lookup `app/web/narration-player.js` already used to pick the
recording, so the words under the label and the voice reading them are one
piece of writing. With no listener answer it is the neutral slot, and that is
what the markup's inline copy carries now.
`scripts/check_match_copy.py` holds the inline copy to the neutral narration
and refuses a `voice_for` key with no narration or no authorship behind it.

**Step 3, `40fbb10`: the freeze is held by tests.**
`tests/test_frozen_narrations.py` asks four things of each of the six: that
the words are the ones `scripts/authored_narrations.py` holds, that the author
is the team and the authorship is the sentence a reader is owed, that the
check still passes in the slot's own persona and listening side and on the
same claim count it was frozen on, and that the places and the opener still
hold. One test strips the authorship off a copy to prove the assertion is not
vacuous.

**Step 4, `115bea7`: the disclosure.** "Who wrote the six, and who verified
them" in `README.md`, under the label section and in the present tense: the
six were written by the team and verified by Prelude's grounding check
against StatsBomb play data, the check reads them exactly as it reads a
model's, and the label is about whether the claims trace to the records
rather than about who put the words in that order. The model pipeline is
named as what it is, with its runs in `docs/narration_runs/` and the reason
the writing is the team's.

**The "AI AUDIO NARRATION" label is unchanged, on Shawn's instruction during
the task.** It was changed to "AUDIO NARRATION" on all three spans that carry
it, the moment card's and the two on the Moments list, and put back, so the
screens are byte for byte what they were.

**Step 5, `6d4d078` and `9843e53`: the six recordings are in the repo.**
`scripts/tts_hero.py` reads `slots` and is keyed by match and `voice_for`
key, so each recording speaks its own listener's telling rather than one
narration per goal spoken three ways; a key with no narration, or one not
recorded as grounded, stops the run. The voices needed no change: the
Storyteller is `en-US_EmmaNatural` and the Buddy `en-US_EthanNatural` in
`app/personas.py`.

Shawn confirmed the Text to Speech instance showed no November usage, and the
run was sent with `--budget 3500`:

| File | Voice | Billed | Bytes |
| ---- | ----- | -----: | ----: |
| `3750191_storyteller_neutral.mp3` | Emma | 371 | 217,124 |
| `3750191_buddy_scored.mp3` | Ethan | 346 | 192,812 |
| `3750191_buddy_conceded.mp3` | Ethan | 324 | 186,452 |
| `3869685_storyteller_neutral.mp3` | Emma | 485 | 225,188 |
| `3869685_buddy_scored.mp3` | Ethan | 449 | 205,724 |
| `3869685_buddy_conceded.mp3` | Ethan | 428 | 223,868 |
| **total** | | **2,403** | 1,251,168 |

2,865 characters were submitted and 2,343 spoken; the difference is the
pronunciation markup, which IBM bills and does not speak. `hero.audio` names
all six and `TestTheAudioMap` passes.

**`scripts/check_vocabulary.py` reads the six now**, because they are the
words a voice actually says. That flagged ten more function words ("again",
"him", "inside", "into", "just", "on", "our", "to", "what", "when"), every
one a full form against a reduced one, a stress variant or the wh cluster,
and all ten are on `CHECKED_NO_ENTRY_NEEDED` in `app/pronunciation.py` with
the reason. None is a heteronym, so there is nothing for a listener to
mishear.

**What the docs stopped claiming.** Three places said no recording exists:
the README's capability list and its mock-player entry, and two passages in
`docs/VOICE.md` recording the 403 of 2026-10-30. The play buttons on the
Moments list are still markup and the README says so; the one on the moment
card plays this listener's recording.

**The suite and the gates.** `pytest -q` reports `1494 passed` and all five
gates exit 0. Seventy nine of those tests were added across the two sessions
of this task, over the resolution, the opener rule, the six, and the freeze.

### Task 14: the fallback restored, the side rule and places required (done)

**Shawn, 2026-11-05, after the zones run overwrote the six: field position is
required and not optional.** The zones run placed the move in one of its
eight kept candidates, so the vocabulary was built and the asking was what
was weak. This task puts the six fallback narrations where a run cannot
reach them, moves the side rule off the thirds of the pitch, makes a place a
condition of being a candidate, and spends one more run.

**Step 1, `a41ea38`: the six are in the repo.** `scripts/fallback_narrations.py`
holds them verbatim as Shawn kept them, re-reads each against `data/raw/` with
the current check in the persona and listening side its slot is written for,
and writes `docs/narration_runs/fallback_2026-11-05.md` and the same answers as
JSON beside it. It exits 1 if any of the six is refused, so a check change that
would cost a fallback is visible rather than quiet. **All six are grounded
today**, and not one of them places the move:

| Slot | Check | Claims | Billed | Places |
| ---- | ----- | -----: | -----: | -----: |
| 1986 `buddy_scored` | grounded | 18 | 295 | 0 |
| 1986 `buddy_conceded` | grounded | 19 | 310 | 0 |
| 1986 `storyteller_neutral` | grounded | 22 | 341 | 0 |
| 2022 `buddy_scored` | grounded | 17 | 331 | 0 |
| 2022 `buddy_conceded` | grounded | 15 | 307 | 0 |
| 2022 `storyteller_neutral` | grounded | 16 | 369 | 0 |

**Step 2, `0e1f1e1`: a side is said only where the ball is clear of the
middle.** "On the left" is `y` under 18 and "on the right" is `y` over 62, the
sides of the penalty area, where `LEFT_Y` and `RIGHT_Y` were the thirds of an
eighty yard pitch at 26.7 and 53.3. The old rule put "on the right" on four
beats between `y` 54.9 and 60.5, a yard or two past the middle, and three of
them fell in one line: the grouped 1986 dribble beat said it three times.

Nine of the twelve places the two hero passages carry are now said with no
side. Butcher's dribble at 68.6, Molina's pass at 71.8 and the long ball's
strike at 68.2 keep it; Beardsley's dribble at 56.4, Fenwick's at 55.1, the
long ball's landing at 54.9 and Enrique's pass at 60.5 lose it.
`BOX_TOP_Y` and `BOX_BOTTOM_Y` are the same two numbers and stay separate
constants, because the box bands ask whether a spot is inside the box and the
side rule asks whether it is out wide.

**One consequence, worth knowing before the pick.** Both of the zones run's
1986 Storyteller candidates say "on the right" over the grouped dribble beat,
and that is now a wrong place: the check refuses them today. The six fallback
narrations say no side anywhere and are untouched by this.

**Step 3, `823e494`: a telling that places the move nowhere is not a
candidate.** `places_missing` in `scripts/narrator_candidates.py`, and not in
`app/grounding.py`: the check refuses a place the records do not hold and a
narration naming no place holds nothing wrong, so grounding stays about truth
and the six fallback narrations still ground. Two things are asked. At least
`PLACES_WANTED` places, which is two, the floor of what rule 17 asks for. And
in a passage holding a long ball, one of those places has to hold the
coordinate the ball was struck from, which is the zones run's own finding: all
four of its 2022 tellings placed the ball where it came down and none where it
was hit.

**The long ball test is read phrase by phrase and not by the action each
phrase was said beside, which is the weaker of the two readings.** The zones
run's 2022 Storyteller passes on an "on the right" it said about Molina's
pass, because that pass and Álvarez's strike are both out wide on the right.
The stronger reading is already in `app/narration_grammar.py` as the `about`
on a zone move, and it would refuse every candidate that run produced, which
is why this is the one built. Tightening it is a change to `places_missing`
and nothing else.

A slot that keeps nothing now prints its dropped list too. `review` stopped at
"No candidate for this slot passed" and the console log was the only record of
why, which would have hidden eleven of this run's refusals; `_slot_candidates`
is lifted out of it whole for that.

**Step 4: the review file was copied aside before anything was sent**, which
Task 13 asked for and nothing automates. The copies are
`narrator_candidates_2026-11-05.before-task14-20261105T2027.md` and the JSON
beside it, in the same directory as
`hero_candidates_2026-10-30.before-task8.json`. **They are the only copy of
the zones run's eight candidates**, and this run overwrote all three 1986
slots with nothing, so the copy was needed within the hour it was made.

**Step 5, the run: all six slots, 77,480 tokens of the 80,000, and it stopped
on the cap.** Effort low, three candidates a slot, two retries allowed, 24
generations and one IAM exchange. It reached fourteen of the eighteen
candidates it asked for and kept one.

| This run, all six slots | |
| --- | ---: |
| generations sent | 24 |
| billed by watsonx | 77,480 |
| of it prompt | 60,567 |
| of it completion | 16,913 |
| the cap | 80,000 |
| unspent | 2,520 |
| candidates reached | 14 of the 18 asked for |
| candidates kept | 1 |
| refused for places | 11 |
| dropped on grounding refusals alone | 2 |
| near copies dropped | 0 |

**The one it kept is the 2022 `buddy_conceded` slot**, on its third attempt,
grounded on 22 claims, 410 billed, and it places the move five times: "deep in
his own half", "on the right", "just inside France's half", "on the right"
again and "on the edge of the box". It is the first candidate of any run to
say where the long ball was struck from. **It carries a `RIGHT SINGLE
QUOTATION MARK` (U+2019) inside "France's"**, which the review file flags and
which would reach the speech service as written.

**Eleven of the fourteen were refused for places, and the refusal is the
finding.** Every 1986 candidate placed the move nowhere at all: nine grounded
tellings of that goal, and not one of them said a band or a side. The prompt
carries rule 17 in every voice and the beats carry the places, and at effort
low the model still writes the 1986 move as a list of defenders. Two of the
2022 candidates placed it once, on the edge of the box, which is where the ball
came down.

**The 1986 slots hold nothing in the review file now.** This run produced all
three of them and kept none, and `merged` replaces a slot a run produced, so
the zones run's five 1986 candidates are out of the file. They are in the
timestamped copy and the fallback three are in the repo, so nothing is lost
this time. The 2022 `storyteller_neutral` slot was never reached, so its zones
run candidate was carried across with its own provenance.

**Twelve grounding refusals, and the 1986 `buddy_scored` slot is where they
are.** Six of the twelve are its, and the shape is the same every time: the
model answered with two whole narrations in one reply, so the first one's
goal was followed by more play and its reaction stood before the finish. Two
other refusals are the model calling Shilton's save a shot ("fired", "struck"
with Shilton as the subject) and one is "set up Maradona" read as a Cuciuffo
assist. The three new ones are worth keeping: "Ah, no." written as the first
sentence rather than the last, "under pressure from Maradona" when `Pressure`
is the presser's record, and "France's" written with a curly apostrophe that
the name check reads as a name it does not record.

**What the three readings of the long ball cost, in one line.** The
`buddy_conceded` candidate that was kept needed three attempts to say "just
inside France's half on the right", and the two before it were refused for the
apostrophe and for "the box" over MacAllister. The phrase the vocabulary wants
is reachable and it is not cheap.

### Task 13: a place on the pitch, and the run that spent the review file (done)

**Shawn, reading the six candidates of 2026-11-05 aloud: they have no field
position.** "Dribbled past Butcher" and "a long ball to MacAllister" give a
listener nothing to place. Two of the eight references say a band ("just
inside his own half") and the other six place the move only with "in his own
half" and "in the box", so the standard itself barely does it either. The
coordinate is on almost every record and nothing was turning it into words.

**Step 1, `1d29e49`: `app/pitch_zones.py`.** Eight bands of `x` and three of
`y`, on Shawn's thresholds, each one a phrase: "deep in his own half" under
40, "in his own half" 40 to 50, "just inside his own half" 50 to 60, "just
inside their half" 60 to 70, "in their half" 70 to 80, "in the final third"
80 up, "on the edge of the box" 96 to 102 inside the box's width, "in the
box" past 102 inside it, and "on the left" and "on the right" outside `y`
26.7 and 53.3. Both box bands ask for the width as well as the line, because
a ball at `x` 110 and `y` 10 is by the byline with the goal frame between it
and the posts, and anything from 80 up that is neither box band is the final
third, which is this module's reading of a coordinate the vocabulary names no
zone for.

**A place is read off the attacking side's own record.** Butcher's `Dribbled
Past` is at (33.0, 11.5) and the `Dribble` that beat him is at (87.1, 68.6),
which is the same place said twice from two ends, so reading a mirrored
record would put "on the left" and "just inside their half" over a dribble
that was neither.

**`Facts` gains the fixture's two teams.** All thirteen records of the 2022
counter are Argentina's, so the side being attacked is not in the passage and
"just inside France's half" has no name to use. They come off the lineups
file `app/recorded_names.py` already reads, which is the same StatsBomb open
data as the event feed.

**Step 2, same commit: which beats carry a place.** The first action, a ball
recovery, each defender gone past, a long ball at both ends, the assist and
the finish. Not every beat and not every pass, because every record carries a
location and a telling that places all of them is the label reading
`beat_line` was written to stop: two of the five 2022 passes say nothing about
where they were played.

**The two beat lists, from `scripts/story_beats_report.py`.** 1986, 24 records
to 10 beats:

```
   1. José Luis Cuciuffo (Argentina), deep in his own half, won the ball back
   2. José Luis Cuciuffo (Argentina) passed it forward to Héctor Enrique
   3. Héctor Enrique (Argentina), in his own half on the right, passed it
      forward to Diego Armando Maradona, which is the assist
   4. Peter Beardsley (England) pressed the player on the ball
   5. Peter Reid (England) pressed the player on the ball
   6. Diego Armando Maradona (Argentina) dribbled past Peter Beardsley just
      inside his own half on the right, Terry Butcher in the final third on
      the right and Terry Fenwick on the edge of the box on the right,
      carrying the ball forward between them, under pressure
   7. Diego Armando Maradona (Argentina) carried the ball forward on a long
      run, ending in the box, under pressure
   8. Terry Butcher (England) pressed the player on the ball
   9. Diego Armando Maradona (Argentina) dribbled past Peter Shilton in the
      box, under pressure
  10. Diego Armando Maradona (Argentina), in the box, shot with his left foot
```

2022, 13 records to 6 beats:

```
   1. Nahuel Molina (Argentina), deep in his own half on the right, passed it
      forward to Alexis MacAllister
   2. Alexis MacAllister (Argentina) passed it forward to Lionel Messi
   3. Lionel Messi (Argentina) passed it forward to Julián Álvarez
   4. Julián Álvarez (Argentina), just inside France's half on the right, hit
      a long ball forward to Alexis MacAllister again, landing on the edge of
      the box on the right
   5. Alexis MacAllister (Argentina), on the edge of the box on the right,
      passed it forward to Ángel Di María, into the box, which is the assist
   6. Ángel Di María (Argentina), in the box, shot first time with his left
      foot
```

**The side rule puts "on the right" on three beats Shawn's own list did not
name**, and all three are just over the line: Beardsley's dribble at `y`
56.4, Fenwick's at 55.1 and the long ball's landing at 54.9, against a
threshold of 53.3. The three Shawn did name a side for are at 68.6, 71.8 and
68.2. The rule as written is what is built, and the cost is that the grouped
1986 dribble beat says "on the right" three times in one line. Moving the
line, or saying a side only where it is clear of it, is a change to
`side_of` in `app/pitch_zones.py` and nothing else.

**The finish says the place instead of "from inside the box".** The box band
is the eighteen yard line and the box's width, so it is the same claim with
one more line in it; saying both would be saying it twice.

**Step 3, `d653794`: a place is a claim, and a wrong one is refused.** Twelve
spellings, hyphens allowed on all of them, and the band and the side are two
moves because either can be wrong on its own. Each is about the action it was
said beside, not about the player: `player_spots` answers where a player was
at any point in the passage, which is right for a half and far too loose for
a band, since three of Maradona's four dribbles are in different bands. The
move before the phrase owns it, or the one after where nothing is behind it,
which is the appositive the beats are written in.

**The two broad phrases are left alone.** "In his own half" and "in the box"
stay the position claims they were, because Maradona's first touch is at `x`
55.2, whose band is "just inside his own half", and three of the eight
references say "in his own half" over it: reading the whole-half phrase as a
band would refuse a true sentence and a reference with it. A band phrase is
exclusive, so "just inside his own half" over Cuciuffo at 35.2 is refused
although it is indeed his own half.

**Shawn's two tests, and two more.** "Álvarez, deep in his own half, hit a
long ball" is refused on 3869685, because his three records are at `x` 62.5,
63.2 and a pass down at 99.3. "Beat Butcher on the left" is refused on
3750191, because every record of Butcher's in the passage is England's and a
place is read off the attacking side's own location; "went past Butcher on
the left" is refused as the wrong side, which is the same sentence with the
reason Shawn meant. A half said with a name is a claim about the name too:
"just inside Argentina's half" is refused as the side in possession and
"Brazil's" as neither side.

**Step 4, `1e45340`: rule 17.** "Place the move on the pitch two or three
times: where it started, where the decisive action happened, and where it
finished. Do not give every beat a place." General to any goal, like rules 15
and 16, and no claim rule answers to it: a wrong place is refused whether or
not a rule asked for one.

**Two reporting gaps closed first, `c2ef0fd`,** because step 6 asks a run to
print what no run could. The places a candidate used, read with the same
grammar the check reads them with, so what is counted is what was verified.
And the refused attempts of a kept candidate: `gather` recorded `refused`
only on a candidate dropped altogether, so the one refusal of the Task 12 run
is on record as the number 2 and nothing else.

**Step 5, the run: all six slots, 66,242 tokens of the 70,000 allowed, and
it stopped on the cap.** Effort low, three candidates a slot, two retries
allowed, twenty calls and one IAM exchange. Eight of the sixteen candidates
it got to were kept, and the seventeenth was not sent.

| This run, all six slots | |
| --- | ---: |
| calls sent | 20 |
| billed by watsonx | 66,242 |
| of it prompt | 54,900 |
| of it completion | 11,342 |
| the cap | 70,000 |
| unspent | 3,758 |
| candidates kept | 8 of the 18 asked for |
| slots with something in them | 6 of 6 |

**The run overwrote the six candidates it was told to keep.** The review file
is named for the day and both runs are on 2026-11-05, and `merged` carries
across only the slots a run did not produce: this run produced all six, so
all six were replaced. They are not recoverable, and nothing in the repo ever
held them. The precedent for keeping them is in the same directory:
`hero_candidates_2026-10-30.before-task8.json`, copied aside by hand before
an earlier overwrite. **Copy the review file aside before any rerun**, which
is the first thing the next run should do and is not built.

**Rule 17 reached one candidate of the six slots.** The 2022 Storyteller
places the move three times ("deep in his own half", "on the right", "on the
edge of the box"), which is exactly what the rule asks for. Four of the other
seven place it once, both 1986 Buddy candidates place it not at all, and no
candidate anywhere said where the long ball was struck from: all four 2022
tellings place it where it came down. The vocabulary works and the asking is
what is weak, which is the finding to read the eight aloud against.

**What the near-copy filter did: seven of the sixteen.** Six on the words, at
0.96, 0.94, 0.94, 0.87, 0.86 and 0.85, and one on the shape. The 1986
`buddy_conceded` slot wrote one telling three times, and two of its three
went; the 2022 `buddy_conceded` slot did the same. One candidate was dropped
on three refusals.

**Five refused attempts, and three of them are new evidence.** Two belong to
kept candidates and would not have been recorded before this task. The model
is wrong in the same three ways each time: "Peter Reid" after "past" when
Reid pressed and was never dribbled past, "pressed" attributed to Maradona
when `Pressure` is the presser's record, and "first time" on the 1986 shot,
which is not recorded first time. The third one cost a whole candidate: the
1986 `buddy_scored` slot was refused three times and twice for that.

**"We won it back through Cuciuffo in half" is kept and reads wrong aloud.**
A word is missing from "in our half" and nothing refused it, because "in
half" is not a phrase the check reads: "own half" is. It is the only kept
candidate with a dropped word in it and it is the 1986 `buddy_scored` slot's
only candidate, so the slot is one telling with a hole in it.

**A gap the beats carry: the recovery line cannot be said back.** The beat
reads "Cuciuffo won the ball back", and a narration saying that is refused
twice over: "won" claims a `Foul Won` and Cuciuffo has none, and "back" is a
direction his records do not go. "Won it back" is the phrase the check holds,
and it is what the references say. Nothing was changed for it here.

**`Spot.in_the_box` is still `x >= 102` with no width.** The zone bands ask
for the box's width and that property does not, so it calls a ball at `x` 110
and `y` 10 inside the box and so does the position claim built on it. Every
recorded location from 102 up in both passages has `y` between 32.1 and 55.1,
so the two readings agree on all the real data; the difference is a hole in
the older one. Tightening it would move `in_the_box` on every beat and every
position claim, which no step asked for.

### Task 12: the hyphen, the Storyteller's full sentences and the two-slot rerun (done)

**Shawn asked for one small, last run after reading the four 2022 candidates
aloud**: the hyphen fix the earlier run's finding named, a rule keeping the
chain shorthand out of the Storyteller's text, and a rerun of `buddy_scored`
and `storyteller_neutral` only. The 2022 `buddy_conceded` candidate and all
three 1986 slots were to be kept as they are, and they were: this run asked
for nothing from them and `merged` carried them across.

**The hyphen, `6cf8fde`: it reads as the space it stands in for.** Three of
the four kept candidates of the earlier run wrote "first-time" or
"left-foot", `PHRASES` held both phrases as two words, and neither was read
as a claim. Nothing false passed, because the record is `first_time` and
`Left Foot`, so the words were true and the check did not look; the two
Storyteller candidates said the foot that way and no other, so a line the app
would label carried an unchecked body part. `hyphens_allowed` puts a hyphen
beside the space in every phrase pattern and every chain marker, so
"under-pressure", "long-ball", "one-touch" and "set-up" read as the claims
they are and "left-footed" reads as the foot. The spelling changes what is
read and never what the records hold: the same words over the 1986 shot are
still refused, and that Storyteller candidate now passes on 17 claims rather
than 15.

**The Storyteller's own idiom, same commit: no pass written as "X to Y".**
Rule 11 for that voice asks for full sentences and a verb in every pass, and
says why: the shorthand is the Buddy's idiom and the Caller's. The references
settled it before the rule did, which is the test: neither Storyteller
reference has a bare chain in it, and both 2022 Buddy references open "Molina
to MacAllister, MacAllister to Messi". Both Storyteller candidates of the
earlier run were a list of passes with three bare chains each. Rule 8 is
unchanged and still offers "X to Y" among the forms a pass may be written as;
this is the one voice that gives it up, and the Caller's style still asks for
the shortest chains.

**The run: two slots, 21,470 tokens of the 30,000 allowed**, over seven calls
and one IAM exchange. 8,530 unspent. Three of the six candidates were kept.

| This run, 2022 `buddy_scored` and `storyteller_neutral` | |
| --- | ---: |
| calls sent | 7 |
| billed by watsonx | 21,470 |
| of it prompt | 17,572 |
| of it completion | 3,898 |
| the cap | 30,000 |
| unspent | 8,530 |
| candidates kept | 3 of 6 |

**The Storyteller rule took.** Its one kept candidate writes every pass with
a verb in it: "Molina passed forward to MacAllister, who found Messi, who
gave it to Álvarez; Álvarez sent a long ball forward to MacAllister, who set
up Di María". No bare chain anywhere in the slot, in the kept candidate or in
the two dropped as near copies, against three in each candidate of the run
before it.

**The hyphen fix is in the claim counts.** The `buddy_scored` candidate that
came back on its second attempt is grounded on 21 claims, which is the most
any 2022 candidate has reached; the earlier run's best was 18. Nothing was
asked of the model to get there: the words it already liked are now read.

**Three of the six went on the near-copy filter**, at 0.93, 0.93 and 0.86,
and `storyteller_neutral` is down to one candidate because of it. That is the
filter working on a slot where the model wrote one telling three times, and
it is also the reason this slot has one rather than three: the shape of the
2022 move is five passes and a finish, and there is less to vary in it than
in the 1986 run.

**One refusal happened and the document does not say what it was.** The
`buddy_scored` candidate 2 is recorded with `attempt` 2 and
`first_attempt_grounded` false, so its first attempt was refused, and the
words and the reason are kept only for a candidate that was dropped
altogether. `gather` records `refused` on a drop and not on a retry that
later passed. It is a reporting gap rather than a check gap, and the fix is
to record the refused attempts of a kept candidate beside the kept text.
Nothing was changed for it here.

### Task 11, the second list: who "under pressure" is about, the beats as phrases, two rules and the near copies (done)

**Shawn read the ten candidates of the first Task 11 rerun aloud and wrote a
second list of steps under the same number.** The task before it is recorded
above; this is the one that followed it on 2026-11-05, and the film is set in
2022, so the Di María narration is the one the video plays and the three 2022
slots are the ones this rerun spent anything on.

**Step 1, `b0d4d2c`: "under pressure" belongs to the player on the ball.**
`support` was never the problem and neither was the pressure record: the
actor was. StatsBomb puts `under_pressure` on the record of the player being
pressed and a `Pressure` on the record of the player pressing him, so reading
the actor off the words landed the claim on Beardsley and asked his own
record for Maradona's flag. The claim is the carrier's now, whoever is named
beside it, and "under pressure from X" is a second claim of its own: X has a
`Pressure` in the buildup. Both have to hold, so the refused narration of the
earlier run passes on twenty claims and "under pressure from Fenwick", who
was dribbled past and pressed nobody, is refused with `'under pressure from
Fenwick': the records hold no pressure by Terry Fenwick in this passage`.

A comma ends the list of pressers, which is the same bluntness `CLAUSE_BREAK`
buys everywhere else and the same price: "under pressure from Beardsley, Reid
and Butcher" checks Beardsley and reads the other two as names. It is a
leniency rather than a false refusal, and it is what keeps "under pressure
from Beardsley, Maradona dribbled past Butcher" from making Maradona a
presser.

**Step 2, `8c1c437`: a beat is a phrase a narrator can say.** The beat read
"Julián Álvarez (Argentina) passed to Alexis MacAllister, long, forward",
with the recorded fields labelled after the name, and four of the five 2022
candidates wrote "Álvarez to MacAllister forward": the label read out loud.
Every beat is one clause now, computed from the same fields. The direction
sits inside the verb phrase, a pass at `LONG_PASS_YARDS` is "a long ball
forward to X", a pass reaching a player who has already received one says
"again", and the finish says first time and names the foot.

**The 2022 beat list, from `scripts/story_beats_report.py`: 13 records to 6
beats.**

```
  - Nahuel Molina (Argentina) passed it forward to Alexis MacAllister
  - Alexis MacAllister (Argentina) passed it forward to Lionel Messi
  - Lionel Messi (Argentina) passed it forward to Julián Álvarez
  - Julián Álvarez (Argentina) hit a long ball forward to Alexis
    MacAllister again
  - Alexis MacAllister (Argentina) passed it forward to Ángel Di María,
    into the box, which is the assist
  - Ángel Di María (Argentina) shot first time with his left foot from
    inside the box
```

**"Into the box" goes after the recipient and not before him**, because the
box is where the ball arrived and he is the player who was in it. MacAllister
played the assist from four yards outside, so "MacAllister passed it into the
box" is a claim about MacAllister's own position, which `player_spots`
refuses and should. A narration told in the beats' own order is grounded on
twenty claims and the same narration with the box moved in front of the
recipient is refused, which is a test.

**Step 3, `72103d7`: rules 15 and 16.** "When a pass is marked long, it is
the turn of the move; give it its own clause." and "When the finish is first
time, say so, with the foot." Both are general to any goal and neither is a
claim rule: the check holds "a long ball" and "first time" to the records
already and nothing refuses a telling that leaves them out. The earlier run
left both out of all ten.

**Step 4, `61b19cd`: a near copy is caught in the words as well as the
shape.** `play_shape` asks whether two tellings make the same moves in the
same order, and it kept two pairs that read the same aloud: "We passed from
Molina to MacAllister" and "We went from Molina to MacAllister" differ in one
word and come out with different shapes, because "passed" is a claim the
grammar reads and "went" is not. So the words are compared too, with every
player name folded to one token, the punctuation gone and the accents folded,
and `difflib`'s ratio over what is left. At 0.8 or higher the later candidate
is dropped.

| Pair, from the earlier run | Ratio |
| -------------------------- | ----: |
| 2022 `buddy_scored` 2 and 3 | 0.971 |
| 2022 `storyteller_neutral` 1 and 2 | 0.912 |
| 1986 `buddy_scored` 1 and 3 | 0.925 |
| 1986 `buddy_conceded` 1 and 3 | 0.867 |
| 1986 `buddy_conceded` 1 and `buddy_scored` 1 | 0.619 |

**Words and not characters, `autojunk` off.** Compared character by
character with the default, `SequenceMatcher` treats any character appearing
in more than one per cent of a sequence over 200 long as junk, which over a
250 character narration is the space and most of the alphabet: two 1986
candidates opening on the same clause scored 0.084 that way.

**Every same-slot pair of 1986 candidates in the document is a near copy at
this threshold**, which is why the pair this is tested against comes from two
different slots. The 1986 slots were not rerun and nothing was dropped from
them: a filter decides what a run keeps and does not reach back into a
document. If 1986 is ever rerun, two of its three slots come back with one
candidate rather than two.

**Step 5, the run: the three 2022 slots, 34,353 tokens of the 45,000
allowed.** Effort low, three candidates a slot, two retries allowed, eleven
calls and one IAM exchange. Four of the nine candidates were kept and 10,647
of the cap is unspent.

| This run, the three 2022 slots | |
| --- | ---: |
| calls sent | 11 |
| billed by watsonx | 34,353 |
| of it prompt | 29,832 |
| of it completion | 4,521 |
| the cap | 45,000 |
| unspent | 10,647 |
| candidates kept | 4 of 9 |
| slots with something in them | 3 of 3 |

The earlier rerun asked the same three slots for the same nine candidates
with no retries, sent nine calls and kept five, and its billed total is only
recorded for all six of its slots together (51,496), so the two runs' token
figures are not comparable and no comparison is printed here.

**2022 `buddy_conceded` has a candidate for the first time in three runs.**
It was empty on both of the earlier runs, and the two it dropped here were
dropped as near copies of the one it kept rather than as refusals.

**Every candidate of this run says the long ball and says first time**,
which is what rules 15 and 16 were for, and none of the four carries a
standalone "forward" after a name, which is what step 2 was for. "Álvarez
sent a long ball to MacAllister" is in all four.

**Five of the nine went on the near-copy filter and one on three refusals.**
The four near copies scored 0.97, 0.91, 0.85 and 0.83. The refusals are the
model being wrong and the check working: "Brilliant!" as an editorial
epithet, Álvarez's 36 yard ball up the pitch called a ball "back" twice, and
"We surged from our half" over a Molina who has no carry in the passage.

**The finding of this run: a hyphen gets a claim past the reading.** Three of
the four kept candidates say "first-time" or "left-foot" with a hyphen, and
`PHRASES` holds "first time" and "left foot" as two words, so neither is read
as a claim and neither is checked. Nothing false passed: the record is
`first_time` and `Left Foot`, so the words are true and the data agrees with
them. But the check did not verify them, and the storyteller candidates say
the foot that way and no other, so their body part is unchecked prose over a
line the app would label. The fix is the hyphenated spelling beside the
spaced one in `PHRASES`, which is a change to `app/narration_grammar.py` and
one test, and nothing was changed for it here.
