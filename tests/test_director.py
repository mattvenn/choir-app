"""The director's view, for checking the scores: ?director shows and plays
every part, starts each song without repeats so the bar numbers are the
score's, and a tap on a note opens a report of it to send on WhatsApp or by
email.
"""

import urllib.parse

from playwright.sync_api import sync_playwright

MINE = "song.parts.filter((_, i) => mine[i]).map(p => p.name)"
DRAWN = "song.parts.filter((_, i) => osmd.Sheet.Instruments[i].Visible).map(p => p.name)"
ALL = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
# the note head of Alto 2's first note in printed bar 38
NOTE = """[...noteInfo].find(([, n]) => n.index === 37 && n.part === "Alto 2" && n.place === 1)[0]"""


def test_director_sees_every_part_without_repeats_and_reports_a_note(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="es-ES")
        # no voice asked: the director's are all of them
        page.goto(f"{server}/?director#triste")
        page.wait_for_function("songId === 'triste' && !loading")
        assert page.evaluate(MINE) == ALL
        assert page.evaluate(DRAWN) == ALL
        assert page.get_attribute("#repeats", "aria-pressed") == "false"
        assert page.evaluate("song.measures.length") == 58  # each bar once
        assert page.is_hidden(".others")

        note = page.evaluate_handle(NOTE).as_element()
        note.scroll_into_view_if_needed()
        box = note.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_selector("#report:not([hidden])")
        what = "Triste reloj, compás 38, Alto 2: nota 1 (Do♯4, «por»)"
        assert page.text_content("#report-what") == what
        # no number in the link: WhatsApp asks who to send it to
        href = page.get_attribute("#report-send", "href")
        assert href.startswith("https://wa.me/?text=")
        assert urllib.parse.unquote(href.split("=", 1)[1]) == f"{what}\n{server}/#triste\n\n"
        # nor an address in the email
        email = urllib.parse.urlparse(page.get_attribute("#report-email", "href"))
        assert (email.scheme, email.path) == ("mailto", "")
        fields = urllib.parse.parse_qs(email.query)
        assert fields["subject"] == ["Triste reloj, compás 38"]
        assert fields["body"] == [f"{what}\n{server}/#triste\n\n"]
        # nothing played: the tap was for the report
        assert page.evaluate("Tone.getTransport().state") != "started"

        page.keyboard.press("Escape")
        assert page.is_hidden("#report")

        # kept for this browser, until ?director=no
        page.goto(f"{server}/#foc")
        page.wait_for_function("songId === 'foc' && !loading")
        assert page.evaluate(MINE) == ALL
        page.goto(f"{server}/?director=no")
        page.wait_for_selector("#voice-picker:not([hidden])")
        browser.close()
