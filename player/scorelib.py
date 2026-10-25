"""Helpers for building the player's scores with music21."""
import bisect
import copy
import re
from pathlib import Path

from music21 import (bar, clef, converter, dynamics, expressions, key, layout, metadata, meter,
                     note, stream, tempo)

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


def load_finale(name: str, tempo_changes: bool = False) -> list[stream.Part]:
    """The parts of a MusicXML file the director exported from Finale, in
    player/sources/, without what the player ignores: tempo (the song sets it),
    dynamics, hairpins and text like "cresc.". With `tempo_changes` the tempo
    marks stay, and the player follows them relative to the first (see events)."""
    parts = list(converter.parse(str(SOURCES / name)).parts)
    for part in parts:
        ignored = [dynamics.Dynamic, expressions.TextExpression]
        if not tempo_changes:
            ignored.append(tempo.MetronomeMark)
        part.remove(list(part.recurse().getElementsByClass(ignored)), recurse=True)
        part.remove([sp for sp in part.spanners if isinstance(sp, dynamics.DynamicWedge)])
        for n in part.recurse().notes:
            # Finale marks where a held syllable ends with a lyric of its own,
            # which comes in with no text, and sometimes writes a lyric twice
            lyrics = []
            for lyric in n.lyrics:
                if lyric.text and not any(l.text == lyric.text for l in lyrics):
                    lyrics.append(lyric)
            # the tie of an elision ("su‿os") comes out as a capital I
            for lyric in lyrics:
                lyric.text = re.sub(r"(?<=[a-zñáéíóú])I(?=[a-zñáéíóú])", "‿", lyric.text)
            n.lyrics = lyrics
    return parts


def to_tenor_clef(part: stream.Part) -> None:
    """Transcribed at written pitch in treble clef: sound an octave lower, show treble-8vb."""
    part.transpose(-12, inPlace=True)
    for c in list(part.recurse().getElementsByClass(clef.Clef)):
        c.activeSite.replace(c, clef.Treble8vbClef())


def write_out_repeats(part: stream.Part, order: list[int], renumber: bool = True) -> stream.Part:
    """The player plays straight through, so repeats are written out: a new part
    with the bars numbered `order` in that order, renumbered from 1 unless
    `renumber` is false (bars are left out, but none comes twice)."""
    bars = {m.number: m for m in part.getElementsByClass(stream.Measure)}
    out = stream.Part()
    offset = 0.0
    shown = {}  # the clef, key, time and tempo in force, by kind
    for number, n in enumerate(order, 1):
        m = copy.deepcopy(bars[n])
        if renumber:
            m.number = number
        # a repeated bar would show the clef, key, time and tempo again; only a change shows
        for kind in (clef.Clef, key.KeySignature, meter.TimeSignature, tempo.MetronomeMark):
            for el in list(m.getElementsByClass(kind)):
                if repr(el) == shown.get(kind):
                    m.remove(el)
                shown[kind] = repr(el)
        # written out, the repeat signs are wrong
        m.removeByClass(bar.Repeat)
        out.insert(offset, m)
        offset += m.duration.quarterLength
    return out


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



def add_lyrics(part: stream.Part, text: str, verse: int = 1) -> None:
    """Lyrics are written one entry per bar, separated by "|". Each syllable goes
    on the next note that isn't the continuation of a tie: "na-" continues the
    word on the next syllable, "_" holds the previous syllable over this note.
    Verse 2 and up go on further lines under verse 1."""
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
            lyric = note.Lyric(syl.rstrip("-"), number=verse)
            lyric.syllabic = ({(False, False): "single", (False, True): "begin",
                               (True, True): "middle", (True, False): "end"}
                              [(in_word, continues)])
            n.lyrics = [lyric] if verse == 1 else n.lyrics + [lyric]
            in_word = continues


def check(score: stream.Score) -> None:
    """Every part has the same bar count and every bar is full."""
    for part in score.parts:
        bars = part.getElementsByClass(stream.Measure)
        bad = [m.number for m in bars if m.duration.quarterLength != m.barDuration.quarterLength]
        print(f"  {part.partName}: {len(bars)} bars" + (f", wrong length: {bad}" if bad else ""))


def events(score: stream.Score) -> dict:
    """Note events per part, in quarter notes at the song's tempo, for the
    browser to play. Where the score has tempo marks, a bar after a change is
    stretched or squeezed to play at its tempo relative to the first mark's."""
    bars = list(score.parts[0].getElementsByClass(stream.Measure))
    starts = [float(m.offset) for m in bars]
    speeds, beats = [], []  # per bar: its tempo relative to the first, and its beat
    first = qpm = None
    time_sig = None
    for m in bars:
        for mark in m.getElementsByClass(tempo.MetronomeMark):
            qpm = mark.getQuarterBPM()
            first = first or qpm
        time_sig = m.timeSignature or time_sig
        speeds.append(qpm / first if qpm else 1.0)
        # for the metronome: 3/4 is 3 beats of 1 quarter, cut time 2 beats of 2,
        # 12/8 4 beats of a dotted quarter
        beats.append([float(time_sig.beatDuration.quarterLength) / speeds[-1], time_sig.beatCount])
    played = [0.0]  # where each bar starts when played, then the end
    for m, speed in zip(bars, speeds):
        played.append(played[-1] + float(m.duration.quarterLength) / speed)

    def when(offset: float) -> float:
        i = max(bisect.bisect_right(starts, offset) - 1, 0)
        return played[i] + (offset - starts[i]) / speeds[i]

    parts = []
    for part in score.parts:
        notes = []
        for n in part.stripTies().flatten().notes:
            start, end = float(n.offset), float(n.offset + n.quarterLength)
            notes += [[p.midi, when(start), when(end) - when(start)] for p in n.pitches]
        parts.append({"name": part.partName, "notes": notes})
    data = {
        "measures": played[:-1],
        "beat": beats[0][0],
        "beatsPerBar": beats[0][1],
        "length": played[-1],
        "parts": parts,
    }
    # where the metre or tempo changes, each bar's beat length and count
    if any(b != beats[0] for b in beats):
        data["bars"] = beats
    return data
