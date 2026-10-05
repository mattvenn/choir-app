"""Foc de Nadal (D. Basomba), arranged for S, A1, A2 and Baritone.

Soprano and altos come from Audiveris (run without text recognition), with the
misreads fixed by hand against the PDF; the baritone is a hand transcription.
"""
import copy

from music21 import converter, dynamics, spanner, stream

from scorelib import SOURCES, add_lyrics, load_abc, make_score, realign_bars, set_rhythm, tie_over

ID = "foc"
TITLE = "Foc de Nadal"
COMPOSER = "D. Basomba"
TEMPO = 100  # quarter notes per minute; the score has no marking
MY_PART = "Baritone"
NAMES = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
ABBREVIATIONS = ["S", "A1", "A2", "B"]
# transcribed from the PDF, see scorelib.add_lyrics for the format
LYRICS = {
    "Soprano": """La | nit de na- | dal fa | fred i ca- | lor el | foc il- lu- |
        mi- na‿els de- | sit- jos de | tots la | nit de na- | dal es- | tre- les al |
        cel si | pa- res l'o- | re- lla se | sen- ten molt | bé i‿el | foc a- com- |
        pa- nya‿amb el | seu cre- pi- | tar cri cri | cri cric ri | cri cri cri | crac |
        i | tots a- bra- | çats _ can- | tem els re- | cords i | els que no‿hi |
        són _ des | de dalt ens | mi- ren La | nit de na- | dal fa | fred i ca- |
        lor el | foc il- lu- | mi- na‿els de- | sit- jos de | tots la | nit de na- |
        dal _ es- | tre- les al | cel""",
    "Alto 1": """ | La nit | de Na- | dal fred | i ca- | lor de- |
        sit- jos | de | tots | La nit | de Na- | dal al |
        cel si | pa- res l'o- | re- lla se | sen- ten molt | bé | el |
        foc | cre- | pi- | ta | cri cri cri | crac |
        | Tots | a | bra- | çats | els que no‿hi |
        són | _ | mi- ren | La nit | de Na- | dal fred |
        i ca- | lor de- | sit- jos | de sit- | jos | nit de Na- |
        dal es- | tre- les al | cel""",
    "Alto 2": """ | La nit | de Na- | dal fred | i ca- | lor de- |
        sit- jos | de _ | tots | La nit | de Na- | dal al |
        cel si | pa- res l'o- | re se _ | sen- ten molt | bé | el |
        foc | cre- | pi- | ta | cri cri cri | crac |
        | Tots | a | bra- | çats | els |
        que no‿hi | són | són | La nit | de Na- | dal fred |
        i ca- | lor de- | sit- jos | de sit- | jos | nit de Na- |
        dal es- | tre- les al | cel""",
    "Baritone": """ | La nit | de _ Na- | dal fred | i ca- | lor de- |
        sit- jos | de | tots | La nit | de _ Na- | dal al |
        cel si | pa- res l'o- | re- lla se | sen- ten molt | bé | el |
        foc _ _ | cre- | pi- | ta | cri | crac |
        | Tots | a | bra- | çats | els |
        que no‿hi | són | són | La nit | de _ Na- | dal fred |
        i ca- | lor de- | sit- jos | de sit- | jos | nit de Na- |
        dal | cel | _""",
}


def build() -> stream.Score:
    audiveris = converter.parse(str(SOURCES / "foc-audiveris.mxl"))
    parts = list(audiveris.parts[:3]) + [load_abc("foc-baritone.abc")]
    fix_audiveris(*parts[:3])
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        add_lyrics(part, LYRICS[part.partName])
    return score


def fix_audiveris(soprano: stream.Part, alto1: stream.Part, alto2: stream.Part) -> None:
    """Corrections checked against the PDF."""
    # Audiveris turns lyric fragments and dots into staccatos, trills, dynamics
    # and slurs that aren't in the score; the PDF has no articulations at all
    for part in (soprano, alto1, alto2):
        for n in part.recurse().notes:
            n.articulations, n.expressions = [], []
        junk = list(part.recurse().getElementsByClass(dynamics.Dynamic))
        junk += [sp for sp in part.spanners if isinstance(sp, spanner.Slur)]
        part.remove(junk, recurse=True)
    # dotted quarter + eighth + quarter, Audiveris read the eighth as a quarter
    for bar in (14, 28, 32):
        set_rhythm(soprano.measure(bar), [1.5, 0.5, 1])
    # three quarters ("cri cri cri"), Audiveris found two dotted quarters
    m = alto2.measure(23)
    m.append(copy.deepcopy(m.notes[-1]))
    set_rhythm(m, [1, 1, 1])
    # the PDF has an extender under "se" here, not a tie
    for n in alto2.measure(15).notes:
        n.tie = None
    # "crac" is tied into bar 25 in every part
    for part in (soprano, alto1, alto2):
        tie_over(part, 24)
    realign_bars(soprano)
    realign_bars(alto2)
