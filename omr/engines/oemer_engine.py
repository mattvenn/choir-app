"""oemer (https://github.com/BreezeWhite/oemer): ML-based OMR, one image per run."""
import subprocess
import sys
from pathlib import Path

from music21 import converter, stream

from .base import OmrEngine


class OemerEngine(OmrEngine):
    name = "oemer"

    def transcribe(self, page_images: list[Path], workdir: Path) -> Path:
        workdir.mkdir(parents=True, exist_ok=True)
        oemer = Path(sys.executable).with_name("oemer")
        page_xmls = []
        for img in page_images:
            xml = workdir / f"{img.stem}.musicxml"
            # oemer keys its cache on the file name only, next to the image
            cache = img.with_suffix(".pkl")
            if cache.exists() and cache.stat().st_mtime < img.stat().st_mtime:
                cache.unlink()
                xml.unlink(missing_ok=True)
            if not xml.exists():
                # -d: rendered PDFs are not skewed; --save-cache makes reruns fast
                subprocess.run([str(oemer), "-d", "--save-cache", "-o", str(workdir), str(img)],
                               check=True, stdout=subprocess.DEVNULL)
            page_xmls.append(xml)
        return merge_pages(page_xmls, workdir / "score.musicxml")


def merge_pages(page_xmls: list[Path], out: Path) -> Path:
    """Concatenate the first part of each page's MusicXML into one part."""
    merged = stream.Part()
    number = 1
    for xml in page_xmls:
        part = converter.parse(str(xml)).parts[0]
        for m in part.getElementsByClass(stream.Measure):
            m.number = number
            number += 1
            merged.append(m)
    score = stream.Score([merged])
    score.write("musicxml", fp=str(out))
    return out
