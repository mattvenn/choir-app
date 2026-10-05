// Score player: OpenSheetMusicDisplay draws the MusicXML, Tone.js plays the
// note events from the matching JSON on a sampled grand piano.
const PIANO_URL = "https://tonejs.github.io/audio/salamander/";
// Salamander has a sample every minor third; the sampler repitches between them
const PIANO_SAMPLES = Object.fromEntries(
  ["A0", "C1", "Ds1", "Fs1", "A1", "C2", "Ds2", "Fs2", "A2", "C3", "Ds3", "Fs3", "A3",
   "C4", "Ds4", "Fs4", "A4", "C5", "Ds5", "Fs5", "A5", "C6", "Ds6", "Fs6", "A6",
   "C7", "Ds7", "Fs7", "A7", "C8"].map(n => [n.replace("s", "#"), `${n}.mp3`]));

const $ = id => document.getElementById(id);
const transport = Tone.getTransport();
const piano = new Tone.Sampler({ urls: PIANO_SAMPLES, baseUrl: PIANO_URL, release: 1 })
  .toDestination();
const click = new Tone.Synth({
  oscillator: { type: "square" },
  envelope: { attack: 0.001, decay: 0.04, sustain: 0, release: 0.01 },
  volume: -12,
}).toDestination();

let song;          // scores/<id>.json
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

  const songs = await getJSON("scores/index.json");
  for (const { id, title } of songs) $("song").add(new Option(title, id));
  // the URL remembers the song, so a reload or a shared link opens it
  const wanted = location.hash.slice(1);
  $("song").value = songs.some(s => s.id === wanted) ? wanted : songs[0].id;
  await loadSong($("song").value);

  await Tone.loaded();
  $("status").textContent = "";
  $("play").disabled = $("stop").disabled = false;
}

async function loadSong(id) {
  if (song) stop();
  song = await getJSON(`scores/${id}.json`);
  document.title = `${song.title} · Choir Practice`;
  history.replaceState(null, "", `#${id}`);
  await osmd.load(`scores/${id}.musicxml`);

  // one column per part, a row each for Show and Hear; your part is on to start
  for (const row of ["part-names", "show-row", "hear-row"]) {
    $(row).replaceChildren($(row).firstElementChild);
  }
  shown = song.parts.map(p => p.name === song.myPart);
  heard = [...shown];
  endSolo();
  song.parts.forEach((part, i) => {
    const name = document.createElement("th");
    name.scope = "col";
    name.textContent = part.name;
    $("part-names").append(name);
    $("show-row").append(checkboxCell(shown, i, `Show ${part.name}`, render));
    $("hear-row").append(checkboxCell(heard, i, `Hear ${part.name}`, endSolo));
  });

  transport.bpm.value = song.tempo;
  $("tempo").value = song.tempo;
  $("tempo-value").textContent = song.tempo;

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
    onChange();
  });
  cell.append(box);
  return cell;
}

// ---- score drawing -------------------------------------------------------

function render() {
  osmd.Sheet.Instruments.forEach((inst, i) => { inst.Visible = shown[i]; });
  osmd.render();
  showBar(currentBar);
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
  $("bar").textContent = `Bar ${index + 1}`;
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

// ---- playback ------------------------------------------------------------

// Every note of every part is scheduled once; muted parts are skipped as they come up.
function schedule() {
  transport.cancel();
  song.parts.forEach((part, i) => {
    for (const [midi, start, dur] of part.notes) {
      const pitch = Tone.Frequency(midi, "midi").toNote();
      transport.schedule(time => {
        if (!heard[i]) return;
        const seconds = dur * 60 / transport.bpm.value;
        piano.triggerAttackRelease(pitch, seconds, time, 0.7);
      }, ticks(start));
    }
  });
  song.measures.forEach((start, i) => {
    transport.schedule(time => Tone.getDraw().schedule(() => showBar(i), time), ticks(start));
    for (let beat = 0; beat < song.beatsPerBar; beat++) {
      transport.schedule(time => {
        if ($("metronome").checked) click.triggerAttackRelease(beat ? "G5" : "C6", 0.03, time);
      }, ticks(start + beat * song.beat));
    }
  });
  // one extra beat so the last note can ring
  transport.schedule(time => Tone.getDraw().schedule(stop, time), ticks(song.length + 1));
}

async function play() {
  await Tone.start();  // browsers only allow audio after a click
  transport.start();
  $("play").textContent = "Pause";
  document.body.classList.add("playing");  // collapses the controls
}

function pause() {
  transport.pause();
  piano.releaseAll();
  $("play").textContent = "Play";
  document.body.classList.remove("playing");
}

function stop() {
  transport.stop();
  piano.releaseAll();
  $("play").textContent = "Play";
  document.body.classList.remove("playing");
  showBar(0);
}

function seek(index) {
  piano.releaseAll();
  transport.ticks = Math.round(song.measures[index] * transport.PPQ);
  showBar(index);
  if (transport.state !== "started") play();
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
  if (e.code !== "Space" || e.repeat || $("play").disabled) return;
  e.preventDefault();
  togglePlay();
});
document.addEventListener("keydown", e => {
  if (e.key.toLowerCase() !== "s" || e.repeat || e.metaKey || e.ctrlKey || e.altKey) return;
  e.preventDefault();  // not type-ahead in the song list
  toggleSolo();
});
$("solo").addEventListener("click", toggleSolo);
// buttons and checkboxes act on Space's keyup, so swallow that too
document.addEventListener("keyup", e => { if (e.code === "Space") e.preventDefault(); });
$("stop").addEventListener("click", stop);
$("song").addEventListener("change", e => {
  e.target.blur();  // so Space goes back to play/pause
  loadSong(e.target.value).catch(showError);
});
$("tempo").addEventListener("input", e => {
  transport.bpm.value = Number(e.target.value);
  $("tempo-value").textContent = e.target.value;
});
$("score").addEventListener("click", e => {
  if ($("play").disabled) return;
  const r = $("score").getBoundingClientRect();
  const bar = barAt(e.clientX - r.left, e.clientY - r.top);
  if (bar >= 0) seek(bar);
});
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(render, 200);
});

function showError(err) {
  $("status").textContent = `Error: ${err.message}`;
  console.error(err);
}

init().catch(showError);
