"""Foc de Nadal (D. Basomba), arranged for S, A1, A2 and Baritone.

The notes are from the director's MusicXML, exported from Finale
(sources/foc.musicxml). Its lyrics leave out every elided syllable ("na‿els",
"i‿el", ...) and get the hyphens wrong around them, so the lyrics are
transcribed from the PDF instead, except the baritone's last two bars: "al cel"
as in the director's file, where the PDF holds "cel" over both. The player
ignores the dynamics, hairpins and "molto ritardando".
"""
from music21 import stream

from scorelib import add_lyrics, load_finale, make_score

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
        dal | al | cel""",
}


def build() -> stream.Score:
    parts = load_finale("foc.musicxml")
    score = make_score(parts, NAMES, ABBREVIATIONS, TITLE, COMPOSER)
    for part in parts:
        for n in part.recurse().notes:
            n.lyrics = []
        add_lyrics(part, LYRICS[part.partName])
    return score
