"""Wellcome (Daniel Basomba), for Soprano, Alto and Baritone.

From the director's MusicXML, exported from Finale 2014 (sources/wellcome.musicxml),
whose lyrics match the PDF. It has no repeats, so there's no version without
them. The player ignores the dynamics; the tempo is the score's (quarter = 76).
There's no tenor line, so tenors get the Baritone.
"""
from music21 import stream

from scorelib import load_finale, make_score

ID = "wellcome"
TITLE = "Wellcome"
GROUP = "Jóvenes"  # the junior choir's
COMPOSER = "Daniel Basomba"
TEMPO = 76  # quarter notes per minute, as marked
MY_PART = "Baritone"
NAMES = ["Soprano", "Alto", "Baritone"]
ABBREVIATIONS = ["S", "A", "B"]


def build() -> stream.Score:
    return make_score(load_finale("wellcome.musicxml"), NAMES, ABBREVIATIONS, TITLE, COMPOSER)
