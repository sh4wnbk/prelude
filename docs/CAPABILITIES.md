# What Prelude can do, at this commit

The authoritative list. `README.md` links here rather than carrying
it, so the short page a judge reads and the long list a reviewer
checks do not drift apart.

## What the demo is, precisely

- **The screens and the navigation work.** You can move through the event list,
  the ticket scanner, ticket details, the live seated screen, the moment card,
  the moments list and Profile, and the bottom tabs switch between them.
  Profile shows the two answers the fan gave, their name and who they are
  with, with Change reopening the question, and the narrator they chose.
- **Scanning and manual entry work.** The scanner reads the QR code on a demo
  ticket from the camera and opens that match; manual entry picks the match from
  a list and takes a seat. Both land on ticket details, and Enter match opens the
  match at its pre-moment state.
- **The moment card plays its narration.** The play button on that card plays
  the recording written for this listener, with the timer and the amber fill
  following the clock and the waveform bars rising and falling with the voice
  through a Web Audio analyser; `app/web/narration-player.js` is the player and
  `hero.audio` in `app/web/matches.json` is where it finds the file. The
  waveform is also the scrubber: dragging it with a finger or a mouse moves the
  recording to the position under the pointer, playing or paused, and the left
  and right arrow keys move five seconds. On the moments list the hero goal's
  card plays that same recording, by the same lookup, so the two screens never
  offer a fan two different voices, and its waveform follows the voice and
  scrubs the same way, because both screens hand their markup to one player.
  Every other card's play button is disabled and says so, and its bars do not
  move, because those moments have no recording.
- **The app has a mark, and the first frame of a load is it.** "Prelude." in
  Syne ExtraBold with the "u" drawn as seven amber elements, over the tagline
  "Leave your seat. Not the game.", on the app background, while the event
  list loads behind it. It is held for 1.5 seconds and then crossfades with
  the list over 300 ms, the mark going as the list comes up, and it is off the
  screen by 2.5 seconds whatever the list did. Those seven
  elements on their own are the icon in the browser tab and on a home screen,
  and the same screen is drawn as a startup image for each iPhone size, so
  opening Prelude from a home screen opens on the mark too.
  [`docs/DESIGN.md`](DESIGN.md) records the mark, the icon, the tagline,
  the timing and where each file lives.
- **Nothing is live.** The demo replays StatsBomb historical data: the 1986
  Argentina vs England quarter-final and the 2022 Argentina vs France final,
  each presented as if it were unfolding now. There is no live feed, no venue,
  and no GPS.

## Everything that runs

This list is read against the code, not written from memory.

**Runs today:**

- `scripts/fetch_statsbomb.py`: downloads the StatsBomb open-data files the
  project uses into `data/raw/` (gitignored, reproducible): the competition and
  match indexes, both matches' event feeds, and both matches' lineups, which
  are what record a player's `player_nickname`.
- `scripts/data_check.py`: reads the 1986 Argentina vs England event feed,
  lists every goal and the shot counts per team, and writes
  [`docs/data_check.md`](data_check.md) from that output.
- `scripts/scan_copy.py`: checks the screens and `app/web/matches.json` for
  banned copy, and for the grounding label sitting anywhere but over narration.
  Exits non-zero on any hit.
- `scripts/check_match_copy.py`: checks every name, minute, score and count in
  `app/web/matches.json` against `data/raw/`, and the inline copy in the screens
  against `app/web/matches.json`. A line that describes the play carries a
  `grounding` block: every key in it is read against the feed, every key has to
  be said in the words, and every claim in the words has to have a key.
- `scripts/make_tickets.py`: writes a demo ticket QR code per match into
  `app/web/assets/tickets/`, and reads each one back with a decoder before it
  counts as written.
- `scripts/brand/build_svg.py`: draws every brand file into
  `app/web/assets/brand/` from one set of numbers and the two variable fonts
  committed beside it, both under the SIL Open Font License, and the launch
  screen as a startup image per iPhone size into `app/web/assets/launch/`.
- `scripts/make_icons.py`: writes the icon set the screens link, from two of
  those files. Both scripts take `--check`, which draws everything, compares it
  with what is committed and writes nothing.
- `scripts/check_docs.py`: checks that these docs still match the code they
  describe, and exits non-zero when one has gone stale.
- `scripts/narration_compare.py`: the paid comparison of the two watsonx
  candidates, by persona. `--plan` prints the narrations, the calls and the
  estimated tokens and makes no call; `--confirm` has to name the same arms as
  `--arms`; `--max-tokens` stops the run between narrations.
- `scripts/freeze_narrations.py`: narrates both hero goals on watsonx with the
  active model and writes the ones the grounding check passed to
  `app/web/narrations.json`, with the facts each cited and the check's
  verdict beside the text. A narration that reaches the template fallback is
  not frozen: the run writes nothing and exits 1. `--plan` prints the call
  count and makes no call; `--confirm` sends it. `--authored` calls no model:
  it writes the six narrations the team wrote, one per `hero.voice_for` key,
  beside the per-goal one and under `slots`, each carrying who wrote it and
  the check's verdict on it, and it refuses to write a narration the check,
  the places rule or the opener rule turns down. The moment card shows the
  narration for the listener's own key and `scripts/tts_hero.py` speaks it,
  so a fan reads the words they are about to hear.
- `scripts/authored_narrations.py`: holds the six hero narrations the team
  wrote, one per slot of the two hero goals, and reads each of them against
  `data/raw/` with the three rules a candidate meets: the grounding check in
  `app/grounding.py` as a goal call, in the persona and for the listening
  side its slot is written for, the places rule and the opener rule. It
  writes `docs/narration_runs/authored_2026-11-07.md` and the same answers as
  JSON, calls no model and freezes nothing. All six pass all three, so it
  exits 0; it exits 1 if one of them stops passing, which is what makes a
  check change that would cost a hero narration visible.
- `scripts/tts_probe.py`: measures which delivery controls change the audio on
  each of the three candidate IBM voices, by synthesizing one fixed sentence
  per arm and reading the duration, the pitch and the bytes back. `--plan`
  prints the character count and makes no call; `--confirm` sends it;
  `--from-audio` re-measures what is already on disk. It writes WAV files
  outside the repo. What it found is in [`docs/VOICE.md`](VOICE.md).
- `scripts/narration_eval.py`: narrates goals several times, in one persona or
  all of them, and measures what came back: the first-attempt and after-retry
  pass rates, coverage of the passage's key beats, words per sentence, tokens
  and time. Writes [`docs/narration_eval.md`](narration_eval.md), which
  holds three runs. Ollama only.
- `app/statsbomb_event_feed.py`: `StatsBombEventFeed`, the EventFeed
  implementation. Reads a match from `data/raw/`, returns its goals as
  moments (periods 1 to 4, so the shootout is excluded), and returns the run-up
  to a goal as untouched source records. `buildup` returns the goal's whole
  possession, plus the previous possession when the goal came from a set piece,
  which is how the foul that won a penalty reaches a caller.
- `tests/test_event_feed.py`: 28 tests over the EventFeed contract, including
  `buildup`. All 28 pass against `app/statsbomb_event_feed.py`.
- `app/narration_provider.py`: one narration interface with two backends,
  Ollama (the default, local) and watsonx.ai (only when named). Callable from
  Python; no screen calls it. `provider()` returns the Ollama backend, and
  nothing reaches watsonx without passing its name.
- `scripts/record_narration_golden.py`: calls the local Ollama server once and
  records the request and response into `tests/golden/`, so the tests can
  replay a real response instead of making a call.
- `scripts/narrate_once.py`: narrates one goal with a real model and prints
  every attempt, the claims the check refused, and whether the first attempt
  was grounded. Defaults to the 1986 goal at 54:18; takes a match id and a
  clock for any other. It needs a local Ollama server and writes nothing.
- `tests/test_narration_provider.py`: 65 tests over the config and both
  backends, including the answer that is all reasoning and no narration, the
  timeout a run sets for itself, the tokens watsonx says it billed and the
  hard cap that stops a run before the next call passes it. All 65
  pass, and none of them opens a connection:
  `tests/conftest.py` replaces `urllib.request.urlopen` and
  `socket.socket.connect` with functions that raise, for every test in the
  suite.
- `app/pitch_zones.py`: turns one recorded location into the phrase a
  narrator says it with: eight bands up the pitch ("deep in his own half",
  "just inside their half", "in the final third", "on the edge of the box",
  "in the box") and three across it ("on the left" and "on the right"
  outside the sides of the penalty area, and nothing for the middle).
  Arithmetic and a word list: one coordinate against one number, read in the
  frame of the team whose record it is, so a place is never read off a
  mirrored defending record. `from_the_other_end` reads one spot from the
  other end of the pitch, which is what a half said with a possessive needs:
  "our own half" is a different half for a fan of either side.
- `tests/test_pitch_zones.py`: 59 tests over the bands, the sides, the
  box's width, the opponent's name in "their half", the zones the two hero
  passages put their beats in, the six places the side rule is set on and the
  spot read from the other end. All 59 pass.
- `app/story_beats.py`: curates one buildup down to the beats a goal call
  tells, which is what `app/goal_call_prompt.py` shows the model: the
  recovery, each pass, each carry of ten yards or more, each dribble past an
  opponent, the pressure on the player with the ball and the finish. Ball
  receipts and touches on the spot are left out, consecutive dribbles past
  are one beat naming the defenders in order with the carries between them
  absorbed, a long carry is a flag and never a yard figure, no beat carries
  a clock, and the play pattern and the own half are said once. The beats
  also place the move, from `app/pitch_zones.py`: the first action, the
  recovery, each defender gone past, a long ball at both ends, the assist
  and the finish, and nothing else, because every record carries a location
  and a telling that places every beat is a list of coordinates with words
  around it. The grounding check still reads a narration against every
  record, so the curation can only narrow what a narration may say.
- `scripts/story_beats_report.py`: prints the beat list for both hero goals
  beside the records it was curated from. Reads `data/raw/` and writes
  nothing.
- `app/narration_prompt.py`: turns one buildup into a numbered list of plain
  past-tense facts, one per recorded event, built by code out of the records
  and naming each player by the recorded nickname where there is one;
  the prompt that asks a model to narrate from that list in the past tense, cite
  the facts each sentence used, and stop on the goal; `NARRATION_STYLE`, the one
  style every narration is written in, printed into that prompt in every voice;
  and the fallback narration, one sentence per fact, assembled with no model.
- `app/plain_characters.py`: rewrites a disguised space or hyphen as the plain
  one: `NO-BREAK SPACE`, `NARROW NO-BREAK SPACE`, every other Unicode space
  separator, `NON-BREAKING HYPHEN`, `MINUS SIGN` and the zero-width
  characters, which are removed rather than replaced. Applied as a model's
  narration arrives in `app/narration.py`, again in `app/grounding.py` before
  a claim is read, and again in `app/tts.py` before a speech request is built.
  A dash is left exactly as written: the em dash and the en dash are refused
  by the check and banned from copy, so rewriting either as a hyphen would
  undo a ban in the one place nobody would look.
- `tests/test_plain_characters.py`: 45 tests over the rewrite, including the
  two characters live candidates actually arrived with, the sixteen space
  separators, the dashes left alone, the em dash still being refused after it
  and the curly apostrophe written as a straight one before a name is read.
  All 45 pass.
- `app/recorded_names.py`: reads `player_nickname` and the two team names out of
  `data/raw/lineups/<match_id>.json` and maps it to the full name the event
  feed records, so a narration can say "Lionel Messi" rather than "Lionel
  Andrés Messi Cuccittini". It is a reader and not a chooser: there is no
  fallback that shortens a name the file does not shorten, so a player with no
  recorded nickname keeps their full recorded name. Maradona is one of those,
  so the 1986 narration says his name in full. The team names are what
  "just inside France's half" needs: all thirteen records of the 2022
  counter are Argentina's, so the side being attacked is not in the passage.
- `tests/test_recorded_names.py`: 7 tests over the reader and over what the two
  lineups files record, including the four nicknames the 2022 hero buildup has
  and the nickname the 1986 file does not record for the scorer. All 7 pass.
- `app/grounding.py`: decides whether a narration's claims trace back to the
  data, sentence by sentence, against the facts that sentence cited. Refuses
  invented names, numbers, clocks and actions; a name or action in the passage
  but not in the cited facts; a name paired with an action no single cited fact
  records; a short form of a player's name that neither the event feed nor the
  lineups file records, while accepting either of the two names they do; a sentence that cites nothing or cites a fact that does not exist; a
  present-tense verb, in a passage that already happened; a narration that does
  not end on the goal's own shot; a wrong shot type or body part; verdict
  nicknames, editorial epithets, claims about the result, lines addressed to the
  fan, em dashes, any angle bracket; and narration that asserts nothing
  checkable. It takes the
  persona and the listener's side, which change one thing: a partisan persona
  may say "we", "our" and "us" about that side, in a sentence citing a fact
  recorded against it, and no other voice may say them at all. The prompt asks
  for none of them in any voice, so that rule is a guard against a model that
  writes the first person anyway rather than a permission anything uses.
- `app/personas.py`: the three personas, each with an id, a name, a one-line
  Profile description of what it sounds like, and whether it is offered to fans
  only. They are separated by sound and not by text: the narration is one style
  in every voice, and each persona now carries the IBM voice Shawn picked for
  it. The rate, the pitch and the two sentence breaks are still `None` and
  marked unconfirmed, because Shawn sets them by ear. Three measured runs
  behind that decision are in `docs/narration_eval.md`. No screen offers a
  choice yet.
- `app/tts.py`: the speech backend. Takes the header, the narration, a persona
  and a situation, and returns the audio bytes IBM Watson Text to Speech
  sent, in the format the caller asked for: WAV by default, MP3 for the
  recordings the site ships.
  Callable from Python; no screen reaches it. It refuses a narration that still
  carries its citation tags, applies the pronunciation table, and puts the
  pauses in only for a voice whose breaks work. Credentials come through
  `app/credentials.py` and a missing one is named before any request.
- `tests/test_tts.py`: 56 tests over the backend, replaying a real recorded
  exchange from `tests/golden/tts_synthesize.json`. All 56 pass, and none of
  them reaches the service.
- `scripts/record_tts_golden.py`: records one real speech exchange for that
  replay. `--plan` prints the request and its character count and makes no
  call; `--confirm` sends it.
- `scripts/check_vocabulary.py`: collects every word the app can speak, from
  the header wording, the event verbs, the narration template, the team names
  in `app/web/matches.json`, the frozen narrations in
  `app/web/narrations.json` (the six the voices read, one per listener, and
  the per-goal one beside them) and the recorded narrations in
  `tests/golden/`, and
  reports the ones the CMU Pronouncing Dictionary lists more than one
  pronunciation for. Exits non-zero when a flagged word has not been reviewed;
  `tests/test_vocabulary.py` is the same condition in the suite. No network:
  the dictionary is a dev dependency and ships its own data.
- `tests/test_vocabulary.py`: 22 tests over the collector, the two review
  lists and the three heteronyms in the table. All 22 pass.
- `scripts/tts_samples.py`: both hero goals in every voice, with the Mate from
  both sides, written outside the repo for Shawn to listen to. The words are
  the orchestrator's header and the code-built narration, so no model runs.
  `--plan` prints the character count and makes no call, `--budget` refuses a
  run above a character count, `--personas` reruns one voice's files without
  paying for the rest, and `--confirm` sends it.
- `scripts/tts_hero.py`: the recordings the site serves, one per listener per
  match, as MP3 under `app/web/assets/`, with `hero.audio` in
  `app/web/matches.json` written from the files on disk. The words are the
  orchestrator's header and the narration for that listener's own
  `hero.voice_for` key, read from `app/web/narrations.json`, so a fan hears
  the words the moment card just showed them rather than the template the
  samples speak. `--plan` prints the character count three ways and makes no
  call, `--budget` refuses a run above the billed count, `--confirm` sends it,
  and `--map` rewrites the map alone. **The six exist:** they were recorded on
  2026-11-07 for 2,403 billed characters of the 3,500 budget, the Storyteller
  on `en-US_EmmaNatural` and the Buddy on `en-US_EthanNatural`, and
  `hero.audio` names all six, so the moment card's play button works for every
  listener.
- `scripts/pad_hero_audio.py`: puts 500 ms of silence in front of each of those
  six files, which is what the iPhone needed. The output wakes after `play()`
  starts, so the opening of the file was landing inside that wake and
  "Argentina" came out as "tina"; Task 24 fixed the Web Audio resume that was
  the other half of it. **Nothing is re-encoded.** Half a second of silence is
  built as its own MP3 and the original's frames are copied after it with
  ffmpeg's concat demuxer, so the spoken audio decodes sample for sample
  identical and keeps its 24000 Hz, its one channel and its own bitrate. It
  calls no service and needs a local ffmpeg, on `PATH` or through
  `PRELUDE_FFMPEG`. `--plan` probes the six and writes nothing, `--confirm`
  pads the ones that are not padded yet and refuses the rest, and `--check`
  decodes both sides and reports the lead-in, the samples and the two
  durations against a git ref. **The six are padded:** each carries a 506.0 ms
  lead-in, every sample behind it is the one the service wrote, and the
  measurements are in `HANDOFF.md`.
- `app/delivery.py`: the delivery table, one row per persona per situation,
  holding the rate, the pitch and the two pauses. The values are Shawn's, set
  by ear, with the rules enforced around them: no lowered pitch, no pause on a
  voice whose breaks do nothing, no rate outside IBM's bounds, and no Mate
  that is cheerful when the other side scored. The situation comes from the
  moment and the listener, never from a model.
- `tests/test_delivery.py`: 47 tests over the situations, the eight rows, the
  values in them, the bounds and the Mate rule. All 47 pass.
- `app/pronunciation.py`: the pronunciation table, word to IPA, with three
  entries: `lead` to `liːd`, which is needed, since Shawn heard "extend the
  lead" read as "led" without it and "leed" with it; `minute` to `ˈmɪnɪt`,
  which all three voices read as "my-NEWT"; and `close` to `kloʊz`, which the
  dictionary flagged and nobody has heard yet. `for_speech` marks the listed
  words up as `<phoneme>` elements for the speech request, and nothing else in
  `app/` may import it: markup in the text a screen shows is a fan reading
  tags, and markup in the text `app/grounding.py` reads is a sound narration
  refused for tags it never wrote. The check refuses any angle bracket, and a
  test reads source as the second layer, for the header, which no check sees.
  Text holding no listed word is returned identically.
- `tests/test_pronunciation.py`: 35 tests over the table, the markup, the
  round trip that proves a pronunciation never changes a word, the seven
  modules forbidden to import it, the one module that applies it, and the real
  1986 narration through the real backend. All 35 pass.
- `tests/test_personas.py`: 27 tests over the config's shape, the ids against
  `app/orchestrator_contract.py`, the three picked voices, the unconfirmed
  prosody fields and the Profile copy. All 27 pass.
- `app/narration.py`: narrates one moment. Generates, checks, regenerates up to
  twice, then falls back to the template, and records every attempt with the
  claims that failed. Nothing ungrounded is returned. The citation tags are
  stripped from the text it returns and kept beside it for audit.
- `app/credentials.py`: finds and reads the credentials file, which lives
  **outside this repo**: `~/.prelude/.env` by default, or wherever
  `PRELUDE_ENV_FILE` points. A path inside the repo is refused rather than
  read. `describe` reports which variable names a file defines and never a
  value, so a missing credential can be diagnosed without one reaching a
  terminal.
- `tests/test_credentials.py`: 29 tests over the loader. Every one writes a
  fake credentials file into a temporary directory; none reads the real one,
  and `tests/conftest.py` points `PRELUDE_ENV_FILE` at an absent path for the
  whole suite so none can.
- `tests/test_narration_prompt.py`: 94 tests over the facts, the numbered fact
  list, the prompt, the one narration style printed in it, the key beats of a
  passage, the move the hero prompt prints as steps, the fallback narration,
  which has to reach every one of those beats, and the recorded fields a goal
  call says out loud: the play pattern, the pressure, the pass recipient and
  length, the assist, the first-time flag, the body part, the two field
  positions read off a coordinate and the duration read off the timestamps.
  All pass.
- `tests/test_grounding.py`: 104 tests over the cited reading of the grounding
  check, one per way a narration can be wrong or can look wrong and be fine,
  including the misdescription it refuses by pairing a name with an action and
  the first person, which only the Mate may use and only over its own side's
  facts. All pass.
- `tests/test_narration_grammar.py`: 131 tests over the goal-call reading in
  `app/narration_grammar.py`, one mechanism at a time: the name parts that
  pick out one player, the pronoun that means the player with the ball, the
  chains, which name owns a claim, who a move is attributed to when a second
  verb joins the same subject, "past X" as a dribble past X, the field
  positions, the shape of a run, which way the ball went, a run with yards in
  it, the carry that is asked to deliver the ball, who "under pressure" is
  about, a hyphen reading as the space it stands in for, the place on the
  pitch a phrase claims and the action it is claimed about, whose half "our
  half" and "their half" name, and the recorded fields a goal call says out
  loud. All pass.
- `tests/test_reference_narrations.py`: 63 tests holding the narration
  standard: the eight reference narrations in `docs/VOICE.md`, checked word
  for word with the narrator and the listener side given, the eleven lines the
  check has to keep refusing, the words a narration may land the finish on,
  the force words it may not, the verdicts about history it may not, and the
  reaction layer: where a reaction may stand, who may cheer in one, what
  makes a short sentence play instead, and the match's own names rather than
  capitalisation deciding whether a reaction names anybody. All pass.
- `tests/test_narrator_candidates.py`: 256 tests over
  `app/goal_call_prompt.py`, `app/story_beats.py` and
  `scripts/narrator_candidates.py`: the four
  styles, one per narrator and situation, the invented match their examples
  are shown through and the reaction each example ends on, the story beats
  the prompt shows and the receipts and short carries it does not, the clock
  no beat and no prompt carries, the six recorded slots read off
  `hero.voice_for`, the price of one
  recording, the request for tellings that differ in structure, the
  reasoning effort the run chooses for itself, the shape that tells two
  tellings from one telling written twice, the rule against hanging the move
  off "who" and the count printed beside each candidate, the places a
  telling has to put the move in and the refusal a telling short of them
  meets, the name a telling has to open on, the call count and
  token estimate the run prints before it sends anything, the hard token
  cap that stops the run and keeps what it had written, and the run with no
  retries. All pass, and none calls a model.
- `tests/test_authored_narrations.py`: 33 tests over the six the team wrote:
  one narration per recorded slot, the authorship carried beside every one of
  them, the opener each of them is held to, the places each of them says, all
  six being grounded, the two earlier 1986 wordings that are still refused for
  a place, and the report going to a temporary directory when the suite runs
  the script, so a run on a later day does not re-date the committed one. All
  pass, and none calls a model.
- `tests/test_narration.py`: 31 tests over the pipeline, covering the retries,
  the fallback, the citation stripping, the failure log, the first-attempt pass
  rate, the characters made plain as a model's text arrives and the attempt
  that came back with reasoning and no narration in it. All pass, and no test
  calls a model.
- `tests/test_narration_eval.py`: 72 tests over the coverage measure, the
  token recorder and the goal selection in `scripts/narration_eval.py`,
  including the live thin narration that passes the grounding check and
  reaches one key beat of five. All pass.
- `app/api.py`: the read-only API described under "Hosted API" below. It runs
  locally with `uvicorn` and is deployed, from `render.yaml`, at
  <https://prelude-api.onrender.com>. The Blueprint's build filter rebuilds it
  only when `app/`, `pyproject.toml`, `uv.lock` or `render.yaml` change, so a
  change to a screen or a doc does not.
  `.github/workflows/keepalive.yml` pings `/health` on a schedule, behind the
  `PRELUDE_KEEPALIVE` repository variable.
- `tests/test_api.py`: 99 tests over the three endpoints, their errors, the
  form the `match` parameter takes, the seven rows of the slot rule, the text
  matching `app/web/narrations.json`, every audio URL being a file under
  `app/web/`, and what the module may not import or write. All pass, and none opens a connection to anywhere but the
  event loop's own wakeup pair.

**Exists but does nothing yet:**

- `app/orchestrator.py`: picks the line said before the narration starts:
  "today" or "tonight" from the kickoff time, a header, and a default persona
  from the listener's side. The shapes and the wording live in
  `app/orchestrator_contract.py`. Callable from Python; no screen calls it yet.
  The header is the game focused one: what the goal did to the score, in the
  same words for every listener.
- `tests/test_orchestrator.py`: 72 tests over the orchestrator, covering every
  goal in both demo matches and a made-up sixty minute sport whose scores move
  three at a time. All 72 pass.
- `app/event_feed.py`: the data shapes and the `EventFeed` interface. A
  contract only; `app/statsbomb_event_feed.py` is what implements it.
- `app/narration_config.py`: the model ids and which one is active. Values
  only, with no behaviour: it reads no environment variable and opens no
  connection.
- The waveform on the moments list, on the one card with a recording. It
  follows the voice, shows the elapsed time and seeks, because that card and
  the moment card hand their markup to one player in
  `app/web/narration-player.js`. Every other card on that list has no
  recording: its play button is disabled and says so, and its bars stay at the
  heights the markup gives them.

**Not built yet:** audio for any moment but the two hero goals, and GPS
presence handling. Narration runs and reaches a reader: `scripts/narrate_once.py`
generates it for one goal, the check decides whether it may carry "Verified
from play data", the pipeline falls back when it may not, and the moment card
shows the frozen narration for this listener with the recording of it beside
the text. What nothing does yet is measure how often a first attempt is
grounded across the nine goals. The screens read their content from
`app/web/matches.json` and carry the selected match between them; the other
moments have neither sound nor narration. Nothing wires the EventFeed to the screens yet: the module returns
moments, event windows and buildups, and no screen reads them.
`docs/narration.md` records what the narration modules are and what they are
not, and `docs/VOICE.md` is the written voice the prompt and the grounding check
enforce between them, with what the check still cannot decide.

No claim in this file is intended to run ahead of the code. If you find one
that does, it is a bug in this file.
