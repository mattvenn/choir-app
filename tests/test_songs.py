"""The song list: the junior choir's songs are listed under "Jóvenes", and
each opens with its score drawn and every bar there to play."""

from playwright.sync_api import sync_playwright

ALL = ["Soprano", "Alto", "Tenor", "Baritone"]
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
        assert [t for t in jovenes if t.startswith(("Triste", "Ich", "Wellcome", "Agnus", "Esa"))] == [
            "Triste reloj", "Ich grolle nicht", "Wellcome", "Agnus Dei", "Esa estrella que brilla"]
        main = listed[:listed.index("Jóvenes")]
        assert not [t for t in main if t.startswith(("Agnus", "Esa"))]
        assert page.evaluate("song.title") == "Ich grolle nicht"
        assert page.evaluate("song.measures.length") == 36
        assert page.evaluate(DRAWN) == ALL
        # Wellcome (Daniel Basomba) is for soprano, alto and baritone, 26 bars
        page.goto(f"{server}/?director#wellcome")
        page.wait_for_function("songId === 'wellcome' && !loading")
        assert page.evaluate("song.title") == "Wellcome"
        assert page.evaluate("song.measures.length") == 26
        assert page.evaluate(DRAWN) == ["Soprano", "Alto", "Baritone"]
        # Dani's version of 3 November 2026: the altos (Alto 1) now start in bar 1
        page.goto(f"{server}/?director#triste")
        page.wait_for_function("songId === 'triste' && !loading")
        alto1 = page.evaluate("song.parts.find(p => p.name === 'Alto').notes[0]")
        assert alto1[:2] == [65, 0]  # F4, at the start
        browser.close()


def test_agnus_and_esa_open(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{server}/?director#esa")
        page.wait_for_function("songId === 'esa' && !loading")
        # the repeats written out: 65 bars, or 33 without them
        assert page.evaluate("song.measures.length") == 33
        assert page.evaluate(DRAWN) == ["Soprano 1", "Soprano 2", "Baritone", "Cello"]
        page.click("#repeats")
        page.wait_for_function("!loading && song.measures.length === 65")
        page.goto(f"{server}/?director#agnus")
        page.wait_for_function("songId === 'agnus' && !loading")
        assert page.evaluate("song.title") == "Agnus Dei"
        assert page.evaluate("song.measures.length") == 55
        assert page.evaluate(DRAWN) == ALL
        # Dani's corrections of 13 November 2026: altos and tenors sing
        # "mun" in bar 46 and "di do" (half, quarter) in bar 47 like the
        # others, and end on B3 and G sharp 3
        bar47 = """name => { const s = song.measures[46], e = song.measures[47];
            return song.parts.find(p => p.name === name).notes
                .filter(n => n[1] >= s && n[1] < e).map(n => [n[0], n[1] - s, n[2]]); }"""
        assert page.evaluate(bar47, "Alto") == [[61, 0, 2], [61, 2, 1]]
        assert page.evaluate(bar47, "Tenor") == [[58, 0, 2], [58, 2, 1]]
        last = "name => song.parts.find(p => p.name === name).notes.at(-1)[0]"
        assert page.evaluate(last, "Alto") == 59  # B3
        assert page.evaluate(last, "Tenor") == 56  # G#3
        browser.close()


# the words under one part's bar of a built score, as the app loads it
LYRICS = """async ([id, part, bar]) => {
    const xml = new DOMParser().parseFromString(
        await (await fetch(`scores/${id}.musicxml`)).text(), "application/xml");
    const parts = [...xml.querySelectorAll("score-part")];
    const pid = parts.find(p => p.querySelector("part-name").textContent === part).id;
    const m = xml.querySelector(`part[id="${pid}"] > measure[number="${bar}"]`);
    return [...m.querySelectorAll("note")].map(n =>
        n.querySelector("lyric text")?.textContent ?? null);
}"""


def test_esa_baritone_sings_jesus_in_bar_49(server):
    """Dani, 13 November 2026: in the app's bar 49 (the score's bar 29) the
    baritone's note had no "sús"; it's sung like the sopranos'."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{server}/?director#esa")
        page.wait_for_function("songId === 'esa' && !loading")
        assert page.evaluate(LYRICS, ["esa", "Baritone", 49]) == ["sús.", None]
        # without repeats, the bar keeps the score's number
        assert page.evaluate(LYRICS, ["esa-short", "Baritone", 29]) == ["sús.", None]
        browser.close()
