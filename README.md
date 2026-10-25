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

A web page for practising Foc de Nadal, Ave Verum Corpus, No olvides, Boga, boga,
Shalala-Bon nadal and Triste reloj: the score is drawn
in the browser from MusicXML (with lyrics), and played on a sampled grand piano.
Tick the parts to show and hear, set the tempo (or tap it in with "Marcar"),
turn on a metronome, and click a bar to play from there. Space is play/pause
and S solos the parts shown.
Repeats are written out; for songs with a version that has each bar once (so
far Boga, boga, Shalala and Triste reloj), "Sin repeticiones" switches to it.
Where a score changes tempo (Triste reloj), playback and the metronome follow it,
in proportion to the tempo set.

For the director to check the scores, `?director` (e.g.
https://mattvenn.github.io/choir-app/?director) shows and plays every part,
starts songs without repeats so the bar numbers are the score's, and a tap on a
note opens a WhatsApp message or an email saying which song, bar, voice and
note it is. It stays on in that browser until `?director=no`.

    .venv/bin/python player/prepare.py                   # builds player/static/scores/
    .venv/bin/python -m http.server -d player/static 8765

then open http://localhost:8765. The transcriptions it builds from are in
`player/sources/`, and each song (lyrics, corrections) is in `player/songs/`.
The built scores in `player/static/scores/` are committed: after changing a
song, run `prepare.py` and commit what it writes (CI checks they match).

## Published on GitHub Pages

Every push to `main` publishes `player/static` to
https://mattvenn.github.io/choir-app/ (see `.github/workflows/pages.yml`).

## Tests

    .venv/bin/pip install -r tests/requirements.txt
    .venv/bin/playwright install chromium
    .venv/bin/pytest tests

These play a song in headless Chrome, with a phone's output delay faked, to
check the highlighted bar moves when the bar is heard. CI runs them too.
