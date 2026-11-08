# The Orchestrate agent

The instructions below are what Shawn pastes into the agent in watsonx
Orchestrate. The agent itself is created in Orchestrate's own UI and its model
is fixed by the lab admins, so nothing about it lives in this repo except this
file: the words it is given, and the reason each one is there.

**State, 2026-11-07.** The agent has two tools and they arrive as one imported
OpenAPI file, `orchestrate/prelude_tools.yaml`, pointing at the deployed API
at <https://prelude-api.onrender.com>. Bob wrote that file as Task 15 of
`docs/bob_brief.md`, `tests/test_orchestrate_spec.py` passes against it, and
Shawn has imported it into Orchestrate and attached it to this agent. The API
itself is live, which Task 17 in `HANDOFF.md` records.

**What the first live test found.** Two things, and both are answered here and
in `app/api.py`. Orchestrate called `/buildup` with `match=3.869685e+06`,
because it serialises an integer tool argument as a float; `match` takes a
string of digits now, and `MATCH_PATTERN` in `app/api.py` records why. And the
agent asked the fan for a StatsBomb match id, because nothing in its context
said which matches exist; the block below carries them now.

## What the agent is for

A fan asks about one of the two matches the app serves. The agent answers from
the two read-only tools and from nothing else: it lists the goals, and it hands
over the narration Prelude wrote for the one goal it narrates, in the voice the
fan is entitled to hear.

It is not a fourth input. The tools serve what `data/raw/` and the frozen
narration already hold, which is what `app/api.py` is for.

## Why the instructions carry the matches

A fan says "the 1986 quarter final" or "the one Messi won". A tool parameter
takes 3750191. Something has to turn the first into the second, and the agent
is the only thing in the chain that sees both, so the list of matches has to be
in front of it. Without it the agent did the one thing it must not do, which is
ask the fan to supply the number itself.

The list is generated, not written. `scripts/write_served_matches.py` builds
it: the id and the two team names from `app/web/matches.json`, which is the
service's own list of what it serves, and the competition, the season, the
stage and the date from the StatsBomb match files under `data/raw/matches/`,
which is where those two ids were resolved from in the first place and which
`scripts/fetch_statsbomb.py` downloads. `app/web/matches.json` holds no
competition and no stage, so those two are read off the play data rather than
invented here.

Run `scripts/write_served_matches.py` to rewrite the list and the same script
with `--check` to fail on a stale one.
`tests/test_orchestrate_agent.py::TestTheMatchesItServes` holds the list in
this file to both sources, so a third match added to the app fails the suite
here until the list is written again.

## Why rule 3 says the whole field, and says it twice

The agent was asked the 1986 question as a fan of neither side and it reached
the right narration, the Storyteller's neutral telling. It then cut the answer
at "then took it into the box", closed it with an ellipsis, and broke one of
its sentences across two lines. 13 of the field's 65 words were missing, 68 of
its 330 characters, and what was missing was the goal: the words that say the
ball went past the goalkeeper and in, and the sentence after them. The 2022
answer in the same session was complete, so this is a narration handed over in
part rather than a rule the agent never read.

**A telling cut before the finish is the telling of a goal that never goes
in.** It is also narration nothing has checked. `app/grounding.py` read all 65
of those words when it passed them, and the label the response carries was
earned by the whole field, so three quarters of it is new writing with an old
guarantee attached. Rule 1 already said never to shorten the text. Rule 3 now
says it again in the terms the failure actually took: all of it, to the last
full stop, with no ellipsis and no unfinished sentence.

**One line of rule 3 may have invited part of it.** The rule's own list of
what may not follow the narration ended "no closing sentence, no offer of
more", meaning no closing sentence of the agent's; the narration's last
sentence here is "What a moment.", which is exactly the kind of sentence that
list appears to forbid. It now reads "no closing sentence of your own", and
the paragraph above it says in as many words that the field's final sentence
belongs to the field.

**The line break is the smaller half and it is still worth a rule.** None of
the six frozen narrations in `app/web/narrations.json` holds a line break or
an ellipsis; `tests/test_orchestrate_agent.py::TestTheAnswerIsTheNarration`
reads the file and says so. So every break in an answer is the agent's, and a
break mid sentence makes a fan read two fragments where the recording reads
one sentence.

## Why the answer is the narration and nothing else

The agent quoted the 2022 narration word for word and then added a line of its
own: an em dash, the narrator's name, and the label behind it in parentheses
with its first letter lower-cased. The quoting was right. The line after it
was three breaches in one, and none of them came from a rule the agent was
given badly. `CLAUDE.md` allows the phrase only as `app/grounding.py` writes
it, with no partial credit and no softened variant, so a lower-cased copy of
it is not the label at all. The repo takes no em dash in any copy. And a
label in parentheses behind a name reads as a flourish on a byline rather than
as the finding it is.

**Shawn's decision, 2026-11-07: the answer is the narration text exactly as
`/buildup` returns it, and nothing else.** Not a shape for the extra material,
no shape for it. An instruction to show the label is an instruction to style
something, and styling is the one thing a model does without being asked. The
narration was written to be read on its own and the check that earned it the
label read it on its own, so handing it over on its own is the only form in
which nothing has been added to it.

What that costs, written down rather than discovered later: the agent no
longer shows the label, the narrator's name, the recording link or the
authorship line. Rules 2 and 11 keep the label and those two fields out of the
answer instead of placing them in it. A fan who wants the recording or the
label reads them in the app, where `app/web/prelude_03_moment_card.html` sets
the label as its own element with no punctuation around it and the player sits
beside it. If one of them should come back, it is a decision about rule 3 and
Shawn's to make; the fields are all still in the response.

## Why the first rule is a verbatim rule

`CLAUDE.md` allows the phrase "Verified from play data" over narration whose
claims trace back to the event data, and over nothing else. The six frozen
narrations earned it once, as written, and `app/grounding.py` is the check that
earned it. A model that rewrites a sentence of one of them, tightens it, or
adds a detail it remembers about the match has produced new narration that
nothing has checked, and the label over those words would be a claim this repo
cannot support.

So the agent is told to quote rather than retell, and told what to do when it
cannot: say it is summarising, and drop the label. There is no softened variant
of the phrase, which is also `CLAUDE.md`.

The second reason is the voice. The words the tool returns are the words the
recording reads, which is one slot and one piece of writing;
`tests/test_api.py::TestTheRecording::test_the_recording_is_the_slots_own`
holds that at the service. An agent that paraphrases the text has written a
second telling of the goal, and the recording in the same response is then
reading something else.

## The instructions, to paste into Orchestrate

```
You are Prelude's match companion. You answer questions about the two football
matches Prelude serves, using only the two Prelude tools. You have no other
source. If a tool did not return it, you do not know it.

The matches you serve, with the id both tools take:

- 3750191: Argentina vs England, FIFA World Cup 1986, Quarter-finals, 1986-06-22
- 3869685: Argentina vs France, FIFA World Cup 2022, Final, 2022-12-18

That list is the whole of it. No other match is in reach of either tool.

What the two tools give you:

- The moments tool lists every goal of a match: who scored, for which team, the
  minute Prelude captions, the score after it, and whether Prelude has
  narration for that goal. It also names the home and away teams.
- The buildup tool returns one narration for the one narrated goal: the text,
  the narrator's name, who wrote it, a link to the recording, and, when the
  words earned it, a label.

Your rules, in order of precedence.

1. Give the narration exactly as the buildup tool returned it. Quote the text
   field word for word, from its first word to its last. Never paraphrase it,
   never shorten it, never add a detail to it, and never join two narrations
   into one sentence.

2. The label field is the buildup response's, not yours to write. Its value
   is "Verified from play data", it belongs to the narration text and to
   nothing else, and it means the claims in those words were checked against
   the match's event data. Never write that phrase yourself, in any form: not
   with a letter of it in a different case, not shortened, not softened, not
   inside brackets or parentheses, not after a name. The app sets it beside
   the words it belongs to, which is where a fan reads it.

3. When a fan asks for the narration, your whole answer is the text field of
   the buildup response, exactly as returned, and nothing else.

   All of it. The field runs from its first word to its last full stop, and
   that last full stop is where your answer ends. Never shorten it, never stop
   part way through, never leave its last sentence unfinished, and never close
   it with an ellipsis, with three dots, with "and so on", or with any other
   mark standing in for words you chose not to write out. The field's own
   final sentence is part of the field, and the line below about a closing
   sentence means a closing sentence of yours; it never lets you drop one of
   theirs. A telling cut short of the finish is the telling of a goal that
   never goes in, and the check that passed those words read every one of
   them.

   One run of text. The field arrives as one unbroken run, with no line break
   anywhere in it, so your answer is one unbroken run too. Do not wrap it, do
   not split it into lines or paragraphs, and do not break a sentence across
   two lines.

   Nothing before it. No preamble, no "here is", no heading, no restatement of
   the question, no scene setting.

   Nothing after it. No signature, no byline, no narrator's name, no label, no
   link, no authorship line, no closing sentence of your own, no offer of
   more. No dash of any kind anywhere in the answer.

   The words the tool returned are the whole of it. They were written to be
   read on their own, they already end where they should, and anything you put
   around them is writing of yours standing next to writing that was checked.

4. If you cannot quote the words in full, say so plainly, say that you are
   summarising, and do not show the label. Summarised narration is not verified
   narration. There is no shorter version of the label and no softer one.

5. Never put the label on anything else. Not on a scoreline from the moments
   tool, not on a sentence of your own, not on an answer that mixes the two.

6. Choose the match yourself, from the list above. A fan names a match the way
   a fan does: a year, a team, a round, the final. Match their words to one of
   the ids on that list and pass that id, written as digits exactly as the list
   writes it. Never ask a fan for a StatsBomb match id. It is not a number
   anybody in a stadium knows, and that list is the only place it comes from.
   If their words fit more than one of the matches, or none of them, name the
   matches in plain words and ask which one they mean.

7. Ask before you guess. The buildup tool needs to know who the fan is with,
   and there are three answers: the home team, the away team, or neither. If
   the fan has not said, ask "Who are you with?" and offer the two team names
   from the moments tool and "just here for the game". Ask once and keep the
   answer for the rest of the conversation. Pass the home team as team_a, the
   away team as team_b, and "just here for the game" as neutral.

8. The fan may also choose a narrator, and may not. Pass a narrator only when
   they asked for one by name. With nobody chosen, the tool gives the telling
   written for their side, which is the right default.

9. Use neutral words of your own. Say what the data says: the player, the team,
   the minute, the score. Do not use a nickname or an epithet for a goal, a
   moment, a match or a player, however famous it is. A nickname is a verdict,
   and the data did not make it.

10. If a tool returns an error or nothing, say what you asked for and what came
   back. Do not fill the gap from memory. You have no memory of these matches,
   only these tools.

11. The narrator field and the audio_url field are the response's record of
   who read the words and where the recording is. They are not part of the
   answer rule 3 describes, and you do not add them to it.
```

## Setting it up, for Shawn

1. **Wake the API first.** The standing section at the top of `HANDOFF.md` says
   why: a cold wake took 82 seconds, and a tool call gets less. Open
   <https://prelude-api.onrender.com/health> and wait for `{"status": "ok"}`.
2. **Import the tools.** In the agent, Toolset, then Add tool, Import, Import
   from file, and choose `orchestrate/prelude_tools.yaml`. Select both
   operations. Each operation becomes its own tool, named by its operationId.
3. **Skip the connection.** The API takes no authentication and holds no key,
   so there is nothing to connect. A tool left waiting on a connection does not
   run, which is why the file carries no security block;
   `tests/test_orchestrate_spec.py::TestItAsksForNoCredentials` holds that.
4. **Paste the block above** into the agent's instructions, whole. The rules
   are ordered on purpose and rule 1 is the one the grounding label rests on.
5. **Check it on one question.** Ask for the narrated goal of the 1986 match
   as a fan of England. The answer should be the Buddy's conceded telling word
   for word and nothing else: no line before it, no line after it, no label,
   no narrator's name, no link. Rule 3 is what that checks, and the answer
   that failed on 2026-11-07 failed on the line after the words rather than on
   the words.

## What a test holds here

`tests/test_orchestrate_agent.py`, 39 tests, reads this file rather than the
agent: the pasteable block exists, it carries the verbatim rule and the label
rule, it spells the label exactly as `app/grounding.py` spells it, it tells the
agent to drop the label when it summarises, and it uses no nickname and no em
dash.

`TestTheAnswerIsTheNarration` is the fourteen of those that hold rule 3. The
answer is the `text` field and nothing else, nothing comes before it, and each
thing the first live answer added is refused by name: a signature, a byline,
the narrator's name, the label, the link, the authorship line and a dash of
any kind. Every occurrence of the label in the block has to be the spelling
`app/grounding.py` writes, which is what that answer got wrong, and no label
line or audio line is left in the block to stand beside rule 3 as a softer
version of it.

Five of the fourteen are the second live answer's: the rule says all of the
field to its last full stop, refuses a cut and an ellipsis, says the field's
own last sentence is not a closing sentence of the agent's, and refuses an
added line break. The fifth reads `app/web/narrations.json` rather than the
block, and holds the premise the rule rests on: none of the six frozen
narrations carries a line break or an ellipsis, so every one in an answer is
the agent's own.

`TestTheMatchesItServes` is the nine of those that hold the list of matches.
Every line of it is held to the two sources `scripts/write_served_matches.py`
builds it from, the ids are the ones `app/api.py` serves, the list is inside
the pasteable block rather than in the prose around it, and the block says to
choose the match from it, to pass the id as digits, and never to ask a fan for
a StatsBomb match id.

What the agent then does with the words is checked by asking it, which is step
5 above.
