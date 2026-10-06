"""Build the player's score files, for every song in songs/.

For each song writes
  player/static/scores/<id>.musicxml  (drawn by OpenSheetMusicDisplay)
  player/static/scores/<id>.json      (note events played by the browser piano)
plus <id>-short.musicxml/.json, each bar once, for songs whose repeats are
written out, and player/static/scores/index.json listing the songs.

    .venv/bin/python player/prepare.py
"""
import json
import re
from pathlib import Path

from music21 import converter, stream

from scorelib import check, events
from songs import ave, boga, foc, no

SONGS = [foc, ave, no, boga]
OUT = Path(__file__).resolve().parent / "static/scores"


def reproducible(musicxml: str) -> str:
    """The scores are committed and CI checks they're up to date, so a rebuild
    must give the same file: drop the date and renumber music21's random part
    and instrument ids (P1, P2, ..., I1, I2, ... in order of appearance)."""
    musicxml = re.sub(r"\s*<encoding-date>.*?</encoding-date>", "", musicxml)
    new_ids: dict[str, str] = {}

    def renumber(m: re.Match) -> str:
        tag, old = m.groups()
        if old not in new_ids:
            kind = "P" if tag.endswith("part") else "I"
            count = sum(v.startswith(kind) for v in new_ids.values())
            new_ids[old] = f"{kind}{count + 1}"
        return f'<{tag} id="{new_ids[old]}"'

    tags = "score-part|part|score-instrument|midi-instrument|instrument"
    return re.sub(rf'<({tags}) id="([^"]+)"', renumber, musicxml)


def write(song, name: str, score: stream.Score) -> None:
    xml = OUT / f"{name}.musicxml"
    score.write("musicxml", fp=str(xml))
    xml.write_text(reproducible(xml.read_text()))
    # re-read so bar offsets reflect any fixed durations
    score = converter.parse(str(xml))
    check(score)
    data = {"title": song.TITLE, "tempo": song.TEMPO, "myPart": song.MY_PART,
            **events(score)}
    (OUT / f"{name}.json").write_text(json.dumps(data))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for song in SONGS:
        print(song.TITLE)
        write(song, song.ID, song.build())
        entry = {"id": song.ID, "title": song.TITLE}
        # the player's "no repeats" checkbox switches to this version
        if hasattr(song, "build_short"):
            print("  without repeats:")
            write(song, f"{song.ID}-short", song.build_short())
            entry["short"] = True
        index.append(entry)
    (OUT / "index.json").write_text(json.dumps(index))
    print(f"wrote {len(SONGS)} songs to {OUT}")


if __name__ == "__main__":
    main()
