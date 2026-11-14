# The data check and the screen scan

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

What the first reading of `data/raw/` found, and what the first copy scan of the screens found, including the three hero claims that did not survive possession 117.

---

## Data-check findings

Match `3750191`, Argentina 2-1 England, quarter-final, 1986-06-22. 2,748 events.

**Goals (3):**

| Player | Team | Minute | Second | Period | `shot.body_part.name` |
| ------ | ---- | -----: | -----: | -----: | --------------------- |
| Diego Armando Maradona | Argentina | 50 | 27 | 2 | `Other` |
| Diego Armando Maradona | Argentina | 54 | 18 | 2 | `Left Foot` |
| Gary Lineker | England | 80 | 37 | 2 | `Head` |

StatsBomb's `minute` floors the match clock, so `50:27` is the 51st minute as a
broadcast would caption it. The three goals reconcile with the `2-1` scoreline
in the match index, which is an independent file.

**Shots: 27 total. Argentina 15, England 12.**

**The 13-of-15 claim does not hold.** Both halves are wrong: Argentina took 15
shots, not 13, and the match total is 27, not 15. Argentina's share is 15/27
(55.6%). The likely origin of the error is that 15 is Argentina's real count,
read as the match total.

This matters downstream: any narration line that leans on shot dominance has to
use 15-of-27, and a line built on "13 of 15" could not carry
"Verified from play data".

## Screen scan results

`scripts/scan_copy.py` checks the four screens, `index.html` and
`app/web/matches.json` for basketball terms, verdict nicknames, "official", the
60-second framing, invented hardware, and em dashes. It also checks where the
grounding label sits, which is a placement rule rather than a banned string;
see below.

**Baseline, 4 hits:**

| File | Line | Category | String |
| ---- | ---: | -------- | ------ |
| `prelude_03_moment_card.html` | 26 | 60-second framing | `60 seconds` |
| `prelude_03_moment_card.html` | 165 | 60-second framing | `60-Second` |
| `prelude_04_moments.html` | 76 | verdict nickname | `Goal of the Century` |
| `prelude_04_moments.html` | 151 | verdict nickname | `Hand of God` |

**Current, 0 hits**, exit code 0. Screens 01 and 02 were clean at baseline: no
basketball terms, no "official", no UWB, haptic or dB, no "Controversy"
anywhere in the set. A separate census of every non-ASCII character found no em
or en dashes, only middle dots, one bullet, one curly apostrophe, and the quote
guillemets.

### The grounding label

`CLAUDE.md` allows "Verified from play data" only over narration whose claims
trace back to the event data. The label was on two screens. On the moment card
it sits beside the narration quote, which is the placement the rule describes.
On Live it sat on the standby pipeline card, above rows reporting whether the
step-away trigger and the narration were switched on. Those rows are app state,
not a claim read from the feed, so the label promised grounding for something
the data never said. **It has been removed from Live** and now sits only beside
the narration quote: "Verified from play data" (`03`).

A regex sweep cannot catch that, because the words were right and only the
position was wrong. `scripts/scan_copy.py` now parses each screen into a tree
and fails if the label does not share a card with a narration element, meaning
one carrying a `data-field` listed in `NARRATION_FIELDS`, currently
`hero_quote`. The walk stops at `html`, `body` and `main`, so a label anywhere
else on a screen that happens to hold narration does not pass. The label in
`app/web/matches.json` is a hit on sight, since copy data carries no markup that
could place it over anything.

Both directions were tested. Putting the label back on the standby card gives
exit 1 and `prelude_02_live_seated.html:89 [ungrounded label]`, reported as
sitting over "STANDBY PIPELINE"; adding it to a `matches.json` caption also
gives exit 1. With both reverted the scan is back to exit 0.

If Phase 5 adds another narration element, add its `data-field` to
`NARRATION_FIELDS` or a correct placement will be reported as a violation.

### Card bodies checked against the data

Two card bodies were tested against `shot.body_part.name`:

- **50:27 Maradona** records `Other`, with `technique: Normal`, `type: Open
  Play`, `xg: 0.379`, location `[110.8, 40.1]`. Nothing in the feed records an
  aerial duel, so "Maradona rises with Shilton and the ball is in" (`removed`)
  was not supported and was rewritten. The surrounding events do support a replacement:
  Peter Reid has both a `Clearance` and an `Error` at 50:26, then Maradona has
  `Ball Recovery`, `Carry` and `Shot` at 50:27. The body now reads "Maradona
  recovers Reid's error and scores from nine yards." (`04`) Nine yards is
  `120 - 110.8` on StatsBomb's 120-yard pitch. A trailing "the body part is
  recorded as Other" was cut in review as a data note rather than card copy.
- **80:37 Lineker** records `Head` at minute 80, so "England's late header sets
  up a tense finish" (`removed`) was supported on both counts and was left
  alone at the time. It came off the screen later, not because it was wrong
  but because 80:37 falls after the session clock, which sits at the 55th
  minute.

### Hero copy checked against possession 117

The solo goal line appeared on two screens and the narration quote on one. All
three were re-derived from `events/3750191.json` before editing (`10eb5a5`).

Possession 117 is the 54:18 goal. It holds four `Dribble` events, every one
with outcome `Complete`, each paired with a `Dribbled Past` event naming the
defender:

| Clock | Dribble location | Dribbled Past |
| ----- | ---------------- | ------------- |
| 54:08 | `[54.4, 56.4]` | Peter Beardsley |
| 54:13 | `[87.1, 68.6]` | Terry Butcher |
| 54:15 | `[97.1, 55.1]` | Terry Fenwick |
| 54:18 | `[112.8, 49.4]` | Peter Shilton |

Maradona's first touch of the move is a `Ball Receipt*` at `x = 55.2`. Halfway
is 60 on a 120-yard pitch, so the run starts inside his own half. The shot is at
`x = 113.4`, giving a span of 58.2 yards.

Three claims did not survive that:

- **"past five England players" (`removed`) was one too many.** Four are
  recorded as dribbled past. The likely fifth is Peter Reid, who has a
  `Pressure` event at 54:08 but no `Dribbled Past`, so the feed does not record
  him as beaten.
- **"60-yard" was a rounded figure.** The run spans 58.2 yards. The copy now
  says "from his own half", which is what `x = 55.2` supports.
- **"turns away from two, still going" (`removed`) has nothing behind it** in
  the feed and was cut.

The hero line on both screens now reads "Maradona's solo run from his own half,
past four England players" (`03`, `04`), and the quote names all four in
feed order: "«...Maradona, inside his own half, past Beardsley, past Butcher,
past Fenwick, rounds Shilton, and finishes.»" (`03`)

### Design tokens worth carrying forward

From `docs/DESIGN.md`, all verified against the markup:

- 29 of 47 colour tokens are declared but never referenced. The whole tertiary
  ramp and the whole error ramp are unused, so the screens define no error state.
- No responsive design exists: zero `sm:`, `md:`, `lg:`, `xl:` or `2xl:`
  utilities, and `screen-edge-tablet` is defined but never applied.
- Focus is defined only on the picker's text inputs. Every button has no focus
  style, and the toggle sets `focus:outline-none` with no replacement.
