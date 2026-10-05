"""PDF -> page images -> isolated voice -> OMR -> MusicXML/MIDI/MP3."""
import subprocess
from pathlib import Path

from music21 import converter, tempo as m21tempo

from .engines import get_engine
from .staves import isolate_staff
from .synth import render


def pdf_to_images(pdf: Path, outdir: Path, dpi: int = 300) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    if not list(outdir.glob("page-*.png")):
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(outdir / "page")], check=True)
    return sorted(outdir.glob("page-*.png"))


def extract_part(pdf: Path, part: int, staves_per_system: int, tempo: float,
                 out: Path, engine_name: str | None = None) -> dict:
    """part is 1-based. Returns paths of the generated files."""
    pages = pdf_to_images(pdf, out / "pages")
    voice_dir = out / f"part{part}"
    voice_dir.mkdir(parents=True, exist_ok=True)
    voice_pages = []
    for page in pages:
        dst = voice_dir / page.name
        systems = isolate_staff(page, dst, part - 1, staves_per_system)
        print(f"{page.name}: {systems} systems")
        if systems:  # skip text-only pages
            voice_pages.append(dst)

    xml = get_engine(engine_name).transcribe(voice_pages, voice_dir / "omr")
    score = converter.parse(str(xml))
    p = score.parts[0]
    p.insert(0, m21tempo.MetronomeMark(number=tempo))
    midi = p.write("midi", fp=str(voice_dir / f"part{part}.mid"))
    wav = render(p, tempo, voice_dir / f"part{part}.wav")
    mp3 = voice_dir / f"part{part}.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-q:a", "4", str(mp3)], check=True)
    return {"musicxml": xml, "midi": Path(midi), "mp3": mp3}
