"""OMR engine interface: page images in, one MusicXML file out."""
from abc import ABC, abstractmethod
from pathlib import Path


class OmrEngine(ABC):
    name: str

    @abstractmethod
    def transcribe(self, page_images: list[Path], workdir: Path) -> Path:
        """Recognise the given page images (in order) and return a single MusicXML path."""
