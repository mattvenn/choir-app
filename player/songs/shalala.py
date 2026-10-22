"""Shalala-Bon nadal (D. Basomba), arranged for S, A1, A2 and Baritone.

All four voices are hand transcriptions of the PDF (Finale 2014, one page).
The whole song is repeated; the repeat is written out, so bar numbers after 13
don't match the PDF. build_short() is the score as printed, each bar once.
The player ignores the dynamics and the fermatas on the last bar.

Lyrics follow the PDF except: the soprano's "la rry Christ-mas" in bar 3 is
"Me-rry" as in the other parts, "Weih-nach-ten" is spelt the same in every
part, and "E-gu-be-rri on" (Basque) is split as two words in every part.
"""
from music21 import stream

from scorelib import add_lyrics, load_abc, make_score, write_out_repeats

ID = "shalala"
TITLE = "Shalala-Bon nadal"
COMPOSER = "D. Basomba"
TEMPO = 56  # the choir's choice; the score has no marking
MY_PART = "Baritone"
NAMES = ["Soprano", "Alto 1", "Alto 2", "Baritone"]
ABBREVIATIONS = ["S", "A1", "A2", "B"]
FILES = ["soprano", "alto1", "alto2", "baritone"]
ORDER = [*range(1, 14), *range(1, 14)]
# one entry per PDF bar, see scorelib.add_lyrics for the format. In bars 4 and
# 5 the altos sing the last "la" again where the soprano ties it.
LYRICS = {
    "Soprano": """Sha- la- la sha- la- la | sha- la- la la- la sha- la |
        Me- rry Christ- mas Bo na- dal | Sha- la- la sha- la- la- la- la |
        sha- la- la sha- la- la | Buon na- ta- le Jo- yeux nö- el |
        Sha- la- la sha- la- la Fe- | liz Na- vi- dad | Sha- la- la sha- la- la |
        sha- la- la sha- la sha- la- la- la- la E- | gu- be- rri on Fro- he Weih- nach- ten |
        Sha- la- la | Sha- la- la Bon na- dal""",
    "Alto 1": """Sha- la- la sha- la- la | sha- la- la sha- la |
        Me- rry Christ- mas Bo na- dal | Sha- la- la _ sha- la- la- la- la |
        sha- la- la sha- la- la _ | Buon na- ta- le Jo- yeux nö- el |
        Sha- la- la sha- la- la Fe- | liz Na- vi- dad | Sha- la- la sha- la- la |
        sha- la- la sha- la sha- la- la- la- la E- | gu- be- rri on Fro- he Weih- nach- ten |
        sha- la- la | Sha- la- la Bon na- dal""",
    "Alto 2": """Sha- la- la sha- la- la | sha- la- la sha- la |
        Me- rry Christ- mas Bon na- dal | Sha- la- la _ sha- la- la- la- la |
        sha- la- la sha- la- la _ | Buon na- ta- le Jo- yeux nö- el |
        Sha- la- la sha- la- la Fe- | liz Na- vi- dad | Sha- la- la sha- la- la |
        sha- la- la sha- la sha- la- la- la- la E- | gu- be- rri on Fro- he Weih- nach- ten |
        sha- la- la | Sha- la- la Bon na- dal""",
    "Baritone": """Sha- la- | la- la | Me- rry Christ- mas Bo na- dal |
        Sha- la- la- la | Sha- la | buon na- ta- le Jo- yeux nöel |
        Sha- la Fe- | liz Na- vi- dad | Sha- la | Sha- la E- | gu- be- rri on |
        Sha- | la""",
}


def load_parts() -> list[stream.Part]:
    return [load_abc(f"shalala-{name}.abc") for name in FILES]


def build() -> stream.Score:
    parts = [write_out_repeats(part, ORDER) for part in load_parts()]
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        bars = LYRICS[part.partName].split("|")
        add_lyrics(part, "|".join(bars[n - 1] for n in ORDER))
    return score


def build_short() -> stream.Score:
    parts = load_parts()
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        add_lyrics(part, LYRICS[part.partName])
    return score
