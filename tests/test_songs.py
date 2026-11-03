"""The song list: the junior choir's songs are listed under "Jóvenes", and
each opens with its score drawn and every bar there to play."""

from playwright.sync_api import sync_playwright

ALL = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
DRAWN = "song.parts.filter((_, i) => osmd.Sheet.Instruments[i].Visible).map(p => p.name)"
LIST = """[...document.querySelectorAll("#song-list li")].map(li => li.textContent.trim())"""


def test_jovenes_songs_listed_and_open(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{server}/?director#ich")
        page.wait_for_function("songId === 'ich' && !loading")
        listed = page.evaluate(LIST)
        jovenes = listed[listed.index("Jóvenes") + 1:]
        assert [t for t in jovenes if t.startswith(("Triste", "Ich"))] == [
            "Triste reloj", "Ich grolle nicht"]
        assert page.evaluate("song.title") == "Ich grolle nicht"
        assert page.evaluate("song.measures.length") == 36
        assert page.evaluate(DRAWN) == ALL
        # Dani's version of 3 November 2026: Alto 1 now starts in bar 1
        page.goto(f"{server}/?director#triste")
        page.wait_for_function("songId === 'triste' && !loading")
        alto1 = page.evaluate("song.parts.find(p => p.name === 'Alto 1').notes[0]")
        assert alto1[:2] == [65, 0]  # F4, at the start
        browser.close()
