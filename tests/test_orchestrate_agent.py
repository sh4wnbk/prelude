r"""The agent instructions, held to the two rules that make them worth pasting.

`docs/orchestrate_agent.md` carries one fenced block, and that block is what
Shawn pastes into the agent in watsonx Orchestrate. The agent is created in
Orchestrate's UI and its model is fixed by the lab admins, so this file is the
only part of it this repo can hold.

Two rules are the reason the file exists.

**The verbatim rule.** The agent quotes the narration the buildup tool
returned, word for word, and does not paraphrase, shorten or add to it. A
rewritten sentence is new narration that nothing has checked.

**The label rule.** "Verified from play data" goes over those exact words and
over nothing else, and an agent that summarises says so and drops the label.
`CLAUDE.md` allows no partial credit and no softened variant, so an agent that
could keep the phrase over its own retelling would be the one way this repo's
central claim could be broken by a machine nobody here wrote.

The label is read from `app/grounding.py` rather than spelled here, which is
the same thing `tests/test_api.py` does for the endpoint.

What the agent does with the words is not checkable from the repo. Step 5 of
the setup list in the doc is how that is checked, by asking it.
"""

import re
from pathlib import Path

import pytest

from app.api import app
from app.grounding import GROUNDING_LABEL

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "orchestrate_agent.md"

FENCE = re.compile(r"^```[a-z]*\n(.*?)^```", re.M | re.S)

#: Nicknames the app's copy already refuses, from the "verdict nickname" rows
#: of `BANNED` in `scripts/scan_copy.py`. The instructions are not screen copy,
#: so that gate does not read them, and a nickname in the words that teach an
#: agent what to say would travel further than one on a screen.
VERDICT_NICKNAMES = ("goal of the century", "hand of god", "controvers")


def doc_text() -> str:
    if not DOC.is_file():
        pytest.fail(f"{DOC.relative_to(ROOT).as_posix()} does not exist")
    return DOC.read_text(encoding="utf-8")


def instructions() -> str:
    """The one fenced block: the words that go into Orchestrate."""
    blocks = FENCE.findall(doc_text())
    assert len(blocks) == 1, f"expected one fenced block, found {len(blocks)}"
    return blocks[0]


def flat() -> str:
    """The block as one lower-case line.

    Every phrase below is checked against this rather than against the raw
    text, because where a sentence wraps is a matter of the margin and a
    rewrap is not a change to the rule.
    """
    return " ".join(instructions().split()).lower()


class TestTheBlockToPaste:
    def test_the_doc_is_in_the_repo(self):
        assert DOC.is_file()

    def test_there_is_exactly_one_block_to_paste(self):
        """Two blocks is an agent half configured, because only one of them
        gets pasted."""
        assert len(FENCE.findall(doc_text())) == 1

    def test_the_block_is_the_whole_brief_and_not_a_fragment(self):
        assert len(instructions().split()) >= 250

    def test_it_names_both_tools(self):
        block = flat()
        assert "moments tool" in block
        assert "buildup tool" in block


class TestTheVerbatimRule:
    def test_it_says_to_quote_word_for_word(self):
        block = flat()
        assert "word for word" in block
        assert "exactly as the buildup tool returned it" in block

    def test_it_forbids_paraphrasing_shortening_and_adding(self):
        block = flat()
        assert "never paraphrase" in block
        assert "never shorten" in block
        assert "never add" in block

    def test_the_verbatim_rule_is_the_first_rule(self):
        """The rules are ordered, and the one the label rests on is first.
        Written as `1.` in the block, so this reads the numbered list."""
        numbered = re.findall(r"^\s*(\d)\.\s+(.*)$", instructions(), re.M)
        assert numbered, "the block has no numbered rules"
        first = next(body for number, body in numbered if number == "1")
        assert "give the narration exactly as the buildup tool" in first.lower()


class TestTheLabelRule:
    def test_it_spells_the_label_the_way_the_check_does(self):
        """Read from `app/grounding.py`, so a change to the phrase fails here
        rather than leaving an agent quoting the old one."""
        assert GROUNDING_LABEL in instructions()

    def test_the_label_is_shown_only_when_the_response_carries_it(self):
        block = flat()
        assert "label field" in block
        assert "nothing else" in block

    def test_a_summary_says_so_and_drops_the_label(self):
        block = flat()
        assert "summarising" in block
        assert "do not show the label" in block

    def test_there_is_no_softened_variant_of_the_label(self):
        """`CLAUDE.md`: no partial credit and no softened variant. An agent
        told only "do not paraphrase" would still invent "partly verified"."""
        assert "no shorter version of the label" in flat()


class TestWhatItAsksAndWhatItWillNotSay:
    def test_it_asks_who_the_fan_is_with(self):
        assert "who are you with?" in flat()
        assert "ask once" in flat()

    def test_the_three_answers_are_the_ones_the_api_takes(self):
        """From the `Literal` in `app/api.py`, through `app.openapi()`, so an
        agent is never taught a fourth answer or a renamed one."""
        enum = next(
            parameter["schema"]["enum"]
            for parameter in app.openapi()["paths"]["/buildup"]["get"]["parameters"]
            if parameter["name"] == "listener"
        )
        block = instructions()
        for value in enum:
            assert value in block, value

    def test_it_forbids_verdict_nicknames(self):
        block = flat()
        assert "nickname" in block
        assert "do not use a nickname" in block

    def test_the_file_uses_no_verdict_nickname_itself(self):
        """Including in the explanation around the block. Naming the nickname
        in order to forbid it would put it in the agent's context, which is
        the one place it must not be."""
        text = doc_text().lower()
        for nickname in VERDICT_NICKNAMES:
            assert nickname not in text, nickname

    def test_it_carries_no_em_dash_and_no_stand_in_for_one(self):
        """`CLAUDE.md`'s rule, and this file is doc copy and pasted copy at
        once. `scripts/check_docs.py` reads the em dash across the docs
        register; the two-hyphen stand-in is checked here."""
        text = doc_text()
        assert "—" not in text
        assert "--" not in text
