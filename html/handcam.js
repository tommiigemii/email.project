// handcam.js (ES module) — GitHub Pages friendly

import {
  FilesetResolver,
  HandLandmarker
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.15";

// =======================
// CONFIG (come nel tuo Python)
// =======================
const PINCH_ON = 0.17;
const PINCH_OFF = 0.20;
const ALPHA = 0.30;
const COOLDOWN_S = 2.0;

// =======================
// LANDMARK IDS
// =======================
const WRIST = 0;
const THUMB_TIP = 4;
const INDEX_TIP = 8;
const MIDDLE_MCP = 9;

// Skeleton connections (per disegnare bene)
const HAND_CONNECTIONS = [
  [0,1],[1,2],[2,3],[3,4],
  [0,5],[5,6],[6,7],[7,8],
  [0,9],[9,10],[10,11],[11,12],
  [0,13],[13,14],[14,15],[15,16],
  [0,17],[17,18],[18,19],[19,20],
  [5,9],[9,13],[13,17]
];

// =======================
// DOM
// =======================
const els = {
  video: document.getElementById("webcam"),
  canvas: document.getElementById("overlay"),
  camToggle: document.getElementById("camToggle"),
  distOut: document.getElementById("distOut"),
  fpsOut: document.getElementById("fpsOut"),
  badge: document.getElementById("gestureBadge"),

  actionImage: document.getElementById("actionImage"),

  pinchAudio: document.getElementById("pinchAudio"),

  imgModal: document.getElementById("imgModal"),
  imgModalImg: document.getElementById("imgModalImg"),
  imgModalClose: document.getElementById("imgModalClose"),
};

const toast = (msg) => {
  if (typeof window.showToast === "function") window.showToast(msg);
};

// Modal close handlers
if (els.imgModalClose && els.imgModal) {
  els.imgModalClose.addEventListener("click", () => {
    els.imgModal.style.display = "none";
  });
  els.imgModal.addEventListener("click", (e) => {
    if (e.target === els.imgModal) els.imgModal.style.display = "none";
  });
}

// =======================
// ACTION ASSETS
// =======================
const actionImages = [
  "assets/actions/1.jpg",
  "assets/actions/2.jpg",
  "assets/actions/3.jpg",
  "assets/actions/4.jpg",
];
let actionIdx = 0;

// =======================
// STATE (come Python)
// =======================
let stream = null;
let running = false;

let handLandmarker = null;
let lastVideoTime = -1;

let pinching = false;
let lastLaunchT = 0;
let dFiltered = null;

let fpsSmooth = 0;
let prevT = 0;

// =======================
// UTILS
// =======================
function dist3(a, b){
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const dz = (b.z ?? 0) - (a.z ?? 0);
  return Math.sqrt(dx*dx + dy*dy + dz*dz);
}

function calcNormalizedDistance(landmarks, id1, id2){
  if (!landmarks || landmarks.length < 21) return null;

  const a = landmarks[id1];
  const b = landmarks[id2];

  const p = landmarks[WRIST];
  const q = landmarks[MIDDLE_MCP];

  const num = dist3(a, b);
  const den = dist3(p, q);

  if (!isFinite(num) || !isFinite(den) || den < 1e-6) return null;
  return num / den;
}

function smoothDistance(d){
  if (d == null) {
    dFiltered = null;
    return null;
  }
  if (dFiltered == null) dFiltered = d;
  else dFiltered = (ALPHA * d) + ((1 - ALPHA) * dFiltered);
  return dFiltered;
}

function computeFPS(){
  const now = performance.now();
  const dt = prevT ? (now - prevT) : 0;
  prevT = now;

  const inst = dt > 0 ? (1000 / Math.max(dt, 1e-6)) : 0;
  fpsSmooth = (0.9 * fpsSmooth) + (0.1 * inst);

  return Math.round(fpsSmooth);
}

function setBadge(text){
  if (els.badge) els.badge.textContent = text;
}

function resizeCanvasToVideo(){
  const w = els.video.videoWidth;
  const h = els.video.videoHeight;
  if (!w || !h) return;

  if (els.canvas.width !== w) els.canvas.width = w;
  if (els.canvas.height !== h) els.canvas.height = h;
}

function clearCanvas(ctx){
  ctx.clearRect(0, 0, els.canvas.width, els.canvas.height);
}

function drawHand(ctx, landmarks){
  const w = els.canvas.width;
  const h = els.canvas.height;

  // lines
  ctx.lineWidth = 2;
  ctx.strokeStyle = "rgba(120,180,255,.85)";
  ctx.beginPath();
  for (const [i, j] of HAND_CONNECTIONS){
    const a = landmarks[i];
    const b = landmarks[j];
    ctx.moveTo(a.x * w, a.y * h);
    ctx.lineTo(b.x * w, b.y * h);
  }
  ctx.stroke();

  // points
  for (let i = 0; i < landmarks.length; i++){
    const p = landmarks[i];
    const x = p.x * w;
    const y = p.y * h;

    const isTip = (i === THUMB_TIP || i === INDEX_TIP);
    ctx.fillStyle = isTip ? "rgba(255,170,120,.95)" : "rgba(130,255,200,.80)";
    ctx.beginPath();
    ctx.arc(x, y, isTip ? 6 : 3, 0, Math.PI * 2);
    ctx.fill();
  }
}

// =======================
// PINCH ACTION (audio + open image modal)
// =======================
function playPinchAudio(){
  try {
    if (!els.pinchAudio) return;
    els.pinchAudio.currentTime = 0;
    const p = els.pinchAudio.play();
    if (p && typeof p.catch === "function") p.catch(() => {});
  } catch (_) {}
}

function openImageModal(src){
  if (!els.imgModal || !els.imgModalImg) return;
  els.imgModalImg.src = src;
  els.imgModal.style.display = "flex";
}

function doActionOnPinchStart(){
  // 1) audio
  playPinchAudio();

  // 2) immagine (cambia + modal)
  actionIdx = (actionIdx + 1) % actionImages.length;
  const src = actionImages[actionIdx];

  if (els.actionImage) els.actionImage.src = src;
  openImageModal(src);

  toast("PINCH_START ✅");
}

// =======================
// GESTURE HANDLER (isteresi + cooldown)
// =======================
function gestureHandler(d){
  if (d == null){
    pinching = false;
    setBadge("✋ NO HAND");
    return;
  }

  const now = performance.now() / 1000;

  if (d < PINCH_ON && !pinching){
    setBadge("🤏 PINCH_START");

    if (now - lastLaunchT >= COOLDOWN_S){
      doActionOnPinchStart();
      lastLaunchT = now;
    }

    pinching = true;
  } else if (d < PINCH_ON && pinching){
    setBadge("🤏 PINCH_HOLD");
  } else if (d > PINCH_OFF && pinching){
    setBadge("✋ PINCH_END");
    pinching = false;
  } else {
    setBadge("✋ OPEN");
  }
}

// =======================
// MEDIAPIPE INIT
// =======================
async function initLandmarker(){
  if (handLandmarker) return;

  const vision = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.15/wasm"
  );

  handLandmarker = await HandLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    },
    runningMode: "VIDEO",
    numHands: 2,
  });
}

// =======================
// WEBCAM CONTROL
// =======================
async function startWebcam(){
  if (running) return;

  if (!navigator.mediaDevices?.getUserMedia){
    toast("Camera non supportata su questo browser");
    return;
  }

  await initLandmarker();

  stream = await navigator.mediaDevices.getUserMedia({
    video: {
      facingMode: "user",
      width: { ideal: 1280 },
      height: { ideal: 720 }
    },
    audio: false
  });

  els.video.srcObject = stream;
  await els.video.play();

  resizeCanvasToVideo();

  running = true;
  els.camToggle.textContent = "⏹ Ferma camera";
  toast("Camera attiva 📷");

  requestAnimationFrame(loop);
}

function stopWebcam(){
  running = false;

  if (stream){
    for (const tr of stream.getTracks()) tr.stop();
  }
  stream = null;

  els.video.srcObject = null;

  const ctx = els.canvas.getContext("2d");
  clearCanvas(ctx);

  els.camToggle.textContent = "📷 Avvia camera";
  if (els.distOut) els.distOut.textContent = "—";
  if (els.fpsOut) els.fpsOut.textContent = "—";
  setBadge("✋ OPEN");

  pinching = false;
  dFiltered = null;

  toast("Camera fermata");
}

// =======================
// LOOP
// =======================
function loop(){
  if (!running) return;

  resizeCanvasToVideo();
  const ctx = els.canvas.getContext("2d");
  const nowMs = performance.now();

  // elabora solo quando arriva un nuovo frame video
  if (els.video.currentTime !== lastVideoTime){
    lastVideoTime = els.video.currentTime;

    const res = handLandmarker.detectForVideo(els.video, nowMs);
    clearCanvas(ctx);

    const hands = res?.landmarks ?? [];
    if (hands.length > 0){
      // disegna tutte le mani
      for (const lm of hands) drawHand(ctx, lm);

      // gesto sulla prima mano (puoi cambiarlo con mano specifica se vuoi)
      const lm0 = hands[0];

      const d = calcNormalizedDistance(lm0, INDEX_TIP, THUMB_TIP);
      const ds = smoothDistance(d);

      if (els.distOut){
        els.distOut.textContent = (ds == null) ? "—" : ds.toFixed(3);
      }

      gestureHandler(ds);
    } else {
      if (els.distOut) els.distOut.textContent = "—";
      gestureHandler(null);
    }

    if (els.fpsOut) els.fpsOut.textContent = String(computeFPS());
  }

  requestAnimationFrame(loop);
}

// UI
els.camToggle.addEventListener("click", async () => {
  try{
    if (!running) await startWebcam();
    else stopWebcam();
  } catch (e){
    console.error(e);
    toast("Errore camera/mediapipe");
    stopWebcam();
  }
});

// (Optional) Autostart: sconsigliato perché i browser spesso bloccano permessi senza click
// startWebcam().catch(()=>{});
