"""Shalala-Bon nadal (D. Basomba), arranged for S, A1, A2 and Baritone.

From the director's MusicXML, exported from Finale 2014 (sources/shalala.musicxml).
The whole song is repeated; build() writes the repeat out, so bar numbers after
13 don't match the score. build_short() is the score as printed, each bar once.
The player ignores the dynamics, the "cresc." and the fermatas on the last bar,
and the file's tempo (quarter = 50, for Finale's playback) gives way to the
choir's.

The altos' "Wei-nach-ten" is spelt "Weih-nach-ten", as in the soprano.
"""
from music21 import converter, bar, dynamics, expressions, stream, tempo

from scorelib import SOURCES, make_score, write_out_repeats

ID = "shalala"
TITLE = "Shalala-Bon nadal"
COMPOSER = "D. Basomba"
TEMPO = 56  # the choir's choice
MY_PART = "Baritone"
NAMES = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
ABBREVIATIONS = ["S", "A1", "A2", "B"]
ORDER = [*range(1, 14), *range(1, 14)]


def load_parts() -> list[stream.Part]:
    parts = list(converter.parse(str(SOURCES / "shalala.musicxml")).parts)
    for part in parts:
        junk = part.recurse().getElementsByClass(
            [tempo.MetronomeMark, dynamics.Dynamic, expressions.TextExpression])
        part.remove(list(junk), recurse=True)
        for n in part.recurse().notes:
            # Finale marks where a held syllable ends with a lyric of its own,
            # which comes in with no text
            n.lyrics = [lyric for lyric in n.lyrics if lyric.text]
            for lyric in n.lyrics:
                if lyric.text == "Wei":
                    lyric.text = "Weih"
    return parts


def build() -> stream.Score:
    parts = [write_out_repeats(part, ORDER) for part in load_parts()]
    # written out, the repeat sign at the end of the first time through is wrong
    for part in parts:
        signs = part.recurse().getElementsByClass(bar.Repeat)
        part.remove(list(signs), recurse=True)
    return make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)


def build_short() -> stream.Score:
    return make_score(load_parts(), NAMES, ABBREVIATIONS, TITLE, COMPOSER)
