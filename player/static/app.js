// Score player: OpenSheetMusicDisplay draws the MusicXML, Tone.js plays the
// note events from the matching JSON on a sampled grand piano.
const PIANO_URL = "https://tonejs.github.io/audio/salamander/";
// Salamander has a sample every minor third; the sampler repitches between them
const PIANO_SAMPLES = Object.fromEntries(
  ["A0", "C1", "Ds1", "Fs1", "A1", "C2", "Ds2", "Fs2", "A2", "C3", "Ds3", "Fs3", "A3",
   "C4", "Ds4", "Fs4", "A4", "C5", "Ds5", "Fs5", "A5", "C6", "Ds6", "Fs6", "A6",
   "C7", "Ds7", "Fs7", "A7", "C8"].map(n => [n.replace("s", "#"), `${n}.mp3`]));

// Interface text, in English if the browser is set to English and Spanish
// otherwise, unless the address says which (?lang=en or ?lang=es, to check
// the other). Part names come from the score, so aren't translated.
const STRINGS = {
  en: {
    appName: "Choir Practice",
    chooseVoice: "Which voice do you sing?",
    chooseVoiceHint: "Each song will show and play your part. You can change your voice later on this page.",
    songs: "Songs",
    play: "Play",
    pause: "Pause",
    tempo: "Tempo (quarter notes a minute)",
    stop: "Stop",
    tap: "Tap",
    tapTitle: "Tap along with the beat to set the tempo",
    resetTempo: bpm => `Back to the score's tempo (${bpm})`,
    repeats: "Repeats",
    repeatsTitle: "Play the repeats, or each bar once",
    noRepeatsTitle: "This song has no version without repeats",
    pauseForRepeats: "Pause to switch the repeats on or off",
    clickVolume: "Metronome volume",
    me: "Me",
    everyone: "Everyone",
    othersTitle: "Fade the other voices in and out",
    yourVoice: voice => `Your voice: ${voice}`,
    directorMode: "Director's view: every voice",
    reportNote: (song, bar, part, n, note, lyric) =>
      `${song}, bar ${bar}, ${part}: note ${n} (${note}${lyric ? `, "${lyric}"` : ""})`,
    reportSubject: (song, bar) => `${song}, bar ${bar}`,
    reportSend: "Report on WhatsApp",
    reportEmail: "Report by email",
    playFromHere: "Play from this bar",
    yourPart: "Your part",
    help: "Help",
    close: "Close",
    helpControls: {
      "home-button": "Back to the song list.",
      play: "Play and pause. On a keyboard, Space does the same.",
      stop: "Stop, and go back to the start.",
      repeats: "Repeats. Switch them off to hear each bar once. Greyed out when a song has no version without them.",
      tap: "Tap along with the beat to set the tempo.",
      tempo: "The tempo. The mark is the score's own; away from it, tap the number to go back to it.",
      speaker: "The metronome's volume. All the way left, it's off.",
      others: "From just your part, slide towards the group to bring the other voices in.",
    },
    helpNotes: [
      "Tap a bar to play from there. While it's playing, it goes there when the bar playing ends, so the beat carries on.",
      "The bars you go back to most are shaded orange. The song list shows how long you've practised each song and how many bars are still hard. It follows the last couple of weeks, so it changes as you get better.",
      "Where a song splits your voice (Alto 1 and Alto 2), choose your line with A1 and A2 at the right of the toolbar.",
      "With a mouse, point at a note to see its name.",
      "Your voice, the repeats and the metronome, and the tempo and the other voices' volume for each song, are remembered on this device.",
      "On a phone, songs work best with the phone turned sideways.",
    ],
    directorNote: "Director's view: every voice is shown and played equally loud, and songs start without repeats so the bar numbers match the score. Tap a note to report a mistake in it on WhatsApp or by email: the message says which song, bar, voice and note, and you add what's wrong and choose who to send it to. To go back to one voice, open the address with ?director=no.",
    error: message => `Error: ${message}`,
    updated: (date, time) => `Last updated ${date} at ${time}`,
    minutes: n => `${n} min`,
    hardBars: (n, weekAgo) => `${n} hard bar${n === 1 ? "" : "s"}` +
      (weekAgo === undefined ? "" : ` (${weekAgo} a week ago)`),
  },
  es: {
    appName: "Ensayo de coro",
    chooseVoice: "¿Qué voz cantas?",
    chooseVoiceHint: "Cada canción mostrará y tocará tu voz. Puedes cambiarla luego en esta página.",
    songs: "Canciones",
    play: "Reproducir",
    pause: "Pausa",
    tempo: "Tempo (negras por minuto)",
    stop: "Parar",
    tap: "Marcar",
    tapTitle: "Toca al ritmo del pulso para fijar el tempo",
    resetTempo: bpm => `Volver al tempo de la partitura (${bpm})`,
    repeats: "Repeticiones",
    repeatsTitle: "Tocar las repeticiones, o cada compás una vez",
    noRepeatsTitle: "Esta canción no tiene versión sin repeticiones",
    pauseForRepeats: "Pausa para activar o desactivar las repeticiones",
    clickVolume: "Volumen del metrónomo",
    me: "Mi voz",
    everyone: "Todos",
    othersTitle: "Sube y baja las otras voces",
    yourVoice: voice => `Tu voz: ${voice}`,
    directorMode: "Vista del director: todas las voces",
    reportNote: (song, bar, part, n, note, lyric) =>
      `${song}, compás ${bar}, ${part}: nota ${n} (${note}${lyric ? `, «${lyric}»` : ""})`,
    reportSubject: (song, bar) => `${song}, compás ${bar}`,
    reportSend: "Avisar por WhatsApp",
    reportEmail: "Avisar por correo",
    playFromHere: "Tocar desde este compás",
    yourPart: "Tu parte",
    help: "Ayuda",
    close: "Cerrar",
    helpControls: {
      "home-button": "Volver a la lista de canciones.",
      play: "Reproducir y pausar. Con teclado, la barra espaciadora hace lo mismo.",
      stop: "Parar y volver al principio.",
      repeats: "Repeticiones. Desactívalas para oír cada compás una vez. En gris si la canción no tiene versión sin ellas.",
      tap: "Toca al ritmo del pulso para fijar el tempo.",
      tempo: "El tempo. La marca es el de la partitura; si te alejas, toca el número para volver a él.",
      speaker: "El volumen del metrónomo. Del todo a la izquierda, no suena.",
      others: "Desde solo tu voz, desliza hacia el grupo para oír las otras voces.",
    },
    helpNotes: [
      "Pulsa un compás para reproducir desde ahí. Si ya suena, salta al acabar el compás, para no perder el pulso.",
      "Los compases a los que más vuelves se marcan en naranja. La lista de canciones muestra cuánto has ensayado cada una y cuántos compases te siguen costando. Sigue las últimas dos semanas, así que cambia a medida que mejoras.",
      "Si una canción divide tu voz (Alto 1 y Alto 2), elige tu línea con A1 y A2 a la derecha de la barra.",
      "Con ratón, señala una nota para ver su nombre.",
      "Tu voz, las repeticiones y el metrónomo, y el tempo y el volumen de las otras voces de cada canción, se guardan en este dispositivo.",
      "En el móvil, las canciones se ven mejor con el teléfono en horizontal.",
    ],
    directorNote: "Vista del director: se muestran todas las voces y suenan igual de fuerte, y las canciones empiezan sin repeticiones para que los números de compás coincidan con la partitura. Pulsa una nota para avisar de un error por WhatsApp o por correo: el mensaje dice la canción, el compás, la voz y la nota, y tú añades qué está mal y eliges a quién enviarlo. Para volver a una sola voz, abre la dirección con ?director=no.",
    error: message => `Error: ${message}`,
    updated: (date, time) => `Actualizado el ${date} a las ${time}`,
    minutes: n => `${n} min`,
    hardBars: (n, weekAgo) => `${n} ${n === 1 ? "compás difícil" : "compases difíciles"}` +
      (weekAgo === undefined ? "" : ` (${weekAgo} hace una semana)`),
  },
};
const askedLang = new URLSearchParams(location.search).get("lang");
const lang = askedLang in STRINGS ? askedLang
  : navigator.language.toLowerCase().startsWith("en") ? "en" : "es";
const t = (key, ...args) => {
  const s = STRINGS[lang][key];
  return typeof s === "function" ? s(...args) : s;
};

// Fill in the page's fixed text from data-i18n* attributes.
function applyLanguage() {
  document.documentElement.lang = lang;
  for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n);
  for (const el of document.querySelectorAll("[data-i18n-title]")) el.title = t(el.dataset.i18nTitle);
  for (const el of document.querySelectorAll("[data-i18n-aria-label]")) {
    el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel));
  }
  setPlayLabel();
  document.title = song && !$("player").hidden ? `${song.title} · ${t("appName")}` : t("appName");
}

const $ = id => document.getElementById(id);

// Settings kept in this browser between visits. Storage can be missing or
// blocked (private windows), so reads fall back to null and writes are dropped.
const store = {
  get(key) {
    try { return JSON.parse(localStorage.getItem(`choir.${key}`)); } catch { return null; }
  },
  set(key, value) {
    try { localStorage.setItem(`choir.${key}`, JSON.stringify(value)); } catch {}
  },
};

// The director's view, for checking the scores: every part shown and played
// alike, each bar once. Not offered on the page: ?director turns it on for
// this browser and ?director=no off again.
const askedDirector = new URLSearchParams(location.search).get("director");
if (askedDirector !== null) store.set("director", askedDirector !== "no");
const director = Boolean(store.get("director"));
document.body.classList.toggle("director", director);

// Google Analytics: which songs get opened and played. Only on the published
// site, so local testing isn't counted. Page views are sent by hand, since a
// song is only a #fragment of the URL.
const GA_ID = location.hostname === "mattvenn.github.io" ? "G-VEP6N5WR4B" : "";
window.dataLayer = window.dataLayer || [];
function gtag() { dataLayer.push(arguments); }
if (GA_ID) {
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  document.head.append(script);
  gtag("js", new Date());
  gtag("config", GA_ID, { send_page_view: false });
}
const track = (event, params) => { if (GA_ID) gtag("event", event, params); };
const trackPage = (path, title) => track("page_view", {
  page_location: location.origin + location.pathname.replace(/\/$/, "") + path,
  page_title: title,
});

// Tone asks for the shortest audio buffer it can get, as for a live instrument;
// on phones, with Bluetooth especially, that crackles. Everything here is
// scheduled ahead, so a longer one costs nothing.
// Made here rather than by Tone, whose own wraps it and hides outputLatency.
const audioContext = new AudioContext({ latencyHint: "playback" });
Tone.setContext(audioContext);
// Notes and ticks are handed to the audio this far ahead (Tone's own is 0.1s).
// When a phone is busy for longer than that, a tick is handed over after its
// time: its 30ms click is cut short or lost, though the longer piano notes
// survive. Pressing play takes this long to start, which isn't noticed.
Tone.getContext().lookAhead = 0.25;
const transport = Tone.getTransport();
// Draw goes by the time the audio is worked out, but it's heard later: after
// the output buffer (longer for the hint above) and, over Bluetooth, the
// headphones' own delay. So what's drawn waits for what's heard.
// The output timestamp says which moment of the audio is coming out now, so
// the gap to the one being worked out is the whole delay in one. Adding up the
// two latencies instead came out 13-19ms more on every device tried, as if
// some of it were counted in both. They're the fallback: before the audio
// starts, where there's no timestamp, or where it's far out (older iPhones
// gave nonsense).
const outputDelay = () => {
  const stamp = audioContext.getOutputTimestamp?.();
  if (stamp?.performanceTime > 0) {
    const heardNow = stamp.contextTime + (performance.now() - stamp.performanceTime) / 1000;
    const delay = audioContext.currentTime - heardNow;
    if (delay >= 0 && delay < 1) return delay;
  }
  return (audioContext.baseLatency || 0) + (audioContext.outputLatency || 0);
};
const drawWhenHeard = (callback, time) => Tone.getDraw().schedule(callback, time + outputDelay());
// What's waiting to be drawn belongs to the music as it was going; after a
// pause, stop or jump it would move the highlight away from where it now is.
const cancelDraws = () => Tone.getDraw().cancel(0);
// Two pianos on the same samples: one plays your part, the other the rest,
// through a gain the slider fades from silent (your part alone) to full
// (the whole choir).
// A sampler only shares a buffer that has already loaded, so the pianos are
// made once the samples are in (see init).
const samples = new Tone.ToneAudioBuffers({ urls: PIANO_SAMPLES, baseUrl: PIANO_URL });
const othersGain = new Tone.Gain(0).toDestination();
let myPiano, othersPiano;
function makePianos() {
  const urls = Object.fromEntries(Object.keys(PIANO_SAMPLES).map(note => [note, samples.get(note)]));
  myPiano = new Tone.Sampler({ urls, release: 1 }).toDestination();
  othersPiano = new Tone.Sampler({ urls, release: 1 }).connect(othersGain);
}
const releaseAll = () => { myPiano?.releaseAll(); othersPiano?.releaseAll(); };
// the slider runs 0 (your part alone) to 100 (everyone); a short ramp, so
// dragging it doesn't click
const setOthers = percent => {
  $("others").value = percent;
  othersGain.gain.rampTo(percent / 100, 0.05);
};
const click = new Tone.Synth({
  oscillator: { type: "square" },
  envelope: { attack: 0.001, decay: 0.04, sustain: 0, release: 0.01 },
}).toDestination();
// the slider runs 0-100; 100 is three quarters of what it was before, which
// could still be set too loud
const CLICK_MAX_GAIN = 0.1875;
const setClickVolume = percent => {
  click.volume.value = Tone.gainToDb(percent / 100 * CLICK_MAX_GAIN);
  // silent: no waves; then one more for each third of the way up
  document.querySelectorAll("#speaker .wave").forEach((wave, i) => {
    wave.classList.toggle("off", percent <= i * 100 / 3);
  });
};

let songs;         // scores/index.json
let song;          // scores/<id>.json
let songId;        // which song is loaded (`song` may be its version without repeats)
// While a score loads, the old one is gone and the new one isn't drawn yet, so
// what reads the drawing (redrawing on a resize, a tap on a bar, the
// highlight, the switches and play) waits; on a phone that can take a while.
let loading = false;
let osmd;
let mine = [];     // per part: whether it's your voice's
let currentBar = 0;

// note times are in quarters; scheduling in transport ticks means a tempo
// change takes effect immediately, even mid-playback
const ticks = quarters => `${Math.round(quarters * transport.PPQ)}i`;

const getJSON = async url => (await fetch(url)).json();

// The choir's four voices, and the part names each looks for in a song, in
// order: songs for three upper voices have one Baritone part for the men.
// "Alto" also matches "Alto 1" and "Alto 2".
const VOICE_PARTS = {
  Soprano: ["Soprano"],
  Alto: ["Alto"],
  Tenor: ["Tenor", "Baritone"],
  Bass: ["Bass", "Baritone"],
};

// Which parts of this song are the voice's; if none, the song's own part.
function voiceParts(voice) {
  for (const name of VOICE_PARTS[voice] ?? []) {
    const flags = song.parts.map(p => p.name === name || p.name.startsWith(`${name} `));
    if (flags.some(Boolean)) return flags;
  }
  return song.parts.map(p => p.name === song.myPart);
}

// Your parts in this song. Where your voice is split (Alto 1 and 2) it's the
// one chosen on the song page, kept per song, or to start with the first.
// `split` is the parts it could be, for the switch.
function myParts() {
  // the director's are all of them, on the same piano at the same volume
  if (director) return { flags: song.parts.map(() => true), split: [] };
  const flags = voiceParts(store.get("voice"));
  const split = flags.flatMap((yours, i) => yours ? [i] : []);
  if (split.length < 2) return { flags, split: [] };
  const saved = store.get(`part.${songId}`);
  const chosen = split.includes(saved) ? saved : split[0];
  return { flags: flags.map((_, i) => i === chosen), split };
}

// "Alto 1" is A1 on the switch, as on the score's later lines
const shortName = name => name.split(" ").map(word => /^\d+$/.test(word) ? word : word[0]).join("");

function showPartSwitch(split) {
  $("part-switch").hidden = !split.length;
  $("part-switch").replaceChildren(...split.map(i => {
    const button = document.createElement("button");
    button.textContent = shortName(song.parts[i].name);
    button.title = song.parts[i].name;
    button.setAttribute("aria-label", song.parts[i].name);
    button.setAttribute("aria-pressed", mine[i]);
    button.addEventListener("click", () => choosePart(i));
    return button;
  }));
}

function choosePart(i) {
  store.set(`part.${songId}`, i);
  mine = song.parts.map((_, k) => k === i);
  for (const button of $("part-switch").children) {
    button.setAttribute("aria-pressed", button.title === song.parts[i].name);
  }
  keepingPlace(render);
}

// On a first visit, ask which voice they sing before anything else opens;
// again from the chooser's "change" link.
function askVoice() {
  $("home").hidden = false;
  $("song-list").hidden = $("voice-line").hidden = true;
  $("voice-picker").hidden = false;
  $("voice-list").replaceChildren();
  return new Promise(resolve => {
    for (const voice of Object.keys(VOICE_PARTS)) {
      const button = document.createElement("button");
      button.textContent = voice;
      button.addEventListener("click", () => {
        store.set("voice", voice);
        track("choose_voice", { voice });
        $("voice-picker").hidden = true;
        $("song-list").hidden = $("voice-line").hidden = false;
        resolve();
      });
      $("voice-list").append(button);
    }
  });
}

async function init() {
  osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay($("score"), {
    autoResize: false,  // we re-render ourselves so the highlight can follow
    backend: "svg",
    drawTitle: true,
    drawSubtitle: false,
    drawPartNames: true,
    // one drawn bar per score bar, so highlighting and clicking line up
    autoGenerateMultipleRestMeasuresFromRestMeasures: false,
  });

  songs = await getJSON("scores/index.json");
  let group;
  for (const { id, title, group: songGroup } of songs) {
    // another group's songs (the junior choir's) come after a heading with its name
    if (songGroup !== group) {
      group = songGroup;
      const heading = document.createElement("li");
      heading.className = "group";
      heading.textContent = group;
      $("song-list").append(heading);
    }
    const link = document.createElement("a");
    link.href = `#${id}`;
    link.dataset.song = id;
    const stats = document.createElement("span");
    stats.className = "stats";
    link.append(title, stats);
    const item = document.createElement("li");
    item.append(link);
    $("song-list").append(item);
  }
  if (!store.get("voice") && !director) await askVoice();
  await route();
  showVersion();

  await Tone.loaded();
  makePianos();
  $("play").disabled = $("stop").disabled = false;
}

// "Last updated <date>" on the chooser, linking to the published commit.
// version.json is written at deploy time, so it's missing when run locally.
async function showVersion() {
  try {
    const { commit, date } = await getJSON("version.json");
    // in the viewer's own time zone
    const day = new Date(date).toLocaleDateString(lang, { day: "numeric", month: "long", year: "numeric" });
    const time = new Date(date).toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" });
    $("updated").href = `https://github.com/mattvenn/choir-app/commit/${commit}`;
    $("updated").textContent = t("updated", day, time);
    $("updated").hidden = false;
  } catch {}
}

// What each control does, beside a copy of its icons from the toolbar, then
// the rest of how it works.
const HELP_ICONS = {
  "home-button": "#home-button svg",
  play: "#play svg",
  stop: "#stop svg",
  repeats: "#repeats svg",
  tap: "#tap svg",
  tempo: null,  // a slider with no icon of its own
  speaker: "#speaker",
  others: ".others svg",
};
function showHelp() {
  $("help-controls").replaceChildren(...Object.entries(t("helpControls")).map(([id, text]) => {
    const icons = document.createElement("span");
    icons.className = "help-icons";
    if (HELP_ICONS[id]) {
      icons.append(...[...document.querySelectorAll(HELP_ICONS[id])].map(svg => svg.cloneNode(true)));
    } else {
      icons.textContent = "♩";
    }
    // shown as they are at their fullest: play, repeats on, every wave
    icons.querySelectorAll(".icon-pause, .icon-off").forEach(el => el.remove());
    icons.querySelectorAll(".off").forEach(el => el.classList.remove("off"));
    icons.querySelectorAll("[id]").forEach(el => el.removeAttribute("id"));
    const item = document.createElement("li");
    item.append(icons, text);
    return item;
  }));
  $("help-notes").replaceChildren(...[...t("helpNotes"), ...(director ? [t("directorNote")] : [])].map(text => {
    const p = document.createElement("p");
    p.textContent = text;
    return p;
  }));
  $("help").showModal();
  // opening puts the focus on Close, which scrolls a long help to the bottom
  $("help").scrollTop = 0;
}

// ---- pages ---------------------------------------------------------------

// The URL says which page is open: #<song id> for a song, nothing for the
// chooser. So a reload or a shared link opens the song, and Back goes home.
async function route() {
  const id = location.hash.slice(1);
  if (songs.some(s => s.id === id)) await showSong(id);
  else showHome();
}

function showHome() {
  if (song) stop();
  $("player").hidden = true;
  $("home").hidden = false;
  document.title = t("appName");
  const voice = store.get("voice");
  $("change-voice").textContent = director ? t("directorMode")
    : voice ? t("yourVoice", voice) : t("chooseVoice");
  $("change-voice").disabled = director;
  showPracticeStats();
  trackPage("/", t("appName"));
}

async function showSong(id) {
  // the score needs to be on screen to be laid out
  $("home").hidden = true;
  $("player").hidden = false;
  window.scrollTo(0, 0);
  if (id === songId) {
    document.title = `${song.title} · ${t("appName")}`;
    render();
  } else {
    await loadSong(id);
  }
  trackPage(`/${id}`, song.title);
}

// The repeats button works on a song with a version without them, and it and
// the part switch only while it isn't playing: each redraws the score, which
// would hold up the music.
function updateSwitches() {
  // songId is unset while the voice is being changed
  const hasShort = songs.find(s => s.id === songId)?.short;
  const playing = document.body.classList.contains("playing");
  $("repeats").disabled = !hasShort || playing || loading;
  $("repeats").title = t(!hasShort ? "noRepeatsTitle" : playing ? "pauseForRepeats" : "repeatsTitle");
  for (const button of $("part-switch").children) button.disabled = playing || loading;
}

// Load song `id`, written out or, if repeats are switched off and the song has
// one, the version with each bar once. Switching between those two keeps the
// tempo and how loud the others are.
async function loadSong(id) {
  loading = true;
  updateSwitches();
  try {
    await loadScore(id);
  } finally {
    loading = false;
    updateSwitches();
  }
}

async function loadScore(id) {
  const sameSong = id === songId;
  if (song) stop();
  const hasShort = songs.find(s => s.id === id).short;
  const noRepeats = $("repeats").getAttribute("aria-pressed") === "false";
  const file = hasShort && noRepeats ? `${id}-short` : id;
  song = await getJSON(`scores/${file}.json`);
  document.title = `${song.title} · ${t("appName")}`;
  history.replaceState(null, "", `#${id}`);
  await osmd.load(`scores/${file}.musicxml`);
  fixLyricHyphens();
  songId = id;
  updateSwitches();

  const parts = myParts();
  mine = parts.flags;
  showPartSwitch(parts.split);

  // as last left on this song, or the song's own tempo and just your part;
  // the tempo goes up to twice the song's own
  if (!sameSong) {
    $("tempo").max = Math.round(song.tempo * 2);
    setTempo(store.get(`tempo.${id}`) ?? song.tempo);
    setOthers(store.get(`others.${id}`) ?? 0);
  }

  currentBar = 0;
  loading = false;  // from here on there's a drawing to read
  render();
  schedule();
}

const saveTempo = () => store.set(`tempo.${songId}`, transport.bpm.value);

// ---- score drawing -------------------------------------------------------

function render() {
  hideReport();  // its note may move
  osmd.Sheet.Instruments.forEach((inst, i) => { inst.Visible = mine[i]; });
  osmd.render();
  indexNotes();
  showBar(currentBar);
  showPending();
  drawHeat();
}

// OSMD lays out each staff's lyrics and then its hyphens, a staff at a time,
// so the hyphen that carries a word onto the next line ("mor- | tis") is
// placed before that line's lyrics are, and can land up on the staff. Lay out
// all the lyrics first, then all the hyphens. The calculator class isn't
// exported, so this patches it from the first score's.
let lyricsFixed = false;
function fixLyricHyphens() {
  if (lyricsFixed) return;
  lyricsFixed = true;
  Object.getPrototypeOf(osmd.graphic.calculator).calculateLyricsPosition = function () {
    for (const inst of this.graphicalMusicSheet.ParentMusicSheet.Instruments) {
      if (inst.HasLyrics) inst.LyricVersesNumbers.sort();
    }
    const entries = new Map();
    for (const system of this.musicSystems) {
      for (const line of system.StaffLines) {
        entries.set(line, this.calculateSingleStaffLineLyricsPosition(
          line, line.ParentStaff.ParentInstrument.LyricVersesNumbers));
      }
    }
    for (const lineEntries of entries.values()) this.calculateLyricsExtendsAndDashes(lineEntries);
  };
}

// ---- note names on hover ---------------------------------------------------

let pitchOf = new Map();  // each drawn note's SVG group → its pitch
// for the director's reports, each drawn note's SVG group → its bar (as an
// index), part, place among the part's notes in the bar, pitch and syllable
let noteInfo = new Map();
function indexNotes() {
  pitchOf = new Map();
  noteInfo = new Map();
  osmd.GraphicSheet.MeasureList.forEach((bar, index) => {
    for (const measure of bar) {
      if (!measure?.ParentStaffLine) continue;  // a hidden part's
      let place = 0;
      for (const entry of measure.staffEntries) {
        for (const voice of entry.graphicalVoiceEntries) {
          for (const note of voice.notes) {
            const g = note.getSVGGElement();
            const { Pitch: pitch, ParentVoiceEntry: voiceEntry } = note.sourceNote;
            if (!g || !pitch) continue;
            pitchOf.set(g, pitch);
            const lyric = voiceEntry.LyricsEntries.values().map(l => l.Text).join(" / ");
            noteInfo.set(g, { index, part: measure.ParentStaff.ParentInstrument.Name,
                              place: ++place, pitch, lyric });
          }
        }
      }
    }
  });
}

const NOTE_NAMES = {
  en: ["C", "D", "E", "F", "G", "A", "B"],
  es: ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"],
}[lang];

// e.g. "Fa♯4": OSMD's pitch has the note as semitones above C, and octave 1
// for the one from middle C, which is octave 4 by the usual numbering
function noteName(pitch) {
  const letter = NOTE_NAMES[[0, 2, 4, 5, 7, 9, 11].indexOf(pitch.FundamentalNote)];
  const accidental = { "-2": "𝄫", "-1": "♭", 1: "♯", 2: "𝄪" }[pitch.AccidentalHalfTones] ?? "";
  return { letter, accidental, octave: pitch.Octave + 3 };
}

const noteText = pitch => {
  const { letter, accidental, octave } = noteName(pitch);
  return `${letter}${accidental}${octave}`;
};

// The label is only rewritten when the note changes: rewriting it on every
// mouse move made Chrome redo the ♯ (which comes from another font) and flicker.
let tipPitch = null;
function showNoteName(e) {
  const pitch = e.pointerType === "mouse" && pitchOf.get(e.target.closest(".vf-stavenote")) || null;
  $("note-tip").hidden = !pitch;
  if (pitch !== tipPitch) {
    tipPitch = pitch;
    if (pitch) {
      const { letter, accidental, octave } = noteName(pitch);
      const sign = document.createElement("span");
      sign.className = "accidental";
      sign.textContent = accidental;
      $("note-tip").replaceChildren(letter, ...(accidental ? [sign] : []), String(octave));
    }
  }
  if (!pitch) return;
  const r = $("score").getBoundingClientRect();
  Object.assign($("note-tip").style, { left: `${e.clientX - r.left}px`, top: `${e.clientY - r.top}px` });
}

// Bounding box in pixels (relative to #score) of bar `index` across all visible staves.
function barBox(index) {
  if (loading) return null;
  const unit = 10 * osmd.zoom;
  const svg = $("score").querySelector("svg");
  const offX = svg.getBoundingClientRect().left - $("score").getBoundingClientRect().left;
  const offY = svg.getBoundingClientRect().top - $("score").getBoundingClientRect().top;
  // hidden parts still have measures, parked at the origin
  const staves = (osmd.GraphicSheet.MeasureList[index] || [])
    .filter(m => m && m.ParentStaffLine && m.ParentStaff.ParentInstrument.Visible);
  if (!staves.length) return null;
  // Top to bottom, in staff spaces, it takes in all its line has drawn above and
  // below the staves: ledger lines, and lyrics, which low notes push further
  // down. Scrolling goes by it, so the words come into view with the bar.
  let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
  for (const m of staves) {
    const ps = m.PositionAndShape;
    const line = m.ParentStaffLine.PositionAndShape;
    const y = line.AbsolutePosition.y;
    left = Math.min(left, ps.AbsolutePosition.x);
    right = Math.max(right, ps.AbsolutePosition.x + ps.Size.width);
    top = Math.min(top, y - 1, y + line.BorderMarginTop);
    bottom = Math.max(bottom, y + 5, y + line.BorderMarginBottom);  // a staff is 4 spaces tall
  }
  const margin = 0.5;
  return {
    left: offX + left * unit,
    top: offY + (top - margin) * unit,
    width: (right - left) * unit,
    height: (bottom - top + 2 * margin) * unit,
  };
}

function showBar(index) {
  currentBar = index;
  const box = barBox(index);
  const hl = $("highlight");
  hl.hidden = !box;
  if (!box) return;
  const moved = hl.style.top !== `${box.top}px`;
  Object.assign(hl.style, {
    left: `${box.left}px`, top: `${box.top}px`,
    width: `${box.width}px`, height: `${box.height}px`,
  });
  if (moved && transport.state === "started") keepInView(box);
}

// Scroll so the bar sits below the sticky header, only if it's out of view:
// out of what's on screen, which on a phone zoomed out or under the browser's
// toolbars is less than the window.
function keepInView(box) {
  const header = document.querySelector("header").offsetHeight;
  const view = window.visualViewport;
  const bottom = view ? Math.min(window.innerHeight, view.offsetTop + view.height) : window.innerHeight;
  const top = $("score").getBoundingClientRect().top + box.top;
  if (top >= header && top + box.height <= bottom) return;
  window.scrollBy({ top: top - header - 16, behavior: "smooth" });
}

function barAt(x, y) {
  for (let i = 0; i < song.measures.length; i++) {
    const b = barBox(i);
    if (b && x >= b.left && x < b.left + b.width && y >= b.top && y < b.top + b.height) return i;
  }
  return -1;
}

// ---- the director's reports ----------------------------------------------

// The drawn note nearest a tap at x, y (relative to #score), if the tap is on
// or close by one: a note head is small to hit on a phone.
function noteNear(x, y) {
  const r = $("score").getBoundingClientRect();
  const reach = 12 * osmd.zoom;
  let best = null, bestDistance = reach;
  for (const g of noteInfo.keys()) {
    const b = g.getBoundingClientRect();
    const dx = Math.max(b.left - r.left - x, 0, x - (b.right - r.left));
    const dy = Math.max(b.top - r.top - y, 0, y - (b.bottom - r.top));
    const distance = Math.hypot(dx, dy);
    if (distance <= bestDistance) [best, bestDistance] = [g, distance];
  }
  return best;
}

// Under the tapped note: which note it is, links that open WhatsApp or an
// email with that and a link to the song filled in, for the director to say
// what's wrong and choose who to send it to, and a button to play from its bar.
let reportBar = 0;
function showReport(g) {
  const { index, part, place, pitch, lyric } = noteInfo.get(g);
  const what = t("reportNote", song.title, printedBar(index), part, place, noteText(pitch), lyric);
  const link = `${location.origin}${location.pathname}#${songId}`;
  $("report-what").textContent = what;
  const message = encodeURIComponent(`${what}\n${link}\n\n`);
  $("report-send").href = `https://wa.me/?text=${message}`;
  const subject = encodeURIComponent(t("reportSubject", song.title, printedBar(index)));
  $("report-email").href = `mailto:?subject=${subject}&body=${message}`;
  reportBar = index;
  const s = $("score").getBoundingClientRect();
  const b = g.getBoundingClientRect();
  Object.assign($("report").style, {
    left: `${Math.min(Math.max(b.left + b.width / 2 - s.left, 140), s.width - 140)}px`,
    top: `${b.bottom - s.top + 8}px`,
  });
  $("report").hidden = false;
}
const hideReport = () => { $("report").hidden = true; };

// ---- practice record -----------------------------------------------------

// Kept per song in this browser: for each printed bar, how many times you went
// back over it and how many times it was played to its end, and the time spent
// playing. The counts halve every two weeks, so they follow how you play now.
// A bar's hardness is how often you go back over it for each time it's played:
// a bar fades as you play on past it, while a song left alone keeps its map.
const HALF_LIFE = 14 * 24 * 3600e3;
const DAY = 24 * 3600e3;
const HARD = 0.5;  // from this hardness a bar counts as hard on the song list

const printedBar = i => song.printedBars?.[i] ?? i + 1;
const barRange = (from, to) => Array.from({ length: to - from + 1 }, (_, k) => from + k);
// the +1 keeps a single slip from marking a bar as hard
const hardness = ([back, played]) => back / (played + 1);
const hardBars = practice => Object.values(practice.bars).filter(c => hardness(c) >= HARD).length;

// A song's record, with its counts aged to now.
function practiceOf(id) {
  const practice = store.get(`practice.${id}`) ?? { bars: {}, seconds: 0, at: Date.now(), history: [] };
  const now = Date.now();
  const fade = 0.5 ** ((now - practice.at) / HALF_LIFE);
  for (const counts of Object.values(practice.bars)) {
    counts[0] *= fade;
    counts[1] *= fade;
  }
  practice.at = now;
  return practice;
}

// Adds practice on the open song: bars (as indexes of the version played) gone
// back over and played to the end, and seconds played. The history is the
// count of hard bars at the end of each day practised, to show progress.
function recordPractice({ back = [], played = [], seconds = 0 }) {
  if (director) return;  // checking a score isn't practising it
  const practice = practiceOf(songId);
  const add = (i, k) => { (practice.bars[printedBar(i)] ??= [0, 0])[k]++; };
  back.forEach(i => add(i, 0));
  played.forEach(i => add(i, 1));
  practice.seconds += seconds;
  practice.last = Date.now();
  const day = Math.floor(practice.last / DAY);
  const hard = hardBars(practice);
  if (practice.history.at(-1)?.[0] === day) practice.history.at(-1)[1] = hard;
  else practice.history = [...practice.history, [day, hard]].slice(-60);
  for (const counts of Object.values(practice.bars)) counts.forEach((n, k) => { counts[k] = Math.round(n * 1000) / 1000; });
  store.set(`practice.${songId}`, practice);
}

// Bar `i` has played to its end. If a bar before it was clicked while playing,
// that's going back over the bars from there to here.
function barPlayed(i) {
  const back = pendingBar !== null && pendingBar <= i ? barRange(pendingBar, i) : [];
  const seconds = (barTicks[i + 1] - barTicks[i]) / transport.PPQ * 60 / transport.bpm.value;
  recordPractice({ back, played: [i], seconds });
}

// Tints each bar by how hard it is, under the highlight.
function drawHeat() {
  if (director) return;  // no practice record
  const { bars } = practiceOf(songId);
  const marks = [];
  song.measures.forEach((_, i) => {
    const level = Math.min(hardness(bars[printedBar(i)] ?? [0, 0]), 1);
    const box = level >= 0.15 && barBox(i);
    if (!box) return;
    const mark = document.createElement("div");
    Object.assign(mark.style, {
      left: `${box.left}px`, top: `${box.top}px`,
      width: `${box.width}px`, height: `${box.height}px`,
      opacity: level,
    });
    marks.push(mark);
  });
  $("heat").replaceChildren(...marks);
}

// Under each song on the list: time practised, when, and how many hard bars,
// with how many there were a week before if that's changed.
function showPracticeStats() {
  const relative = new Intl.RelativeTimeFormat(lang, { numeric: "auto" });
  for (const { id } of songs) {
    const practice = practiceOf(id);
    const stats = [];
    if (practice.last) {
      const today = Math.floor(Date.now() / DAY);
      stats.push(t("minutes", Math.max(1, Math.round(practice.seconds / 60))),
                 relative.format(Math.floor(practice.last / DAY) - today, "day"));
      const hard = hardBars(practice);
      const weekAgo = practice.history.findLast(([day]) => day <= today - 7)?.[1];
      if (hard || weekAgo) stats.push(t("hardBars", hard, weekAgo === hard ? undefined : weekAgo));
    }
    const line = document.querySelector(`#song-list [data-song="${id}"] .stats`);
    line.textContent = stats.join(" · ");
    line.hidden = !stats.length;
  }
}

// ---- playback ------------------------------------------------------------

// Tone turns a tick position into seconds at the tempo of the moment and back,
// and files the event on the whole tick below, so where an event lands can be a
// tick out depending on the tempo it was scheduled at. Each bar line's tick is
// noted when the song is scheduled, so jumps go to where its events really are.
let barTicks = [];  // per bar, then the end of the song
const eventTick = quarters => Math.floor(transport.toTicks(ticks(quarters)));

// Every note of every part is scheduled once, yours on one piano and the rest on the other.
function schedule() {
  transport.cancel();
  barTicks = [...song.measures, song.length].map(eventTick);
  song.parts.forEach((part, i) => {
    for (const [midi, start, dur] of part.notes) {
      const pitch = Tone.Frequency(midi, "midi").toNote();
      transport.schedule(time => {
        const seconds = dur * 60 / transport.bpm.value;
        (mine[i] ? myPiano : othersPiano).triggerAttackRelease(pitch, seconds, time, 0.7);
      }, ticks(start));
    }
  });
  song.measures.forEach((start, i) => {
    transport.schedule(time => drawWhenHeard(() => showBar(i), time), ticks(start));
    // two ticks early, so it's before a jump at the bar line; not through Draw,
    // which drops what it can't draw in time, as in a tab in the background
    transport.schedule(() => barPlayed(i), `${barTicks[i + 1] - 2}i`);
    // songs that change metre or tempo give each bar's beat
    const [length, count] = song.bars?.[i] ?? [song.beat, song.beatsPerBar];
    for (let beat = 0; beat < count; beat++) {
      transport.schedule(time => {
        if (Number($("click-volume").value)) click.triggerAttackRelease(beat ? "G5" : "C6", 0.03, time);
      }, ticks(start + beat * length));
    }
  });
  // one extra beat so the last note can ring
  transport.schedule(time => drawWhenHeard(stop, time), ticks(song.length + 1));
}

// the play button shows a pause icon while playing (see style.css)
function setPlayLabel() {
  const label = t(document.body.classList.contains("playing") ? "pause" : "play");
  $("play").title = label;
  $("play").setAttribute("aria-label", label);
}

async function play() {
  await Tone.start();  // browsers only allow audio after a click
  // counted from a stop, not on every resume after a pause
  if (transport.state === "stopped") track("play", { song: songId });
  transport.start();
  document.body.classList.add("playing");  // the play button shows pause
  setPlayLabel();
  updateSwitches();
  // showBar only scrolls when the highlight moves, and after a stop it's already
  // waiting on bar 1, maybe far off screen
  const box = barBox(currentBar);
  if (box) keepInView(box);
}

function pause() {
  cancelJump();
  cancelDraws();
  transport.pause();
  releaseAll();
  document.body.classList.remove("playing");
  setPlayLabel();
  updateSwitches();
  drawHeat();
}

function stop() {
  cancelJump();
  cancelDraws();
  transport.stop();
  releaseAll();
  document.body.classList.remove("playing");
  setPlayLabel();
  updateSwitches();
  showBar(0);
  drawHeat();
}

// Clicking a bar: stopped or paused, play from it now; playing, go to it when
// the bar playing ends, so the beat carries on.
function goToBar(index) {
  if (transport.state === "started") queueJump(index);
  else seek(index);
}

function seek(index) {
  // paused, clicking the bar you stopped in or one before it is going back over them
  if (transport.state === "paused" && index <= currentBar) {
    recordPractice({ back: barRange(index, currentBar) });
  }
  cancelJump();
  cancelDraws();
  releaseAll();
  transport.ticks = barTicks[index];
  showBar(index);
  if (transport.state !== "started") play();
}

// The transport's loop makes the jump on the exact tick: at the next bar line
// it goes back (or forward) to the clicked bar, then the loop is switched off.
// Until then the clicked bar is marked as waiting.
let pendingBar = null;
function queueJump(index) {
  // transport.ticks is already a little ahead of what's heard
  const barLine = barTicks.find(t => t > transport.ticks);
  pendingBar = index;
  // The loop points go through the same rounding, so each is set a tick early:
  // the loop starts just before the clicked bar's first notes, and goes back
  // just before the next bar's would sound. A tick is a few milliseconds.
  transport.setLoopPoints(Tone.Ticks(Math.max(barTicks[index] - 1, 0)), Tone.Ticks(barLine - 1));
  transport.loop = true;
  showPending();
}

transport.on("loop", time => {
  transport.loop = false;
  // unless another bar has been clicked in the moment before it's heard
  const done = pendingBar;
  drawWhenHeard(() => {
    if (pendingBar !== done) return;
    pendingBar = null;
    showPending();
  }, time);
});

function cancelJump() {
  transport.loop = false;
  pendingBar = null;
  showPending();
}

function showPending() {
  const box = pendingBar === null ? null : barBox(pendingBar);
  $("pending").hidden = !box;
  if (box) {
    Object.assign($("pending").style, {
      left: `${box.left}px`, top: `${box.top}px`,
      width: `${box.width}px`, height: `${box.height}px`,
    });
  }
}

// ---- tempo ---------------------------------------------------------------

// Tempo in quarter notes per minute, as on the slider, kept within its range.
const clampTempo = bpm => Math.round(Math.min(Math.max(bpm, $("tempo").min), $("tempo").max));

// Sets the tempo, and shows how it compares with the score's: a tick on the
// slider where the score's is, and the number becomes a button back to it.
function setTempo(bpm) {
  bpm = clampTempo(bpm);
  transport.bpm.value = bpm;
  $("tempo").value = bpm;
  const own = clampTempo(song.tempo);
  const { min, max } = $("tempo");
  $("tempo-tick").style.setProperty("--at", (own - min) / (max - min));
  const button = $("tempo-value");
  button.textContent = bpm;
  button.disabled = bpm === own;
  button.title = button.disabled ? "" : t("resetTempo", own);
  if (button.disabled) button.removeAttribute("aria-label");
  else button.setAttribute("aria-label", `${bpm}. ${t("resetTempo", own)}`);
}

function resetTempo() {
  setTempo(song.tempo);
  saveTempo();
}

// Tap the button along with the beat (the metronome's click) to set the tempo:
// from the second tap on, it follows the average of the last few gaps. A pause
// of 2 seconds starts a new count.
let taps = [];
function tap() {
  const now = performance.now() / 1000;
  if (taps.length && now - taps.at(-1) > 2) taps = [];
  taps = [...taps, now].slice(-5);
  if (taps.length < 2) return;
  const gap = (taps.at(-1) - taps[0]) / (taps.length - 1);
  // in cut time a beat is a half note, so the quarter-note tempo is twice the taps
  setTempo(60 / gap * song.beat);
  saveTempo();
}

// ---- wiring --------------------------------------------------------------

const togglePlay = () => {
  if (loading) return;
  transport.state === "started" ? pause() : play();
};
$("play").addEventListener("click", togglePlay);
// Space is play/pause everywhere, instead of scrolling or pressing the focused control
document.addEventListener("keydown", e => {
  if (e.code !== "Space" || e.repeat || $("play").disabled || $("player").hidden) return;
  e.preventDefault();
  togglePlay();
});
// buttons and checkboxes act on Space's keyup, so swallow that too
document.addEventListener("keyup", e => { if (e.code === "Space") e.preventDefault(); });
// back to the start, and up to the top of the score to see it
$("stop").addEventListener("click", () => {
  stop();
  window.scrollTo({ top: 0, behavior: "smooth" });
});
$("home-button").addEventListener("click", () => {
  history.pushState(null, "", location.pathname + location.search);
  showHome();
});
// song links, and Back/Forward between a song and the chooser
window.addEventListener("popstate", () => { route().catch(showError); });
// Redraw the score with `change`, keeping the highlighted bar where it was on
// screen though the score is laid out differently: the page keeps its height
// while it's redrawn, the highlight goes straight to the bar instead of
// sliding, then the page scrolls.
async function keepingPlace(change) {
  const anchor = $("highlight").getBoundingClientRect().top;
  const wrap = $("score-wrap");
  wrap.style.minHeight = `${wrap.offsetHeight}px`;
  $("highlight").style.transition = "none";
  try {
    await change();
    wrap.style.minHeight = "";
    window.scrollBy(0, $("highlight").getBoundingClientRect().top - anchor);
  } catch (err) {
    showError(err);
  } finally {
    wrap.style.minHeight = "";
    $("highlight").getBoundingClientRect();  // so the jump is drawn before sliding comes back
    $("highlight").style.transition = "";
  }
}

// Switching version stays on the same printed bar (its first time through,
// going to the written-out one), so play carries on from there.
$("repeats").addEventListener("click", e => {
  const button = e.currentTarget;
  const repeats = button.getAttribute("aria-pressed") === "false";
  button.setAttribute("aria-pressed", repeats);
  store.set("repeats", repeats);
  const bar = printedBar(currentBar);
  keepingPlace(async () => {
    await loadSong(songId);
    // or, from a first ending, which the version without repeats leaves out, the bar after
    const index = Math.max(song.measures.findIndex((_, i) => printedBar(i) >= bar), 0);
    transport.ticks = barTicks[index];
    showBar(index);
  });
});
// repeats on or off is remembered across songs; to start with, on, except for
// the director, who checks each bar once, against the score's bar numbers
$("repeats").setAttribute("aria-pressed", store.get("repeats") ?? !director);
// the metronome volume is remembered across songs, the tempo for each song
if (store.get("clickVolume") !== null) $("click-volume").value = store.get("clickVolume");
setClickVolume(Number($("click-volume").value));
$("click-volume").addEventListener("input", e => {
  setClickVolume(Number(e.target.value));
  store.set("clickVolume", Number(e.target.value));
});
$("others").addEventListener("input", e => {
  setOthers(Number(e.target.value));
  store.set(`others.${songId}`, Number(e.target.value));
});
$("help-button").addEventListener("click", showHelp);
$("change-voice").addEventListener("click", async () => {
  await askVoice();
  songId = null;  // so the song open before is loaded again with the new voice
  showHome();
});
$("tempo").addEventListener("input", e => {
  setTempo(Number(e.target.value));
  saveTempo();
});
$("tap").addEventListener("click", tap);
$("tempo-value").addEventListener("click", resetTempo);
$("score").addEventListener("click", e => {
  if (loading) return;
  const r = $("score").getBoundingClientRect();
  const [x, y] = [e.clientX - r.left, e.clientY - r.top];
  // the director's tap on a note opens its report; elsewhere it plays the bar
  const note = director && noteNear(x, y);
  if (note) return showReport(note);
  hideReport();
  if ($("play").disabled) return;
  const bar = barAt(x, y);
  if (bar >= 0) goToBar(bar);
});
for (const [id, by] of [["report-send", "whatsapp"], ["report-email", "email"]]) {
  $(id).addEventListener("click", () => {
    track("report", { song: songId, by });
    hideReport();
  });
}
$("report-play").addEventListener("click", () => {
  hideReport();
  if (!$("play").disabled) goToBar(reportBar);
});
document.addEventListener("keydown", e => { if (e.key === "Escape") hideReport(); });
$("score").addEventListener("pointermove", showNoteName);
$("score").addEventListener("pointerleave", () => {
  $("note-tip").hidden = true;
  tipPitch = null;
});
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  // a score still loading is drawn at the new size once it's in
  resizeTimer = setTimeout(() => { if (song && !loading && !$("player").hidden) render(); }, 200);
});

function showError(err) {
  $("status").textContent = t("error", err.message);
  console.error(err);
}

applyLanguage();
init().catch(showError);
