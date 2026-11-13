"""Every screen, both matches, every listener state: nothing throws, nothing 404s.

`app/web/match-content.js` is shared, so a change for one screen is a change
for all seven. Task 29's run was seven screens by two matches by four listener
states, 56 loads, looking for a console error, a page error and a request that
came back 404. That run was a throwaway script; this is it kept.

The one 404 a load is allowed is `/favicon.ico`, which the browser asks for on
its own and which no screen links to.

What the screens load from a CDN, Tailwind and the three font families, is not
counted here: the suite serves `app/web/` and not those, the deployed site
loads them from the same places, and a slow or blocked CDN is not the screens
being broken. `OUTSIDE` in the conftest is the list, and `fan.outside` keeps
what those hosts failed to answer for a reader to look at.

The scanner is here too, and it is the one screen a camera is needed for. It is
loaded rather than used: the camera is refused in a headless run, so what this
asks of it is that it renders and does not throw, which is what Task 29 asked.
`tests/test_match_choice.py` holds what it does with a ticket.
"""

import pytest

from tests.browser.conftest import ALL_SCREENS, LISTENERS, MATCH_REQUIRED, PICKER

#: A fan who has not answered "Who are you with" yet, beside the three who
#: have. `None` writes nothing.
LISTENER_STATES = (None,) + LISTENERS


@pytest.mark.parametrize("screen", ALL_SCREENS)
def test_the_screen_loads_without_an_error(fan, screen, match_ids):
    """Both matches by the four listener states, on this one screen."""
    seen = []
    for match_id in match_ids:
        for listener in LISTENER_STATES:
            fan.remember(match_id=match_id, listener=listener)
            fan.goto(screen, match=match_id)
            fan.page.wait_for_load_state("domcontentloaded")
            fan.page.wait_for_timeout(250)
            seen.append((screen, match_id, listener))
    assert not fan.errors, (fan.errors, seen)
    assert not fan.console, (fan.console, seen)
    assert not fan.unexpected_404s(), (fan.unexpected_404s(), seen)


@pytest.mark.parametrize("screen", MATCH_REQUIRED)
def test_the_screen_renders_the_match_in_the_url(fan, screen, match_ids, matches):
    """And it renders the one in the URL, not the one in its own markup.

    The inline copy on every screen but the list is the 1986 match, so a
    screen that rendered its markup rather than the fetch would pass the 1986
    load and fail this one.
    """
    for match_id in match_ids:
        fan.remember(match_id=match_id, listener="team_a")
        fan.visit(screen, match=match_id)
        rendered = fan.page.evaluate(
            "() => document.documentElement.getAttribute('data-match-rendered')"
        )
        assert rendered == str(match_id), (screen, match_id, rendered)


def test_the_list_carries_the_match_through_its_links(fan, match_ids):
    """Every local link on a screen about one match passes that match on, so a
    fan never arrives at a screen that has to send them back."""
    for match_id in match_ids:
        for screen in MATCH_REQUIRED:
            fan.remember(match_id=match_id, listener="neutral")
            fan.visit(screen, match=match_id)
            links = fan.page.evaluate(
                """() => Array.from(document.querySelectorAll('a[href]'))
                     .map(a => a.getAttribute('href'))
                     .filter(h => /\\.html/.test(h))"""
            )
            assert links, (screen, match_id)
            for href in links:
                assert "match=%d" % match_id in href, (screen, match_id, href)


def test_the_list_links_carry_no_match_before_one_is_chosen(fan):
    page = fan.goto(PICKER)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(300)
    links = page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href]'))
             .map(a => a.getAttribute('href'))
             .filter(h => /\\.html/.test(h))"""
    )
    for href in links:
        assert "match=" not in href, href
