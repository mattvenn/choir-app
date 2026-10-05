"""Helpers for building the player's scores with music21."""
from pathlib import Path

from music21 import clef, converter, layout, metadata, note, stream, tempo, tie

SOURCES = Path(__file__).resolve().parent / "sources"


def load_abc(name: str) -> stream.Part:
    """One part from an ABC transcription in player/sources/."""
    part = converter.parse(str(SOURCES / name)).parts[0]
    # the ABC import numbers bars from 0; tempo comes from the song instead
    for m in part.getElementsByClass(stream.Measure):
        m.number += 1
    for mark in part.recurse().getElementsByClass(tempo.MetronomeMark):
        mark.activeSite.remove(mark)
    return part


def to_tenor_clef(part: stream.Part) -> None:
    """Transcribed at written pitch in treble clef: sound an octave lower, show treble-8vb."""
    part.transpose(-12, inPlace=True)
    for c in list(part.recurse().getElementsByClass(clef.Clef)):
        c.activeSite.replace(c, clef.Treble8vbClef())


def make_score(parts: list[stream.Part], names: list[str], abbreviations: list[str],
               title: str, composer: str) -> stream.Score:
    for part, name, abbr in zip(parts, names, abbreviations, strict=True):
        part.partName, part.partAbbreviation = name, abbr
        part.id = abbr
        # let OSMD lay out the systems itself
        for el in part.recurse().getElementsByClass(layout.LayoutBase):
            el.activeSite.remove(el)
    score = stream.Score(parts)
    score.insert(0, metadata.Metadata(title=title, composer=composer, movementName=title))
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


def realign_bars(part: stream.Part) -> None:
    """Bars after one whose length changed keep their old offsets otherwise."""
    offset = 0.0
    for m in part.getElementsByClass(stream.Measure):
        part.setElementOffset(m, offset)
        offset += m.duration.quarterLength


def add_lyrics(part: stream.Part, text: str) -> None:
    """Lyrics are written one entry per bar, separated by "|". Each syllable goes
    on the next note that isn't the continuation of a tie: "na-" continues the
    word on the next syllable, "_" holds the previous syllable over this note."""
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
        print(f"  {part.partName}: {len(bars)} bars" + (f", wrong length: {bad}" if bad else ""))


def events(score: stream.Score) -> dict:
    """Note events per part, in quarter notes, for the browser to play."""
    bars = score.parts[0].getElementsByClass(stream.Measure)
    time_sig = bars[0].timeSignature
    parts = []
    for part in score.parts:
        notes = [[p.midi, float(n.offset), float(n.quarterLength)]
                 for n in part.stripTies().flatten().notes for p in n.pitches]
        parts.append({"name": part.partName, "notes": notes})
    return {
        "measures": [float(m.offset) for m in bars],
        # for the metronome: 3/4 is 3 beats of 1 quarter, cut time 2 beats of 2
        "beat": float(time_sig.beatDuration.quarterLength),
        "beatsPerBar": time_sig.beatCount,
        "length": float(bars[-1].offset + bars[-1].duration.quarterLength),
        "parts": parts,
    }
