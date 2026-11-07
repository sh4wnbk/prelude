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
| `app/grounding.py` | the same | a sound narration refused for markup it never wrote |
| a model | the same | nothing says a pronunciation to a model |

**The check refuses markup now, and it did not when this was measured.**
An earlier version of this docstring said a marked-up narration would be
refused for an ungrounded name. It was not: both forms came back grounded on
all 35 claims of the 1986 narration, because the check reads names, actions,
clocks and numbers against the facts a sentence cited and `phoneme`,
`alphabet` and `ipa` are none of those. So the markup was accepted, labelled
"Verified from play data", and read out with the tags in it. `BANNED_PATTERNS`
in `app/grounding.py` now refuses any narration holding `<` or `>`, labelled
"markup", which nothing the prompt or the template writes ever holds.

So the second row of the table is loud rather than silent: the narration is
refused, and what is lost is a narration that was fine. The first and third
rows are as quiet as they ever were, so no module in `app/` imports this one
except the speech backend, and
`tests/test_pronunciation.py::TestNothingElseAppliesIt` is what holds that. It
reads source rather than behaviour, and it is the second layer: the check
catches markup arriving at it, this catches a module that could write markup
into a header, where there is no check to arrive at.

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
#:
#: `minute` is the second, and the clearer case of the two. All three voices
#: read "Minute 54." as "my-NEWT", the adjective meaning tiny, where the app
#: means the unit of time and only ever means the unit of time: the word
#: reaches speech from `template_narration` in `app/narration_prompt.py`,
#: which writes the clock. The CMU Pronouncing Dictionary lists
#: `M AY0 N UW1 T` beside `M IH1 N AH0 T` for it, so the voices were picking a
#: real pronunciation of the written word rather than misreading it.
#: `close` is the third, and the first that came from the dictionary rather
#: than from a listener. `scripts/check_vocabulary.py` flagged it as a
#: heteronym, `K L OW1 S` against `K L OW1 Z`, and the app says it in exactly
#: one place: `HEADER_WORDING[CLOSE_GAP]` in `app/orchestrator_contract.py`,
#: which is "{scorer} close the gap." That is the verb, so it is `kloʊz`, and
#: a voice reading it as `kloʊs` would be saying the adjective.
#:
#: **Nobody has heard this one yet,** and nobody has heard `minute` with its
#: entry either; Shawn confirms both after November 1. `lead` is settled: he
#: heard it with the entry in his own test and again in the hero samples,
#: which carry it. This one is a reading of the header plus a dictionary
#: rather than a listener's finding, and it is in because the sentence it
#: governs leaves no room for the other pronunciation. If the voices turn out
#: to say it correctly, the entry costs 44 characters on a transition neither
#: hero goal uses, which is the cheapest way to be wrong available here.
#:
#: `di` is the fourth, and it arrived with the frozen narrations: the 2022
#: hero goal is Di María's, so the 2022 recording says the name four times
#: and the moment card shows it. The dictionary lists `D IY1` beside `D AY1`,
#: and those are two different words rather than two accents: `D AY1` is the
#: English "die". The name is Spanish and the syllable is "dee", so it is
#: `diː`. Nobody has heard it; it joins `minute` and `close` in waiting for
#: Shawn's ear after November 1.
#:
#: It is the second entry found by the dictionary rather than by a listener,
#: and the first found on a word the app speaks only because a model chose
#: to write it. The template never said "Di": it wrote the full recorded name
#: in one breath, and the sweep reads names as separate words.
PRONUNCIATIONS: Mapping[str, str] = {
    "lead": "liːd",
    "minute": "ˈmɪnɪt",
    "close": "kloʊz",
    "di": "diː",
}

#: Words the dictionary flags that were looked at and need no entry, each with
#: the reason. `scripts/check_vocabulary.py` reads every word the app can
#: speak against the CMU Pronouncing Dictionary and flags any spelling with
#: more than one listed pronunciation;
#: `tests/test_vocabulary.py::TestEveryFlaggedWordHasBeenReviewed` fails on a
#: flagged word that is neither here nor in `PRONUNCIATIONS`, so new
#: vocabulary cannot reach a voice unreviewed.
#:
#: **A reason rather than a bare list**, because the two kinds of flag are not
#: alike. Most are reduction or accent variants of one word, where either
#: pronunciation is the same word and a listener would not notice. A few are
#: heteronyms, where the two pronunciations are different words, and those are
#: the ones that end up in `PRONUNCIATIONS`. A word sitting here with its
#: reason is a review somebody can disagree with; a word sitting on a bare
#: list is a word somebody silenced.
CHECKED_NO_ENTRY_NEEDED: Mapping[str, str] = {
    # Function words, flagged because a full and a reduced form are both
    # listed. Every English speaker alternates between them by position in a
    # sentence, and a voice choosing either is saying the same word. Forcing
    # one would make the delivery worse, not better: "thee gap" is wrong in a
    # way "the gap" never is.
    "a": "full and reduced forms of one word, AH0 and EY1",
    "an": "full and reduced forms of one word",
    "and": "full and reduced forms of one word",
    "as": "AE1 Z and EH1 Z are accent variants of one word",
    "for": "full and reduced forms, F AO1 R down to F ER0",
    "in": "a stress variant only, IH0 N and IH1 N",
    "it": "a stress variant only, IH1 T and IH0 T",
    "the": "thuh and thee, which a speaker picks by what follows",
    "was": "W AA1 Z and W AH0 Z are accent variants of one word",
    "his": "full and reduced forms of one word, HH IH1 Z and HH IH0 Z",
    "with": "voiced and voiceless th, and both are the same word",
    # Ten more function words, from the six narrations the team wrote. Each
    # is the same alternation as the eleven above: a full form and a reduced
    # one, a stress variant, or the wh cluster said with or without the h.
    # Not one of them is a heteronym, so there is nothing for a listener to
    # mishear.
    "again": "AH0 G EH1 N and AH0 G EY1 N are accent variants of one word",
    "him": "full and reduced forms of one word, HH IH1 M and IH0 M",
    "inside": "which syllable carries the stress, and both are the word",
    "into": "the unstressed second syllable only",
    "just": "full and reduced forms of one word, JH AH1 S T and JH IH0 S T",
    "on": "AA1 N and AO1 N are the cot-caught vowel, which the voices merge",
    "our": "one syllable or two, and both are the word",
    "to": "full and reduced forms of one word, T UW1 down to T AH0",
    "what": "the wh cluster, said with or without the h",
    "when": "the wh cluster and the vowel, and both are the word",
    # A name, from the frozen 2022 narration. Unlike "di" in the same name,
    # the two listed forms here are one name said two ways: the first vowel
    # is the cot-caught vowel, which the voices merge.
    "allister": "AO1 L IH0 S T ER0 and AE1 L IH0 S T ER0 are one name",
    # Verbs from EVENT_VERBS, flagged on unstressed vowels. The syllable that
    # differs is the one nobody hears: "received" as R AH0 or R IH0 or R IY0
    # is the same word said by three people from three places.
    "carried": "the vowel before r, which the voices merge either way",
    "intercepted": "unstressed vowels, and one listed form drops the first t",
    "received": "the unstressed first syllable only",
    "recovered": "the unstressed first syllable only",
    "won": "W AH1 N and W AA1 N are accent variants of one word",
    # From the recorded Ollama exchange, which is a smoke-test answer rather
    # than a narration: "The football match ended in a thrilling 2-1 victory
    # for the home team." Collected because it is text this app recorded a
    # model saying, and reviewed on the same footing as everything else.
    "ended": "the unstressed second syllable only",
    "victory": "three syllables or two, and both are the word",
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
