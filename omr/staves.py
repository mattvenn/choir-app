"""Find staves on a page image and blank out all but one voice per system.

OMR engines tend to treat multi-staff scores as piano music, so we hand them
a page containing only the staff we want. Engine independent.
"""
from pathlib import Path

import cv2
import numpy as np


def find_staves(gray: np.ndarray, line_frac: float = 0.4) -> list[tuple[int, int]]:
    """Return (top, bottom) y of each 5-line staff, top to bottom."""
    dark = gray < 128
    rows = dark.sum(axis=1) > line_frac * gray.shape[1]
    # collapse runs of dark rows into single staff lines
    lines, y = [], 0
    while y < len(rows):
        if rows[y]:
            start = y
            while y < len(rows) and rows[y]:
                y += 1
            lines.append((start + y - 1) / 2)
        y += 1
    staves = []
    i = 0
    while i + 4 < len(lines):
        group = lines[i:i + 5]
        gaps = np.diff(group)
        if gaps.max() < 1.5 * gaps.min():  # evenly spaced => one staff
            staves.append((int(group[0]), int(group[-1])))
            i += 5
        else:
            i += 1
    return staves


def staff_start_x(gray: np.ndarray, top: int, bottom: int) -> int:
    """x where the staff lines begin: first run of `run` columns with 4+ of 5 lines drawn.

    Requiring a run skips vertical marks (brackets, braces) that cross every line.
    """
    run = 40
    dark = gray < 128
    rows = np.linspace(top, bottom, 5).round().astype(int)
    # a line may be a few pixels thick and the estimate off by one
    hits = sum(dark[max(r - 2, 0):r + 3].any(axis=0) for r in rows) >= 4
    full = np.convolve(hits, np.ones(run), mode="valid") == run
    return int(np.argmax(full)) if full.any() else 0


def isolate_staff(img_path: Path, out_path: Path, index: int, staves_per_system: int) -> int:
    """Write a copy of the page keeping only staff `index` (0-based) of every system.

    Returns the number of systems found.
    """
    gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    staves = find_staves(gray)
    if len(staves) % staves_per_system:
        raise ValueError(f"{img_path.name}: found {len(staves)} staves, "
                         f"not a multiple of {staves_per_system}")
    out = np.full_like(gray, 255)
    for s in range(index, len(staves), staves_per_system):
        top, bottom = staves[s]
        # keep the band halfway to the neighbouring staves (ledger lines, lyrics)
        above = (staves[s - 1][1] + top) // 2 if s > 0 else 0
        below = (bottom + staves[s + 1][0]) // 2 if s + 1 < len(staves) else gray.shape[0]
        # drop the part name and the system bracket left of the staff, they
        # confuse staff-line detection once the other staves are gone
        start = staff_start_x(gray, top, bottom)
        out[above:below, start:] = gray[above:below, start:]
        # the system barline and bracket hooks poke out above/below the staff
        edge = start + (bottom - top) // 2
        out[above:top - 2, :edge] = 255
        out[bottom + 3:below, :edge] = 255
    cv2.imwrite(str(out_path), out)
    return len(staves) // staves_per_system
