"""Registry of OMR engines. Pick one with OMR_ENGINE (default: oemer)."""
import os

from .base import OmrEngine

_ENGINES = {
    "oemer": "omr.engines.oemer_engine:OemerEngine",
}


def get_engine(name: str | None = None) -> OmrEngine:
    name = name or os.environ.get("OMR_ENGINE", "oemer")
    if name not in _ENGINES:
        raise ValueError(f"unknown OMR engine {name!r}, choose from {sorted(_ENGINES)}")
    module, cls = _ENGINES[name].split(":")
    return getattr(__import__(module, fromlist=[cls]), cls)()
