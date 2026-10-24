"""The highlighted bar should move when the bar is heard, not when it's worked out.

On a phone, and over Bluetooth especially, sound comes out a good while after
the audio graph has worked it out (the output buffer, then the headphones' own
delay). A desktop browser has next to none, so this fakes a phone's: the page's
AudioContext reports the delays below, and each time a bar is highlighted the
test checks where the transport was that long ago, which is what's being heard.

    .venv/bin/pip install -r tests/requirements.txt
    .venv/bin/playwright install chromium
    .venv/bin/pytest tests
"""

import functools
import http.server
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

STATIC = Path(__file__).parent.parent / "player" / "static"

BASE_LATENCY = 0.1    # seconds: a "playback" output buffer
OUTPUT_LATENCY = 0.3  # seconds: Bluetooth headphones
# the highlight is drawn on the next animation frame, a few times a second
# headless; well under the delay being faked
TOLERANCE = 0.06

FAKE_LATENCY = f"""
for (const [name, value] of [["baseLatency", {BASE_LATENCY}], ["outputLatency", {OUTPUT_LATENCY}]]) {{
  Object.defineProperty(AudioContext.prototype, name, {{ get: () => value }});
}}
"""

# Wraps showBar to note, for each bar highlighted, how far off what's heard is.
RECORD_BARS = f"""
window.bars = [];
const shownBar = showBar;
showBar = index => {{
  // the first bar, shown early, would be looked up from before the transport started
  if (transport.state === "started" && index > 0) {{
    const heardAt = Tone.getContext().currentTime - {BASE_LATENCY + OUTPUT_LATENCY};
    const ticksOff = transport.getTicksAtTime(heardAt) - barTicks[index];
    bars.push({{ index, off: ticksOff / transport.PPQ * 60 / transport.bpm.value }});
  }}
  shownBar(index);
}};
"""


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=STATIC)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_highlight_follows_what_is_heard(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script(FAKE_LATENCY)
        page.goto(f"{server}/#ave")
        # the piano samples come from the network
        page.wait_for_selector("#play:not([disabled])", timeout=60_000)
        page.evaluate(RECORD_BARS)
        page.click("#play")
        page.wait_for_function("bars.length >= 4", timeout=30_000)
        bars = page.evaluate("bars")
        browser.close()

    for bar in bars:
        assert abs(bar["off"]) < TOLERANCE, (
            f"bar {bar['index'] + 1} highlighted {-bar['off']:.3f}s before it was heard"
        )
