# Generating practice audio from sheet music: OMR evaluation

*2026-10-05. Notes from the first exploration session for the choir app.*

## Why this matters

The README asks the app to generate audio for a part when no recording exists yet. The
director often has the sheet music before he has recorded the parts. Several other features
also need a machine-readable score, not just a PDF:

- clicking a bar to start playback there
- looping a section
- syncing a recording to the score
- hearing the other parts (left/right ear, all parts, all but mine)

All of these need the notes and bar positions for every part. This document records what we
learned about getting them from the scores we have.

## The test material

| File | Source | What's in the PDF |
|---|---|---|
| `Foc de nadal.pdf` | Daniel Basomba's own arrangement, **Finale 2014** | Engraved vector glyphs, 4 staves (S, A1, A2, Baritone), 45 bars, D major, 3/4, no tempo marking |
| `Ave Verum Corpus K618 ... .pdf` | Pueri Cantores public-domain edition, **Sibelius 5** | Engraved, 6 staves per system (SATB + organ), 46 bars, D major, cut time, ♩=66. Page 4 is text only |
| `Boga, boga copia.pdf` | Photocopy | 150 dpi bitmap scan (JBIG2) with handwritten pencil marks |
| `WhatsApp Audio ... .aac` | Recordings | Voices 2 and 4 of Boga Boga (~80 s and ~75 s) |

None of the PDFs contain machine-readable notes. Even the engraved ones only hold
music-font glyphs (Opus, Maestro), so the notes can only be recovered by reading the image.

## Background: Optical Music Recognition (OMR)

Turning a score image into notes is a well-known hard problem. It's harder than text OCR:

- **Notation is two-dimensional.** Pitch depends on staff position, clef, key signature and earlier accidentals in the bar.
- **Duration depends on several small details:** note head, stem, flags, beams, dots and tuplets.
- **Symbols overlap:** staff lines, beams, slurs, and lyrics underneath the notes.
- **One error spreads.** A misread clef shifts every note that follows it.

Expected accuracy is roughly 80–95% on clean engravings, and much lower on photocopies.

**The director uses Finale.** Finale exports MusicXML (File → Export → MusicXML), which gives
exact notes with no recognition step. MakeMusic discontinued Finale in August 2024. If he
moves to Dorico, Sibelius or MuseScore, all of them export MusicXML too.

## What was built

A small `omr/` package where the recognition engine can be swapped:

- `omr/engines/base.py`: the `OmrEngine` interface (page images in, MusicXML out).
- `omr/engines/__init__.py`: an engine registry, chosen with `OMR_ENGINE` or `--engine`.
- `omr/engines/oemer_engine.py`: runs oemer once per page and merges the pages with music21.
- `omr/staves.py`: finds the 5-line staves by horizontal projection and blanks out every staff except the wanted voice. It also removes the part name and system bracket. This step works with any engine.
- `omr/synth.py`: a small numpy additive synth, so no soundfont or fluidsynth is needed.
- `omr/pipeline.py` and `omr/cli.py`: PDF → page images → isolated voice → OMR → MusicXML/MIDI/MP3.

```
python -m omr.cli "music/Foc de nadal.pdf" --part 4 --staves 4 --tempo 100 --out out/foc
```

## Engines tried

### oemer 0.1.8 (Python, ML-based): not usable

- **Installation:** needs workarounds on macOS / Python 3.14 (see `requirements.txt`):
  - 0.1.5 crashes on the removed `np.int` alias.
  - 0.1.8 declares `onnxruntime-gpu`, which has no macOS build, so it must be installed with `--no-deps`.
  - OpenCV 5 changed the output of `HoughLinesP`, so OpenCV has to stay below 5.
- **Speed:** about 3 minutes of neural network inference per page. `--save-cache` writes a
  ~147 MB `.pkl` per page next to the input image. That's five 2280×1612 per-pixel label
  maps stored as int64. The cache is keyed by file name only, so the engine now deletes it
  when the image is newer.
- **On full pages:** it assumes piano grand staves. The four choir staves came back as one
  "Piano" part with alternating clefs.
- **On isolated single-staff pages:** staff-line extraction failed its own assertion on Foc
  page 1 and Ave page 2. Ave page 1 produced 2 bars out of about 16, and ignored the key
  signature (C instead of C♯).

### Audiveris 5.10.2 (Java, via Docker): good on simple layouts

There's no official image. `louie8821/audiveris` is a drum-notation build. The best
maintained image we found is `pgligic/audiveris:5.10.2-no-text`. It's amd64 only, so it runs
under emulation on Apple Silicon and natively on a droplet. Its entrypoint just waits, so
call the binary directly:

```
docker run --rm --platform linux/amd64 --entrypoint /opt/audiveris/bin/Audiveris \
  -v "$PWD/music:/in:ro" -v "$PWD/out/audiveris:/out" pgligic/audiveris:5.10.2-no-text \
  -batch -sheets 1 2 3 -export -output /out "/in/<file>.pdf"
```

- Takes about 2 minutes per page under emulation. Handles multi-part scores directly, so no staff isolation is needed.
- A text-only page (Ave page 4) makes the whole export fail. Use `-sheets` to skip it.

### Claude reading the page images: used as the reference

Each 4th-staff system was cropped and zoomed, and every bar was read. Notes near the top
line, where line and space are hard to tell apart, were measured in pixels against the staff
lines instead of judged by eye or guessed from the harmony. Two of these measurements
corrected what the harmony suggested: Foc bar 30 is G3 (not A3), and Ave bar 37 is B2 (a
deceptive cadence). The result was written as ABC and converted to MusicXML/MIDI/MP3.

This is a candidate for a third engine: the finished app would call the Claude API with the
page images.

## Results: 4th part of each piece

Audiveris output compared with the Claude transcription, bar by bar:

| | Foc de Nadal (Baritone) | Ave Verum (Bass) |
|---|---|---|
| oemer | crashed | crashed (2 bars from page 1) |
| Audiveris | **44 / 45 bars identical** | **25 / 46 bars identical** |
| Claude transcription | reference | reference |

**Foc de Nadal:** the only difference is bar 19, where Audiveris has the C♯3 as a quarter
instead of an eighth (it has a flag). That makes the bar 3½ beats long.

**Ave Verum:** the Audiveris errors fall into three groups:

- **Wrong clef for a whole system (bars 8–14):** it read the bass staff as treble, so every note is a sixth too high (e.g. B4 instead of D3).
- **Dropped notes:** whole notes turned into rests (bars 10, 18, 40, 43), and half notes went missing (bars 3–6).
- **Invented rhythms:** bars 28 and 34 got triplet-like values, and bar 31 has 4½ beats.

**Sharps (Foc de Nadal):** the key signature is 2 sharps (F♯, C♯) and the baritone staff has
no other accidentals. Both transcriptions independently have the same pitch content: 10 F♯,
1 C♯, no F♮ or C♮. The rendered MIDI contains only A B C♯ D E F♯ G.

**Caveat:** this measures agreement with the Claude transcription, not true accuracy.
Audiveris matching it on Foc is the only independent confirmation. A MusicXML export of Foc
de Nadal from Finale would give real ground truth.

## Automatic checks on OMR output

These checks need no reference score:

- every bar's length matches the time signature
- the bar count is right
- the key signature and clef are as expected
- the notes fit the voice's range

Of the 21 bad Audiveris bars in Ave Verum, 16 would be flagged:

- **By bar length:** bars 3, 4, 5, 6, 10, 17, 28, 31, 34, 37.
- **By range:** the wrong-clef system, bars 8–14.

The ones missed are notes turned into rests where the bar still adds up (18, 40, 41, 43) and
a merged note (35).

## Recommendations for the app

1. **Preferred input:** MusicXML (or MIDI) exported from the director's notation software, uploaded with the PDF. It's exact and gives the bar structure needed for click-to-play, looping and part mixing.
2. **For PDFs and photocopies:** run OMR in the background and treat the result as a **draft**. Run the automatic checks, highlight suspect bars, and let the admin listen and fix the draft or replace it with MusicXML before singers see it.
3. **Default OMR engine:** Audiveris in Docker.
4. **Next engine to test:** add a Claude-API engine and compare it on the same pieces and on the Boga Boga photocopy.
5. **Drop oemer.**
6. **Recordings:** a real recording replaces the synthesized audio for its part.
7. **Not yet handled:** the synth ignores tempo changes such as Foc's *molto ritardando* (bar 42). The default Foc tempo of ♩=100 is a guess.

## Generated files (not committed)

`out/` and `music/` are git-ignored:

- `out/claude/`: the reference transcriptions (`.abc`, `.musicxml`, `.mid`, `.mp3`)
- `out/audiveris/`: Audiveris MusicXML (`.mxl`) and its project files (`.omr`)
- `out/foc`, `out/ave`: oemer runs and caches (~600 MB, safe to delete)
