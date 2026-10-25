"""Pages lets browsers keep files for 10 minutes, so a page opened soon after a
new version is published can be the old one. The deploy puts the commit on
app.js's address (app.js?v=<commit>); the page checks it against version.json
and loads itself again if it's old, and fetches the scores with the same ?v=.
"""

import json

from playwright.sync_api import sync_playwright

SET_VOICE = 'localStorage.setItem("choir.voice", \'"Alto"\')'
OURS = "aaaaaaa"


def open_published(p, server, published):
    """The page as the deploy leaves it, from commit OURS, with version.json
    saying `published` is the newest; returns how often it loaded and the
    scores it asked for."""
    page = p.chromium.launch().new_page()
    page.add_init_script(SET_VOICE)
    loads, scores = [], []

    def index(route):
        loads.append(1)
        html = route.fetch().text().replace('app.js"', f'app.js?v={OURS}"')
        route.fulfill(body=html, content_type="text/html")

    page.route(f"{server}/", index)
    page.route("**/version.json", lambda route: route.fulfill(
        body=json.dumps({"commit": published + "0" * 33, "date": "2026-10-25T16:00:00+01:00"}),
        content_type="application/json"))
    page.on("request", lambda r: "/scores/" in r.url and scores.append(r.url))
    page.goto(f"{server}/#ave")
    # the date is shown once the page is staying: waiting for it outlasts a reload
    page.wait_for_selector("#updated:not([hidden])", state="attached")
    page.wait_for_function("songId === 'ave' && !loading")
    return page, loads, scores


def test_an_up_to_date_page_stays_and_asks_for_this_versions_scores(server):
    with sync_playwright() as p:
        page, loads, scores = open_published(p, server, OURS)
        assert len(loads) == 1
        assert page.is_visible("#player")
        assert scores and all(url.endswith(f"?v={OURS}") for url in scores)


def test_an_old_page_loads_the_new_version_once(server):
    # the reload here still gets the old page, as from a cache that's slow to
    # catch up: it tries once, then carries on with the old one
    with sync_playwright() as p:
        page, loads, _ = open_published(p, server, "bbbbbbb")
        page.wait_for_timeout(500)
        assert len(loads) == 2
        assert page.is_visible("#player")
