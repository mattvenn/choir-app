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

* should be easy to install on a digital ocean droplet
* doesn't need to scale, just a proof of concept
* start with the  audio recordings and the 3 pdfs in this directory
	* the audio recordings are for the 2nd and 4th voices of boga boga


# player (first version)

A web page for practising Foc de Nadal and Ave Verum Corpus: the score is drawn
in the browser from MusicXML (with lyrics), and played on a sampled grand piano.
Tick the parts to show and hear, set the tempo, turn on a metronome, and click
a bar to play from there. Space is play/pause and S solos the parts shown.

    .venv/bin/python player/prepare.py                   # builds player/static/scores/
    .venv/bin/python -m http.server -d player/static 8765

then open http://localhost:8765. The transcriptions it builds from are in
`player/sources/`, and each song (lyrics, corrections) is in `player/songs/`.
The built scores in `player/static/scores/` are committed: after changing a
song, run `prepare.py` and commit what it writes (CI checks they match).

## Published on GitHub Pages

Every push to `main` publishes `player/static` to
https://mattvenn.github.io/choir-app/ (see `.github/workflows/pages.yml`).

## Install on a droplet

The player is a static site, so nginx serves it directly and there is no
service to run. These steps assume nginx is already installed, as for
online_questions. Replace `choir.example.com` with your domain, and point the
domain's DNS A record at the droplet.

1. Get the code (the built scores are included, so no Python is needed):

   ```bash
   sudo git clone https://github.com/mattvenn/choir-app.git /opt/choir-app
   ```

2. Set your domain in `choir-app.nginx` (the `server_name` line), then enable it:

   ```bash
   cd /opt/choir-app
   sudo cp choir-app.nginx /etc/nginx/sites-available/choir-app
   sudo ln -sf /etc/nginx/sites-available/choir-app /etc/nginx/sites-enabled/choir-app
   sudo nginx -t && sudo systemctl reload nginx
   ```

3. Open http://choir.example.com.

4. Optional, for https (if certbot is installed):

   ```bash
   sudo certbot --nginx -d choir.example.com
   ```

To update later:

```bash
cd /opt/choir-app && sudo git pull
```

No nginx reload is needed for updates.
