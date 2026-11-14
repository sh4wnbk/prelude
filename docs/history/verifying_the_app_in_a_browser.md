# Verifying the app in a browser, before the browser suite existed

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

The method used from Phase 2 to Task 29, when every browser check was a script written for one task and thrown away. Task 30 replaced it with `tests/browser/`. **One claim in here is out of date on purpose: it says no browser automation is installed, which was true when it was written.** `HANDOFF.md` carries the current method and the measurement traps, which still hold.

---

## Verifying the app in a browser

Phase 2 verified the screens by rendering them. A click through needs more than
that, and none of what follows is derivable from the screens or from the rest of
this file, so it is recorded rather than worked out again.

### Serve it, do not open the files

`match-content.js` fetches `app/web/matches.json`, so a screen opened straight
off the filesystem fails that fetch and falls back to the inline 1986 copy. The
fallback is deliberate and quiet, which means a filesystem run looks like a
working app while confirming almost nothing. Serve the directory instead, from
`app/web/`:

    ..\..\.venv-prelude\Scripts\python.exe -I -m http.server 8099 --bind 127.0.0.1

The `?v=__V__` placeholder stays literal when the app is served this way, since
CI substitutes it only on deploy. The server ignores query strings, so every
asset still resolves.

**`data-match-rendered` on `documentElement` is the signal** that a screen
rendered from `matches.json` rather than falling back to the inline copy. Wait
for it before reading any value, or an assertion can quietly pass against the
1986 markup while claiming to check 2022.

**The step-away state is `sessionStorage` under `prelude.moment.<match_id>`,
set to `"1"`.** Seeding or clearing that key is how a session carrying old state
is reproduced. It is per tab, so it has to be set on the origin and then
navigated within the same tab.

### Driving it

No browser automation is installed. `.venv-prelude` holds the test runner and
its dependencies only, and putting a driver there would add browser packages to
the venv that runs the gates. Chrome is still absent on this machine. Edge is at
`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.

Playwright drives that Edge with `channel="msedge"` and needs no browser
download, so a scratch venv outside the repo is enough. It sets the layout
viewport through the DevTools protocol, which is the thing `--window-size`
failed to do in the Phase 2 review.

### Two measurements that look like defects and are not

Both produced a false failure before being run down, and both will recur:

- **Decorative glows read as horizontal overflow.** Each card carries an
  absolutely positioned blur placed outside its own box, and the card clips it
  with `overflow-x: hidden`. `getBoundingClientRect()` reports the unclipped
  geometry, so a naive sweep flags it every time. The claim that matters is
  whether the document scrolls at all: at 390 px and at 900 px the screens
  report `scrollWidth` equal to `clientWidth`, and `window.scrollTo(9999, 0)`
  leaves `scrollX` at 0.
- **The framed body measures 422 px, not 390.** Above the 501 px breakpoint
  `phone-frame.css` sets `box-sizing: content-box` with a 16 px bezel, so the
  border box is 390 plus 32 while the screen area is exactly 390. Read
  `body.clientWidth`, not the bounding rect.

Two further non-defects: the browser requests `/favicon.ico` on its own and
gets a 404, which nothing in the app references; and the Moments filter row
clips its last chip at 390 px because that row is `overflow-x: auto` and
scrolls.

### Driving the scanner

A camera cannot be clicked, so the scan screen is verified by giving Chromium a
fake capture device whose frames are a clip of a ticket code. A QR image becomes
a `.y4m` clip, and Edge is launched with `--use-fake-device-for-media-stream`
and `--use-file-for-fake-video-capture`, which is a ticket held up to the lens
as far as the page can tell.

Two things this machine cannot show you. Edge on Windows ships no usable
`BarcodeDetector`, so the real browser always takes the jsQR path here: that
branch is covered by substituting a stub detector, one that works and one that
fails, which exercises the integration rather than a native decoder. And a
denied camera is simulated by making `getUserMedia` reject with the error name
the browser would use, since a headless run cannot refuse a permission prompt by
hand.

### Test values are literals, not derived from each other

A run once reported that manual entry was given Section 332 and the ticket
showed 3320, and the same row for the other match read 118 going in and 1180
coming out. Nothing in the app was wrong. The harness built that row's section
by appending a character to the section used in the row above it, so it really
did type 3320, and the check really did pass.

The defect was in what the report let a reader conclude. Two numbers that
disagree on their face, printed side by side and marked as passing, are
indistinguishable from the form corrupting what it is given, and nothing in the
line said which it was. Derived test data costs more than it saves.

Every seat a check types is now a literal written next to the check, the paths
that should agree use the same literal, and the assertion covers the whole way
through: what the inputs hold when Continue is pressed, what ticket details
renders, and what Live renders. The seat is carried as a string from the input
to `sessionStorage` to the screen, with no parsing or arithmetic anywhere on
that path, which is why it cannot gain a digit.

Measured for both matches, with the same input through all three ways in:

| Input | Picker form | Scanner form | Ticket link |
| ----- | ----------- | ------------ | ----------- |
| 1986, Sec 108 Row 14 Seat 8 | 108/14/8 | 108/14/8 | 108/14/8 |
| 2022, Sec 215 Row 9 Seat 6 | 215/9/6 | 215/9/6 | 215/9/6 |

A typed seat of 332/7/21 for 1986 and 118/2/9 for 2022 comes through both forms
unchanged and produces the same Live ticket line either way. A link carries only
a seat this app holds, so the shared input the three paths can all take is the
seat on the ticket itself.

### What the click through confirmed

Both matches were driven end to end in Edge, in a session with no saved state
and again in one carrying saved state for both matches. The event list, the Live
states before and after Heading out, Moments stopping at the session clock,
Change event, and Heading out returning after a switch all behave as the settled
decisions above describe, at 390 px and at 900 px. The per-match reset holds in
both directions, and picking one match leaves the other match's key untouched.
