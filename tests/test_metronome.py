"""The metronome shouldn't lose ticks when the browser is briefly busy.

Notes and ticks are handed to the audio a little ahead of time. A tick is a
30ms click, so if a phone is busy for longer than that margin and the tick is
handed over after its time, it's cut short or lost. This plays a song with
the page stalling for 150ms every so often, as a phone does, and checks every
tick was handed over before it was due.
"""

from playwright.sync_api import sync_playwright

STALL_MS = 150

# notes how far ahead of its time each tick is handed to the audio
RECORD_TICKS = """
window.ahead = [];
const trigger = click.triggerAttackRelease.bind(click);
click.triggerAttackRelease = (note, duration, time) => {
  if (note) ahead.push(time - audioContext.currentTime);
  return trigger(note, duration, time);
};
"""


def test_ticks_survive_the_page_stalling(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script('localStorage.setItem("choir.voice", \'"Bass"\')')
        page.add_init_script('localStorage.setItem("choir.clickVolume", "60")')
        page.goto(f"{server}/#no")
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        page.evaluate(RECORD_TICKS)
        page.evaluate(f"""setInterval(() => {{
          const start = performance.now();
          while (performance.now() - start < {STALL_MS});
        }}, 1300)""")
        page.click("#play")
        page.wait_for_function("ahead.length >= 16", timeout=30_000)
        ahead = page.evaluate("ahead")
        browser.close()

    late = [round(a * 1000) for a in ahead if a <= 0]
    assert not late, f"ticks handed over this many ms after their time: {late}"
