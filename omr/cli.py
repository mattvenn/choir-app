import argparse
from pathlib import Path

from .pipeline import extract_part

ap = argparse.ArgumentParser(description="Generate practice audio for one voice from a score PDF")
ap.add_argument("pdf", type=Path)
ap.add_argument("--part", type=int, required=True, help="voice number, 1 = top staff")
ap.add_argument("--staves", type=int, default=4, help="staves per system (incl. accompaniment)")
ap.add_argument("--tempo", type=float, default=100, help="quarter notes per minute")
ap.add_argument("--engine", default=None, help="OMR engine (default $OMR_ENGINE or oemer)")
ap.add_argument("--out", type=Path, required=True)
a = ap.parse_args()
for kind, path in extract_part(a.pdf, a.part, a.staves, a.tempo, a.out, a.engine).items():
    print(f"{kind}: {path}")
