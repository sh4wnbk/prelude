# The label, and the two layers under it

The label is **"Verified from play data"**, written once in `app/narration.py`
so nothing spells it differently or softens it. There is no partial credit and
no shortened variant: it goes over narration that passed the check in
`app/grounding.py`, and over nothing else.

What it claims is that **every event in the narration happened as told**. A
narration has two layers, and that sentence is exactly true of both.

**The play** is who, what, where and how it finished, and it is checked claim
by claim against `data/raw/`: the names, the passes from one named player to
another, the defenders gone past, the positions on the pitch, which way the
ball went, how far a carry ran, the body part the goal was scored with.
Nothing in it is inferred, recalled or softened, and a narration with one
unsupported claim in it is refused whole.

**The reaction** is the narrator feeling the moment, in at most eight words:
"Oh, lovely!", "What a finish!", and for the side that conceded "Ah, no.". It
stands once, at the goal, with nothing after it, and it is not checked against
the data, because it asserts nothing about the data: no player, no team, no
pronoun, no number, nothing about where the ball was or what anybody did. It
is the narrator's own voice, and it leaves the label's claim untouched. It is
still held to everything else: no verdict about where the goal stands among
other goals, no words for how hard the ball was struck, and never "you".

## Who wrote the six, and who verified them

**The six hero narrations were drafted with an AI assistant, edited by Shawn,
and verified by Prelude's grounding check against StatsBomb play data.** There
is one per listener per hero goal, in `scripts/authored_narrations.py` and
frozen into `app/web/narrations.json`, which records that same sentence beside
each of them: drafted with an AI assistant, edited by Shawn, verified by the
grounding check. The draft and the edit are the team, and the team is not the
watsonx pipeline below. The moment
card shows the one for the listener's own key while `scripts/tts_hero.py`
speaks it. The check reads them exactly as it reads a model's: as a goal
call, in the persona and for the listening side the slot is written for, claim
by claim against `data/raw/`. The label means what it
says about them, because the label is about whether the claims trace to the
records and not about who put the words in that order.

**The model pipeline is real and its runs are in
[`docs/narration_runs/`](narration_runs).** `openai/gpt-oss-120b` on
watsonx writes narrations from the story beats through
`app/goal_call_prompt.py`, the same check reads them, and
`scripts/narrator_candidates.py` is the run that produces candidates. Those
runs are why the six were written rather than taken from the pipeline: at
`reasoning_effort` low the model would not place the move on the pitch, so the
candidates gave a listener nowhere to stand. The reports in that directory are what each run produced,
including the one per-goal narration a model wrote that is still frozen
beside the six and still re-checked.

[`docs/VOICE.md`](VOICE.md) has the two layers in full, the eight
reference narrations that are the standard for the play, and what the check
still cannot decide. [`docs/VERIFICATION.md`](VERIFICATION.md) has one
test per kind of claim and one per kind of mistake.
