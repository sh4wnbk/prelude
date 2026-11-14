# Tasks 7 to 10, Bob's sessions, and what they settled

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

The candidate runs that later runs replaced, every Bob session from task 7 to task 13 with the brief it was built to, and the decisions settled after tasks 4b, 6 and 6d.

---

### Task 10's run: the ten candidates the fixes replaced

**The first run of 2026-11-05 billed 76,542 of its 80,000 and stopped on the
cap** in the 2022 `buddy_scored` slot, with ten candidates over five slots.
Shawn read those ten aloud, and Task 11 is what the reading found: one hole in
the check and three things the pipeline was doing to the output. The
candidates themselves are gone from the review file, which the rerun
overwrote; what they showed is in the Task 11 record.

### Task 9d: the eighteen candidates the curation replaced

**Task 9d was run end to end at `reasoning_effort` high and nothing was
frozen.** The eighteen are in
`C:\Users\shawn\prelude-review\narrator_candidates_2026-10-31.md`. Shawn read
them aloud on 2026-10-31 and the finding is what Task 10 is: they echo the
fact list, because the prompt handed over every recorded event.

**What that run cost.** About 817,000 tokens in all, of which 311,081 is
counted off watsonx's own `usage` object and the rest is estimated at the
14,473 tokens a call the counted runs averaged. The counting was added part
way through, which is why two of the four runs are an estimate:

| Run | Calls | Tokens |
| --- | ----: | -----: |
| the probes that measured what high effort needs | 9 | 65,038 counted |
| six slots, lost to a read timeout after one slot | 5 | about 72,000 |
| six slots, 16 of 18 kept | 30 | about 434,000 |
| the two `buddy_scored` slots again | 11 | 154,821 counted |
| the 2022 `buddy_scored` slot again | 6 | 91,222 counted |

**High effort against low, now that both have been run on this prompt.** Task
9d's eighteen at high cost about 817,000 tokens; Task 10's run at low billed
76,542 for twenty-six calls and stopped on a cap. The tellings at high were
not better, which was the open question at the end of Task 9d, and the
curation in `app/story_beats.py` is what changed the tellings rather than the
effort.

### Task 8: the candidate run Task 9 replaced

**Task 8 is run, nothing is frozen, and the freeze is one command away.** The
candidates are in `C:\Users\shawn\prelude-review\hero_candidates_2026-10-30.md`,
with the same data beside it as JSON. Both goals were rerun, so both are this
run's. Shawn picks one per goal and then:

```
.\.venv-prelude\Scripts\python.exe -I scripts\freeze_narrations.py --pick 3750191=3 --pick 3869685=3 --confirm
```

That path calls no model: the words already exist, so it reads them out of the
candidates document, re-runs the grounding check against `data/raw/`, and
writes `app/web/narrations.json` with the model that wrote them and which
candidate it was. Without `--confirm` it prints the pick and writes nothing.
It refuses a slot that is not in the file, a goal picked twice, a goal that is
not a hero, and a pick that leaves one hero unpicked. **The 1986 slots have
gaps: they are 1, 3 and 4, because slots 2 and 5 were refused.**

**Eight candidates, not ten: 1986 came back three of five.** Both of the two
that failed did so the same way, and it is the citation rather than the
sentence. The hero block prints the Beardsley step as "Diego Armando
Maradona, from facts 10, 11, 12: dribbled past Peter Beardsley", and the model
wrote the sentence citing `[10]` alone. Fact 10 is "Peter Beardsley (England)
was dribbled past", which names Beardsley and not Maradona, so his name is in
the buildup and not in the facts that sentence cited, and the check refuses it
correctly. Five of the six failed attempts are that; the sixth wrote no
citation tags at all, which is the failure
`app/narration_prompt.py::build_prompt` already describes as the harder one.

**Whether the prompt invites it cannot be told from ten generations.** The
same shortened citation is what the Task 7 prompt fix was aimed at, and that
rerun came back five of five; this one came back three of five at the same
temperature 0.8. The only change to the 1986 prompt since is one name
("Héctor Enrique" rather than "Héctor Adolfo Enrique"), which is not in any
sentence that failed. So it is either sampling or a prompt that still allows
the short citation, and the honest answer is that this run cannot say which.
Asking for one fact number per sentence, or restating that a step's sentence
cites every number printed for it, is the next thing to try, and it is a
prompt change rather than a check change.

**The 2022 goal came back five of five, all five naming all five players.**
That is the thing the Task 6 narration was short on: it named three of five
and left out Messi and Álvarez, and every candidate here names Molina,
MacAllister, Messi, Álvarez and Di María in order. They differ only in the
closing phrase and in whether a receipt is said as "received the ball" or
"received", a spread of 87 characters and 204 billed.

**Every candidate is grounded, carries one clock, ends on a sentence saying it
scored, and covers every key beat.** 1986: five of five beats, seven of the
eight recorded players, Peter Reid the one unnamed, which is right because
Reid only pressed and no fact pairs him with anything else. 2022: one of one
beat, five of five players.

**No candidate carries an unusual character.** `odd_characters` reports none
across all eight, after two of the previous run's candidates carried one. That
is not evidence the problem is gone: `app/plain_characters.py` now rewrites a
disguised space or hyphen as the model's text arrives in `app/narration.py`,
so a character that did arrive was made plain before the review file measured
anything. The review file no longer distinguishes "the model wrote none" from
"the model wrote one and it was fixed", which is a reporting loss taken
knowingly: the fix is worth more than the report, and recording what was
rewritten is a change to `Attempt` that this task did not ask for.

**Every pair fits the budget, so the price is not the thing to choose on.**
`scripts/tts_hero.py --budget` is 3,000 billed characters for the six
recordings. The cheapest pair is 1986 slot 3 with 2022 slot 3 at 2,688, and
the most expensive is 1986 slot 4 with 2022 slot 4 at 2,934. All fifteen
pairs are under 3,000, with between 66 and 312 characters to spare. The 1986
narrations run 1,473 to 1,515 billed and the 2022 ones 1,215 to 1,419.

**The 1986 narration still says "Diego Armando Maradona" six times, and the
data is why.** Task 8 was asked for recorded common names, and
`data/raw/lineups/3750191.json` records no `player_nickname` for him: the
field is null. So there is nothing shorter to say that the data says, and
`app/recorded_names.py` does not pick a surname out of a full name, because
that would be this repo's judgement about what a player is called rather than
a value read from the match. What 1986 did gain is "Héctor Enrique" for
"Héctor Adolfo Enrique", which is the one nickname in that buildup.

The 2022 goal is where the change lands: "Lionel Messi" for "Lionel Andrés
Messi Cuccittini", "Ángel Di María" for "Ángel Fabián Di María Hernández",
"Nahuel Molina" for "Nahuel Molina Lucero", "Alexis MacAllister" for "Alexis
Mac Allister". Julián Álvarez has none recorded and so is said in full.

**Still owed then: the recordings.** They were made in Task 15, on 2026-11-07, of the six narrations the team wrote. What that task was waiting on at the time: The Text to Speech instance is
disabled above its Lite cap until November 1, so `scripts/tts_hero.py
--confirm` has not been sent and `hero.audio` is still `{}`. What to listen
for: a candidate that says "at 54:02" or "at 35:12" once still reads a colon
between two numbers aloud, which nothing here knows the sound of, and `di` in
"Di María" is still unheard.

**The vocabulary sweep has nothing to review after the pick, and that was
measured rather than assumed.** `scripts/check_vocabulary.py` reads the frozen
narrations, so a freeze changes the words it sweeps: "MacAllister" is a word
no narration has held before, and the full names that go ("Fabián",
"Hernández", "Cuccittini") take their words with them. Run with every one of
the eight candidates standing in for the frozen pair, the gate's own flagging
reports no unreviewed word either way, because a name has to carry two listed
CMU pronunciations to be flagged at all and none of these does. `di` is
already in the table, from the Task 6 narration.

### Task 7: the candidate run Task 8 replaced

**Task 7's candidates no longer exist.** Task 8 reran both goals, into the
same candidates document, so what the file holds is Task 8's eight and not
these. The reason for the rerun is in Task 8's record above: the names. What
is kept here is what the run measured, because the prompt fixes and the
prices it found are still true.

**Nothing was frozen then either**, and the freeze path is unchanged: it
reads a candidate out of the document, re-checks it against `data/raw/`, and
writes `app/web/narrations.json`. It refuses a slot that is not in the file,
a goal picked twice, a goal that is not a hero, and a pick that leaves one
hero unpicked, because freezing one of the two would leave one moment card
speaking a narration chosen on the evidence and the other speaking one chosen
before it. The slot numbers are the asked-for slots and have gaps.

**The 1986 goal was rerun with the fixed prompt and a length target, and it
went from two usable candidates to five.** Every one of the five is grounded,
eight sentences, one clock, ends on a sentence saying it scored, names seven of
the eight recorded players (all three who touched the ball, and the four
defenders beaten; Reid only pressed and no candidate names him, which is
right), and covers five of five key beats. None was dropped for its price.
`--match 3750191 --alongside 3869685=4` spent 12 generations of the 15 it was
allowed, plus one IAM exchange.

**They are five slots but two narrations.** Slots 1, 2 and 3 are one text of
447 characters at 1,458 billed, ending "Diego Armando Maradona shot and
scored". Slots 4 and 5 are one text of 466 characters at 1,503 billed, ending
"shot with his left foot and scored", which reaches the body part the earlier
1986 candidate never did. The length target is what converged them: asked for
about 450 characters, the model wrote the same telling over and over.

**Slot 5 carried a `NARROW NO-BREAK SPACE` (U+202F) inside "Terry Butcher",
which made slot 4 the one to pick of that pair.** It was the second invisible
character a candidate has arrived with, after the `NON-BREAKING HYPHEN` in the
run before it, and both passed `app/grounding.py` correctly: a narrow space is
whitespace, so the name either side of it still matched, and a hyphen is not a
name, an action, a clock or a number. `odd_characters` in
`scripts/hero_candidates.py` now reports any character that is neither plain
ASCII nor a letter, so the review file names them. It reports rather than
refuses: what may be labelled is `app/grounding.py`'s to say, and extending
its rules is a decision rather than a fix.

**The length target is 450 characters, and it is a price rather than a style.**
`HERO_TARGET_CHARACTERS` in `app/narration_prompt.py`, stated in the hero
prompt in characters and in words, with the reasoning on the constant: the
usable 1986 candidate before it came to 459 characters and 1,491 billed, and
the one that spelled every clock out in words came to 988 and 4,299, more than
the whole run may spend. `scripts/hero_candidates.py` is what enforces a
price, by dropping a grounded candidate whose recordings would not fit, since
nothing in a prompt can make a model count.

**What a pair now costs, and what it leaves for 2022.** The cheaper 1986 text
at 1,458 billed leaves 1,542 of the 3,000 budget for the other goal; the one
naming the left foot at 1,503 leaves 1,497. Both are comfortable: the five
2022 candidates of the first run came to between 1,488 and 1,605, so a 2022
rerun has room, though not unlimited room. Of those five, three fitted beside
the cheaper 1986 text and two fitted beside the longer one. That arithmetic is
a guide to what a rerun should aim at rather than a live option, because those
candidates no longer exist: see the mistake below.

**One mistake, and it cost the 2022 candidates.** The candidates document is
named by the day, and the 1986 rerun wrote that filename again, so the file
went from holding both goals to holding 1986 alone. The five 2022 candidates
in it are gone, and with them their `tagged_text`, which is the only copy of
the citations the model wrote and what a freeze re-reads before committing
anything. Their plain text survives in this file's history and in the session
report; the citations do not, and writing them by hand would make them this
repo's rather than the model's. So **freezing a 2022 narration now needs the
2022 goal rerun**, which is 15 generations, and the Task 6 narration it would
replace is still what `app/web/narrations.json` holds, so nothing is broken
while that waits.

`merged` in `scripts/hero_candidates.py` is why it cannot happen again: a
rerun carries across every goal it did not narrate, keeping that goal's own
provenance, and `tests/test_hero_candidates.py::TestMergingARerunIntoTheDocument`
holds it. A rerun of 2022 would therefore leave the 1986 five in place.

**`scripts/hero_candidates.py --refresh` remeasures without calling a model.**
The report has gained two columns since the first run (the narration's length,
and the unusual characters), and a review file written before a measurement
existed cannot be read against it. Refresh recomputes the price, the coverage
and the check from `data/raw/` for every candidate already written, and
refuses to rewrite the file if any of them has stopped passing.

**The 1986 run found a real prompt problem, and it is fixed.** Three of the
five slots in the first run failed all three attempts the same way: the model
wrote one sentence per defender in the form "Peter Beardsley was dribbled past
and Diego Armando Maradona carried the ball", and the check refuses it,
correctly, because no cited fact records a `Carry` involving Beardsley and
rule 4 asks for one action a line. The hero block was what invited it: a step
for the scorer printed as "dribbled, carried the ball" beside a beat naming
Beardsley. It now prints as "dribbled past Peter Beardsley", citing all three
facts, and a note under the step list says a dribble step is one sentence. The
rerun's five for five is that fix measured.

**The clock rule is fixed too.** It said no digits besides the one clock, and
one candidate obeyed by spelling every clock out in words instead: "at minute
fifty-four seconds two" on each of twelve sentences. Nothing in
`app/grounding.py` objects, since a clock in words carries no digits and makes
no number claim, so it passed, cost 4,299 billed, and carried the non-breaking
hyphen. The rule now says the clock is written as the fact writes it, digits
and colon, with that fact's own clock as the example, and refuses the time in
words anywhere. `app/grounding.py` is unchanged by either fix.

**The run cost 23 generations of the 30 allowed on the first run and 12 of 15
on the rerun**, plus one IAM exchange each: `openai/gpt-oss-120b` through the
chat endpoint at `reasoning_effort` low, decoding pinned to temperature 0.8,
top_p 0.9, top_k 40. The decoding is pinned because watsonx decodes greedily
unset, and five greedy candidates are one candidate five times.

**Still owed then: the recordings.** They were made in Task 15, on 2026-11-07, of the six narrations the team wrote. What that task was waiting on at the time: The Text to Speech instance is
disabled above its Lite cap until November 1, so `scripts/tts_hero.py
--confirm` has not been sent and `hero.audio` is still `{}`. What to listen
for: a candidate that says "at 54:02" once still reads a colon between two
numbers aloud, which nothing here knows the sound of, and `di` in "Di Maria"
is still unheard.

**Task 7's brief, and the state it started from.**

**Bob task 13 is built and checked.** `4e61a10` renamed the id to `buddy` in
every live file; both written files pass `--check`, and the follow-up updated
the docs that cited the test names it renamed. `pytest -q` reports
`718 passed` and all five gates pass. It cost 21.07 Bobcoins, five times a
typical task, because a rename across 18 files is mostly reading: broad
mechanical edits are expensive for Bob, small targeted ones are cheap.

**The frozen narrations are grounded but not ready to record.** Read as audio,
the 2022 one names 4 of the 13 recorded events and leaves out Messi and
Álvarez; neither one says the shot scored; every sentence carries a clock; and
the 1986 one does not name Maradona until the last line. All four are prompt
choices, not grounding limits, and they are cheap to fix on watsonx before the
voice is spent. Task 7, briefed to Claude Code, asks for five grounded
candidates per goal with those fixed, for Shawn to choose from.

### Before Task 7: Bob task 13

**Bob task 13 in `docs/bob_brief.md` renames the persona id from `mate` to
`buddy`**, Shawn's call on 2026-10-30, made before the hero recordings exist
because their filenames are built from the id. Live code, data and tests
change; the past does not: `scripts/narration_eval.py`, `docs/narration_eval.md`,
this file's history and `bob_sessions/` keep "Mate" for the runs made under that
name. The docs that describe the current state are the follow-up's.
While it was briefed, every failure was in `tests/test_buddy_rename.py`.

**The rename comes first, and the recordings after it.** `scripts/tts_hero.py`
names each file `<match_id>_<key>.mp3` from `hero.voice_for`, so the six
recordings are `mate_scored` and `mate_conceded` today and `buddy_scored` and
`buddy_conceded` once Task 13 lands. Recording before the rename would mean
paying for the audio twice or renaming files the map is written from, and the
Lite allowance is monthly.

**Claude Code Task 6 is done and the words are settled.** The narrations are
the model's, frozen in `app/web/narrations.json`, shown on the moment card and
read by `scripts/tts_hero.py`. See "Phase 5, task 6" above for the run, both
texts and the new price. The rename does not touch them: a narration is one
text for every voice, and the id appears nowhere in it.

**Then one command, and it cannot run before November 1.** The Text to Speech
instance is disabled above its Lite cap until the month turns:

```
.\.venv-prelude\Scripts\python.exe -I scripts\tts_hero.py --confirm
```

It costs 1,959 billed characters against a `--budget` of 2,000. Then commit
the six MP3s and the `hero.audio` map, drive all three listeners on both
matches to see the timer and the waveform move, and hand Shawn the file table
in "Phase 5, task 5", with its keys renamed.

**What to listen for has changed.** `minute` is no longer in either recording,
because the model wrote clocks rather than "Minute 54". The two new things are
`di` in "Di María", which has an entry nobody has heard, and the clock values
themselves: the narrations say "at 54:08" and "at 35:22", and nothing here
knows how a Natural voice reads a colon between two numbers. No gate can flag
that, because a digit is not a word.

### Before Task 13

**Bob task 12 is built and checked.** `35c91b6` made the four changes in the
brief. In Chromium, Profile marked The Buddy for an England fan and The
Storyteller for a neutral listener, showed the coming-soon note on tapping The
Caller, and showed Change as an outline under the amber current card. Its
export is committed in `d0837ac`.

### Before Task 12

**The 403 is explained: the Text to Speech instance is disabled above its Lite
cap.** Shawn read it in IBM Cloud on 2026-10-30: "Inactive. Instance disabled
with reason_code IBMCLOUD_SERVICE_INSTANCE_ABOVE_CAP", plan Lite. It comes back
with the new month.

**Decisions on 2026-10-30, Shawn's.** What judges hear is recorded, never live:
the Text to Speech cap is 10,000 characters a month on a shared instance, and
live voice would let judges exhaust it. The recordings will speak a narration
written once by gpt-oss-120b and frozen after passing the grounding check, not
the template (Phase 5, Task 6, to be run by Claude Code). In production the
narration and voice move onto the phone (an on-device model and the phone's
own speech, with the same grounding check and fallback), which is vision, not
built. A "fresh telling" button that rewrites the narration on screen is a
stretch idea, with the bird's-eye view.

**Bob task 12 in `docs/bob_brief.md` puts "Your narrator" on Profile.** The
three narrators are shown with the one the fan's answer picked marked, tapping
another says it is coming soon, the partisan persona is shown as "The Buddy"
(its id stays `mate`), and Change becomes an outline so it does not compete
with the amber current card. A dry run of the brief passed every test then
collected and, in Chromium, marked The Buddy for an England fan and The
Storyteller for a neutral one and showed the note on tapping The Caller; it
was reverted.

While it was briefed, every failure was in `tests/test_narrators.py`.

### The hero recordings, once the service answers

**The six recordings are not generated: Watson Text to Speech answered HTTP
403 to every request on 2026-10-30.** Everything around them is built, the
words and the price are known, and `hero.audio` in `app/web/matches.json` is
still `{}`, so the moment card's play button stays disabled for all three
listeners. See "Phase 5, task 5" below for the run, the evidence and what is
owed.

**Shawn: check the Text to Speech instance in IBM Cloud.** Nothing in this
repo can read the usage counter, and the 403 body carries no reason, so
whether this is the Lite plan's monthly characters, a disabled key or a
deleted instance is a question for the console. The credentials file is
intact: `app/credentials.py` reports `C:\Users\shawn\.prelude\.env defines
TTS_API_KEY, TTS_URL, TTS_VOICE, WATSONX_API_KEY, WATSONX_PROJECT_ID,
WATSONX_URL`, by name and no value. Once it answers, the whole of task 5 is
one command:

```
.\.venv-prelude\Scripts\python.exe -I scripts\tts_hero.py --confirm
```

**Bob task 11 is built, checked and fixed.** `35708cd` built the player to the
brief, but in Chromium with a silent test file under one key the play button
stayed disabled for every listener: the player read `Prelude.whenMatches`'s
argument as the list of matches when it is the document. The follow-up reads
`doc.matches`, returns on a failed fetch, and adds a test that fails on the
original. Rechecked: the Argentina fan's key played, paused, advanced the
timer and waveform and replayed; the two keys with no file stayed disabled.
`pytest -q` reports `675 passed` and all five gates pass. Nothing more can be
heard until the recordings exist, after the November 1 TTS reset.

### Bob task 11, as it was briefed

**Bob task 11 in `docs/bob_brief.md` wires the moment card's player to real
audio.** Which recording a fan hears is decided in Python by
`scripts/write_headers.py`, from `default_persona` and `situation`, and
written as `hero.voice_for`; the browser looks its answer up in `hero.audio`,
which stays empty until the hero recordings are generated after the
November 1 TTS reset, so until then the play button is disabled. A dry run of
the brief passed every test then collected and, in Chromium with a silent test file under
one key, played and paused, advanced the timer and the waveform, replayed, and
left the button disabled for the two keys with no file; it was reverted.

The dry run also found that a player loaded in the `<head>` sees no buttons, so the brief
requires the `DOMContentLoaded` start that `match-content.js` uses.

`pytest -q` reports `13 failed, 661 passed`. Every failure is in
`tests/test_narration_player.py`.

### Before Task 11: Task 7 is done

**Bob task 10 is built and checked, and with it the Task 7 work.** `4ef3aa0`
built the Profile screen to the brief. Driven in Chromium it showed "Shawn |
Argentina", Change reopened the card on Live with Argentina pressed and the
name filled, the new answer held without reopening on reload, and Profile then
showed "Olivia | Just here for the game". Two corrections: `asked()` matched
"ask" anywhere in the query, and now reads `ask=1` as a parameter; and the
screen carried its own Tailwind config instead of the shared one, with a dark
`primary-container`, so its amber looked disabled on Shawn's phone. The shared
head is restored and a test now holds every screen to one config. `pytest -q`
reports `501 passed` and all four gates pass. Change was then given the
Heading out treatment, `text-on-primary` with `shadow-lg
shadow-primary-container/20`, Shawn's pick for consistency with the app's main
actions over an outline. The Task 7 plan's persona cards
on Profile move to Phase 5, once there are voices to pick.

### Bob task 10, as it was briefed

**Shawn found the answer could not be changed.** It lasts the tab's session and
a refresh keeps it, so a fan who typed a name was stuck with it. Bob task 10 in
`docs/bob_brief.md` adds a Profile screen with the name, the side for the
match and a Change button that reopens the card on Live, and makes the person
icon and the Profile tab lead to it. The persona cards wait for Phase 5, when
there are voices to choose. A dry run of the brief, driven in Chromium, showed
"Shawn | Argentina", reopened the card with Argentina pressed and the name
filled, saved the new answer without reopening on reload, and showed "Olivia |
Just here for the game"; it was reverted. `pytest -q` reports
`24 failed, 476 passed`, all of them `tests/test_profile.py`. Bob's task 9
export is committed.

### Bob task 9, its follow-up

**Bob task 9 is built, checked and corrected.** `c6fc1ad` built the card to
the brief, and in headless Chromium at 390 wide it asked "Who are you with
tonight?" on both matches, kept Continue disabled until a choice, stored the
answer and the trimmed name in `sessionStorage`, did not reappear on reload,
and gave "...Here's how it happened, Olivia." on the moment card. The same
run caught one bug: a name holding `$&` came out mangled, because it was passed
to `replace()` as the replacement. The follow-up fixed it and added a test that
fails on Bob's version, and swapped four classes the app did not already use
for its own tokens. `pytest -q` reports `476 passed` and all four gates pass.
Once the Tailwind and font hosts were allowed for this workspace, a styled run
at 390 wide showed two problems with the choices, both fixed: the selected
choice set light text on amber and was hard to read, and the unselected choices
had the card's own background, so they read as plain text rather than buttons.
Selected now uses `text-on-primary-container`, as Continue does, and unselected
sits on `bg-surface-container-highest`. Two older wraps on the Live screen are
cosmetic and not changed: "AT VENUE · GPS" breaks inside its pill, and the seat
line leaves "6" alone on its second line for 2022.

### Bob task 9, as it was briefed

**Bob task 9 in `docs/bob_brief.md` is briefed.** The card asks, once per match
on the Live screen, who the fan is with and what to call them; both answers stay
in `sessionStorage`. The name goes on the header's last sentence ("...Here's
how it happened, Olivia."), Shawn's call on 2026-10-29. The Live badge stops
wrapping, the one cosmetic finding from the visual check at `c0568a8`, which
otherwise passed on both matches, locally and live, at 390 and 1280 wide.
`pytest -q` reports `15 failed, 460 passed`, all of them
`tests/test_listener_card.py`. After Bob: a browser check of the card's
behaviour, then the Profile tab.

### Before Task 9

**Bob task 8 is built and checked.** `30116a2` changed exactly the five values
in the brief. `pytest -q` reports `459 passed`, all four gates pass, and
`scripts/check_match_copy.py` now holds every match to one missed goal. Its
export is committed and was scanned for key-shaped strings, with none found.

### Bob task 8, as it was briefed

**Shawn found that the 1986 step-away missed two goals.** The fan left at 48'
at 0 to 0 and came back at 55' to 2 to 0, with goals at 50:27 and 54:18 in the
window and one buildup on the card. 2022 was already one goal. His decision on
2026-10-29: the 1986 fan leaves at 52' at 1 to 0. `scripts/check_match_copy.py`
now refuses any window that holds more or fewer than one goal, so the rule
outlives this fix, and it fails on 1986 until Bob's Task 8 in
`docs/bob_brief.md` landed, with 6 failures in `tests/test_live_before.py`
while it was briefed.

A moment card that tells several missed goals in order is a planned feature,
not built: real fans can miss more than one, and that card would play each
buildup with its own header.

### Before Task 8: Bob task 7

**Bob task 7 is built and checked.** `8215108` touched only
`app/web/matches.json` and the moment card, made the six changes in the brief
and reran `scripts/write_headers.py` (`--check` passes). `pytest -q` reports
`452 passed` and all four gates pass. Its export was committed in `76e0d15`
and scanned for key-shaped strings, with none found.

**Checked in headless Chromium on both matches, at 390 by 844 and 1280 by
800, after the commit.** The rendered header is each match's line ending
"Here's how it happened.", the share button carries "Maradona's solo goal as
it happened." and "Di María's counter goal as it happened.", "STEPPED AWAY"
appears nowhere on the card, and the Live screen shows "Ready when you are."
after Heading out and the settled helper before it. That run had no network,
so the Tailwind and font CDNs did not load and the layout was not judged:
the look still needs a real-phone check on the live site.

**Next:** Shawn checks the moment card on his phone, then the "Who are you
with" card and the name get briefed for Bob.

### Bob task 7, as it was briefed

**Bob task 6 is built and checked.** `aab7093` added
`scripts/write_headers.py`, which runs the orchestrator over the data and
writes `hero.opening` into `app/web/matches.json`, and the moment card's
heading now shows it. Its diff touched only the three files the brief allowed
plus the script's output, the script holds no header text of its own, and
`--check` passed. Its session export was committed in `95341d1` and scanned
for key-shaped strings, with none found.

**Task 7 is split into Bob tasks, and the second is briefed.** Bob builds in
tight sessions; this chat writes each brief with failing tests and checks his
commit; Claude Code does the real-browser check and the larger doc updates. Bob
task 7 in `docs/bob_brief.md` is the copy Shawn settled on 2026-10-29: the
"YOU STEPPED AWAY" label removed, "Ready when you are." after Heading out,
"Listen on Prelude." as the share title, "...as it happened." share texts, and
the header ending "Here's how it happened." The tail is already changed in
`app/orchestrator_contract.py` and the tests, so Bob reruns the script. After
it: the "Who are you with" card and the name, then the Profile tab.

**The suite was red on purpose while it was briefed**, with 13 failures, all
of them Bob's Task 7.

**Fixed while briefing it:** the kickoff comments in
`tests/test_orchestrator.py` called 16:00 and 18:00 the real kickoffs. They now
say the times are chosen for the rule, and that the match index records 19:00
and 17:00. The stale `_note` in `app/web/matches.json` is item 6 of Bob's
task.

**Still owed to Claude Code:** commit Bob's task 7 export once Shawn has
saved it, take it off `DELIBERATELY_ABSENT`, and check the moment card and
the Live screen in a real browser on both matches at 390px and on desktop. The three things to hold on to through all of Task 7:

- **The header does not change by listener.** One moment gives one line to a
  fan of either side and to a listener with none. The "Who are you with"
  answer picks the persona through `default_persona`, and nothing else.
- **The name is added on the phone**, after the narration has been generated,
  and it is never sent to a model or a server.
- **No screen shows a header yet.** Task 7 is what puts it on the moment card,
  so `scripts/scan_copy.py` and `scripts/check_match_copy.py` both start
  caring about the header's copy at that point.

Three functions in `app/orchestrator.py` have no caller: `phase`,
`score_state` and `outcome`. They stay, and "Phase 4, the follow-up after Bob
task 5" under What was built says where they are and why removing them is a
later Bob task. Check whether Task 7 wants any of them before that is raised.

### Settled after task 6d

Three decisions, all Shawn's, all taken on the measured runs rather than on
an argument about prompts.

**The personas are separated by sound, not by text.** Three attempts at three
registers gave one register back each time: 0.6 words per sentence of spread
on `granite4:micro` with the register described, 2.1 on
`openai/gpt-oss-120b` described, 1.9 shown as a worked example. The narration
text is one style for every persona now, and each persona becomes an IBM voice
plus SSML prosody in Phase 5: rate, pitch, and breaks between sentences.

**Comprehension comes first.** The Caller's energy comes from emphasis and
pitch, with a rate only modestly above the Storyteller's and a ceiling on it.
Sentence breaks let each beat land, with a slightly longer break before the
goal sentence. Shawn sets the rates by ear in Phase 5, words per minute is
measured from the real audio, and the measured ceiling goes into config. The
Phase 5 entry in the Plan carries this.

**The header becomes game-focused.** It states what the goal did to the score,
not how the fan should feel. Allegiance no longer changes the header: it picks
the persona. Task 2 above is that change, and `docs/VOICE.md` carries the
wording.

### Settled earlier (Task 4b and Task 6)

**Task 4b is run and Task 6 is finished. Both decisions are Shawn's, and
Task 7 waits on them.**

**The model.** `openai/gpt-oss-120b` grounded 33 of 33 narrations on the first
attempt with no fallback, against `ibm/granite-4-h-small` at 16 of 54 with 23
fallbacks, and it costs fewer tokens per narration because it does not retry.
It is six tenths of a second slower a narration. `ACTIVE_CANDIDATE` in
`app/narration_config.py` is still Granite, and switching it is the one line
that file was written for. Nothing in the repo assumes either way.

**Two things to know before switching it.** The comparison ran on the chat
endpoint, so whatever ships has to pass `chat=True`, and
`openai/gpt-oss-120b` needs `reasoning_effort: low` or it spends about 1,500
tokens thinking before every narration.

**The personas.** The question Task 6c left open is answered and the answer is
no: on both paid models the three voices write the same narration. The Mate
reaches for the first person on the larger model, 9 of 12, and writes "Our
Peter Beardsley was dribbled past." The three options from Task 6c still
stand, with better evidence under them now: leave the personas as they are,
rewrite the styles and remeasure the same way, or ship fewer of them. A fourth
is open now that a model follows instructions this exactly: give each persona
its own worked example in the prompt rather than a description of a register,
since what reached this model was the rules and not the prose.

### Settled by Task 4b and Task 6 (the old next action)

**Task 6 is finished and Task 7 is next, after Shawn has read the Task 6c
numbers.** The three personas are built, wired into the prompt and the check,
and measured. What the measurement says is that on `granite4:micro` the three
voices are not separable: words per sentence is 4.9 to 5.5 across all of them,
and the Mate never once used the first person it is the only voice allowed.

**That is a decision for Shawn rather than a bug to fix.** Three options, and
nothing in the repo assumes one of them:

1. Leave it. The personas are a Phase 5 and Task 7 feature and the model that
   ships them is chosen in Task 4b, which is where this should be retested.
2. Make the styles harder for a small model to ignore, and remeasure the same
   three goals the same way so the before and after are comparable.
3. Drop to two personas, or to one, if the voices cannot be told apart on the
   model that ships.

**Task 4b now has a third arm worth running**, since the persona prompt is
the one that costs first-attempt grounding: one candidate with a persona and
one without, on the same goals, so the cost is measured on a model that might
not pay it.

**Bob's task 4 export is committed.** It was scanned first, as
`bob_sessions/README.md` requires, and nothing was scrubbed: no variable name
from `.env.example`, no token, no key-shaped string and no URL carrying a
query string.

Task 4b, the paid watsonx comparison, can run at any point and has one extra
arm recorded in the Plan: one candidate without the beats block, on the five
multi-beat goals only.

**Read `docs/narration_eval.md` first.** It is the measured state of the
narration, and it now holds two runs. Task 4a found grounding healthy on the
development model (22 of 27 first attempts) and completeness absent: all
fourteen model narrations on the goals where coverage can move cited the shot
and nothing else. Task 4c named the beats in the prompt and took coverage on
those goals from 42% to 95%, at a cost of two first attempts out of fifteen,
all of them on the 22:24 penalty. Any further prompt change should be measured
the same way rather than argued about.

The pass rate is worth re-measuring after any prompt change: `--goals` and
`--runs` make a one-goal check cheap, and the full twenty-seven takes about
fourteen minutes on CPU.

What is in place:

| What | Where |
| ---- | ----- |
| The contract | `app/event_feed.py`, shapes and protocol |
| The implementation | `app/statsbomb_event_feed.py`, class `StatsBombEventFeed` |
| The tests | `tests/test_event_feed.py`, 28 tests, all passing |
| The buildup tests | the 14 in `tests/test_event_feed.py::TestBuildup` |
| The brief it was built to | `docs/bob_brief.md` |

Run the suite with `.\.venv-prelude\Scripts\python.exe -m pytest`.

Settled while writing the narration copy:

- **Set-piece buildup needs the prior possession. Settled and built.**
  `buildup` is on `EventFeed` in `app/event_feed.py` and implemented in
  `app/statsbomb_event_feed.py`; `docs/bob_brief.md` carries the brief it was
  built to as Task 3. `event_window` was left alone, as its truncation rule is
  deliberate. Narration calls `buildup` for a set piece rather than widening
  the window.
- **"Verified from play data" is the whole point of the raw-record rule.** Every
  line that carries the label has to trace to an event in the window it was
  written from. A line that cannot be pointed at does not get the label, and
  there is no softened variant of the phrase.

The EventFeed and moment-detection module stays reserved for IBM Bob. It is
built, but `CLAUDE.md` still governs it: further work on moment detection is
Bob's, and Phase 4 should call the module rather than reach around it.

**Session exports go in `bob_sessions/`,** one per task, committed rather than
ignored, and scrubbed of credentials before each commit. See
`bob_sessions/README.md` and `.bobignore`.

**Before starting:** run `scripts/fetch_statsbomb.py`, since `data/raw/` is
gitignored and absent from a fresh clone.

### Settled during the Phase 2 review

- **2022 defining moments are periods 1 to 4 only.** A shootout has no buildup
  to narrate, so excluding it is the right default.
- **`Moment` carries no period field.** Accepted as it stands. Bob can add one
  later, with the tests, if the module needs it.
