# simple web app for a community choir

a demo that might become more featured / polished later.

for now the features these are the features

## admin side

* load a pdf of sheet music
* optionally load a recording of the music being played or sung
* if no recording is available, generate the audio from the uploaded music
* if we have the music and the recording, be able to sync them, so that users can practice sections and the audio lines up
* have some settings like the name, any notes to be aware of, override bpm

## user side

* choose the song to practice
* choose the part (usually there are 4 parts)
* adjust the speed (default is what's set by the music or admin)
* shows the music and plays the recording
* easily play, stop, rewind. random access - be able to click on a bar (or maybe a line) and the music starts from there
* loop a section to practice
* works on mobile
* stretch goal - be able to hear the other parts while singing:
	* other part in left ear and user's part in right ear. 
	* all parts mixed in both ears
	* all parts but mine


# tech

* hosted as a static site on GitHub Pages
* doesn't need to scale, just a proof of concept
* start with the  audio recordings and the 3 pdfs in this directory
	* the audio recordings are for the 2nd and 4th voices of boga boga


# player (first version)

A web page for practising Foc de Nadal, Ave Verum Corpus, No olvides, Boga, boga and
Shalala-Bon nadal: the score is drawn
in the browser from MusicXML (with lyrics), and played on a sampled grand piano.
Tick the parts to show and hear, set the tempo (or tap it in with "Marcar"),
turn on a metronome, and click a bar to play from there. Space is play/pause
and S solos the parts shown.
Repeats are written out; for songs with a version that has each bar once (so
far Boga, boga and Shalala), "Sin repeticiones" switches to it.

    .venv/bin/python player/prepare.py                   # builds player/static/scores/
    .venv/bin/python -m http.server -d player/static 8765

then open http://localhost:8765. The transcriptions it builds from are in
`player/sources/`, and each song (lyrics, corrections) is in `player/songs/`.
The built scores in `player/static/scores/` are committed: after changing a
song, run `prepare.py` and commit what it writes (CI checks they match).

## Published on GitHub Pages

Every push to `main` publishes `player/static` to
https://mattvenn.github.io/choir-app/ (see `.github/workflows/pages.yml`).
