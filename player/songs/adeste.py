"""Adeste Fideles (J. Reading), SATB, no. 58 in the choir's book.

All four voices are hand transcriptions of the PDF, which has soprano and
alto on one staff and tenor and bass on another, both in treble-8 clef; the
player shows the bass in bass clef instead, as the director asked. The
upbeat is padded with rests into bar 1, so bar numbers are one more than
counting from the first full bar. The choir doesn't sing the score's repeat
(bars 10-21), only the D.C.: build() writes out verse 1, then verse 2, each
bar once, so bar numbers in the second verse don't match the score. build_short() is each bar once, with both verses under the
notes and without the repeat signs, so it shows what it plays.
"""
from music21 import clef, meter, stream

from scorelib import add_lyrics, load_abc, make_score, to_tenor_clef, write_out_repeats

ID = "adeste"
TITLE = "Adeste Fideles"
COMPOSER = "J. Reading"
TEMPO = 84  # Andante moderato; the score has no number, 84 is the choir's
MY_PART = "Bass"
NAMES = ["Soprano", "Alto", "Tenor", "Bass"]
ABBREVIATIONS = ["S", "A", "T", "B"]
BARS = 21
# each verse goes straight through, without the score's repeat
VERSE = list(range(1, BARS + 1))
ORDER = VERSE * 2
# one entry per bar, see scorelib.add_lyrics for the format. Verse 2 is only
# printed up to "festinemus", in bar 13, where both go on with "Venite adoremus".
VERSE_1 = {
    "Soprano": """A- | de- ste, fi- | de- les, | lae- ti, tri- um- | phan- tes. Ve- |
        ni- te, ve- | ni- _ te in | Béth- _ le- | em: | Na- tum vi- | de- te |
        Re- gem An- ge- | lo- rum. Ve- | ni- te, ad- o- | re- mus, ve- |
        ni- te ad- o- | re- mus, ve- | ni- te ad- o- | re- mus _ | Do- _ mi- | num.""",
    "Alto": """A- | de- ste, fi- | de- les, | lae- ti, tri- um- | phan- tes. Ve- |
        ni- _ te, ve- | ni- te in | Béth- _ le- | em: | Na- tum _ vi- | de- _ te |
        Re- gem An- ge- | lo- rum. Ve- | ni- te, ad- o- | re- mus, ve- |
        ni- te ad- o- | re- mus, ve- | ni- te ad- o- _ | re- mus _ | Do- mi- | num.""",
    "Tenor": """A- | de- ste, fi- | de- les, | lae- ti, tri- um- | phan- tes. Ve- |
        ni- te, ve- | ni- _ te in | Béth- _ le- | em: | Na- tum vi- | de- te |
        Re- gem An- ge- | lo- rum. Ve- | ni- te, ad- o- | re- mus, ve- |
        ni- te ad- o- | re- mus, ve- | ni- te ad- o- | re- mus | Do- _ mi- | num.""",
    "Bass": """A- | de- ste, fi- | de- les, | lae- ti, tri- um- | phan- tes. Ve- |
        ni- te, ve- | ni- _ te in | Béth- le- | em: | Na- tum vi- | de- te |
        Re- gem An- ge- | lo- rum. | | | | ve- |
        ni- te ad- o- | re- _ mus _ | Do- mi- | num.""",
}
VERSE_2 = {
    "Soprano": """En | gre- ge re- | lic- to | hu- mi- les ad | cu- nas, vo- |
        ca- ti pas- | to- _ res ap- | pro- _ pe- | rant: | Et nos o- | van- ti |
        gra- du fes- ti- | ne- mus. _""",
    "Alto": """En | gre- ge re- | lic- to | hu- mi- les ad | cu- nas, vo- |
        ca- _ ti pas- | to- res ap- | pro- _ pe- | rant: | Et nos _ o- | van- _ ti |
        gra- du fes- ti- | ne- mus. _""",
    "Tenor": """En | gre- ge re- | lic- to | hu- mi- les ad | cu- nas, vo- |
        ca- ti pas- | to- _ res ap- | pro- _ pe- | rant: | Et nos o- | van- ti |
        gra- du fes- ti- | ne- mus. _""",
    "Bass": """En | gre- ge re- | lic- to | hu- mi- les ad | cu- nas, vo- |
        ca- ti pas- | to- _ res ap- | pro- pe- | rant: | Et nos o- | van- ti |
        gra- du fes- ti- | ne- mus.""",
}


def verse_2(part: stream.Part) -> str:
    """Verse 2 for every bar, holding ("_") over the bars where only verse 1 is printed."""
    bars = VERSE_2[part.partName].split("|")
    for m in list(part.getElementsByClass(stream.Measure))[len(bars):]:
        sung = [n for n in m.notes if not (n.tie and n.tie.type in ("stop", "continue"))]
        bars.append(" _" * len(sung))
    return "|".join(bars)


def written_out(voice: str) -> str:
    """The words for ORDER: verse 1, then verse 2, whose own words stop after
    "festinemus" in bar 13 and go on with verse 1's "Venite adoremus"."""
    first = VERSE_1[voice].split("|")
    second = VERSE_2[voice].split("|")
    second[12] = " ".join(second[12].split()[:2] + first[12].split()[2:])
    second += first[len(second):]
    return "|".join([first[n - 1] for n in VERSE] + [second[n - 1] for n in VERSE])


def load_parts(order: list[int]) -> list[stream.Part]:
    parts = []
    for voice in NAMES:
        # written out in `order`, which also drops the score's repeat signs
        part = write_out_repeats(load_abc(f"adeste-{voice.lower()}.abc"), order)
        if voice in ("Tenor", "Bass"):
            to_tenor_clef(part)
        if voice == "Bass":
            # the director wants the bass in bass clef, at the same (sounding) pitch
            for c in list(part.recurse().getElementsByClass(clef.Clef)):
                c.activeSite.replace(c, clef.BassClef())
        for ts in part.recurse().getElementsByClass(meter.TimeSignature):
            ts.symbol = "common"  # the score writes C, not 4/4
        parts.append(part)
    return parts


def build() -> stream.Score:
    parts = load_parts(ORDER)
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        add_lyrics(part, written_out(part.partName))
    return score


def build_short() -> stream.Score:
    parts = load_parts(list(range(1, BARS + 1)))
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        add_lyrics(part, VERSE_1[part.partName])
        add_lyrics(part, verse_2(part), 2)
    return score
