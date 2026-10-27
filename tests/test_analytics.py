"""Google Analytics counts page views by title, so a page must report the same
title whichever language it's shown in, or it's counted as two pages.
"""

from playwright.sync_api import sync_playwright

SET_VOICE = 'localStorage.setItem("choir.voice", \'"Alto"\')'
PAGE_VIEWS = """dataLayer.filter(a => a[0] === "event" && a[1] === "page_view")
  .map(a => [a[2].page_location.replace(location.origin, ""), a[2].page_title])"""


def page_views(p, server, lang):
    """The page views sent on opening the home page and then a song."""
    page = p.chromium.launch().new_page()
    page.add_init_script(SET_VOICE)
    page.goto(f"{server}/?lang={lang}")
    page.wait_for_selector("#home:not([hidden])")
    page.evaluate("location.hash = 'ave'")
    page.wait_for_function("songId === 'ave' && !loading")
    page.wait_for_function(f"({PAGE_VIEWS}).length === 2")
    return page.evaluate(PAGE_VIEWS)


def test_page_views_are_the_same_in_english_and_spanish(server):
    with sync_playwright() as p:
        english = page_views(p, server, "en")
        spanish = page_views(p, server, "es")
    assert english == spanish
    assert english == [["/", "Choir Practice"], ["/ave", "Ave Verum Corpus"]]


EVENTS = """name => dataLayer.filter(a => a[0] === "event" && a[1] === name)
  .map(a => a[2])"""


def test_moving_the_others_slider_is_counted_once_when_let_go(server):
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.add_init_script(SET_VOICE)
        page.goto(f"{server}/#ave")
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        # a drag: many inputs, then one change on letting go
        page.evaluate("""() => {
          const slider = document.getElementById("others");
          for (const value of [5, 10, 15, 20]) {
            slider.value = value;
            slider.dispatchEvent(new Event("input", { bubbles: true }));
          }
          slider.dispatchEvent(new Event("change", { bubbles: true }));
        }""")
        events = page.evaluate(f"({EVENTS})('others_volume')")
    assert events == [{"song": "ave", "others": 20}]


def test_play_says_how_loud_the_others_are(server):
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.add_init_script(SET_VOICE)
        page.add_init_script('localStorage.setItem("choir.others.ave", "35")')
        page.goto(f"{server}/#ave")
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        page.click("#play")
        page.wait_for_function(f"({EVENTS})('play').length === 1")
        events = page.evaluate(f"({EVENTS})('play')")
    assert events == [{"song": "ave", "others": 35}]
