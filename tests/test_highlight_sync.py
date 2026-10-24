"""The highlighted bar should move when the bar is heard, not when it's worked out.

On a phone, and over Bluetooth especially, sound comes out a good while after
the audio graph has worked it out (the output buffer, then the headphones' own
delay). A desktop browser has next to none, so this fakes a phone's: the page's
AudioContext reports the delays below, and each time a bar is highlighted the
test checks where the transport was that long ago, which is what's being heard.

The app goes by the output timestamp (which moment of the audio is coming out
now), or, where there isn't one, by the two latencies added up. Each is faked
on its own, with a different delay, so the test shows which one was used.

    .venv/bin/pip install -r tests/requirements.txt
    .venv/bin/playwright install chromium
    .venv/bin/pytest tests
"""

import pytest
from playwright.sync_api import sync_playwright

BASE_LATENCY = 0.1    # seconds: a "playback" output buffer
OUTPUT_LATENCY = 0.3  # seconds: Bluetooth headphones
# seconds: the whole delay, as the output timestamp has it; far enough from
# the two added up for the test to tell which was used
STAMP_DELAY = 0.55
# the highlight is drawn on the next animation frame, a few times a second
# headless; well under the delay being faked
TOLERANCE = 0.06

FAKE_LATENCY = f"""
for (const [name, value] of [["baseLatency", {BASE_LATENCY}], ["outputLatency", {OUTPUT_LATENCY}]]) {{
  Object.defineProperty(AudioContext.prototype, name, {{ get: () => value }});
}}
"""
# the moment coming out now is STAMP_DELAY behind the one being worked out
FAKE_STAMP = f"""
AudioContext.prototype.getOutputTimestamp = function () {{
  return {{ contextTime: this.currentTime - {STAMP_DELAY}, performanceTime: performance.now() }};
}};
"""
# as before the audio has started, or in a browser without it
NO_STAMP = """
AudioContext.prototype.getOutputTimestamp = () => ({ contextTime: 0, performanceTime: 0 });
"""

# Wraps showBar to note, for each bar highlighted, how far off what's heard is,
# when the sound takes `delay` seconds to come out.
RECORD_BARS = """delay => {
window.bars = [];
const shownBar = showBar;
showBar = index => {
  // the first bar, shown early, would be looked up from before the transport started
  if (transport.state === "started" && index > 0) {
    const heardAt = Tone.getContext().currentTime - delay;
    const ticksOff = transport.getTicksAtTime(heardAt) - barTicks[index];
    bars.push({ index, off: ticksOff / transport.PPQ * 60 / transport.bpm.value });
  }
  shownBar(index);
};
}"""


@pytest.mark.parametrize("stamp, delay", [
    (FAKE_STAMP, STAMP_DELAY),
    (NO_STAMP, BASE_LATENCY + OUTPUT_LATENCY),
], ids=["output timestamp", "latencies, without one"])
def test_highlight_follows_what_is_heard(server, stamp, delay):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script(FAKE_LATENCY)
        page.add_init_script(stamp)
        # past the first visit's question
        page.add_init_script('localStorage.setItem("choir.voice", \'"Bass"\')')
        page.goto(f"{server}/#ave")
        # the piano samples come from the network
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        page.evaluate(RECORD_BARS, delay)
        page.click("#play")
        page.wait_for_function("bars.length >= 4", timeout=30_000)
        bars = page.evaluate("bars")
        browser.close()

    for bar in bars:
        assert abs(bar["off"]) < TOLERANCE, (
            f"bar {bar['index'] + 1} highlighted {-bar['off']:.3f}s before it was heard"
        )
