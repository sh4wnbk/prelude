# Verification

What this repo claims, and what checks each claim. Every statement below names
the file that does the checking and a test that holds it, or says that nothing
does.

The rule the whole of it serves is in `CLAUDE.md`: report executed evidence,
meaning the command run and its real output, not a claim that something works.
`docs/HARNESS.md` is how to run these things; this is what they decide.

## Six surfaces, six checkers

Claims live in six places in this repo, and each has something that reads it
back against the data or the code.

| What is claimed | Where the claim sits | What checks it |
| --------------- | -------------------- | -------------- |
| narration says only what the records say | generated text | `app/grounding.py` |
| every name, minute, score and count on a screen | `app/web/matches.json` and the screens | `scripts/check_match_copy.py` |
| no banned copy, and the grounding label only over narration | the screens | `scripts/scan_copy.py` |
| the docs describe code that exists | `README.md`, `HANDOFF.md`, `docs/` | `scripts/check_docs.py` |
| the shot and goal counts in the data report | `docs/data_check.md` | `scripts/data_check.py`, which generates it |
| every word the app speaks has one pronunciation, or a reviewed reason | `app/pronunciation.py` | `scripts/check_vocabulary.py`, and `tests/test_vocabulary.py` in the suite |

A seventh is narrower and worth naming: `scripts/make_tickets.py` writes a QR code
and then reads it back off the PNG with a real decoder, comparing byte for byte,
because writing an image is not evidence that it holds the payload. It exits
non-zero on a mismatch or a code that will not decode.

## Verifying narration

`app/grounding.py` decides whether a narration may carry "Verified from play
data". `docs/VOICE.md` is the voice; this is the checking.

**It has two readings, and the narration's own shape picks one.** A narration
carrying a citation tag is read against the numbered facts each sentence cited,
which `app/narration_prompt.py` builds by code out of the records. A narration
carrying none is a goal call, which is what the framework in `docs/VOICE.md`
asks for, and `app/narration_grammar.py` reads the sentence itself: the names,
the pronoun that means the player with the ball, the chains, "past X", which
way the ball went, and the recorded fields a goal call says out loud. Both readings refuse the same
nicknames, epithets, outcome claims, dashes and markup, and both hold the same
rule about where an exclamation mark may stand.

**A goal call has two layers, and the check reads one of them.** The play
(who, what, where, how it finished) is traced to the records, claim by claim.
The reaction (the narrator feeling the moment: "Oh, lovely!", "What a
finish!", "Ah, no.") is the narrator's own voice: it may stand once, at the
goal, after the play has landed the finish, and nothing in it is traced to a
record, because a sentence of at most `REACTION_WORDS` words with no name, no
pronoun, no digit and no claim about a recorded field points at nothing the
records could refuse. Everything else still applies to it: the banned
verdicts, the force words, "you", the clock, the digits, the tense and who may
cheer. "Verified from play data" means every event happened as told, and the
reaction tells no event.

One test per kind of claim, and one per kind of mistake. The cited reading:

| Claim kind | Refused when | Test |
| ---------- | ------------ | ---- |
| `name` | the player or team is in no cited fact | `tests/test_grounding.py::TestNotGrounded::test_an_invented_player` |
| `name` | the player is in the passage but in no cited fact | `tests/test_grounding.py::TestNotGrounded::test_a_name_in_the_buildup_but_not_in_the_cited_facts` |
| `name` | a real player was not in this passage at all | `tests/test_grounding.py::TestNotGrounded::test_a_real_player_who_is_not_in_this_passage` |
| `name` | a demonym names a team that is not playing | `tests/test_grounding.py::TestNotGrounded::test_a_demonym_for_a_team_that_is_not_playing` |
| `action` | the event type is in no cited fact | `tests/test_grounding.py::TestNotGrounded::test_an_action_that_is_in_the_buildup_but_not_in_the_cited_facts` |
| `action` | the event type is not in the buildup at all | `tests/test_grounding.py::TestNotGrounded::test_an_action_that_is_not_in_the_buildup` |
| `pairing` | a name and an action meet in no single cited fact | `tests/test_grounding.py::TestMisdescription::test_a_defender_who_pressured_was_not_dribbled_past` |
| `clock` | the clock belongs to a fact the sentence did not cite | `tests/test_grounding.py::TestNotGrounded::test_a_clock_from_a_fact_the_sentence_did_not_cite` |
| `number` | a bare digit is neither a cited minute nor the goal's second | `tests/test_grounding.py::TestNotGrounded::test_a_number_that_is_not_a_minute` |
| `shot_type` | the goal is called a set piece it was not | `tests/test_grounding.py::TestNotGrounded::test_a_goal_turned_into_a_set_piece` |
| `body_part` | the body part is not the recorded one | `tests/test_grounding.py::TestNotGrounded::test_the_wrong_body_part` |
| `tense` | a present-tense verb, in a passage that already happened | `tests/test_grounding.py::TestTense::test_a_present_tense_sentence_is_flagged` |
| `tense` | the tense sits in an auxiliary, "is dribbled past" | `tests/test_grounding.py::TestTense::test_an_auxiliary_carries_the_tense_too` |
| `ending` | the last sentence does not cite the goal's shot | `tests/test_grounding.py::TestEnding::test_a_last_sentence_that_does_not_cite_the_shot_is_refused` |
| `untagged` | the sentence cites no fact | `tests/test_grounding.py::TestNotGrounded::test_a_sentence_that_cites_nothing` |
| `citation` | the cited number is not one of the facts | `tests/test_grounding.py::TestNotGrounded::test_a_citation_that_is_not_one_of_the_facts` |
| `first person` | "we", "our" or "us" from a voice that is not partisan | `tests/test_grounding.py::TestThePartisanVoice::test_our_from_the_caller_fails` |
| `side` | a partisan "we" over facts recording the other team | `tests/test_grounding.py::TestThePartisanVoice::test_the_same_sentence_citing_the_other_team_fails` |
| `unverifiable` | the narration asserts nothing checkable | `tests/test_grounding.py::TestNotGrounded::test_narration_that_asserts_nothing_checkable` |
| banned | a verdict nickname | `tests/test_grounding.py::TestNotGrounded::test_a_verdict_nickname` |
| banned | an editorial epithet | `tests/test_grounding.py::TestNotGrounded::test_an_editorial_epithet` |
| banned | a claim about the result, "won the match" | `tests/test_grounding.py::TestTense::test_won_the_match_is_refused` |
| banned | a line addressed to the fan | `tests/test_grounding.py::TestEnding::test_a_closing_line_addressed_to_the_fan_is_refused` |
| banned | an em dash | `tests/test_grounding.py::TestNotGrounded::test_an_em_dash` |
| banned | markup, which is any angle bracket | `tests/test_grounding.py::TestNotGrounded::test_markup` |

And the goal-call reading, whose tests are in
`tests/test_narration_grammar.py` and `tests/test_reference_narrations.py`:

| Claim kind | Refused when | Test |
| ---------- | ------------ | ---- |
| `name` | the name fits no player the passage records | `tests/test_narration_grammar.py::TestTheNamesAGoalCallMaySay::test_an_invented_name_is_reported_rather_than_skipped` |
| `name` | the name fits two players, so it names neither | `tests/test_narration_grammar.py::TestTheNamesAGoalCallMaySay::test_a_forename_two_players_share_fits_neither` |
| `chain` | no pass from the first player to the second is recorded | `tests/test_narration_grammar.py::TestTheChain::test_a_pass_the_records_do_not_hold_is_refused` |
| `chain` | "set up" over a pass that is not the recorded assist | `tests/test_narration_grammar.py::TestTheChain::test_set_up_has_to_be_the_recorded_assist` |
| `chain` | "a long ball" over a pass under `LONG_PASS_YARDS` | `tests/test_narration_grammar.py::TestTheChain::test_a_pass_that_is_not_long_enough_is_refused_as_a_long_ball` |
| `past` | "past X" where no dribble past X is recorded | `tests/test_narration_grammar.py::TestPastAndAround::test_a_player_who_was_only_pressed_past_is_refused` |
| `action` | "picked it up" where no record puts the ball at their feet | `tests/test_narration_grammar.py::TestTheRecordedFieldsSaidOutLoud::test_picked_it_up_is_any_recorded_touch` |
| `action` | "under pressure" where no record of theirs carries it | `tests/test_narration_grammar.py::TestTheRecordedFieldsSaidOutLoud::test_under_pressure_is_refused_where_nothing_records_it` |
| `action` | "under pressure from X" where no `Pressure` record of X's is in the passage | `tests/test_narration_grammar.py::TestWhoUnderPressureIsAbout::test_a_player_who_never_pressed_is_refused` |
| `position` | "in his own half" or "in the box" over a coordinate that is not | `tests/test_narration_grammar.py::TestWhereOnThePitch::test_a_pass_the_player_did_not_follow_is_not_his_position` |
| `straight` | a run called straight that strays from the line | `tests/test_narration_grammar.py::TestTheShapeOfTheRun::test_the_claim_is_refused_over_the_1986_carries` |
| `direction` | "forward" or "back" against the change in x on a pass or a carry | `tests/test_narration_grammar.py::TestWhichWayTheBallWent::test_the_same_pass_called_back_is_refused` |
| `run` | "drove", "ran" or "burst" over a carry under `RUN_YARDS` | `tests/test_narration_grammar.py::TestARunHasYardsInIt::test_a_carry_under_a_yard_is_not_a_run` |
| `carry_delivery` | a carry asked to hand the ball to another player | `tests/test_narration_grammar.py::TestACarryDoesNotDeliverTheBall::test_a_carry_asked_to_deliver_is_refused` |
| `shot_type` | "first time" over a shot not recorded as struck first time | `tests/test_narration_grammar.py::TestTheRecordedFieldsSaidOutLoud::test_first_time_is_the_2022_shot_and_not_the_1986_one` |
| `shot_type` | "first-time" with a hyphen, over the same shot: a hyphen is the space it stands in for | `tests/test_narration_grammar.py::TestAHyphenIsTheSameClaimAsASpace::test_the_same_words_over_the_1986_shot_are_refused` |
| `body_part` | the body part is not the goal's | `tests/test_narration_grammar.py::TestTheRecordedFieldsSaidOutLoud::test_the_body_part_is_the_goals` |
| `duration` | a span the timestamps do not give | `tests/test_narration_grammar.py::TestTheRecordedFieldsSaidOutLoud::test_a_duration_the_passage_did_not_take` |
| `clock` | any clock at all, which a goal call does not carry | `tests/test_reference_narrations.py::TestNoClockReachesTheNarration` |
| `number` | any digit at all, for the same reason | `tests/test_reference_narrations.py::TestNoClockReachesTheNarration` |
| `ending` | nothing in the narration is a claim the goal's own record holds | `tests/test_reference_narrations.py::TestTheFinishMayBeSaidPlainly::test_a_narration_that_lands_on_nothing_is_still_refused` |
| `side` | a partisan "we" over a clause recording the other team | `tests/test_reference_narrations.py::TestTheFirstPersonNeedsTheListenersOwnPlay` |
| `cheer` | an exclamation mark where the listener would not cheer | `tests/test_reference_narrations.py::TestWhereAnExclamationMarkMayStand` |
| `reaction` | a reaction before the finish, or a second one after it | `tests/test_reference_narrations.py::TestTheReactionLayer::test_a_reaction_before_the_finish_is_refused` |
| banned | force the record does not hold, "smashed it home" | `tests/test_reference_narrations.py::TestTheForceIsNotInTheRecord` |
| banned | a verdict about history, "the best of all time" | `tests/test_reference_narrations.py::TestAVerdictAboutHistory` |

**The verdict is whole-narration.** `CLAUDE.md` gives no partial credit, so a
narration passes or fails together; `app/grounding.py` returns every failing
claim rather than the first, which both a retry and the failure log need
(`tests/test_grounding.py::TestNotGrounded::test_every_failing_claim_is_reported_not_just_the_first`),
and each failure says which sentence it was in
(`tests/test_grounding.py::TestNotGrounded::test_a_failure_says_which_sentence_it_was_in`).

**A false positive is the expensive kind here,** because the narration is thrown
away whole: a wrongly refused attempt costs good copy and makes a model look
worse than it is. So the tests that accept narration carry as much weight as the
tests that refuse it, and several of them exist because a live run produced
exactly that failure:

| Narration that has to be accepted | Test |
| --------------------------------- | ---- |
| a sentence opening on an ordinary word, such as "Finally" | `tests/test_grounding.py::TestGrounded::test_a_sentence_can_start_with_an_ordinary_word` |
| a possessive, "Argentina's Maradona" | `tests/test_grounding.py::TestGrounded::test_a_possessive_names_the_same_team` |
| an accent spelled plainly, "Hector" for "Héctor" | `tests/test_grounding.py::TestGrounded::test_an_accented_name_spelled_plainly` |
| a clock quoted off the fact the sentence cites | `tests/test_grounding.py::TestGrounded::test_a_clock_quoted_from_the_fact_it_cites` |
| one sentence drawing on several facts | `tests/test_grounding.py::TestGrounded::test_one_sentence_may_span_several_facts` |
| the tag written after the full stop, as the live model wrote it | `tests/test_grounding.py::TestGrounded::test_tags_written_after_the_full_stops` |
| a demonym over a fact recorded against that team | `tests/test_grounding.py::TestGrounded::test_a_demonym_grounds_against_its_team` |
| "won a foul", which is a recorded `Foul Won` event | `tests/test_grounding.py::TestTense::test_won_a_foul_is_allowed` |
| a past participle the facts use, "was dribbled past" | `tests/test_grounding.py::TestTense::test_the_past_participle_on_its_own_is_fine` |
| a whole narration in the past tense, ending on the goal | `tests/test_grounding.py::TestTense::test_a_past_tense_narration_passes` |

**The fallback is checked like anything else.** It is assembled from the facts
with no model, so it is grounded by construction, and
`tests/test_grounding.py::TestGrounded::test_every_fallback_narration_is_grounded`
runs the check over it for all nine goals in both matches rather than trusting
that. The pipeline checks it again at runtime
(`tests/test_narration.py::TestFallback::test_the_fallback_is_checked_like_any_other_narration`),
and if it ever failed, `app/narration.py` raises instead of returning something
unlabelled
(`tests/test_narration.py::TestFallback::test_an_ungroundable_fallback_raises_rather_than_voicing_it`).

**Nothing ungrounded is returned.** Whatever the model does,
`tests/test_narration.py::TestFallback::test_nothing_ungrounded_is_ever_returned`
re-checks the text that comes back, over four different model behaviours.

## Verifying the label

The phrase is written once, as `GROUNDING_LABEL` in `app/grounding.py`, so
nothing spells it differently or softens it
(`tests/test_narration.py::TestFirstAttemptPasses::test_it_is_labelled`). It
sits with the check that earns it: `app/narration.py` imports it from there to
label what passed, and the hosted service in `app/api.py` imports it to put it
beside a frozen narration, so neither spells it again
(`tests/test_api.py::TestTheLabel::test_the_label_is_the_one_the_check_writes`).

On the screens it is a placement rule rather than a string, which a regex sweep
cannot see: the words are correct and the position is not. So
`scripts/scan_copy.py` parses the markup into a parent-linked tree and asks what
each label is actually sitting over, counting it grounded only when it shares a
card with a narration field. Its own comment records why: the label once sat on
the Live standby pipeline card, above rows reporting whether a trigger and the
narration were switched on, which is app state and not a claim read from the
feed. Nothing tests `scripts/scan_copy.py` itself; it is a gate, and its
evidence is its output.

## Verifying the screens

`scripts/check_match_copy.py` is handed the values the copy claims and looks each
one up in `data/raw/`: every name, minute, score, count, body part, play pattern
and assist. It does not search the data for goals or buildups, because finding
moments is the EventFeed module's job.

Its last run checked both matches and reported that the quoted 1986 hero names
(Maradona, Beardsley, Butcher, Fenwick, Shilton) are all recorded in possession
117, and that the index scores reconcile with the feed. `HANDOFF.md` carries
that output.

The seats on the ticket screens are not checked against the data, and that is
deliberate: `scripts/make_tickets.py` records why, which is that a seat is the
fan's own ticket rather than a claim about the match, so it carries no grounding
obligation.

## Verifying the docs

`scripts/check_docs.py` checks the quotable claims and not the prose. Eight
checks, each one there because a claim went stale once:

| Check | What it decides |
| ----- | --------------- |
| `check_design_citations` | a class string quoted in `docs/DESIGN.md` is in the screen it cites |
| `check_design_landmarks` | the header and nav bullets cite all four screens, and are right about each |
| `check_quoted_pytest_result` | the `pytest -q` output quoted in `docs/bob_brief.md` is still what pytest prints |
| `check_test_count` | a count of tests in a doc matches what pytest collects for the target it names |
| `check_cited_tests` | every test, class or node id a doc cites is one pytest collects |
| `check_referenced_paths` | a path in backticks exists, or is on the deliberately absent list |
| `check_quoted_screen_copy` | screen copy quoted in `HANDOFF.md` is in the screen it names, and copy marked `removed` is in none |
| `check_no_em_dashes` | no doc holds an em dash or an en dash |

`check_design_citations` used to check file and line. A line number is correct
when written and wrong after the next markup change, which happened three times,
and once a repair pointed a citation at the wrong element without anything
noticing. A class string travels with the element it names, so the only way to
break it now is to change the markup the doc describes, which is exactly when
the doc should be updated. `scripts/check_docs.py` carries that reasoning in
the function's own docstring.

`check_cited_tests` is the newest and is what keeps this document honest: every
node id in the tables above is checked against a live `pytest --collect-only`
run, so a renamed test breaks the gate instead of leaving a citation that points
nowhere. It accepts the three forms pytest addresses, a file, a class in a file
and one test, and it also checks a class or test named on its own where the
sentence around it makes the file clear.

Nothing tests `scripts/check_docs.py` itself. It is a gate: its evidence is the
count it prints and its exit code.

## What is not verified

- **Direction in a narration.** The check reads a sentence against the facts it
  cited and not its grammar, so "Maradona passed to Enrique" and "Enrique passed
  to Maradona" cite the same facts and both pass. `docs/VOICE.md` works through
  this and the rest of what pairing cannot decide.
- **Tense, beyond a list of verbs.** `PRESENT_TENSE` in `app/grounding.py`
  covers the verbs the facts and the narration use, and
  `tests/test_grounding.py::TestTense::test_the_present_tense_of_every_action_word_is_refused`
  holds every entry in it. A verb outside that table carries no tense as far as
  the check is concerned.
- **What a closing line means.** The `ending` rule holds where a narration
  stops, not what its last sentence says, and a closer can cite the goal's fact
  as easily as the goal sentence can. The second person is what catches one in
  practice; a closer that avoids it and asserts nothing checkable is caught by
  nothing, which
  `tests/test_grounding.py::TestEnding::test_what_the_ending_rule_alone_cannot_catch`
  records.
- **How much a narration says.** A single grounded sentence passes.
  `app/grounding.py` refuses narration that asserts nothing checkable, not
  narration that asserts too little, and nothing enforces the sentence count the
  prompt asks for. One live run returned exactly one sentence; `HANDOFF.md`
  records it.
- **Verbs that are not claims.** `ACTION_CLAIMS` in `app/grounding.py` is
  deliberately narrow and grows from live failures, so a verb outside it is not
  checked against anything.
  `tests/test_grounding.py::TestHelpers::test_every_action_claim_names_event_types_a_fact_can_say`
  keeps the table itself honest, which is a different thing from covering every
  verb.
- **The pass rate.** Nothing runs the pipeline over the nine goals and writes
  down how often a first attempt is grounded.
- **Prose, in any doc.** `scripts/check_docs.py` checks quotable claims. A
  sentence that is simply wrong about why something was built passes every gate
  in this repo.
- **The gates themselves, by anything automatic.** No workflow runs them; see
  `docs/HARNESS.md`.
