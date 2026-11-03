"""Each voice gets its own line: in every song, Tenor and Bass open on
different parts, unless the song is listed below as one where the men share a
line. Ich grolle nicht's four lines are all sung, so its tenors sing the third
line, Alto 2 (treble clef), and its basses the Baritone.
"""

import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

SCORES = Path(__file__).parent.parent / "player" / "static" / "scores"
SONGS = [s["id"] for s in json.loads((SCORES / "index.json").read_text())]

# songs whose tenors and basses both sing the one Baritone line, as the app has
# done since the voice picker came in
SHARED = {"foc", "shalala", "triste"}

# per song, the line each voice opens on where it isn't the voice's own name
EXPECTED = {
    "ich": {"Soprano": ["Soprano"], "Alto": ["Alto 1"],
            "Tenor": ["Alto 2"], "Bass": ["Baritone"]},
}

MINE = "song.parts.filter((_, i) => mine[i]).map(p => p.name)"
DRAWN = "song.parts.filter((_, i) => osmd.Sheet.Instruments[i].Visible).map(p => p.name)"


def lines(page, server, song_id, voice):
    page.evaluate(f"localStorage.setItem('choir.voice', JSON.stringify('{voice}'))")
    page.goto(f"{server}/#{song_id}")
    page.reload()
    page.wait_for_function(f"songId === '{song_id}' && !loading")
    mine, drawn = page.evaluate(MINE), page.evaluate(DRAWN)
    assert mine == drawn, f"{song_id}, {voice}: plays {mine} but shows {drawn}"
    return mine


@pytest.mark.parametrize("song_id", SONGS)
def test_tenor_and_bass_get_their_own_line(server, song_id):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(server)
        got = {v: lines(page, server, song_id, v) for v in ["Soprano", "Alto", "Tenor", "Bass"]}
        browser.close()
    if song_id in EXPECTED:
        assert got == EXPECTED[song_id]
    if song_id in SHARED:
        assert got["Tenor"] == got["Bass"] == ["Baritone"]
    else:
        assert got["Tenor"] != got["Bass"], f"{song_id}: tenors and basses both get {got['Bass']}"
