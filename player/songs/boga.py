"""Boga, boga (Arín), SATB, from a photocopy.

All four voices are hand transcriptions of the PDF. Bars 1-7 and 8-16 are each
sung twice, in Basque then in Spanish; the repeats are written out, so bar
numbers don't match the PDF. The ending (17-20) is printed with both texts; the
written-out version sings the Basque one. build_short() is the score as printed,
each bar once, with both verses under the notes. The player ignores the fermatas, including the rest
in bar 19 where everyone shouts "¡¡¡Boga!!!".
"""
from music21 import meter, stream

from scorelib import add_lyrics, load_abc, make_score, to_tenor_clef, write_out_repeats

ID = "boga"
TITLE = "Boga, boga"
COMPOSER = "Arín"
TEMPO = 63  # the choir's choice; the score marks quarter = 50
MY_PART = "Bass"
NAMES = ["Soprano", "Alto", "Tenor", "Bass"]
ABBREVIATIONS = ["S", "A", "T", "B"]
ORDER = [*range(1, 8), *range(1, 8), *range(8, 17), *range(8, 17), 17, 18, 19, 20]
# one entry per PDF bar, see scorelib.add_lyrics for the format: the two verses
# of bars 1-16, then the ending in each language. Soprano and alto share words,
# as do tenor and bass.
LYRICS = {
    "upper": ("""Bo- ga, | bo- ga, ma- ri- ñe- | la, Juan bear | de- gu u- rru- ti- |
        ra bai In- di- | e- ta- ra bai In- di- | e- ta- ra. | Ez |
        det mi- ki- ku- | si- ko zu- | re kai e- de- | rra. A- |
        gur on- da- rro- | a- ko i- | txa- so bas- te- | rra.""",
              """Bo- ga, | bo- ga, ma- ri- ne- | ro, la bar- | qui- lla no vol- ve- |
        rá, va le- jos | de a- quí, va le- jos | de a- quí. | A- |
        diós, no te ve- | ré más tie- | rra don- de na- | cí. A- |
        diós, ri- be- ra | del mar que | me mi- rais par- | tir.""",
              """Ma- | ri- ñe- | la, ma- ri- ñe- | la.""",
              """Ma- | ri- ne- | ro, ma- ri- ne- | ro."""),
    "lower": ("""Bo- ga, | bo- ga, ma- ri- ñe- | la, ma- ri- ñe- la, Juan bear |
        de- gu u- rru- ti- | ra, u- rru- ti- ra, | bai In- die- ta- ra, |
        bai In- die- ta- ra. | | Ez det mi- ki- | ku- si- ko |
        zu- re kai e- de- | rra kai e- de- rra. A- |
        gur on- da- rro- | a- ko i- | txa- so bas- te- | rra.""",
              """Bo- ga, | bo- ga, ma- ri- ne- | ro, ma- ri- ne- ro, la bar- |
        qui- lla no vol- ve- | rá, no vol- ve- rá, | va le- jos de‿a- quí, |
        va le- jos de‿a- quí. | | A- diós no te | ve- ré más |
        tie- rra don- de na- | cí, don- de na- cí. A- |
        diós, ri- be- ra | del mar que | me mi- rais par- | tir.""",
              """ | Ma- ri- ñe- | la, ma- ri- ñe- | la.""",
              """ | Ma- ri- ne- | ro, ma- ri- ne- | ro."""),
}


def verses(voice: str) -> tuple[str, str]:
    """The Basque and Spanish words for every PDF bar, ending included."""
    basque, spanish, end_basque, end_spanish = LYRICS["upper" if voice in ("Soprano", "Alto")
                                                      else "lower"]
    return f"{basque} | {end_basque}", f"{spanish} | {end_spanish}"


def lyrics(voice: str) -> str:
    """The words for the written-out repeats: each section in Basque, then Spanish."""
    basque, spanish = (text.split("|") for text in verses(voice))
    bars = basque[:7] + spanish[:7] + basque[7:16] + spanish[7:16] + basque[16:]
    if len(bars) != len(ORDER):
        raise ValueError(f"{voice}: {len(bars)} bars of lyrics, {len(ORDER)} in score")
    return "|".join(bars)


def load_parts() -> list[stream.Part]:
    parts = [load_abc(f"boga-{voice.lower()}.abc") for voice in NAMES]
    to_tenor_clef(parts[2])
    for part in parts:
        for ts in part.recurse().getElementsByClass(meter.TimeSignature):
            ts.symbol = "common"  # the score writes C, not 4/4
    return parts


def build() -> stream.Score:
    parts = [write_out_repeats(part, ORDER) for part in load_parts()]
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        add_lyrics(part, lyrics(part.partName))
    return score


def build_short() -> stream.Score:
    parts = load_parts()
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        for verse, text in enumerate(verses(part.partName), 1):
            add_lyrics(part, text, verse)
    return score
