"""Ave Verum Corpus, soprano bars 12 and 17: the edition writes A, G sharp,
G with no accidental, so the sharp carries on and both Gs are G sharp.
(Bar 4 is different: there the last G has a natural.)"""

from playwright.sync_api import sync_playwright

G, G_SHARP, A = 67, 68, 69
SOPRANO = "song.parts.find(p => p.name === 'Soprano').notes"
# soprano pitches drawn in a bar (1-based), as OpenSheetMusicDisplay draws them
DRAWN = """bar => {
  const soprano = osmd.Sheet.Instruments.find(i => i.Name === 'Soprano');
  const pitches = [];
  for (const row of osmd.GraphicSheet.MeasureList) for (const measure of row) {
    if (!measure || measure.ParentStaff.ParentInstrument !== soprano) continue;
    if (measure.MeasureNumber !== bar) continue;
    for (const entry of measure.staffEntries) for (const voice of entry.graphicalVoiceEntries)
      for (const note of voice.notes) if (!note.sourceNote.isRest()) pitches.push(note.sourceNote.halfTone);
  }
  return pitches;
}"""


def played(page, bar):
    start, end = page.evaluate(f"[song.measures[{bar - 1}], song.measures[{bar}]]")
    return [n[0] for n in page.evaluate(SOPRANO) if start <= n[1] < end]


def test_soprano_bars_12_and_17_are_g_sharp(server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{server}/?director#ave")
        page.wait_for_function("songId === 'ave' && !loading")
        assert played(page, 12) == [A, G_SHARP, G_SHARP]
        assert played(page, 17) == [A, G_SHARP, G_SHARP]
        assert played(page, 4) == [A, G_SHARP, G]  # this one does have a natural
        # OSMD's halfTone is MIDI pitch - 12
        assert page.evaluate(DRAWN, 12) == [A - 12, G_SHARP - 12, G_SHARP - 12]
        assert page.evaluate(DRAWN, 17) == [A - 12, G_SHARP - 12, G_SHARP - 12]
        browser.close()


def test_soprano_bars_12_and_17_print_one_sharp():
    """As in the edition: a sharp on the first G only, no sign on the second."""
    import xml.etree.ElementTree as ET
    from pathlib import Path
    xml = ET.parse(Path(__file__).parent.parent / "player/static/scores/ave.musicxml")
    soprano = xml.find("part")
    for bar in ("12", "17"):
        notes = [n for n in soprano.find(f"measure[@number='{bar}']").iter("note")
                 if n.find("pitch") is not None]
        assert [n.findtext("accidental") for n in notes] == [None, "sharp", None]
