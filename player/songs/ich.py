"""Ich grolle nicht (Robert Schumann, words by Heinrich Heine), arranged for
S, A1, A2 and Baritone.

From the director's MusicXML, exported from Finale 2014 (sources/ich.musicxml).
It has no repeats, so there's no version without them. The player ignores the
dynamics, "ritenuto" and "a tempo"; the score has no tempo marking, so the
tempo is the file's (quarter = 90, set for Finale's playback). The sopranos
divide in bars 28-29 and both notes play. The lyrics are the file's, which
match the PDF, except two the file puts on the sopranos' rests: a "," in bar
24 is left out, and "Ich" in bar 26 goes on the next note, as the PDF has it.
"""
from music21 import note, stream

from scorelib import load_finale, make_score

ID = "ich"
TITLE = "Ich grolle nicht"
GROUP = "Jóvenes"  # the junior choir's
COMPOSER = "Robert Schumann"
TEMPO = 90  # quarter notes per minute, the file's
MY_PART = "Baritone"
NAMES = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
ABBREVIATIONS = ["S", "A1", "A2", "B"]


def load_parts() -> list[stream.Part]:
    parts = load_finale("ich.musicxml")
    soprano = parts[0]
    comma = soprano.measure(24).getElementsByClass(note.Rest)[0]
    rest, after = soprano.measure(26).notesAndRests[2:4]
    if [l.text for l in comma.lyrics] != [","] or [l.text for l in rest.lyrics] != ["Ich"] \
            or after.lyrics:
        raise ValueError("Ich grolle nicht: the lyrics on the sopranos' rests have moved")
    comma.lyrics = []
    after.lyrics, rest.lyrics = rest.lyrics, []
    return parts


def build() -> stream.Score:
    return make_score(load_parts(), NAMES, ABBREVIATIONS, TITLE, COMPOSER)
