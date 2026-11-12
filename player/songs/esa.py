"""Esa estrella que brilla (words and music by D. Basomba), for Soprano 1,
Soprano 2, Baritone and Cello.

From the director's MusicXML, exported from Finale (sources/esa.musicxml),
where the third line is unnamed: it's in bass clef, and is called the Baritone
here. Each voice sings a line, top to bottom: sopranos Soprano 1, altos Soprano
2, tenors the Baritone, basses the cello.

The score says "D.C. al Fine" at bar 29, but its second ending leads straight
into bars 30-38 ("Coro"), the opening written out again, so the player goes
straight through: bars 2-9, 11-18, 21-28 and 30-37 are each repeated with
first and second endings, and the song ends at bar 38. build() writes the
repeats out, so bar numbers after 9 don't match the score. build_short() goes
through each section once, taking the second endings; its bars keep the
score's numbers. The tempo is the file's (quarter = 90; the score has no
marking). The player ignores the dynamics, "rit.", "pizz."/"arco", the trios'
marks ("a-b", "Coro") and the "*" (sin director) marks.

The lyrics are the file's, which match the PDF, except that Finale left out
some elided syllables ("sa‿es", "que‿ha", "de‿a", "to‿y"): they're put back
from the PDF. Soprano 2's pick-up in bar 29 has no words in the PDF; it gets
"sús. E sa‿es", as the sopranos sing in bar 9. Misprints in both are
corrected: Soprano 2's "dón-se" (bars 4 and 32) is "dón-de" and "ci-co" (bar
35) is "ci-do", as the others sing, and the Baritone's "LLe-vad" is "Lle-vad".
The "sús" printed under the cello's last bar is left out.
"""
from music21 import note, stream

from scorelib import load_finale, make_score, write_out_repeats

ID = "esa"
TITLE = "Esa estrella que brilla"
GROUP = "Jóvenes"  # the junior choir's
COMPOSER = "D. Basomba"
TEMPO = 90  # quarter notes per minute, the file's
MY_PART = "Baritone"
NAMES = ["Soprano 1", "Soprano 2", "Baritone", "Cello"]
ABBREVIATIONS = ["S1", "S2", "B", "Vc"]


# score bars 2-8 with ending 9, again with ending 10; 11-16 with ending 17-18,
# again with ending 19-20; 21-27 with ending 28, again with 29; then the Coro,
# 30-36 with ending 37, again with ending 38
ORDER = [1, *range(2, 10), *range(2, 9), 10, *range(11, 19), *range(11, 17), 19, 20,
         *range(21, 29), *range(21, 28), 29, *range(30, 38), *range(30, 37), 38]
SHORT_ORDER = [*range(1, 9), 10, *range(11, 17), 19, 20, *range(21, 28), 29,
               *range(30, 37), 38]
# syllables missing from the file, from the PDF: by part, (bar, sung note) →
# syllable, counting the notes in the bar that start a syllable (not the ends
# of ties)
MISSING = {
    "Soprano 1": {
        (1, 2): "sa‿es", (6, 2): "que‿ha", (9, 3): "sa‿es", (13, 3): "de‿a",
        (17, 2): "to‿y", (19, 2): "to‿y", (29, 3): "sa‿es", (34, 2): "que‿ha",
    },
    "Soprano 2": {
        (1, 2): "sa‿es", (9, 3): "sa‿es", (13, 3): "de‿a", (17, 2): "to‿y", (19, 2): "to‿y",
        (29, 1): "sús.", (29, 2): "E", (29, 3): "sa‿es",
    },
    "Baritone": {(2, 2): "sa‿es", (17, 2): "to‿y", (19, 2): "to‿y"},
    "Cello": {},
}
# misprints: by part, (bar, old) → new
MISPRINTS = {
    "Soprano 2": {(4, "se"): "de", (32, "se"): "de", (35, "co"): "do"},
    "Baritone": {(11, "LLe"): "Lle"},
    "Cello": {(38, "sús"): None},
}


def load_parts() -> list[stream.Part]:
    parts = load_finale("esa.musicxml")
    for part, name in zip(parts, NAMES, strict=True):
        for (bar, old), new in MISPRINTS.get(name, {}).items():
            found = [(n, l) for n in part.measure(bar).notes for l in n.lyrics if l.text == old]
            if len(found) != 1:
                raise ValueError(f"Esa estrella: {name} bar {bar} has {len(found)} '{old}'")
            n, lyric = found[0]
            if new is None:
                n.lyrics = [l for l in n.lyrics if l is not lyric]
            else:
                lyric.text = new
        for (bar, place), text in MISSING[name].items():
            sung = [n for n in part.measure(bar).notes
                    if not (n.tie and n.tie.type in ("stop", "continue"))]
            n = sung[place - 1]
            if n.lyrics:
                raise ValueError(f"Esa estrella: {name} bar {bar} note {place} already has "
                                 f"{[l.text for l in n.lyrics]}")
            n.lyrics = [note.Lyric(text, syllabic="single")]
    return parts


def build() -> stream.Score:
    parts = [write_out_repeats(part, ORDER) for part in load_parts()]
    return make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)


def build_short() -> stream.Score:
    parts = [write_out_repeats(part, SHORT_ORDER, renumber=False) for part in load_parts()]
    return make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
