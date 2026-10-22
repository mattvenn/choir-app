// Score player: OpenSheetMusicDisplay draws the MusicXML, Tone.js plays the
// note events from the matching JSON on a sampled grand piano.
const PIANO_URL = "https://tonejs.github.io/audio/salamander/";
// Salamander has a sample every minor third; the sampler repitches between them
const PIANO_SAMPLES = Object.fromEntries(
  ["A0", "C1", "Ds1", "Fs1", "A1", "C2", "Ds2", "Fs2", "A2", "C3", "Ds3", "Fs3", "A3",
   "C4", "Ds4", "Fs4", "A4", "C5", "Ds5", "Fs5", "A5", "C6", "Ds6", "Fs6", "A6",
   "C7", "Ds7", "Fs7", "A7", "C8"].map(n => [n.replace("s", "#"), `${n}.mp3`]));

// Interface text, in English if the browser is set to English and Spanish
// otherwise. Part names come from the score, so aren't translated.
const STRINGS = {
  en: {
    appName: "Choir Practice",
    songs: "Songs",
    play: "Play",
    pause: "Pause",
    stop: "Stop",
    solo: "Solo",
    soloTitle: "Hear only the parts shown (S)",
    tap: "Tap",
    tapTitle: "Tap along with the beat to set the tempo",
    resetTempo: bpm => `Back to the score's tempo (${bpm})`,
    noRepeats: "No repeats",
    clickVolume: "Metronome volume",
    loading: "Loading piano…",
    show: "Show",
    hear: "Hear",
    showPart: part => `Show ${part}`,
    hearPart: part => `Hear ${part}`,
    ears: "Ears",
    earsTitle: "Move the parts shown to one ear and the others to the other. In the middle, both ears hear everything.",
    hint: "Click a bar to play from there (while playing, it goes there at the next bar line). Space: play/pause. S: solo the parts shown. Ears: move your part to one ear and the others to the other. The bars you go back to most are shaded orange.",
    error: message => `Error: ${message}`,
    updated: (date, time) => `Last updated ${date} at ${time}`,
    minutes: n => `${n} min`,
    hardBars: (n, weekAgo) => `${n} hard bar${n === 1 ? "" : "s"}` +
      (weekAgo === undefined ? "" : ` (${weekAgo} a week ago)`),
  },
  es: {
    appName: "Ensayo de coro",
    songs: "Canciones",
    play: "Reproducir",
    pause: "Pausa",
    stop: "Parar",
    solo: "Solo",
    soloTitle: "Oír solo las voces visibles (S)",
    tap: "Marcar",
    tapTitle: "Toca al ritmo del pulso para fijar el tempo",
    resetTempo: bpm => `Volver al tempo de la partitura (${bpm})`,
    noRepeats: "Sin repeticiones",
    clickVolume: "Volumen del metrónomo",
    loading: "Cargando piano…",
    show: "Ver",
    hear: "Oír",
    showPart: part => `Ver ${part}`,
    hearPart: part => `Oír ${part}`,
    ears: "Oídos",
    earsTitle: "Lleva las voces visibles a un oído y las demás al otro. En el centro, se oye todo en los dos.",
    hint: "Pulsa un compás para reproducir desde ahí (si ya suena, salta al acabar el compás). Espacio: reproducir/pausa. S: solo de las voces visibles. Oídos: lleva tu voz a un oído y las demás al otro. Los compases a los que más vuelves se marcan en naranja.",
    error: message => `Error: ${message}`,
    updated: (date, time) => `Actualizado el ${date} a las ${time}`,
    minutes: n => `${n} min`,
    hardBars: (n, weekAgo) => `${n} ${n === 1 ? "compás difícil" : "compases difíciles"}` +
      (weekAgo === undefined ? "" : ` (${weekAgo} hace una semana)`),
  },
};
const lang = navigator.language.toLowerCase().startsWith("en") ? "en" : "es";
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
Tone.setContext(new Tone.Context({ latencyHint: "playback" }));
const transport = Tone.getTransport();
// Two pianos on the same samples, each through its own panner: one plays the
// parts shown, the other the rest, so each can go to its own ear. Panned to
// the middle, the stereo samples pass through as they are.
// A sampler only shares a buffer that has already loaded, so the pianos are
// made once the samples are in (see init).
const samples = new Tone.ToneAudioBuffers({ urls: PIANO_SAMPLES, baseUrl: PIANO_URL });
const myPan = new Tone.Panner(0).toDestination();
const othersPan = new Tone.Panner(0).toDestination();
let myPiano, othersPiano;
function makePianos() {
  const urls = Object.fromEntries(Object.keys(PIANO_SAMPLES).map(note => [note, samples.get(note)]));
  myPiano = new Tone.Sampler({ urls, release: 1 }).connect(myPan);
  othersPiano = new Tone.Sampler({ urls, release: 1 }).connect(othersPan);
}
const releaseAll = () => { myPiano?.releaseAll(); othersPiano?.releaseAll(); };
// the slider runs -100 (your part in the left ear) to 100 (in the right)
const setEars = percent => {
  myPan.pan.value = percent / 100;
  othersPan.pan.value = -percent / 100;
};
const click = new Tone.Synth({
  oscillator: { type: "square" },
  envelope: { attack: 0.001, decay: 0.04, sustain: 0, release: 0.01 },
}).toDestination();
// the slider runs 0-100; 100 is as loud as the first version, which was too loud
const CLICK_MAX_GAIN = 0.25;
const setClickVolume = percent => {
  click.volume.value = Tone.gainToDb(percent / 100 * CLICK_MAX_GAIN);
};

let songs;         // scores/index.json
let song;          // scores/<id>.json
let songId;        // which song is loaded (`song` may be its version without repeats)
let osmd;
let shown = [];   // per part
let heard = [];
let beforeSolo = null;  // what was heard before solo was switched on
let currentBar = 0;

// note times are in quarters; scheduling in transport ticks means a tempo
// change takes effect immediately, even mid-playback
const ticks = quarters => `${Math.round(quarters * transport.PPQ)}i`;

const getJSON = async url => (await fetch(url)).json();

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
  for (const { id, title } of songs) {
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
  await route();
  showVersion();

  await Tone.loaded();
  makePianos();
  $("status").textContent = "";
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

// Load song `id`, written out or, if "no repeats" is ticked and the song has
// one, the version with each bar once. Switching between those two keeps the
// parts and tempo chosen.
async function loadSong(id) {
  const sameSong = id === songId;
  if (song) stop();
  const hasShort = songs.find(s => s.id === id).short;
  $("short-option").hidden = !hasShort;
  const file = hasShort && $("short").checked ? `${id}-short` : id;
  song = await getJSON(`scores/${file}.json`);
  document.title = `${song.title} · ${t("appName")}`;
  history.replaceState(null, "", `#${id}`);
  await osmd.load(`scores/${file}.musicxml`);
  fixLyricHyphens();
  songId = id;

  // one column per part, a row each for Show and Hear: as last left on this
  // song, or to start with just your part
  for (const row of ["part-names", "show-row", "hear-row"]) {
    $(row).replaceChildren($(row).firstElementChild);
  }
  if (!sameSong) {
    const saved = store.get(`parts.${id}`);
    const fits = flags => Array.isArray(flags) && flags.length === song.parts.length;
    if (saved && fits(saved.shown) && fits(saved.heard) && saved.shown.some(Boolean)) {
      ({ shown, heard } = saved);
    } else {
      shown = song.parts.map(p => p.name === song.myPart);
      heard = [...shown];
    }
  }
  endSolo();
  song.parts.forEach((part, i) => {
    const name = document.createElement("th");
    name.scope = "col";
    name.textContent = part.name;
    $("part-names").append(name);
    $("show-row").append(checkboxCell(shown, i, t("showPart", part.name), render));
    $("hear-row").append(checkboxCell(heard, i, t("hearPart", part.name), endSolo));
  });
  $("ears-cell").colSpan = song.parts.length;

  // as last left on this song, or the song's own
  if (!sameSong) setTempo(store.get(`tempo.${id}`) ?? song.tempo);

  currentBar = 0;
  render();
  schedule();
}

// A checkbox bound to flags[i]; onChange runs after the flag is updated.
function checkboxCell(flags, i, label, onChange) {
  const cell = document.createElement("td");
  const box = document.createElement("input");
  box.type = "checkbox";
  box.checked = flags[i];
  box.setAttribute("aria-label", label);
  box.addEventListener("change", () => {
    flags[i] = box.checked;
    // OSMD can't draw a score with no parts
    if (flags === shown && !shown.some(Boolean)) {
      flags[i] = box.checked = true;
      return;
    }
    saveParts();
    onChange();
  });
  cell.append(box);
  return cell;
}

const saveTempo = () => store.set(`tempo.${songId}`, transport.bpm.value);
const saveParts = () => store.set(`parts.${songId}`, { shown, heard });

// ---- score drawing -------------------------------------------------------

function render() {
  osmd.Sheet.Instruments.forEach((inst, i) => { inst.Visible = shown[i]; });
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
function indexNotes() {
  pitchOf = new Map();
  for (const bar of osmd.GraphicSheet.MeasureList) {
    for (const measure of bar) {
      for (const entry of measure?.staffEntries ?? []) {
        for (const voice of entry.graphicalVoiceEntries) {
          for (const note of voice.notes) {
            const g = note.getSVGGElement();
            if (g && note.sourceNote.Pitch) pitchOf.set(g, note.sourceNote.Pitch);
          }
        }
      }
    }
  }
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
  const unit = 10 * osmd.zoom;
  const svg = $("score").querySelector("svg");
  const offX = svg.getBoundingClientRect().left - $("score").getBoundingClientRect().left;
  const offY = svg.getBoundingClientRect().top - $("score").getBoundingClientRect().top;
  // hidden parts still have measures, parked at the origin
  const staves = (osmd.GraphicSheet.MeasureList[index] || [])
    .filter(m => m && m.ParentStaffLine && m.ParentStaff.ParentInstrument.Visible);
  if (!staves.length) return null;
  let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
  for (const m of staves) {
    const ps = m.PositionAndShape;
    left = Math.min(left, ps.AbsolutePosition.x);
    right = Math.max(right, ps.AbsolutePosition.x + ps.Size.width);
    top = Math.min(top, ps.AbsolutePosition.y);
    bottom = Math.max(bottom, ps.AbsolutePosition.y + 4);  // a staff is 4 spaces tall
  }
  // in staff spaces: ledger lines above, ledger lines and lyrics below
  const above = 2, below = 5;
  return {
    left: offX + left * unit,
    top: offY + (top - above) * unit,
    width: (right - left) * unit,
    height: (bottom - top + above + below) * unit,
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

// Scroll so the bar sits below the sticky header, only if it's out of view.
function keepInView(box) {
  const header = document.querySelector("header").offsetHeight;
  const top = $("score").getBoundingClientRect().top + box.top;
  if (top >= header && top + box.height <= window.innerHeight) return;
  window.scrollBy({ top: top - header - 16, behavior: "smooth" });
}

function barAt(x, y) {
  for (let i = 0; i < song.measures.length; i++) {
    const b = barBox(i);
    if (b && x >= b.left && x < b.left + b.width && y >= b.top && y < b.top + b.height) return i;
  }
  return -1;
}

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

// Every note of every part is scheduled once; muted parts are skipped as they come up.
function schedule() {
  transport.cancel();
  barTicks = [...song.measures, song.length].map(eventTick);
  song.parts.forEach((part, i) => {
    for (const [midi, start, dur] of part.notes) {
      const pitch = Tone.Frequency(midi, "midi").toNote();
      transport.schedule(time => {
        if (!heard[i]) return;
        const seconds = dur * 60 / transport.bpm.value;
        (shown[i] ? myPiano : othersPiano).triggerAttackRelease(pitch, seconds, time, 0.7);
      }, ticks(start));
    }
  });
  song.measures.forEach((start, i) => {
    transport.schedule(time => Tone.getDraw().schedule(() => showBar(i), time), ticks(start));
    // two ticks early, so it's before a jump at the bar line; not through Draw,
    // which drops what it can't draw in time, as in a tab in the background
    transport.schedule(() => barPlayed(i), `${barTicks[i + 1] - 2}i`);
    for (let beat = 0; beat < song.beatsPerBar; beat++) {
      transport.schedule(time => {
        if (Number($("click-volume").value)) click.triggerAttackRelease(beat ? "G5" : "C6", 0.03, time);
      }, ticks(start + beat * song.beat));
    }
  });
  // one extra beat so the last note can ring
  transport.schedule(time => Tone.getDraw().schedule(stop, time), ticks(song.length + 1));
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
  document.body.classList.add("playing");  // collapses the controls
  setPlayLabel();
  // showBar only scrolls when the highlight moves, and after a stop it's already
  // waiting on bar 1, maybe far off screen
  const box = barBox(currentBar);
  if (box) keepInView(box);
}

function pause() {
  cancelJump();
  transport.pause();
  releaseAll();
  document.body.classList.remove("playing");
  setPlayLabel();
  drawHeat();
}

function stop() {
  cancelJump();
  transport.stop();
  releaseAll();
  document.body.classList.remove("playing");
  setPlayLabel();
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
  Tone.getDraw().schedule(() => {
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

// ---- solo ----------------------------------------------------------------

// Hear only the parts that are shown; again to go back to what was heard before.
function toggleSolo() {
  if (beforeSolo) {
    heard.splice(0, heard.length, ...beforeSolo);
    endSolo();
  } else {
    beforeSolo = [...heard];
    heard.splice(0, heard.length, ...shown);
    $("solo").setAttribute("aria-pressed", "true");
  }
  $("hear-row").querySelectorAll("input").forEach((box, i) => { box.checked = heard[i]; });
  saveParts();
}

// Ticking a Hear box by hand also ends solo, keeping what's ticked.
function endSolo() {
  beforeSolo = null;
  $("solo").setAttribute("aria-pressed", "false");
}

// ---- wiring --------------------------------------------------------------

const togglePlay = () => transport.state === "started" ? pause() : play();
$("play").addEventListener("click", togglePlay);
// Space is play/pause everywhere, instead of scrolling or pressing the focused control
document.addEventListener("keydown", e => {
  if (e.code !== "Space" || e.repeat || $("play").disabled || $("player").hidden) return;
  e.preventDefault();
  togglePlay();
});
document.addEventListener("keydown", e => {
  if (e.key.toLowerCase() !== "s" || e.repeat || e.metaKey || e.ctrlKey || e.altKey) return;
  if ($("player").hidden) return;
  e.preventDefault();
  toggleSolo();
});
$("solo").addEventListener("click", toggleSolo);
// buttons and checkboxes act on Space's keyup, so swallow that too
document.addEventListener("keyup", e => { if (e.code === "Space") e.preventDefault(); });
$("stop").addEventListener("click", stop);
$("home-button").addEventListener("click", () => {
  history.pushState(null, "", location.pathname + location.search);
  showHome();
});
// song links, and Back/Forward between a song and the chooser
window.addEventListener("popstate", () => { route().catch(showError); });
$("short").addEventListener("change", e => {
  e.target.blur();  // so Space goes back to play/pause
  loadSong(songId).catch(showError);
});
// the metronome volume is remembered across songs, the tempo for each song
if (store.get("clickVolume") !== null) $("click-volume").value = store.get("clickVolume");
setClickVolume(Number($("click-volume").value));
$("click-volume").addEventListener("input", e => {
  setClickVolume(Number(e.target.value));
  store.set("clickVolume", Number(e.target.value));
});
// which ear your part goes to is remembered across songs too
if (store.get("ears") !== null) $("ears").value = store.get("ears");
setEars(Number($("ears").value));
$("ears").addEventListener("input", e => {
  setEars(Number(e.target.value));
  store.set("ears", Number(e.target.value));
});
$("tempo").addEventListener("input", e => {
  setTempo(Number(e.target.value));
  saveTempo();
});
$("tap").addEventListener("click", tap);
$("tempo-value").addEventListener("click", resetTempo);
$("score").addEventListener("click", e => {
  if ($("play").disabled) return;
  const r = $("score").getBoundingClientRect();
  const bar = barAt(e.clientX - r.left, e.clientY - r.top);
  if (bar >= 0) goToBar(bar);
});
$("score").addEventListener("pointermove", showNoteName);
$("score").addEventListener("pointerleave", () => {
  $("note-tip").hidden = true;
  tipPitch = null;
});
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => { if (song && !$("player").hidden) render(); }, 200);
});

function showError(err) {
  $("status").textContent = t("error", err.message);
  console.error(err);
}

applyLanguage();
init().catch(showError);
