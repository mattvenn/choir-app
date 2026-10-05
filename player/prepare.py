"""Build the player's score files for Foc de Nadal.

Takes the 4-part Audiveris MusicXML, swaps in the hand-checked baritone, fixes
the bars Audiveris misread, adds the lyrics (Audiveris was run without text
recognition) and writes
  player/static/scores/foc.musicxml  (drawn by OpenSheetMusicDisplay)
  player/static/scores/foc.json      (note events played by the browser piano)

    .venv/bin/python player/prepare.py
"""
import copy
import json
from pathlib import Path

from music21 import converter, dynamics, layout, note, spanner, stream, tempo, tie

ROOT = Path(__file__).resolve().parent.parent
AUDIVERIS = ROOT / "out/audiveris/Foc de nadal.mxl"
BARITONE = ROOT / "out/claude/foc-baritone.musicxml"
OUT = ROOT / "player/static/scores"

TITLE = "Foc de Nadal"
COMPOSER = "D. Basomba"
TEMPO = 100  # quarter notes per minute; the score has no marking
NAMES = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
ABBREVIATIONS = ["S", "A1", "A2", "B"]
# Lyrics transcribed from the PDF, one entry per bar. Each syllable goes on the
# next note that isn't the continuation of a tie: "na-" continues the word on the
# next syllable, "_" holds the previous syllable over this note.
LYRICS = {
    "Soprano": """La | nit de na- | dal fa | fred i ca- | lor el | foc il- lu- |
        mi- na‿els de- | sit- jos de | tots la | nit de na- | dal es- | tre- les al |
        cel si | pa- res l'o- | re- lla se | sen- ten molt | bé i‿el | foc a- com- |
        pa- nya‿amb el | seu cre- pi- | tar cri cri | cri cric ri | cri cri cri | crac |
        i | tots a- bra- | çats _ can- | tem els re- | cords i | els que no‿hi |
        són _ des | de dalt ens | mi- ren La | nit de na- | dal fa | fred i ca- |
        lor el | foc il- lu- | mi- na‿els de- | sit- jos de | tots la | nit de na- |
        dal _ es- | tre- les al | cel""",
    "Alto 1": """ | La nit | de Na- | dal fred | i ca- | lor de- |
        sit- jos | de | tots | La nit | de Na- | dal al |
        cel si | pa- res l'o- | re- lla se | sen- ten molt | bé | el |
        foc | cre- | pi- | ta | cri cri cri | crac |
        | Tots | a | bra- | çats | els que no‿hi |
        són | _ | mi- ren | La nit | de Na- | dal fred |
        i ca- | lor de- | sit- jos | de sit- | jos | nit de Na- |
        dal es- | tre- les al | cel""",
    "Alto 2": """ | La nit | de Na- | dal fred | i ca- | lor de- |
        sit- jos | de _ | tots | La nit | de Na- | dal al |
        cel si | pa- res l'o- | re se _ | sen- ten molt | bé | el |
        foc | cre- | pi- | ta | cri cri cri | crac |
        | Tots | a | bra- | çats | els |
        que no‿hi | són | són | La nit | de Na- | dal fred |
        i ca- | lor de- | sit- jos | de sit- | jos | nit de Na- |
        dal es- | tre- les al | cel""",
    "Baritone": """ | La nit | de _ Na- | dal fred | i ca- | lor de- |
        sit- jos | de | tots | La nit | de _ Na- | dal al |
        cel si | pa- res l'o- | re- lla se | sen- ten molt | bé | el |
        foc _ _ | cre- | pi- | ta | cri | crac |
        | Tots | a | bra- | çats | els |
        que no‿hi | són | són | La nit | de _ Na- | dal fred |
        i ca- | lor de- | sit- jos | de sit- | jos | nit de Na- |
        dal | cel | _""",
}


def build_score() -> stream.Score:
    audiveris = converter.parse(str(AUDIVERIS))
    baritone = converter.parse(str(BARITONE)).parts[0]
    # the ABC import numbers bars from 0 and carries the guessed tempo
    for m in baritone.getElementsByClass(stream.Measure):
        m.number += 1
    for mark in baritone.recurse().getElementsByClass(tempo.MetronomeMark):
        mark.activeSite.remove(mark)

    parts = list(audiveris.parts[:3]) + [baritone]
    for part, name, abbr in zip(parts, NAMES, ABBREVIATIONS):
        part.partName, part.partAbbreviation = name, abbr
        part.id = abbr
        # let OSMD lay out the systems itself
        for el in part.recurse().getElementsByClass(layout.LayoutBase):
            el.activeSite.remove(el)
    fix_audiveris(*parts[:3])
    for part in parts:
        add_lyrics(part, LYRICS[part.partName])

    score = stream.Score(parts)
    score.insert(0, audiveris.metadata)
    score.metadata.title, score.metadata.composer = TITLE, COMPOSER
    score.metadata.movementName = TITLE  # Audiveris puts the file name here
    return score


def set_rhythm(m: stream.Measure, lengths: list[float]) -> None:
    """Give the notes/rests of bar `m` these lengths, back to back."""
    offset = 0.0
    for n, ql in zip(m.notesAndRests, lengths, strict=True):
        n.quarterLength = ql
        m.setElementOffset(n, offset)
        offset += ql
    m.duration = None


def tie_over(part: stream.Part, bar: int) -> None:
    """Tie the last note of `bar` to the first note of the next bar."""
    part.measure(bar).notes[-1].tie = tie.Tie("start")
    part.measure(bar + 1).notes[0].tie = tie.Tie("stop")


def fix_audiveris(soprano: stream.Part, alto1: stream.Part, alto2: stream.Part) -> None:
    """Corrections checked against the PDF."""
    # Audiveris turns lyric fragments and dots into staccatos, trills, dynamics
    # and slurs that aren't in the score; the PDF has no articulations at all
    for part in (soprano, alto1, alto2):
        for n in part.recurse().notes:
            n.articulations, n.expressions = [], []
        junk = list(part.recurse().getElementsByClass(dynamics.Dynamic))
        junk += [sp for sp in part.spanners if isinstance(sp, spanner.Slur)]
        part.remove(junk, recurse=True)
    # dotted quarter + eighth + quarter, Audiveris read the eighth as a quarter
    for bar in (14, 28, 32):
        set_rhythm(soprano.measure(bar), [1.5, 0.5, 1])
    # three quarters ("cri cri cri"), Audiveris found two dotted quarters
    m = alto2.measure(23)
    m.append(copy.deepcopy(m.notes[-1]))
    set_rhythm(m, [1, 1, 1])
    # the PDF has an extender under "se" here, not a tie
    for n in alto2.measure(15).notes:
        n.tie = None
    # "crac" is tied into bar 25 in every part
    for part in (soprano, alto1, alto2):
        tie_over(part, 24)
    # bars after a changed one keep their old offsets otherwise
    for part in (soprano, alto2):
        offset = 0.0
        for m in part.getElementsByClass(stream.Measure):
            part.setElementOffset(m, offset)
            offset += m.duration.quarterLength


def add_lyrics(part: stream.Part, text: str) -> None:
    bars = [b.split() for b in text.split("|")]
    measures = list(part.getElementsByClass(stream.Measure))
    if len(bars) != len(measures):
        raise ValueError(f"{part.partName}: {len(bars)} bars of lyrics, {len(measures)} in score")
    in_word = False
    for m, syllables in zip(measures, bars):
        sung = [n for n in m.notes if not (n.tie and n.tie.type in ("stop", "continue"))]
        if len(sung) != len(syllables):
            raise ValueError(f"{part.partName} bar {m.number}: {len(sung)} notes, "
                             f"lyrics {syllables}")
        for n, syl in zip(sung, syllables):
            if syl == "_":
                continue
            continues = syl.endswith("-")
            lyric = note.Lyric(syl.rstrip("-"))
            lyric.syllabic = ({(False, False): "single", (False, True): "begin",
                               (True, True): "middle", (True, False): "end"}
                              [(in_word, continues)])
            n.lyrics = [lyric]
            in_word = continues


def check(score: stream.Score) -> None:
    """Every part has the same bar count and every bar is full."""
    for part in score.parts:
        bars = part.getElementsByClass(stream.Measure)
        bar_q = bars[0].barDuration.quarterLength
        bad = [m.number for m in bars if m.duration.quarterLength != bar_q]
        print(f"{part.partName}: {len(bars)} bars" + (f", wrong length: {bad}" if bad else ""))


def events(score: stream.Score) -> dict:
    bars = score.parts[0].getElementsByClass(stream.Measure)
    parts = []
    for part in score.parts:
        notes = [[p.midi, float(n.offset), float(n.quarterLength)]
                 for n in part.stripTies().flatten().notes for p in n.pitches]
        parts.append({"name": part.partName, "notes": notes})
    return {
        "title": TITLE,
        "tempo": TEMPO,
        "measures": [float(m.offset) for m in bars],
        "length": float(bars[-1].offset + bars[-1].duration.quarterLength),
        "parts": parts,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    xml = OUT / "foc.musicxml"
    build_score().write("musicxml", fp=str(xml))
    # re-read so bar offsets reflect the fixed durations
    score = converter.parse(str(xml))
    check(score)
    (OUT / "foc.json").write_text(json.dumps(events(score)))
    print(f"wrote {xml} and foc.json")


if __name__ == "__main__":
    main()
