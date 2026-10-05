"""Ave Verum Corpus K. 618 (Mozart), SATB, Pueri Cantores edition.

All four voices are hand transcriptions of the PDF (Audiveris got too much
wrong); the organ part is left out.
"""
from music21 import meter, stream

from scorelib import add_lyrics, load_abc, make_score, to_tenor_clef

ID = "ave"
TITLE = "Ave Verum Corpus"
COMPOSER = "W. A. Mozart"
TEMPO = 66  # Adagio, quarter = 66 in this edition
MY_PART = "Bass"
NAMES = ["Soprano", "Alto", "Tenor", "Bass"]
ABBREVIATIONS = ["S", "A", "T", "B"]
# transcribed from the PDF, see scorelib.add_lyrics for the format
LYRICS = {
    "Soprano": """ | | A- ve, _ | a- _ ve | ve- _ rum _ | cor- _ pus, | na- tum |
        de Ma- rí- a | vír- _ gi- | ne, | ve- re | pas- _ sum | im- _ mo- | lá- _ tum in |
        cru- | _ ce pro | hó- _ mi- | ne. | | | | Cu- jus |
        la- _ tus | per- _ fo- _ | rá- _ tum | un- da | flu- _ xit et | sán- _ _ gui- | ne, | es- to |
        no- _ bis _ | præ- gu- | stá- _ tum in | mor- | _ tis ex- | á- _ mi- | ne, in | mor- |
        _ | _ _ _ _ | _ _ _ tis ex- | á- _ mi- | ne. | | | """,
    "Alto": """ | | A- ve, | a- ve | ve- _ rum _ | cor- _ pus, | na- tum |
        de Ma- rí- a | vír- _ gi- | ne, | ve- re | pas- sum | im- mo- | lá- _ tum |
        in | cru- ce pro | hó- mi- | ne. | | | | Cu- jus |
        la- tus | per- fo- | rá- _ tum | un- da | flu- _ xit et | sán- _ _ gui- | ne, | es- to |
        no- _ bis _ | præ- gu- | stá- _ tum in | mor- | _ tis ex- | á- _ mi- | ne, | in |
        mor- _ | _ | _ _ tis ex- | á- _ mi- | ne. | | | """,
    "Tenor": """ | | A- ve, | a- ve | ve- rum | cor- pus, | na- tum |
        de Ma- rí- a | vír- gi- | ne, | ve- re | pas- _ sum | im- mo- | lá- _ tum |
        in | cru- ce pro | hó- mi- | ne. | | | | Cu- jus |
        la- tus _ | per- _ _ fo- | rá- _ tum | un- da | flu- _ xit et | sán- _ gui- | ne, | |
        es- to | no- _ bis _ | præ- gu- | stá- _ tum in | mor- tis ex- | á- mi- | ne, | in |
        mor- _ | _ _ _ _ | _ tis ex- | á- _ mi- | ne. | | | """,
    "Bass": """ | | A- ve, | a- ve | ve- rum | cor- pus, | na- tum |
        de Ma- rí- a | vír- gi- | ne, | ve- re | pas- _ sum | im- mo- | lá- _ tum |
        in | cru- ce pro | hó- mi- | ne. | | | | Cu- jus |
        la- _ tus | per- fo- | rá- _ tum | un- da | flu- _ xit et | sán- _ gui- | ne, | |
        es- to | no- _ bis _ | præ- gu- | stá- _ tum in | mor- tis ex- | á- mi- | ne, | in |
        mor- _ | _ | _ tis ex- | á- mi- | ne. | | | """,
}


def build() -> stream.Score:
    parts = [load_abc(f"ave-{voice}.abc") for voice in ("soprano", "alto", "tenor", "bass")]
    to_tenor_clef(parts[2])
    for part in parts:
        for ts in part.recurse().getElementsByClass(meter.TimeSignature):
            ts.symbol = "cut"  # the edition writes alla breve, not 2/2
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        add_lyrics(part, LYRICS[part.partName])
    return score
