"""A first visit asks which voice you sing; each song then shows and plays it,
with a slider to bring the other voices in.

Songs don't all have the same parts: some are Soprano, Alto, Tenor, Bass and
some Soprano, Alto 1, Alto 2, Baritone, so each voice has to find its part in
either.
"""

import pytest
from playwright.sync_api import sync_playwright

# voice: its parts in an SATB song and in a S/A1/A2/Bar one
CASES = {
    "Soprano": (["Soprano"], ["Soprano"]),
    "Alto": (["Alto"], ["Alto 1"]),  # split, so the first to start with
    "Tenor": (["Tenor"], ["Baritone"]),
    "Bass": (["Bass"], ["Baritone"]),
}

MINE = "song.parts.filter((_, i) => mine[i]).map(p => p.name)"
DRAWN = "song.parts.filter((_, i) => osmd.Sheet.Instruments[i].Visible).map(p => p.name)"
# where the others' volume is heading: before play, the audio clock hasn't started
OTHERS_GAIN = "othersGain.gain.getValueAtTime(Tone.now() + 1)"
SET_VOICE = 'localStorage.setItem("choir.voice", \'"Alto"\')'


def open_song(page, server, song_id):
    page.goto(f"{server}/#{song_id}")
    page.wait_for_function(f"songId === '{song_id}'")


def set_slider(page, value):
    page.eval_on_selector(
        "#others", f"el => {{ el.value = {value}; el.dispatchEvent(new Event('input')); }}")


@pytest.mark.parametrize("voice", CASES)
def test_first_visit_asks_voice_and_songs_start_on_it(server, voice):
    satb, upper = CASES[voice]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # a shared link, opened for the first time, still asks first
        page.goto(f"{server}/#ave")
        page.wait_for_selector("#voice-picker:not([hidden])")
        assert page.is_hidden("#player")
        page.click(f"#voice-list button:text-is('{voice}')")
        page.wait_for_function("songId === 'ave'")
        assert page.evaluate(MINE) == satb
        assert page.evaluate(DRAWN) == satb

        open_song(page, server, "foc")
        assert page.evaluate(MINE) == upper
        assert page.evaluate(DRAWN) == upper

        # asked only once
        page.goto(server)
        page.wait_for_selector("#song-list a")
        assert page.is_hidden("#voice-picker")
        assert page.text_content("#change-voice").endswith(voice)
        browser.close()


def test_voice_can_be_changed_from_the_chooser(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script(f"if (!localStorage.getItem('choir.voice')) {SET_VOICE}")
        open_song(page, server, "ave")
        page.click("#home-button")
        page.click("#change-voice")
        page.wait_for_selector("#voice-picker:not([hidden])")
        page.click("#voice-list button:text-is('Tenor')")
        page.click("#song-list a[data-song='ave']")
        page.wait_for_function("mine[2]")
        assert page.evaluate(MINE) == ["Tenor"]
        assert page.evaluate(DRAWN) == ["Tenor"]
        browser.close()


def test_slider_fades_the_others_in_and_is_kept_per_song(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script(SET_VOICE)
        open_song(page, server, "ave")
        # a new song starts on just your part
        assert page.input_value("#others") == "0"
        assert page.evaluate(OTHERS_GAIN) == pytest.approx(0, abs=0.01)

        set_slider(page, 100)
        assert page.evaluate(OTHERS_GAIN) == pytest.approx(1, abs=0.01)

        page.reload()
        page.wait_for_function("songId === 'ave'")
        assert page.input_value("#others") == "100"

        open_song(page, server, "foc")
        assert page.input_value("#others") == "0"
        browser.close()


def test_help_opens_and_closes(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 700})
        page.add_init_script(SET_VOICE)
        page.goto(server)
        page.click("#help-button")
        assert page.evaluate("$('help').open")
        # every control has its icon (the tempo, a note), and it opens at the top
        assert page.locator("#help-controls li").count() == 8
        assert page.evaluate("$('help').scrollTop") == 0
        page.click("#help form button")
        assert not page.evaluate("$('help').open")
        browser.close()


def test_repeats_wait_for_a_pause_and_keep_the_bar(server):
    # where the highlighted bar is on screen
    on_screen = "Math.round(document.getElementById('highlight').getBoundingClientRect().top)"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 844, "height": 390})  # a phone, sideways
        page.add_init_script(SET_VOICE)
        page.goto(f"{server}/#boga")
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        # printed bar 12, second time through, in the written-out version: well
        # down the page, and further down than in the version without repeats
        page.evaluate("seek(song.printedBars.lastIndexOf(12))")
        page.wait_for_function("document.body.classList.contains('playing')")
        # switching would stop the music, so it can't be done while playing
        assert page.is_disabled("#repeats")
        page.click("#play")  # pause
        assert page.is_enabled("#repeats")
        page.wait_for_timeout(500)  # done scrolling to it
        where = page.evaluate(on_screen)

        page.click("#repeats")
        page.wait_for_function("!song.printedBars && currentBar === 11")
        # the same bar, in the same place on screen (to a pixel or two of rounding)
        assert abs(page.evaluate(on_screen) - where) <= 3

        # and back, to the first time through
        page.click("#repeats")
        # the bar is set once the score is redrawn, a moment after the song's data
        page.wait_for_function("!!song.printedBars && currentBar === song.printedBars.indexOf(12)")
        assert abs(page.evaluate(on_screen) - where) <= 3

        # play carries on from there, not from the start
        page.click("#play")
        page.wait_for_function("transport.state === 'started'")
        assert page.evaluate("transport.ticks >= barTicks[song.printedBars.indexOf(12)]")
        browser.close()


def test_repeats_are_remembered_across_songs_and_visits(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script(SET_VOICE)
        page.goto(f"{server}/#boga")
        page.wait_for_function("songId === 'boga' && !loading")
        assert page.get_attribute("#repeats", "aria-pressed") == "true"
        page.click("#repeats")
        page.wait_for_function("!song.printedBars && !loading")

        # another song, and coming back another day, start without them too
        page.goto(f"{server}/#shalala")
        page.wait_for_function("songId === 'shalala' && !loading")
        assert page.get_attribute("#repeats", "aria-pressed") == "false"
        assert page.evaluate("song.measures.length") == 13
        page.reload()
        page.wait_for_function("songId === 'shalala' && !loading")
        assert page.evaluate("song.measures.length") == 13
        browser.close()


@pytest.mark.parametrize("asked, help_text", [("en", "Help"), ("es", "Ayuda"), ("fr", "Help")])
def test_the_address_can_choose_the_language(server, asked, help_text):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="en-GB")
        page.add_init_script(SET_VOICE)
        # one there isn't, like fr, goes by the browser as before
        page.goto(f"{server}/?lang={asked}")
        page.wait_for_selector("#song-list a")
        assert page.text_content("#help-button") == help_text
        # and it stays in a song and back
        page.click("#song-list a[data-song='ave']")
        page.wait_for_function("songId === 'ave'")
        page.click("#home-button")
        assert page.text_content("#help-button") == help_text
        browser.close()


def test_a_split_voice_chooses_its_line(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script(f"if (!localStorage.getItem('choir.voice')) {SET_VOICE}")
        # not split here: no switch
        open_song(page, server, "ave")
        assert page.is_hidden("#part-switch")

        open_song(page, server, "foc")
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        assert page.locator("#part-switch button").all_text_contents() == ["A1", "A2"]
        assert page.evaluate(MINE) == ["Alto 1"]
        page.click("#part-switch button:text-is('A2')")
        page.wait_for_function("mine[2]")
        assert page.evaluate(MINE) == ["Alto 2"]
        assert page.evaluate(DRAWN) == ["Alto 2"]
        assert page.get_attribute("#part-switch button:text-is('A2')", "aria-pressed") == "true"

        # kept for the song
        page.reload()
        page.wait_for_function("songId === 'foc'")
        assert page.evaluate(MINE) == ["Alto 2"]

        # redrawing would hold up the music, so not while playing
        page.click("#play")
        page.wait_for_function("transport.state === 'started'")
        assert page.is_disabled("#part-switch button:text-is('A1')")
        page.click("#play")
        page.wait_for_function("transport.state === 'paused'")
        assert page.is_enabled("#part-switch button:text-is('A1')")
        browser.close()


@pytest.mark.parametrize("meanwhile", [
    "window.dispatchEvent(new Event('resize'))",  # a phone's address bar sliding away
    "document.getElementById('score').dispatchEvent("
    "new MouseEvent('click', {clientX: 150, clientY: 300, bubbles: true}))",
    "document.getElementById('repeats').click()",
], ids=["resize", "tap on the score", "repeats again"])
def test_nothing_reads_a_score_still_loading(server, meanwhile):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 700})
        page.add_init_script(SET_VOICE)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{server}/#boga")
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        # the new score takes a moment to come, as on a phone
        page.route("**/*.musicxml", lambda route: (page.wait_for_timeout(300), route.continue_()))
        page.evaluate(f"document.getElementById('repeats').click(); setTimeout(() => {{ {meanwhile} }}, 30)")
        page.wait_for_function("!song.printedBars && !loading")
        page.wait_for_timeout(500)
        assert errors == []
        assert page.is_visible("#highlight")
        browser.close()
