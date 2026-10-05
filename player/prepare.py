"""Build the player's score files, for every song in songs/.

For each song writes
  player/static/scores/<id>.musicxml  (drawn by OpenSheetMusicDisplay)
  player/static/scores/<id>.json      (note events played by the browser piano)
and player/static/scores/index.json listing the songs.

    .venv/bin/python player/prepare.py
"""
import json
from pathlib import Path

from music21 import converter

from scorelib import check, events
from songs import ave, foc

SONGS = [foc, ave]
OUT = Path(__file__).resolve().parent / "static/scores"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for song in SONGS:
        print(song.TITLE)
        xml = OUT / f"{song.ID}.musicxml"
        song.build().write("musicxml", fp=str(xml))
        # re-read so bar offsets reflect any fixed durations
        score = converter.parse(str(xml))
        check(score)
        data = {"title": song.TITLE, "tempo": song.TEMPO, "myPart": song.MY_PART,
                **events(score)}
        (OUT / f"{song.ID}.json").write_text(json.dumps(data))
        index.append({"id": song.ID, "title": song.TITLE})
    (OUT / "index.json").write_text(json.dumps(index))
    print(f"wrote {len(SONGS)} songs to {OUT}")


if __name__ == "__main__":
    main()
