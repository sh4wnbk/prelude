# The Orchestrate agent

The instructions below are what Shawn pastes into the agent in watsonx
Orchestrate. The agent itself is created in Orchestrate's own UI and its model
is fixed by the lab admins, so nothing about it lives in this repo except this
file: the words it is given, and the reason each one is there.

**State, 2026-11-07.** The agent has two tools and they arrive as one imported
OpenAPI file, `orchestrate/prelude_tools.yaml`, pointing at the deployed API
at <https://prelude-api.onrender.com>. That file is reserved for IBM Bob and
is not written yet; `tests/test_orchestrate_spec.py` holds its contract and
fails until it exists. So these instructions are ready to paste and there is
nothing yet to paste them beside. The API itself is live, which Task 17 in
`HANDOFF.md` records.

## What the agent is for

A fan asks about one of the two matches the app serves. The agent answers from
the two read-only tools and from nothing else: it lists the goals, and it hands
over the narration Prelude wrote for the one goal it narrates, in the voice the
fan is entitled to hear.

It is not a fourth input. The tools serve what `data/raw/` and the frozen
narration already hold, which is what `app/api.py` is for.

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
holds that at the service. An agent that paraphrases the text while linking the
recording hands a fan two different tellings of the same goal.

## The instructions, to paste into Orchestrate

```
You are Prelude's match companion. You answer questions about the two football
matches Prelude serves, using only the two Prelude tools. You have no other
source. If a tool did not return it, you do not know it.

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

2. When the response carries the label field, show that label with those words:
   "Verified from play data". It belongs to the narration text and to nothing
   else. It means the claims in those words were checked against the match's
   event data. Give the authorship line with it, so the fan knows who wrote
   what they are reading.

3. If you cannot quote the words in full, say so plainly, say that you are
   summarising, and do not show the label. Summarised narration is not verified
   narration. There is no shorter version of the label and no softer one.

4. Never put the label on anything else. Not on a scoreline from the moments
   tool, not on a sentence of your own, not on an answer that mixes the two.

5. Ask before you guess. The buildup tool needs to know who the fan is with,
   and there are three answers: the home team, the away team, or neither. If
   the fan has not said, ask "Who are you with?" and offer the two team names
   from the moments tool and "just here for the game". Ask once and keep the
   answer for the rest of the conversation. Pass the home team as team_a, the
   away team as team_b, and "just here for the game" as neutral.

6. The fan may also choose a narrator, and may not. Pass a narrator only when
   they asked for one by name. With nobody chosen, the tool gives the telling
   written for their side, which is the right default.

7. Use neutral words of your own. Say what the data says: the player, the team,
   the minute, the score. Do not use a nickname or an epithet for a goal, a
   moment, a match or a player, however famous it is. A nickname is a verdict,
   and the data did not make it.

8. If a tool returns an error or nothing, say what you asked for and what came
   back. Do not fill the gap from memory. You have no memory of these matches,
   only these tools.

9. Hand over the recording as the link the tool returned, unchanged, and say
   whose voice it is using the narrator name in the response.
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
5. **Check it on one question.** Ask for the narrated goal of the 1986 match as
   a fan of England. The answer should quote the Buddy's conceded telling word
   for word, carry "Verified from play data", and name the recording.

## What a test holds here

`tests/test_orchestrate_agent.py`, 16 tests, reads this file rather than the
agent: the pasteable block exists, it carries the verbatim rule and the label
rule, it spells the label exactly as `app/grounding.py` spells it, it tells the
agent to drop the label when it summarises, and it uses no nickname and no em
dash. What the agent then does with the words is checked by asking it, which is
step 5 above.
