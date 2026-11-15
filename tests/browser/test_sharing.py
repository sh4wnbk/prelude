"""The moment card's share button, on both of the paths a browser can take.

The button sends a link and a line of text. There is no clip in this repo and
no code that cuts one, which is why the label is "SHARE" and the gate in
`scripts/scan_copy.py` keeps the old one out.

Two paths, and a browser takes one of them without being asked:

- **With a share sheet**, `navigator.share` is handed the title, the line for
  the match on screen and this card's own URL, and the sheet does the rest.
- **Without one**, the link goes to the clipboard, and the button says "LINK
  COPIED" only once that write has resolved.

The second path is the one this was written for. It used to say "COPIED" for
1.5 seconds on every click of that branch, whether anything had been copied or
not, and there are two ways for nothing to have been: `writeText` can be
refused, and `navigator.clipboard` is undefined outside a secure context. Both
are checked here, and in both the rule is the same: nothing on screen claims a
copy that did not happen.

**The line is read out of `app/web/matches.json`**, not written down, so a
share text that drifted from the match's own copy fails here. The two labels
are written down, because they are the button's copy rather than data.

The confirmation is asked of every frame a `MutationObserver` recorded rather
than of the state the button settled in: a line that flashed for 80 ms is a
line a fan can read, and `CLAUDE.md` counts it.
"""

import pytest

from tests.browser.conftest import LISTENERS, MOMENT_CARD, PLAY_OFFERED

#: The button's own copy. `tests/test_screen_copy.py` holds the markup to the
#: same two strings.
SHARE_LABEL = "SHARE"
COPIED_LABEL = "LINK COPIED"

#: What the card's own script allows the confirmation, from `COPIED_MS`.
COPIED_MS = 1500

#: A share sheet that records what it was given instead of opening one.
SHARE_SHEET = """
window.__shared = [];
Object.defineProperty(navigator, 'share', {
  configurable: true,
  value: function (data) {
    window.__shared.push(data);
    return Promise.resolve();
  },
});
"""

#: No share sheet, which is every desktop browser and some phones. The
#: property is defined as undefined rather than deleted, because the real one
#: lives on the prototype.
NO_SHARE_SHEET = """
Object.defineProperty(navigator, 'share', {
  configurable: true, value: undefined,
});
"""

#: A clipboard that refuses. This is what a browser does when the page is not
#: the active document, when the permission is denied, and on Safari outside a
#: gesture it recognises.
CLIPBOARD_REFUSES = """
Object.defineProperty(navigator, 'clipboard', {
  configurable: true,
  value: {
    writeText: function () {
      return Promise.reject(new DOMException('denied', 'NotAllowedError'));
    },
  },
});
"""

#: No clipboard at all, which is any page outside a secure context. Reaching
#: `writeText` through this throws rather than rejecting, so it is the other
#: half of the same rule.
NO_CLIPBOARD = """
Object.defineProperty(navigator, 'clipboard', {
  configurable: true, value: undefined,
});
"""

#: Every state the button's label passed through, recorded from before the
#: page's own scripts run. The same method the label and the launch screen are
#: checked with.
WATCH_THE_BUTTON = """
window.__shareFrames = [];
(function () {
  function read() {
    const root = document.documentElement;
    const label = root ? document.getElementById('shareLabel') : null;
    const icon = root ? document.getElementById('shareIcon') : null;
    if (!label) return;
    window.__shareFrames.push({
      label: label.textContent,
      icon: icon ? icon.textContent : null,
    });
  }
  read();
  const observer = new MutationObserver(read);
  document.addEventListener('DOMContentLoaded', function () {
    read();
    observer.observe(document.documentElement, {
      subtree: true, childList: true, characterData: true,
    });
  });
})();
"""

BUTTON = """() => {
  const label = document.getElementById('shareLabel');
  const icon = document.getElementById('shareIcon');
  const action = document.getElementById('shareAction');
  return {
    label: label ? label.textContent : null,
    icon: icon ? icon.textContent : null,
    labelled: !!(icon && icon.getAttribute('aria-hidden') === 'true'),
    text: action ? action.getAttribute('data-share-text') : null,
  };
}"""


def open_card(fan, match_id, listener, *scripts):
    """The card, settled, with `scripts` installed before any of its own."""
    fan.remember(match_id=match_id, listener=listener)
    for script in scripts:
        fan.page.add_init_script(script)
    fan.page.add_init_script(WATCH_THE_BUTTON)
    fan.visit(MOMENT_CARD, match=match_id)
    fan.page.wait_for_function(PLAY_OFFERED)
    return fan.page


def frames(fan):
    return fan.page.evaluate("() => window.__shareFrames || []")


def said_copied(fan):
    return [one for one in frames(fan) if COPIED_LABEL in (one["label"] or "")]


@pytest.mark.parametrize("listener", LISTENERS)
def test_the_share_sheet_is_given_the_link_and_the_line(
    fan, match_ids, matches, listener
):
    """With a share sheet, nothing is copied and nothing is confirmed: the
    sheet is the confirmation."""
    for match_id in match_ids:
        page = open_card(fan, match_id, listener, SHARE_SHEET)
        page.click("#shareAction")
        shared = page.evaluate("() => window.__shared")
        assert len(shared) == 1, (match_id, listener, shared)
        one = shared[0]
        assert one["url"] == page.url, (match_id, one)
        assert one["title"] == "Listen on Prelude.", (match_id, one)
        # The line is the match's own, out of matches.json rather than written
        # down here, so the card showing one match's line over another's goal
        # fails.
        assert one["text"] == matches[match_id]["hero"]["share_text"], (
            match_id, one,
        )
        assert page.evaluate(BUTTON)["label"] == SHARE_LABEL
        assert not said_copied(fan), frames(fan)
        assert not fan.errors, fan.errors


def test_the_button_says_what_it_sends(fan, match_ids):
    """The label is the thing it does. It offered a clip before, and a clip is
    not among the three inputs or anything built from them.

    **The name a reader hears is the name this asks for**, through the role
    selector, which is Chromium's own accessible-name computation and not the
    element's text. Measured on 2026-11-15, this button was named "ios_share
    SHARE" and the one beside it "replay_10 REPLAY 10S": a Material Symbol
    span holds a ligature, and the ligature was being read out as a word
    before the label. Both icons are hidden from a reader now.
    """
    for match_id in match_ids:
        page = open_card(fan, match_id, "neutral", SHARE_SHEET)
        state = page.evaluate(BUTTON)
        assert state["label"] == SHARE_LABEL, (match_id, state)
        assert state["labelled"] is True, (match_id, state)
        named = page.get_by_role("button", name=SHARE_LABEL, exact=True)
        assert named.count() == 1, (match_id, state)
        beside = page.get_by_role("button", name="REPLAY 10S", exact=True)
        assert beside.count() == 1, match_id


def test_without_a_share_sheet_the_link_goes_to_the_clipboard(fan, match_ids):
    """The clipboard is read back rather than the write being watched: what
    the button promises is that the link is on the clipboard."""
    fan.context.grant_permissions(
        ["clipboard-read", "clipboard-write"], origin=fan.server.base,
    )
    for match_id in match_ids:
        page = open_card(fan, match_id, "neutral", NO_SHARE_SHEET)
        page.click("#shareAction")
        page.wait_for_function(
            "() => document.getElementById('shareLabel').textContent === %r"
            % COPIED_LABEL
        )
        held = page.evaluate("() => navigator.clipboard.readText()")
        assert held == page.url, (match_id, held)
        state = page.evaluate(BUTTON)
        assert state["label"] == COPIED_LABEL, (match_id, state)
        assert state["icon"] == "done", (match_id, state)
        assert not fan.errors, fan.errors


def test_the_confirmation_stands_down_and_the_button_is_a_share_button_again(
    fan, match_ids
):
    fan.context.grant_permissions(
        ["clipboard-read", "clipboard-write"], origin=fan.server.base,
    )
    for match_id in match_ids:
        page = open_card(fan, match_id, "neutral", NO_SHARE_SHEET)
        page.click("#shareAction")
        page.wait_for_function(
            "() => document.getElementById('shareLabel').textContent === %r"
            % SHARE_LABEL,
            timeout=COPIED_MS + 4000,
        )
        state = page.evaluate(BUTTON)
        assert state["label"] == SHARE_LABEL, (match_id, state)
        assert state["icon"] == "ios_share", (match_id, state)


def test_a_refused_copy_says_nothing(fan, match_ids):
    """`writeText` rejects. Nothing was copied, so no frame of the button may
    say that anything was."""
    for match_id in match_ids:
        page = open_card(fan, match_id, "neutral",
                         NO_SHARE_SHEET, CLIPBOARD_REFUSES)
        page.click("#shareAction")
        # Longer than the confirmation would have stood, so a confirmation
        # that appeared and went is still caught by the recorded frames.
        page.wait_for_timeout(COPIED_MS + 500)
        assert not said_copied(fan), (match_id, frames(fan))
        state = page.evaluate(BUTTON)
        assert state["label"] == SHARE_LABEL, (match_id, state)
        assert state["icon"] == "ios_share", (match_id, state)
        assert not fan.errors, fan.errors


def test_no_clipboard_at_all_says_nothing_either(fan, match_ids):
    """Outside a secure context there is no `navigator.clipboard`, so reaching
    `writeText` throws where the refusal rejects. The card takes neither as
    something to announce, and neither leaves an error on the page."""
    for match_id in match_ids:
        page = open_card(fan, match_id, "neutral",
                         NO_SHARE_SHEET, NO_CLIPBOARD)
        page.click("#shareAction")
        page.wait_for_timeout(COPIED_MS + 500)
        assert not said_copied(fan), (match_id, frames(fan))
        assert page.evaluate(BUTTON)["label"] == SHARE_LABEL, match_id
        assert not fan.errors, fan.errors
        assert not fan.console, fan.console
