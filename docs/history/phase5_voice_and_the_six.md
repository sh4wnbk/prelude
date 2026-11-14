# Phase 5: the voice, the audio and the six narrations

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

Every Phase 5 record, from the Text to Speech facts through the probe, the pronunciation table, the refused hero run and the freeze.

---

### Phase 5: the Watson Text to Speech facts

Recorded here because Task 3 built no audio code and these are not in the
repo. They came from Shawn, not from the credentials file, which nothing here
opens.

| What | Value |
| ---- | ----- |
| Service | IBM Watson Text to Speech |
| Instance | the Dallas instance in the team's IBM Cloud account |
| `TTS_URL` | that instance's service URL |
| `TTS_VOICE` | an IBM voice name |
| Working default | `en-GB_GeorgeExpressive` |
| Alternative | `en-GB_GeorgeNatural` |

**The final voice pick is Shawn's, by ear, later.** Do not settle it from a
spec sheet. The two files in the gitignored `voice_test/` are an earlier
audition of the same pair.

### Phase 5, task 1, step 1: the delivery probe

**The plan this task started from would not have worked, and reading the docs
is what caught it.** It set each persona's rate and pitch with `<prosody>`
tags. IBM's SSML reference says "The `<prosody>` element is not supported for
Natural voices", and all three candidate voices are Natural voices. The same
page says the service silently ignores unsupported SSML, so the tags would
have been accepted, the audio would have come back, and every persona would
have sounded the same.

`scripts/tts_probe.py` measured what does work. Six arms a voice, 18 calls,
642 submitted characters against a 3,000 budget, and the audio is in
`C:\Users\shawn\prelude_voice\probe` for Shawn to compare by ear.

| Control | Heidi | Emma | Ethan |
| ------- | ----- | ---- | ----- |
| `rate_percentage`, both ways | works | works | works |
| `pitch_percentage`, upward | works | works | works |
| `pitch_percentage`, downward | ignored | ignored | ignored |
| `<break time="600ms"/>` | works | ignored | ignored |
| `<prosody>` rate or pitch | ignored | ignored | ignored |

`docs/VOICE.md` carries the durations and the pitches. Three findings behind
that table shaped everything after it:

**"Ignored" was measured, not inferred.** Those responses are byte for byte
identical to the plain one, same SHA-256. A control that does nothing and a
control too subtle to hear are indistinguishable by any other measure, which
is why the probe hashes the audio.

**The break works on one voice of three,** and on that one a 600 ms break
added 1.36s. IBM labels `<break>` beta for Natural voices with timing that may
vary, and that is what varying looks like. Pauses are a Caller-only control.

**Pitch moves up and not down.** +20 works on all three voices and -20 is
ignored on all three, measured twice in two separate runs. It is not that
negatives are refused: an earlier arm at -50 halved Heidi's pitch exactly,
222.2 Hz to 111.1 Hz, the -12.00 semitones IBM documents. Where between -50
and -20 it stops being honoured is not known here, and nothing depends on
knowing.

**Two measurement notes, both corrected before anything was written down.**
The WAV header's length field is a streaming placeholder, `0xFFFFFFFF` for
both the RIFF size and the data chunk, so `wave.getnframes()` reported
89478.49 seconds for every file on every voice and every delta came out zero.
The duration now comes from the bytes that arrived. And duration cannot see a
pitch change at all, so the probe estimates f0 by autocorrelation; it agrees
with the service's own arithmetic, 3.16 semitones predicted for a 20 percent
rise against 3.16, 2.67 and 3.16 measured.

`--from-audio` re-measures the files already on disk and sends nothing, which
is how both corrections were made without paying for the audio twice.

### Phase 5, task 1: what was built on top of the probe

**The voices are recorded and the delivery is not.** `app/personas.py` carries
one voice each with `voice_confirmed` true, which says Shawn chose them rather
than that this repo listened to them. The four delivery numbers left that file
for `app/delivery.py`, keyed by persona and situation: the probe settled that a
delivery is per request and that the same voice does not deliver a goal for
the listener's side and one against it the same way, and a single rate on a
persona could not say that. Every value in all eight rows was a placeholder
at that point; task 2 filled them in.

**The rules around the empty table are the work.** Filling it in is an edit to
one file and a run of the suite, because the bounds are already enforced: no
lowered pitch, since the service ignores one; no pause on a voice whose breaks
do nothing; IBM's own bounds on the rate; and the Mate never brighter or
quicker when the other side scored, written as a comparison between its own
two rows so it survives any pair of numbers picked by ear.

**The pronunciation table reaches the speech request and nothing else.** The
guard is structural, because neither failure announces itself: a header
carrying markup still reads correctly to anything that strips tags, and a
narration marked up before the grounding check comes back refused for an
ungrounded name, which sends a reader to the wrong file.

**`<phoneme>` took two arms to settle and the first was worthless.** Asking
for `liːd` returned byte-identical audio, which reads exactly like the
`<prosody>` result and means nothing of the kind: an element asking a voice
for what it already does cannot be told from one thrown away. Asking for
`lɛd`, the metal, changed the audio on all three voices, so the element is
honoured.

**The entry is needed, and a wrong conclusion about it was corrected in task
2.** This file said the identical `liːd` audio proved the voices already say
"lead" correctly, so the entry cost 44 characters and changed nothing audible.
That was a conclusion about one sentence dressed up as a conclusion about a
word. The probe spoke "Argentina take the lead.", and both hero headers say
"Argentina **extend** the lead." Shawn listened to that one: "led" without the
entry, "leed" with it. So the entry is doing real work on the shipped path,
and nothing was spent re-proving it, because a listener hearing the difference
is the evidence this question takes.

Two mistakes in one measurement, and both are worth not repeating: asking a
control for what the voice already does, and measuring one sentence to settle
a word. A pronunciation is a property of a word in a context.

**The suite replays a real exchange and makes no call.**
`tests/golden/tts_synthesize.json` cost 83 submitted characters to record. It
holds the request and the first 128 bytes of the response, with the full length
and SHA-256 of the rest, and it says so in its own provenance block: the
backend returns the bytes it was handed without examining them, so that is
what a replay has to assert.

**Nothing secret can reach a fixture.** `SpeechRequest` carries the path, the
query and the body and not the host, because `TTS_URL` holds an instance id,
and its `Authorization` header reads redacted because the real one is built
inside `send` and lives for one call. That is what made the recorded request
safe to commit.

**The hero samples are eight files in `C:\Users\shawn\prelude_voice\samples`.**
The first run was six calls for eight files, 1,794 submitted characters
against a budget of 2,500: with the delivery table empty the Mate's two sides
built the identical request, so two files were the same audio under two names,
and the script said which rather than paying twice and hiding it. Task 2
regenerated the four Mate files once the table was filled in, four calls and
1,196 submitted characters. The Caller and Storyteller files are still from
the first run and carry no delivery. `docs/VOICE.md` lists all eight with
their lengths.

### Phase 5, task 3: "minute", and looking words up instead of hearing them

**All three voices read "Minute 54." as "my-NEWT".** The app means the unit of
time and only ever means it: the word comes from `template_narration`, which
opens a narration on the clock, so it is the first sentence of most of what a
fan hears. `minute` to `ˈmɪnɪt` is the second entry. No synthesis was spent on
it, since October's allowance is near its limit and the element is already
proven by the `lɛd` arm; Shawn confirms it by ear after November 1.

**The voices were not misreading it.** The CMU Pronouncing Dictionary lists
`M AY0 N UW1 T` beside `M IH1 N AH0 T` for that spelling. Both entries so far
are heteronyms, both were caught by a person listening after the audio was
paid for, and both were predictable from a dictionary before anybody listened.

**So the vocabulary is now looked up in advance.**
`scripts/check_vocabulary.py` collects every word the app can speak, from the
header wording, the event verbs, the narration template, the team names in
`app/web/matches.json` and the recorded narrations in `tests/golden/`, and
reports any spelling the dictionary lists more than one pronunciation for. 54
words on this commit, 19 flagged.
`tests/test_vocabulary.py::TestEveryFlaggedWordHasBeenReviewed::test_no_flagged_word_is_unreviewed`
fails on a flagged word that is neither in `PRONUNCIATIONS` nor on
`CHECKED_NO_ENTRY_NEEDED`, so new vocabulary cannot reach a voice unreviewed.
That was checked by removing "the" from the reviewed list and watching it go
red.

**It found one thing worth finding.** "close" is a heteronym, and the header
says "close the gap" on one transition, where it is the verb. It is the third
entry and the first that came from the dictionary rather than from a listener,
so nobody has heard it: Shawn confirms it with the other two after the reset.
Sixteen of the nineteen need nothing and carry their reasons in
`app/pronunciation.py`; they are full against reduced forms of function words
and unstressed vowels in verbs. One word, "miscontrolled", is not in the
dictionary at all and is reported as unchecked rather than flagged.

**The dictionary is a dev dependency and is never fetched.** `cmudict` ships
its data in the package, which is what lets the suite run it with the network
blocked.

**A claim in three documents was wrong and is corrected.** They said a
narration marked up before the grounding check would be refused for an
ungrounded name. It is not: the plain and the marked-up 1986 narration both
come back grounded on the same 35 claims, because the check reads names,
actions, clocks and numbers against cited facts and "phoneme", "alphabet" and
"ipa" are none of those. So that mistake would be accepted, labelled "Verified
from play data" and read out with the markup in it, with nothing raising. The
structural test that reads source is the only guard against it, which is now
what the documents say. **Task 4 changed that:** the check refuses markup
outright and the structural test is the second layer.

**One housekeeping note.** `uv add` writes to `.venv`, not to the
`.venv-prelude` that `CLAUDE.md` names, and it created a stray one. The
dependency was installed with `UV_PROJECT_ENVIRONMENT=.venv-prelude uv sync`
and the stray directory was removed. Worth remembering for the next
dependency.

**What is owed.** The Caller's rate ceiling, which is words per minute off
real audio and is `None` until something measures it: the Caller's rate being
set at +10 does not settle how high anybody may set it. Regenerating the
Caller and Storyteller samples, once Shawn has heard the Mate and knows
whether the numbers are close. And a decision on where between -50 and -20
`pitch_percentage` stops being honoured, if anything ever needs a lowered
pitch. And Shawn's ear on the two unheard pronunciation entries after
November 1, which is "minute" and "close"; this said all three and was
corrected in task 4. "lead" has been heard with its entry, in Shawn's own
test and in the hero samples, which carry it.

### Phase 5, task 4: the grounding check refuses markup

**The hole task 3 measured is closed.** `BANNED_PATTERNS` in
`app/grounding.py` refuses any narration containing `<` or `>`, labelled
"markup", beside the em dash rule. Narration here is plain prose: nothing the
prompt or the template writes holds either character, so there is no good
narration to lose by refusing both.

**It is the characters and not the element.** Matching `<phoneme` would catch
the one mistake anybody has made and nothing else, and a half-written tag is
not a smaller problem than a whole one.
`tests/test_grounding.py::TestNotGrounded::test_markup` and
`::test_either_bracket_on_its_own` hold that.

**The measurement that used to say the opposite now says this.**
`tests/test_pronunciation.py::TestTheClockInARealNarration` ran the real 1986
narration through `for_speech` and asserted both forms came back grounded on
the same 35 claims. It now asserts the marked-up form is refused with
"markup" and nothing else, and that the plain narration still passes on its
35. The structural test that reads source is kept and is now described as the
second layer: the check catches marked-up narration arriving at it, and
`TestNothingElseAppliesIt` catches a module that could write markup into a
header, which no check ever sees.

**Four documents said the source test was the only guard** and now say what
the check does: `docs/VOICE.md`, `README.md`, `docs/VERIFICATION.md` (a
`banned` row for markup) and the `app/pronunciation.py` docstring. Two stale
counts went with them: the README called `lead` the table's one entry, which
task 3 made three, and `docs/VOICE.md` called it "the first and so far only".

**The pronunciation record is corrected.** Shawn heard "lead" with its entry
in his own test and in the hero samples, so it is settled; "minute" and
"close" are the two nobody has heard, and they wait for November 1. Three
places said or implied all three were waiting.

`pytest -q` reports `660 passed` and the four gates pass.

### Phase 5, task 5: the hero recordings, built and refused

**The script and the words were finished and there was no audio.** Watson
Text to Speech answered `HTTP 403 Forbidden` to the first call of the run on
2026-10-30, so nothing was written, `hero.audio` stayed `{}`, and steps 3 and
4 of the task (the Chromium check and Shawn's listening pass) could not
happen. The recordings were made in Task 15, on 2026-11-07, of six narrations
rather than two. The body it sent back:

```
{"code":403,"error":"Forbidden",
 "more_info":"https://cloud.ibm.com/docs/watson?topic=watson-forbidden-error",
 "trace":"c8d0be4c-f414-49c1-85be-cc866ffbb8ce"}
```

**The 403 is not the format and not the length.** One five character request
was sent twice, once asking for WAV and once for MP3, and both came back 403
(traces `91c1e3a4-8494-4529-a3cd-38de6a27c518` and
`628c2cb9-316b-486e-a45c-11ee22a43347`). So the account refuses every
synthesis request, which rules out the MP3 Accept header this task added and
rules out the size of the run. What it does not establish is the reason: the
body carries none, nothing in this repo can read the usage counter, and the
credentials file is intact by name. That is Shawn's to look at in IBM Cloud,
and it is the next first action above.

**What IBM bills is now known, and it is none of the numbers printed before.**
Shawn checked IBM's documentation: SSML counts toward the character count and
whitespace does not. So a request costs its submitted length less its spaces,
which is `billed_characters` on `SpeechRequest` in `app/tts.py`, and it sits
between the two figures this repo had been printing. Every budget from here is
set on it. The three counts for the run, from `--plan`:

| Count | Characters | What it is |
| ----- | ---------: | ---------- |
| submitted | 2,070 | the text as sent, markup and spaces counted |
| billed | 1,818 | the price: markup counted, whitespace not |
| spoken | 1,530 | the words a listener hears |

The brief's ceiling was 2,000. On the submitted count the run was 70 over and
`--budget` refused it; on the billed count it is 182 under, which is why it
was sent. Five documents and docstrings that said IBM does not publish which
count it charges for now say what it charges for.

**Three recordings per match, and every one of them speaks the template.** No
model ran. The header is the orchestrator's, with no listener name in it,
through `openings` in `scripts/write_headers.py`; the narration is
`template_narration` in `app/narration_prompt.py`, the fallback assembled out
of the numbered facts, through `narration_for` in `scripts/tts_samples.py`.
The same words as the eight hero samples, in MP3 rather than WAV because
these are committed and served.

The 1986 text, 363 submitted and 318 billed, is the header

> Argentina extend the lead. Argentina 2, England 0. Here's how it happened.

and the narration

> Minute 54. Peter Beardsley was dribbled past. Terry Butcher was dribbled
> past. Terry Fenwick was dribbled past. Peter Shilton was dribbled past.
> Diego Armando Maradona shot and scored for Argentina.

The 2022 text, 327 submitted and 288 billed, is the header

> Argentina extend the lead. Argentina 2, France 0. Here's how it happened.

and the narration

> Minute 35. Lionel Andrés Messi Cuccittini passed. Julián Álvarez passed.
> Alexis Mac Allister passed. Ángel Fabián Di María Hernández shot and scored
> for Argentina.

Both carry the pronunciation markup on "lead" and on "minute", which is the
point of the listening pass: "Minute 54" and "Minute 35" are the first thing
each recording says after the header, and nobody has yet heard the `minute`
entry.

**The six files, for Shawn to listen to when they exist.** None of these is on
disk yet. Each is `app/web/assets/audio/<match_id>_<key>.mp3`, and the key is
the `hero.voice_for` value the browser looks up, so the name says which fan
hears it.

| File | Voice | Listener | Listen for |
| ---- | ----- | -------- | ---------- |
| `3750191_mate_scored.mp3` | Ethan, +10 rate, +10 pitch | with Argentina | "Minute 54" |
| `3750191_mate_conceded.mp3` | Ethan, -10 rate, 0 pitch | with England | "Minute 54", and that it is not cheerful |
| `3750191_storyteller_neutral.mp3` | Emma, 0 rate | no side | "Minute 54" |
| `3869685_mate_scored.mp3` | Ethan, +10 rate, +10 pitch | with Argentina | "Minute 35" |
| `3869685_mate_conceded.mp3` | Ethan, -10 rate, 0 pitch | with France | "Minute 35", and that it is not cheerful |
| `3869685_storyteller_neutral.mp3` | Emma, 0 rate | no side | "Minute 35" |

**The map is written from the files on disk, not from the plan.** A monthly
allowance can refuse a run part way through, so `scripts/tts_hero.py` writes
each file as its response arrives and `--map` then fills `hero.audio` with
whatever is actually there. A partial run therefore leaves a map pointing only
at real files, which is what
`tests/test_narration_player.py::TestTheAudioMap`
holds it to, once per match, and the listeners with no recording keep a disabled button rather
than a broken one.

**One hour lost to a refusal that looked like a silent crash, and it was
neither.** The first `--confirm` exited 1 with the last line on screen being
`sending 6 calls`, and the second, captured to a file, looked the same from
the tail. The error handler had worked both times: stderr is unbuffered and
redirected stdout is block-buffered, so the refusal was sitting at the *head*
of the captured file, above output printed before it. Read the whole file, or
redirect the two streams separately. A guess that it was an encoding fault in
the handler was wrong, and the comment it put in `scripts/tts_hero.py` has
been corrected; `sys.stderr` is reconfigured for UTF-8 there anyway, as a
guard on a body this one did not need.

**What is owed, and it is step 1 of the task over again.** Once the service
answers: run `--confirm`, commit the six files, commit `hero.audio`, drive all
three listeners on both matches in Chromium to see the timer and the waveform
move, and hand Shawn the table above. Nothing else in the task is outstanding.

`pytest -q` reports `680 passed` and all five gates pass.

### Phase 5, task 6: the narrations are the model's, and they are frozen

**Both goals were grounded on the first attempt, so the run cost 2 calls of
the 6 it was allowed.** `scripts/freeze_narrations.py --plan` printed the
count first: at most six generations, two goals at three attempts each, plus
one IAM exchange. `--confirm` on 2026-10-30 needed one attempt per goal,
`openai/gpt-oss-120b` through the chat endpoint at `reasoning_effort` low and
`max_new_tokens` 2000. No retry, no fallback, one IAM exchange. The 1986
narration passed on 33 claims and the 2022 one on 40.

That matches what Task 4b measured rather than being luck: 33 of 33 narrations
grounded on the first attempt is why this candidate is active.

**What is frozen, in `app/web/narrations.json`.** 1986:

> Peter Beardsley was dribbled past at 54:08. Terry Butcher was dribbled past
> at 54:13. Terry Fenwick was dribbled past at 54:15. Peter Shilton was
> dribbled past at 54:18. Diego Armando Maradona shot with his left foot from
> open play at 54:18.

2022:

> Nahuel Molina Lucero passed at 35:12. Alexis Mac Allister received the ball
> at 35:14. Ángel Fabián Di María Hernández received the ball at 35:22. Ángel
> Fabián Di María Hernández shot at 35:22.

Beside each: the tagged text the check passed, the facts it cited with the
`event_id` each was read from, which sentence cited which, and the verdict.

**The words are terser than the template's and carry more than it did.** The
model dropped "Minute 54." and put a clock on every sentence instead, and it
reached for `shot.body_part` and `play_pattern` on the 1986 goal: "with his
left foot from open play" is in the facts and the template never said it. The
2022 narration is four sentences where the buildup offers thirteen facts, and
it does not name Messi or Álvarez, who are in the card's quote. That is the
model's editing rather than a hole: a narration cites what it uses, and the
check reads what it cites.

**Neither narration says the goal went in,** and both are grounded anyway. The
check's ending rule is that the last sentence cites the goal's own shot fact,
which both do. The facts are built from one record each and a `Shot` record is
a shot; the goal is in the header above the narration, which says the score.

**The hero recordings now speak these words, and the price moved.**
`scripts/tts_hero.py` reads `app/web/narrations.json` instead of calling
`template_narration`, so what a judge hears and what a judge reads are one
text. From `--plan`:

| Count | Was | Now | What it is |
| ----- | --: | --: | ---------- |
| submitted | 2,070 | 2,268 | the text as sent, markup and spaces counted |
| billed | 1,818 | 1,959 | the price: markup counted, whitespace not |
| spoken | 1,530 | 1,746 | the words a listener hears |

**The run clears the 2,000 budget by 41 characters.** That is thin enough to
say out loud: one more pronunciation entry on a word either narration says
would push it over, and `--budget` would refuse the run. Raising it is a
decision, not a fix, so it is left at 2,000.

**Spoken is now below billed, where it used to be above it.** Nothing changed
in the counting. The frozen narrations carry more markup than the template
did, because the 2022 one says "Di" twice and each costs a `<phoneme>`
element, and markup is billed while the whitespace it displaces is not.

**The vocabulary sweep now reads the frozen narrations,** because those words
reach a voice and a model writes from a wider vocabulary than the template
does. It found four words nobody had reviewed and one of them is a real
heteronym.

**`di` is the fourth entry in the pronunciation table.** The dictionary lists
`D IY1` beside `D AY1`, and the second is the English "die" rather than an
accent on a Spanish name. The 2022 recording says it twice and the 2022 moment
card shows it, so it is `diː`. It is the second entry found by the dictionary
rather than by a listener, after `close`, and the first found on a word the
app speaks only because a model chose to write it: the template wrote the full
recorded name in one breath and never said "Di" on its own.

The other three went on `CHECKED_NO_ENTRY_NEEDED` with their reasons: `his`
and `with` are function words with full and reduced forms, and `allister` is
one name under the cot-caught vowel the voices merge.

**Two things nobody has heard, and they are not the two that were owed.**
`minute` is no longer in either hero recording: the model wrote clocks instead
of "Minute 54", so the entry is still unheard but the hero recordings are no
longer what would settle it. What they will settle instead is `di`, and a
question no entry covers: **the narrations now read clock values aloud**,
"at 54:08" and "at 35:22", and nothing here knows how an IBM Natural voice
reads a colon between two numbers. It is not vocabulary, since a digit is not
a word and no dictionary entry governs it, so no gate can flag it. It is the
first thing to listen for after November 1.

**The moment card shows the narration under the header** with the grounding
label beside it, and the quote block is kept: it does not conflict. Both
quotes name the same players in the same order as the facts their narration
cites, and the 2022 quote names two more.

**The card's one label moved rather than being duplicated.** It sat at the
foot of the card beside the quote. Two copies of the same promise on one card
reads as a defect rather than as a stronger guarantee, so the label is beside
the narration, which is the only text on the screen a test re-checks.
`NARRATION_FIELDS` in `scripts/scan_copy.py` gained `hero_narration`, which
the file itself says to do when Phase 5 adds a narration element.

**`scan_copy.py` caught two things worth it having caught.** It refuses the
grounding label in a copy file, because a data file carries no markup that
could place the label over anything, and both the `label` field in
`narrations.json` and a comment in `match-content.js` were hits. The data file
now records `"labelled": true`, the permission rather than the words, and the
label is spelled in `app/narration.py` and in the markup and nowhere else.

**Checked in Edge at 390px over a local server**, all three URLs reaching
`data-match-rendered`: the default and `?match=3750191` show the 1986
narration, `?match=3869685` shows the 2022 one, one label each, after the
narration and inside its card, no horizontal scroll.

**Not run, and still owed: the recordings.** The Text to Speech instance is
disabled above its Lite cap until November 1, so `scripts/tts_hero.py
--confirm` was not sent. Everything in front of it is ready and the price is
1,959 billed characters.

`pytest -q` reports `714 passed` and all five gates pass.

**One thing was already red before this task started.** `check_docs.py` exited
1 on `d0837ac`: that commit added `bob_sessions/phase5_task12_narrators.md`
and left it on `DELIBERATELY_ABSENT` in `scripts/check_docs.py`, so the gate
reported it as existing while listed as absent. The list is empty again
(`d1757b3`). The suite was `694 passed` and the other four gates were green.
