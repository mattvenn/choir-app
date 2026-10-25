"""Triste reloj (Diana Bengoechea), arranged for S, A1, A2 and Baritone.

From the director's MusicXML, exported from Finale 2014 (sources/triste.musicxml).
Bars 32-41 are repeated; build() writes the repeat out, so bar numbers after 41
don't match the score. build_short() is the score as printed, each bar once.
The tempo marks stay (quarter = 88, the 12/8 section dotted quarter = 76, then
88 again) and the player follows them. It ignores the dynamics, the solo and
clapping marks ("solistas", "palmas", X).

The lyrics are the file's, which match the PDF except that Finale left out
the elided syllables ("me‿es", "y‿a", ...) and the baritone's "ta" in bar 39:
they're put back from the PDF. Two misprints in both are corrected: Alto 2's
"titocc" in bar 13 is "toc", as in the bars around it, and Alto 1's "suIos" in
bar 51 is "su‿os" (scorelib.load_finale). Where the PDF has no hyphens (most of
bars 32-46, and "ti qui toc" from bar 47), neither does the player.
"""
from music21 import note, stream

from scorelib import load_finale, make_score, write_out_repeats

ID = "triste"
TITLE = "Triste reloj"
GROUP = "Jóvenes"  # the junior choir's
COMPOSER = "Diana Bengoechea"
TEMPO = 88  # quarter notes per minute, as marked
MY_PART = "Baritone"
NAMES = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
ABBREVIATIONS = ["S", "A1", "A2", "B"]
ORDER = [*range(1, 42), *range(32, 59)]
# syllables missing from the file, from the PDF: by part, (bar, sung note) →
# syllable, counting the notes in the bar that start a syllable (not the ends
# of ties); "-" at the end continues the word
MISSING = {
    "Soprano": {
        (32, 3): "me‿es", (34, 3): "va‿a", (36, 5): "vio‿im", (37, 5): "le‿a",
        (38, 3): "y‿a", (38, 6): "me‿im", (38, 9): "si‿a",
        (40, 2): "y‿a", (40, 5): "me‿im", (40, 7): "si‿a",
        (45, 3): "se‿y", (45, 4): "va‿a",
    },
    "Alto 1": {
        (5, 3): "y‿a-", (5, 8): "su‿os-", (20, 1): "se‿o-", (20, 2): "ye‿el",
        (20, 5): "se‿ha", (21, 2): "do‿el",
        (32, 3): "ya‿han", (32, 9): "y‿el", (32, 12): "me‿es",
        (34, 3): "ya‿han", (34, 9): "y‿el", (34, 12): "va‿a",
        (36, 5): "vio‿im", (37, 5): "le‿a",
        (38, 3): "y‿a", (38, 6): "me‿im", (38, 9): "si‿a",
        (40, 2): "y‿a", (40, 5): "me‿im", (40, 7): "si‿a",
        (45, 3): "se‿y", (45, 4): "va‿a", (51, 3): "y‿a-",
    },
    "Alto 2": {
        (38, 3): "si‿a", (40, 2): "si‿a", (45, 3): "se‿y", (45, 4): "va‿a",
    },
    "Baritone": {
        (13, 8): "su‿hu-", (15, 4): "se‿a-",
        (32, 3): "ya‿han", (32, 9): "y‿el", (32, 12): "me‿es",
        # printed "se‿s"; the director says "me‿es", as in bar 32
        (34, 3): "ya‿han", (34, 9): "y‿el", (34, 12): "me‿es",
        (39, 3): "ta", (45, 3): "se‿y", (45, 4): "va‿a",
    },
}


def load_parts() -> list[stream.Part]:
    parts = load_finale("triste.musicxml", tempo_changes=True)
    for lyric in parts[2].measure(13).notes[0].lyrics:
        if lyric.text == "titocc":
            lyric.text = "toc"
    for part in parts:
        for (bar, place), text in MISSING[part.partName].items():
            sung = [n for n in part.measure(bar).notes
                    if not (n.tie and n.tie.type in ("stop", "continue"))]
            n = sung[place - 1]
            if n.lyrics:
                raise ValueError(f"{part.partName} bar {bar} note {place} already has {n.lyrics}")
            n.lyrics = [note.Lyric(text.rstrip("-"),
                                   syllabic="begin" if text.endswith("-") else "single")]
    return parts


def build() -> stream.Score:
    parts = [write_out_repeats(part, ORDER) for part in load_parts()]
    return make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)


def build_short() -> stream.Score:
    return make_score(load_parts(), NAMES, ABBREVIATIONS, TITLE, COMPOSER)
