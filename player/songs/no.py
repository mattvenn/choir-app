"""No olvides, John (in C major), SATB.

All four voices are hand transcriptions of the PDF. Its two repeats (each with
first and second endings) are written out, so bar numbers don't match the PDF.
"""
from music21 import stream

from scorelib import add_lyrics, load_abc, make_score, write_out_repeats

ID = "no"
TITLE = "No olvides"
COMPOSER = ""
TEMPO = 100  # quarter notes per minute; the score has no marking
MY_PART = "Bass"
NAMES = ["Soprano", "Alto", "Tenor", "Bass"]
ABBREVIATIONS = ["S", "A", "T", "B"]
# PDF bars 1-7 with ending 8, again with ending 9, then 10-16 with ending 17,
# again with ending 18, then 19-20
ORDER = [*range(1, 8), 8, *range(1, 8), 9, *range(10, 17), 17, *range(10, 17), 18, 19, 20]
# one entry per PDF bar, see scorelib.add_lyrics for the format; the parts only
# differ in bar 2, where the tenor holds "de‿a" instead of singing "quí"
LYRICS = """Si‿al gu- na vez cuan- do‿es- | tés le- jos de‿a quí |
    sur- can- do‿el mar o per- | di- do‿en la ciu- dad | Te sien- tes tris- te y sin |
    ga- nas de se- guir No‿ol- | vi- des nun- ca‿es te lu- gar no‿ol- |
    vi- des John | vi- des John Es- | cu- cha, no o- yes a los |
    pá- ja- ros can- tar No‿a- | le- gran el al- ma y te |
    ha- cen ol- vi- dar Si | te sien- tes tris- te so- lo | de- bes re- cor- dar el |
    can- to‿a- le- gre de tu‿ho- gar no‿ol- | vi- des John Es- | vi- des John el |
    can- to‿a- le- gre de tu‿ho- gar no‿ol- | vi- des John"""


def lyrics(voice: str) -> str:
    bars = LYRICS.split("|")
    if voice == "Tenor":
        bars[1] = "tés le- jos de‿a _"
    return "|".join(bars[n - 1] for n in ORDER)


def build() -> stream.Score:
    parts = [write_out_repeats(load_abc(f"no-{voice.lower()}.abc"), ORDER) for voice in NAMES]
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        add_lyrics(part, lyrics(part.partName))
    return score
