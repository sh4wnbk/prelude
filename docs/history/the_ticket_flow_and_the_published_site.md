# The ticket flow, the published site and the type scale

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

How the demo tickets, the scanner, the ticket screen, the Pages deploy, the readable type and the desktop backdrop were built. The decisions these records settled are listed in `HANDOFF.md` under Decisions still in force.

---

## Demo tickets

**The seats are settled.** 1986 is Sec 108, Row 14, Seat 8. 2022 is Sec 215,
Row 9, Seat 6. The 1986 seat was settled earlier; the 2022 seat had never been
set and was chosen when the ticket codes were generated, so it is the one value
here that no earlier decision produced.

These are demo fixture data, not play data. The seat is the fan's own ticket
rather than a claim about the match, which is why it carries no grounding
obligation; the same already applied to the section and row, neither of which
comes from `data/raw/`. This does not add a fourth input.

`app/web/matches.json` now carries `section`, `row` and `seat` per match as
separate fields, alongside the `ticket` line that Live renders. Live shows the
seat: "Sec 108 · Row 14 · Seat 8" (`02`). The "Ticket: " prefix came
off when a 414pt phone showed it wrapping to two lines: the icon beside it
already says what the line is.

**`scripts/make_tickets.py`** writes one QR code per match to
`app/web/assets/tickets/`, named for the match id. The payload is a URL,
`<site>/?ticket=<match_id>:<section>:<row>:<seat>`:

| File | Payload | Size |
| ---- | ------- | ---: |
| `app/web/assets/tickets/3750191.png` | `https://sh4wnbk.github.io/prelude/?ticket=3750191:108:14:8` | 444 bytes |
| `app/web/assets/tickets/3869685.png` | `https://sh4wnbk.github.io/prelude/?ticket=3869685:215:9:6` | 452 bytes |

**A URL, because a phone's own camera app only offers to open what it
recognises.** The codes used to carry a bare `prelude:...` string, which an
iPhone read back as text with nothing to do: "No usable data found". That made
the codes work only from inside Prelude's own scanner, pointed at another
screen, which is not what the README was promising. A https link opens the app
at that ticket from any camera app, with nothing to install and nothing to type.

`index.html` parses `?ticket=` and hands the seat to the ticket screen, which is
the screen that knows `app/web/matches.json` and so is the one that can say
whether the seat is a ticket this app holds. A link naming a seat we do not hold
is ignored rather than displayed, and `documentElement` carries
`data-ticket-link`, `accepted` or `rejected`, which is how a test can tell.

**The scanner reads both forms.** A code carrying the URL and a code carrying
the old `prelude:` string reduce to the same four fields before the same check
runs, so a code printed earlier keeps working.

The payload is built from the structured fields rather than parsed back out of
the display line, so the code and the copy cannot drift. The script refuses to
write anything if they disagree, or if any part of the payload is missing from
the data, and both refusals were tested.

Writing an image proves nothing about what it holds, so each PNG is read back
with a real decoder (`zxing-cpp`) and compared byte for byte; a code that does
not round trip exits non-zero. Both decode exactly. Generation uses `segno`, now
a project dependency; the decoder and `pillow` are dev dependencies.

**The scanner reads these codes**, and the next section records how. The
payload format is a contract between `scripts/make_tickets.py` and
`app/web/prelude_05_scan.html`, and both read the seat fields from
`app/web/matches.json`, so neither can drift from the other.

## Ticket scanning

`app/web/prelude_05_scan.html` reads the QR code on a demo ticket and opens the
ticket details for that match. Scan ticket on the list opens the scanner, and
the code decides the match, so the card selected on the list no longer rides
along with the button. Built from the Stitch scan mockup's layout and
viewfinder.

**Two readers, one handler.** `BarcodeDetector` where the browser has it, and
jsQR pinned at `1.4.0` from jsDelivr with an integrity hash where it does not,
because iPhone Safari has no `BarcodeDetector`. A detector that fails part way
through falls back to jsQR for the rest of the session rather than failing every
frame. `documentElement` carries `data-reader`, which is how a test can tell
which one ran.

**A code is a ticket only when the whole payload matches** one in
`app/web/matches.json`: match id, section, row and seat. Those two tickets are
the only ones this app knows about, so anything else is not a ticket it can
open. An unrecognized code shows "Ticket not recognized" and the scanner keeps
running, because the next frame may hold a code it does know.

**Reading a code does not start the match.** The seat travels to the ticket
screen, and Enter match there is what clears that match's `sessionStorage` key
and leaves the other match's alone. Backing out of the ticket screen therefore
changes nothing.

**With no camera to use**, the viewfinder is replaced by a plain message and the
manual entry button stays. That covers permission denied, no camera found, and a
camera that will not start, each with its own message. Manual entry takes the
same ticket code and refuses anything else the same way.

**The shell states the camera grant, and does not depend on it.**
`index.html` holds every screen in an iframe, and that iframe now carries
`allow="camera"`. It is not what makes the scanner work there: Permissions
Policy defaults the camera to `self`, so a same-origin frame inherits it. That
was measured rather than assumed, by serving the shell with the attribute
stripped out and scanning a ticket anyway, which worked. The attribute stays
because it says the grant out loud, and because it is what a cross-origin shell
would need.

**Stripped from the mockup**, as the task required: the FPS, FOV, zoom and ISO
readouts, the parity and locking-on lines, auto-detect active, the torch button,
the format chips including Apple Wallet, and the StatsBomb verifies footer. Three
more came out for the same reason the list exists. The stylised QR target inside
the viewfinder was a drawing of what a camera would show, and the viewfinder now
shows a camera. The "view scan instructions" link went nowhere. The optical HUD
and active verification wording described machinery that is not there: the screen
reads a code, and the status pill now reports what the camera is actually doing.

**Manual entry on the picker is built.** The free-text matchup and venue input
is gone. The match comes from a select built from `app/web/matches.json`, the
stadium fills in from the chosen match rather than being typed, and the section,
row and seat are the only things a fan enters. Continue stays disabled until a
match is picked and all three fields hold something that is not whitespace, and
it opens the ticket details screen, the same one a scan opens.

**A seat entered by hand is that fan's own ticket**, so it overrides the one in
`matches.json` for that match for the rest of the session. It lives in
`sessionStorage` as JSON under `prelude.ticket.<match_id>`, next to
`prelude.moment.<match_id>`, and `match-content.js` prefers it when it renders
the Live ticket line. A seat typed for one match does not appear on the other,
and a new session falls back to the seat in `matches.json`.

**There is one manual entry, and both screens mount it.** This was an open
question and it is now settled: the scanner used to ask for a ticket code, which
meant typing `prelude:3750191:108:14:8`, a string printed nowhere a fan can
read. Asking for it was a worse failure than no fallback at all, because it
looked like a way in. Both screens now show the same form, built once in
`app/web/manual-entry.js` and put on a screen with `Prelude.mountManualEntry`.
The ticket code field is gone.

The form is script rather than markup precisely so there is one copy of it.
`docs/DESIGN.md` cites it as `js`, and `scripts/check_docs.py` treats that as a
source it can verify anchors in, the way it does a screen. `scripts/scan_copy.py`
reads the scripts as well now, because copy is screen copy wherever it is
written.

What the camera path and the form path check is still different, and that is the
point rather than an inconsistency. A scanned code must match a ticket this app
knows, because a code either decodes to one or it does not. A typed seat is
accepted as given, because where someone is sitting is theirs to state and
carries no data obligation. The copy
above Scan ticket now reads "Reads the QR code on your ticket and opens that
match." (`01`). The old line promised to set a venue and a section from a
ticket, which was never true of the button and is still not what it does: it
opens the scanner, and the code names the match.

## Ticket details

`app/web/prelude_06_ticket.html` is where both ways in arrive, and the only
place the match is actually entered. Built from the Stitch ticket mockup. The
match comes from `app/web/matches.json`; the seat comes from whatever put it in
`sessionStorage`, the scanner or manual entry. Opened with no stored seat, a
reload after the session ended or a bookmark, it falls back to the seat
`matches.json` holds for that match, which is the inline copy already in the
markup.

**Enter match** clears that match's step-away key and opens Live at its
pre-moment state, with the ticket's seat on it. **Scan different ticket** goes
back to the scanner. **Edit details** appears only for a ticket entered by hand,
and returns to the list with the manual panel open and the seat still in it, so
correcting one field is not a retype. The pill says how the ticket arrived,
"Ticket scanned" or "Entered by hand", which is the only thing it claims.

**Three rows, each describing something real**: at venue with GPS, naming the
stadium; play data connected, which is the picker's own status string; and
"Tap Heading out when you leave your seat.", which is an instruction rather than
a claim about machinery.

**Removed from the mockup**, as the task required: the year and the date
everywhere, the telemetry lock line, "Step-away tracking armed", and the
Stitch-hosted stadium image. The pass ID went with them, because `#AZT-86-108`
carries the year and nothing issues pass IDs, so a year-free version would be an
invented identifier. Four more came out for the same reason the rule exists.
"Lower bowl", "aisle adj" and "reserved" are claims about a seat that no data
makes. The gate and concourse strip invents a way into a stadium. The torch
button has nothing to toggle on a screen with no camera, and was already struck
from the scanner. The vibrate call on the primary button was invented hardware
feedback. "Ticket verified, match locked" became the arrival pill, since nothing
is verified about a seat someone typed.

## Published

The site is deployed from `main` by `.github/workflows/pages.yml`, which stamps
the commit into every `__V__` placeholder and uploads `app/web/` only.

**The camera needs the live site, not a file.** `getUserMedia` is refused
outside a secure context, so the scanner works on
`https://sh4wnbk.github.io/prelude/` and on `localhost`, and not from a screen
opened off the filesystem. The README carries both ticket QR codes so a phone
can scan one off the page.

**Verified on the live site at `a836eb7`**, entering through `index.html` the
way a visitor does, in a browser emulating a phone: both matches scan to their
own ticket and open Live with the scanned seat, and both reach the same place
through manual entry with a typed seat. The reader reported itself as jsQR,
which is the path an iPhone takes. What that run cannot prove is a real iOS
Safari camera prompt on a physical handset.

**A phone may refuse to autoplay the camera** even once it is granted. That is a
separate failure from having no camera, so the scanner keeps them apart: a
refused `play()` shows a Tap to start the camera button rather than the no
camera message, and scanning begins on that tap.

## Readable type, and the reader can zoom

Reported from an iPhone XR: the smallest text read as fine print, and nothing
the reader could do got round it. Both halves are fixed.

**The label scale moved from 9/11/13 to 13/14/16.** 12/13/15 was the first
attempt and came back as still tight on the XR, so these sizes are the second
reading rather than the first. `label-sm` carried 66 of the
uses across the screens and `manual-entry.js`, so it is the one that mattered,
but all three moved together: the order of the scale and the gaps in it are
unchanged, and leaving `label-lg` at 13px would have put `label-md` level with
it. It is one edit repeated identically in six screens, because the
`<script id="tailwind-config">` block is one block and the design system rests
on it staying byte-identical. It still is, now sha256 `44927b9a0feedea2`,
3210 chars.

**`user-scalable=no` and `maximum-scale=1.0` are gone** from all six screens and
from `index.html`, which is the page a phone loads first. Both had to go: either
one alone still blocks pinch to zoom on iOS.

**The manual entry fields are 16px**, the one literal type size in the system.
iOS zooms the page when a field under 16px takes focus, and it could not do that
while zooming was blocked. Unblocking zoom brings that behaviour back, so the
fields sit at the threshold where it never fires. Without this the fix would
have traded fine print for a page that lurches every time a seat is typed.

**One thing the bigger type broke, and it is fixed.** The narration label on
Moments, "AI AUDIO NARRATION · PLAY DATA SYNC", is in a span that truncates, and
at 12px it no longer fitted on one line, so it rendered as
"AI AUDIO NARRATION · PLAY DATA…". The truncation is gone from those two spans
and the line wraps instead, which shows all of it. Nothing else lost content:
the verified marker, the Live ticket line and the seat tiles all still read in
full.

Measured on every screen at 390px and at 414px, the XR's width: document
scrollWidth equal to clientWidth, `window.scrollTo(9999, 0)` leaving scrollX at
0, no unclipped element past the body box, and no leaf element whose own text is
wider than its box. The behaviour suites were re-run unchanged.

**What the measurements cannot settle.** Nothing overflows and the computed
sizes are 13, 14, 16 and 16px, but whether that reads comfortably in the hand is
not something a desktop browser at 414px can answer. It took two readings on a
real XR to get here, which is the useful part of the record: the first fix
measured completely clean and was still wrong.

At these sizes several lines that used to sit on one now wrap: the two status
pills on Live, its ticket line, and the status line on the event cards. Nothing
is hidden or clipped, and that was checked rather than assumed, by looking for
any leaf element whose own text is wider than its box. Wrapping is the cost of
the larger type and it was taken deliberately.

## Stadium backdrop on desktop

Above the 501px breakpoint the page sits on `app/web/assets/stadium-bg.jpg`,
blurred and dimmed, so a desktop window reads as a phone held at a match rather
than a phone on a flat field. At 500px and narrower nothing applies: the screens
are pixel for pixel what they were, which was checked by comparing screenshots
with and without the rules rather than by eye.

**The frame is drawn in two places and both needed it.** `phone-frame.css`
serves a screen opened on its own; `app/web/index.html` carries its own copy and
does not link the stylesheet, and the site root serves `index.html`. A backdrop
written only in the stylesheet would have been invisible to everyone visiting
the demo.

**What nearly went wrong.** With the rules in place, the computed styles were
all correct, the image was `cover` and centred, the blur was 8px, the overlay
was 70%, and the page still rendered flat black. Measuring the rendered pixels
rather than the stylesheet showed the backdrop sitting at a luminance of exactly
19, which is `#101319`: the shell's `body` fills the viewport and the base layer
paints it that colour, so it covered the backdrop on `html`. The fix is one
line, `background-color: transparent` on `body` above the breakpoint. The trap
worth remembering is that an opacity sweep looked like the obvious remedy and
would have made the page lighter without ever revealing the photograph.

The image is a match night seen from behind one goal: four floodlight towers, a
full crowd, players on the pitch. Mean luminance 49.5 of 255, with 44% of its
pixels below 32 and 1% above 192, which is the lights. It replaced a darker and
emptier stadium that needed a 70% dim to sit behind the phone; this one carries
the crowd and the lights that make it read as a match, and takes 50%.

The phone stays the brightest thing on screen, but only peak brightness shows
it: 227 for its amber button against 131 for the brightest floodlight, at every
width. Do not use the mean. The two are close enough at 1920 and 2560 that the
answer flips with the crop: measured over the phone's screen area the phone led
45.6 to 45.2, and measured over the whole handset including its bezel it trailed
41.6 to 42.3. Both numbers are real and neither means anything, which is the
point. The phone is a dark panel with bright accents on a blurred page, so what
makes it read is peak contrast and sharpness, not average light.

It is 122KB: 1920px wide, JPEG quality 75, the same treatment the previous
backdrop got. A photograph that is blurred 8px and dimmed to half can take far
more compression than it looks like it should, and phones never pay for it at
all: the media query means they do not request it, measured as zero requests at
390px against one at 1920px.
