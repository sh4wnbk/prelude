"""How a word is said, which is not what a word says.

One table, word to IPA, and one function that marks those words up for the
speech service. It exists because "lead" is two words in English: the metal is
`lɛd` and the thing a team takes is `liːd`. The header says "take the lead" on
two of the five transitions in `app/orchestrator_contract.py` and "extend the
lead" on a third, so this is not a hypothetical.

**And it is not hypothetical in the other direction either: the entry is
needed.** Both hero headers say "Argentina extend the lead", and Shawn heard
that read as "led" without the entry and "leed" with it. `docs/VOICE.md`
records that, and records the measurement that got it wrong first: the probe
spoke "Argentina take the lead", which these voices say correctly unaided, and
reading that as a verdict on the word rather than on the sentence is how the
entry nearly came out. A pronunciation is a property of a word in a context.

**It reaches the speech request and nothing else.** That is the whole design
constraint, and it is worth spelling out because the alternative is so easy to
reach for. A pronunciation is markup: `<phoneme alphabet="ipa" ph="liːd">`.
Were it applied any earlier, the markup would travel with the text:

| Reader | What it would see | Why that is wrong |
| ------ | ----------------- | ----------------- |
| the screen | `take the <phoneme ...>lead</phoneme>.` | a fan reading tags |
| `app/grounding.py` | the same | a name or a number inside a tag is a name the check cannot match, so a grounded narration would be refused for being pronounceable |
| a model | the same | nothing says a pronunciation to a model |

So no module in `app/` imports this one except the speech backend, and
`tests/test_pronunciation.py::TestNothingElseAppliesIt` is what holds that:
the header the screen shows and the narration the check reads are the same
strings they were before this file existed.

**It says the same words.** `spoken_text` strips the markup back off, and
`for_speech` is only ever a pronunciation: a round trip returns the input
exactly, which is
`tests/test_pronunciation.py::TestItSaysTheSameWords`.
A table entry that changed a word rather than its pronunciation would fail
that test, which is the point of having it.

**Text with no listed word comes back untouched.** Not merely equivalent:
identical, the same string. Every tag costs billable characters, roughly 40 of
them each time on a plan that charges by the character, and the escaping that
SSML needs is only needed once there is markup to escape. So the common case
sends exactly what the screen shows and pays nothing for the feature.

**Only the words in the table are marked.** This is a table and not a
pronunciation engine: a word is here because somebody heard the service say it
wrong. `lead` is the one entry, and
`tests/test_pronunciation.py::TestTheTable` holds the shape the next entry has
to fit.

Standard library only, like the rest of `app/`.
"""

import re
from typing import Mapping

#: Word to IPA. Lower case keys; the match is case insensitive and the word
#: keeps the case it had, because the text inside a `<phoneme>` element is
#: what a client that cannot speak it falls back to showing or saying.
#:
#: `lead` is the first entry and the reason this file exists: `liːd`, the lead
#: a team takes, not `lɛd`, the metal. The header says "take the lead" and
#: "extend the lead", and it is the second of those that needs this: Shawn
#: heard "extend the lead" read as "led" without the entry.
PRONUNCIATIONS: Mapping[str, str] = {
    "lead": "liːd",
}

#: IBM supports `<phoneme>` on every voice, with IPA as one of its two
#: alphabets. This is the element as the service documents it.
PHONEME = '<phoneme alphabet="ipa" ph="{ipa}">{word}</phoneme>'

#: The three characters that cannot appear raw in markup. Order matters on the
#: way out and in reverse on the way back, so `&amp;lt;` survives a round trip
#: rather than becoming `<`.
ESCAPES = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"))

#: The listed words, longest first, so a table holding both a word and a
#: phrase containing it marks the phrase.
_WORDS = re.compile(
    r"\b(" + "|".join(
        re.escape(word) for word in sorted(PRONUNCIATIONS, key=len, reverse=True)
    ) + r")\b",
    re.IGNORECASE,
)

#: A marked word, for reading the markup back off.
_PHONEME = re.compile(
    r'<phoneme alphabet="ipa" ph="[^"]*">(.*?)</phoneme>', re.DOTALL
)


class AlreadyMarkedUp(ValueError):
    """`for_speech` was handed text that already carries pronunciation markup.

    Applying it twice would nest one `<phoneme>` element inside another, which
    is not a thing to recover from: it means a caller is building the speech
    text in two places, and the second one does not know about the first.
    """


def escape(text: str) -> str:
    """The three characters SSML cannot carry raw."""
    for raw, escaped in ESCAPES:
        text = text.replace(raw, escaped)
    return text


def unescape(text: str) -> str:
    """`escape` backwards, in reverse order so a literal `&amp;` survives."""
    for raw, escaped in reversed(ESCAPES):
        text = text.replace(escaped, raw)
    return text


def for_speech(text: str, as_ssml: bool = False) -> str:
    """`text` with every listed word marked up for the speech service.

    Returns `text` itself, unchanged and unescaped, when no listed word is in
    it: the overwhelmingly common case, and it should cost nothing.

    `as_ssml` escapes it anyway. That is for a caller adding markup of its
    own, such as the pauses `app/tts.py` puts between sentences: once there is
    any element in the body the whole body is parsed as SSML, and a raw `&` in
    it is a 400 from the service rather than an ampersand.
    """
    if "<phoneme" in text:
        raise AlreadyMarkedUp(
            "this text already carries pronunciation markup; for_speech is "
            "applied once, where the speech request is built"
        )
    if not _WORDS.search(text):
        return escape(text) if as_ssml else text

    out = []
    end = 0
    for match in _WORDS.finditer(text):
        out.append(escape(text[end : match.start()]))
        word = match.group(1)
        out.append(
            PHONEME.format(
                ipa=PRONUNCIATIONS[word.lower()], word=escape(word)
            )
        )
        end = match.end()
    out.append(escape(text[end:]))
    return "".join(out)


def spoken_text(ssml: str) -> str:
    """The words `ssml` says, with the pronunciation markup taken back off.

    The inverse of `for_speech`, and that is a property worth having rather
    than a convenience: a table entry that changed a word instead of its
    pronunciation would show up as a round trip that did not return its input.

    Text with no markup in it comes back as it arrived. Unescaping it anyway
    would rewrite a literal `&amp;` that was never an escape, and the round
    trip has to hold on the path where nothing was marked up too.
    """
    if "<phoneme" not in ssml:
        return ssml
    return unescape(_PHONEME.sub(r"\1", ssml))
