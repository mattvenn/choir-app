"""Agnus Dei (D. Basomba), in B major, for S, A1, A2 and Baritone. The score's
Alto 1 is the altos' line and Alto 2 the tenors', so they're named Alto and Tenor.

From the director's MusicXML, exported from Finale (sources/agnus.musicxml).
It has no repeats, so there's no version without them. The tempo is the
score's (quarter = 80); the player ignores the dynamics, "ritardando" and
"a tempo". The lyrics are the file's, which match the PDF.
"""
from music21 import stream

from scorelib import load_finale, make_score

ID = "agnus"
TITLE = "Agnus Dei"
GROUP = "Jóvenes"  # the junior choir's
COMPOSER = "D. Basomba"
TEMPO = 80  # quarter notes per minute, as marked
MY_PART = "Baritone"
NAMES = ["Soprano", "Alto", "Tenor", "Baritone"]
ABBREVIATIONS = ["S", "A", "T", "B"]


def build() -> stream.Score:
    return make_score(load_finale("agnus.musicxml"), NAMES, ABBREVIATIONS, TITLE, COMPOSER)
