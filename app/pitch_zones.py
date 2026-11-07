"""Where on the pitch something happened, as a phrase a narrator can say.

**Read aloud, the six candidates of 2026-11-05 have no field position in
them.** "Dribbled past Butcher" and "a long ball to MacAllister" give a
listener nothing to place: the move could be happening anywhere between the
two goals. The records hold the answer on every event, because StatsBomb
writes a location on almost all of them, and the only reason a narration was
not saying it is that nothing turned a coordinate into words.

`Spot.in_own_half` and `Spot.in_the_box` in `app/narration_prompt.py` already
read a coordinate against a line, and they are two lines on a pitch a hundred
and twenty yards long. This is the same arithmetic at the resolution a
commentator speaks at: eight bands up the pitch and three across it, each one
a phrase, each one a claim `app/narration_grammar.py` can refuse.

**The vocabulary is Shawn's and the geometry is StatsBomb's.** The pitch is
120 by 80 with `x` running towards the goal the recorded player's own team is
attacking, which is what lets one set of bands read correctly for either side.

| Said | Where |
| ---- | ----- |
| "deep in his own half" | `x` under 40 |
| "in his own half" | 40 to 50 |
| "just inside his own half" | 50 to 60 |
| "just inside their half" | 60 to 70 |
| "in their half" | 70 to 80 |
| "in the final third" | 80 to 96, and 96 and up outside the box's width |
| "on the edge of the box" | 96 to 102, within the box's width |
| "in the box" | 102 and up, within the box's width |
| "on the left" | `y` under 18 |
| "on the right" | `y` over 62 |

**The two halves of a phrase are two claims.** "In the final third on the
right" is a band up the pitch and a third across it, and either can be wrong
on its own, so `zone_of` and `side_of` answer separately and
`app/narration_grammar.py` reads them as two moves. A spot between the two
lines gets no side at all, which is most of the pitch by width and is why nine
of the twelve zone phrases the two hero passages carry are said with no side
after them.

**A side is said only where the ball is clear of the middle, and the first
rule was not.** The thirds of an eighty yard pitch put the lines at 26.7 and
53.3, and on that reading three beats of the 1986 dribble and the 2022 long
ball's landing were "on the right" at `y` 54.9, 55.1, 56.4 and 60.5, which is
a yard or two past the middle and reads as a claim a listener would not make.
It also made the grouped 1986 dribble beat say "on the right" three times in
one line. So the lines are the sides of the penalty area instead: a ball wide
of the box's width is wide, and anything between them is central and is said
with no side. `BOX_TOP_Y` and `BOX_BOTTOM_Y` are the same two numbers, and
they stay separate constants because they answer a different question: the box
bands ask whether a spot is inside the box, and these ask whether it is out
wide.

**A half can be said with a possessive, and then it is read from that side's
end of the pitch.** "Deep in our own half" told for a fan of the side that
conceded is their own half and not the half the records are written in, so
`from_the_other_end` answers the band `PITCH_X` less the recorded `x`. The
three own-half bands and the two "their half" ones are the same places read
from the two ends, which is what lets one set of words answer for either
side; `app/narration_grammar.py` resolves which side a possessive names.

**The box needs its width and the final third is what is left.** A ball at
`x` 110 and `y` 10 is past the eighteen yard line and nowhere near the box: it
is by the byline with the goal frame between it and the posts. So both box
bands ask for `y` between 18 and 62, and anything from 80 up that is not one
of them is the final third. That last clause is this module's own reading
rather than Shawn's vocabulary, which names no zone for a ball past the
eighteen yard line and wide of the box; the final third is true of it and is
the band it is in.

**It is not `Spot.in_the_box`, and the difference is the width.** That
property is `x >= 102` alone, so it calls a ball at `x` 110 and `y` 10 inside
the box, and the position claim built on it reads the same way. Nothing in
either hero passage sits there (every recorded location from 102 up has `y`
between 32.1 and 55.1), so the two readings agree on all the real data and
the difference is a hole in the older one rather than a disagreement. It is
left alone here because no step asked for it and tightening it would move
`in_the_box` on every beat and every position claim; `HANDOFF.md` records it.

Standard library only, and no judgement about the play: every answer is one
coordinate against one number.
"""

from app.narration_prompt import BOX_X, HALFWAY_X, Spot

#: Where a team's own half stops being deep, in StatsBomb's yards of `x`.
DEEP_X = 40.0

#: Where "in his own half" gives way to "just inside his own half".
OWN_HALF_X = 50.0

#: Where "just inside their half" gives way to "in their half". The halfway
#: line itself is `HALFWAY_X` in `app/narration_prompt.py`, which is the one
#: line these bands share with the older position claim.
JUST_INSIDE_X = 70.0

#: Where the final third starts, which is also where "in their half" stops.
FINAL_THIRD_X = 80.0

#: Where the edge of the box starts. Eighteen yards short of `BOX_X`, which is
#: the eighteen yard line itself.
EDGE_X = 96.0

#: The box's width, in StatsBomb's yards of `y`. The pitch is 80 wide and the
#: box is 44, so it runs from 18 to 62 with 18 either side of it.
BOX_TOP_Y = 18.0
BOX_BOTTOM_Y = 62.0

#: The two lines across the pitch that make a left, a middle and a right.
#: Shawn's numbers: the sides of the penalty area, so a side is said only
#: where the ball is clear of the middle. They are `BOX_TOP_Y` and
#: `BOX_BOTTOM_Y` by value and not by meaning; the module docstring has the
#: reading the thirds of the pitch gave and why it was dropped.
LEFT_Y = 18.0
RIGHT_Y = 62.0

#: The eight bands up the pitch, as the words for them.
DEEP_IN_OWN_HALF = "deep in his own half"
IN_OWN_HALF = "in his own half"
JUST_INSIDE_OWN_HALF = "just inside his own half"
JUST_INSIDE_THEIR_HALF = "just inside their half"
IN_THEIR_HALF = "in their half"
FINAL_THIRD = "in the final third"
EDGE_OF_THE_BOX = "on the edge of the box"
THE_BOX = "in the box"

#: The two sides, as the words for them. A spot between the two lines is in
#: neither and is said with no side.
ON_THE_LEFT = "on the left"
ON_THE_RIGHT = "on the right"

#: Every band, in the order they run up the pitch. `tests/test_pitch_zones.py`
#: reads it to check the vocabulary is a partition rather than a list.
ZONES: tuple[str, ...] = (
    DEEP_IN_OWN_HALF,
    IN_OWN_HALF,
    JUST_INSIDE_OWN_HALF,
    JUST_INSIDE_THEIR_HALF,
    IN_THEIR_HALF,
    FINAL_THIRD,
    EDGE_OF_THE_BOX,
    THE_BOX,
)

#: Both sides, in the order `y` runs.
SIDES: tuple[str, ...] = (ON_THE_LEFT, ON_THE_RIGHT)

#: The two bands whose words say "their", which is the opponent's half and is
#: the one place a zone phrase can be said with a team's name in it.
THEIR_HALF_ZONES = frozenset({JUST_INSIDE_THEIR_HALF, IN_THEIR_HALF})

#: The three bands that are a team's own half, in the order they run away from
#: that team's own goal. They are the bands a half said with a possessive can
#: name, because "deep in our own half" and "just inside France's half" are
#: the same three bands read from one end of the pitch or the other.
OWN_HALF_ZONES: tuple[str, ...] = (
    DEEP_IN_OWN_HALF,
    IN_OWN_HALF,
    JUST_INSIDE_OWN_HALF,
)

#: The length of the pitch, in StatsBomb's yards of `x`. A location is written
#: in the frame of the team whose record it is, so one end's `x` is `PITCH_X`
#: less the other's: Álvarez struck the long ball at `x` 63.2, which is 56.8
#: from France's end.
PITCH_X = 120.0


def from_the_other_end(place: Spot) -> Spot:
    """One spot as the side at the other end of the pitch would place it.

    For a half said with a possessive, which is a claim about one side's own
    half and has to be read in that side's frame: "just inside our half" told
    for a France fan is 56.8 up the pitch from France's goal and 63.2 from
    Argentina's, and only the first reading makes it just inside a half.

    **`y` is left as it was, and that is deliberate.** The bands this is for
    are the three of a team's own half, which ask about `x` alone, and a side
    said after one of them ("just inside our half on the right") is a separate
    claim that `side_of` reads in the attacking frame wherever it was said.
    Flipping `y` here would move a side claim nothing asked to move.
    """
    return Spot(x=PITCH_X - place.x, y=place.y)


def in_the_box_width(place: Spot) -> bool:
    """Whether a spot is between the two sides of the penalty area."""
    return BOX_TOP_Y <= place.y <= BOX_BOTTOM_Y


def zone_of(place: Spot) -> str:
    """Which band up the pitch a spot is in, as the phrase for it.

    Read in the frame of the team whose record it is, so it may only be
    called with the attacking side's own location: a `Dribbled Past` is
    written on the defender's record, which StatsBomb mirrors, and the band
    it falls in there is the band at the other end of the pitch. Terry
    Butcher's `Dribbled Past` is at `x` 33.0 and the `Dribble` that beat him
    is at 87.1, which is the same place said twice from two ends.
    """
    if place.x < DEEP_X:
        return DEEP_IN_OWN_HALF
    if place.x < OWN_HALF_X:
        return IN_OWN_HALF
    if place.x < HALFWAY_X:
        return JUST_INSIDE_OWN_HALF
    if place.x < JUST_INSIDE_X:
        return JUST_INSIDE_THEIR_HALF
    if place.x < FINAL_THIRD_X:
        return IN_THEIR_HALF
    if place.x < EDGE_X:
        return FINAL_THIRD
    if not in_the_box_width(place):
        # Past the edge of the box and wide of it, which is the final third
        # and is not the box however far up the pitch it is.
        return FINAL_THIRD
    if place.x < BOX_X:
        return EDGE_OF_THE_BOX
    return THE_BOX


def side_of(place: Spot) -> str:
    """Which side of the pitch a spot is on, or "" for the middle third."""
    if place.y < LEFT_Y:
        return ON_THE_LEFT
    if place.y > RIGHT_Y:
        return ON_THE_RIGHT
    return ""


def zone_for(place: Spot, opponent: str | None = None) -> str:
    """One spot as the whole phrase: the band, and the side where there is one.

    "In the final third on the right" for Maradona's dribble past Butcher at
    (87.1, 68.6), and "deep in his own half" with nothing after it for
    Cuciuffo's recovery at (35.2, 50.4), which is in the middle third by
    width. `opponent` is passed on to `said_as`, so the two bands that say
    "their" are said with the other side's name where the caller knows it.
    """
    side = side_of(place)
    zone = said_as(zone_of(place), opponent)
    return "{} {}".format(zone, side) if side else zone


def holds(zone: str, place: Spot) -> bool:
    """Whether a spot is where this phrase says, band or side.

    The bands are exclusive, so a phrase naming the wrong one is wrong even
    where the two overlap in plain English: a ball at `x` 35 is in its own
    half and the phrase for it is "deep in his own half", so "just inside his
    own half" over it is refused. The one phrase this is not true of is "in
    his own half", which `app/narration_grammar.py` reads as the half claim it
    already had rather than as a band; the reason is written down there.
    """
    if zone in SIDES:
        return side_of(place) == zone
    return zone_of(place) == zone


def said_as(zone: str, opponent: str | None) -> str:
    """One zone phrase with "their" replaced by the opponent's own name.

    "Just inside France's half" rather than "just inside their half", which
    is what a listener needs to place the 2022 long ball: "their" in a
    narration told for a France fan is the side he is not on. The two bands
    that say "their" are the only ones this touches, and a caller with no
    opponent name in hand gets the phrase as it stands.
    """
    if opponent is None or zone not in THEIR_HALF_ZONES:
        return zone
    return zone.replace("their half", "{}'s half".format(opponent))
