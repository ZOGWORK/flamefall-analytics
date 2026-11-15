// Measure rendering cost of each page with headless Chrome over the DevTools protocol.
// usage: node scripts/measure.mjs <base url> [label]     (serve the built site first, for example
//        `npm run build` then `npx serve out -l 3211`, and pass http://localhost:3211)
// Set CHROME_PATH to the Chrome or Chromium executable if it is not in the default Windows location.
// Numbers move from run to run and from machine to machine: compare two builds measured back to back.
// For each page: load cost, main-thread time while idle (anything still animating shows up here),
// frame pacing while idle and while scrolling, and the cost of moving a control.
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:3211";
const LABEL = process.argv[3] ?? "run";
const CHROME = process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9333;
const PAGES = (process.env.PAGES ?? "/,/flex/,/catalogue/,/scenario/,/models/,/unknowns/,/deck/").split(",");
const INJECT = process.env.INJECT ?? "";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  "--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "perf-"))}`,
  "--window-size=1440,900", "--no-first-run", "--disable-extensions", "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding", "--disable-background-timer-throttling", "--disable-features=CalculateNativeWinOcclusion", "about:blank",
], { stdio: "ignore" });

let version;
for (let i = 0; i < 50; i++) {
  try { version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); break; } catch { await sleep(200); }
}
const ws = new WebSocket(version.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let nextId = 1;
const pending = new Map();
const listeners = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { const { resolve, reject } = pending.get(m.id); pending.delete(m.id); if (m.error) reject(new Error(m.error.message)); else resolve(m.result); }
  else for (const l of listeners) l(m);
});
const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
  const id = nextId++; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params, sessionId }));
});
const once = (method, sessionId, timeout = 30000) => new Promise((resolve, reject) => {
  const t = setTimeout(() => reject(new Error(`timeout waiting for ${method}`)), timeout);
  const l = (m) => { if (m.method === method && m.sessionId === sessionId) { clearTimeout(t); listeners.splice(listeners.indexOf(l), 1); resolve(m.params); } };
  listeners.push(l);
});

const metrics = async (s) => Object.fromEntries((await send("Performance.getMetrics", {}, s)).metrics.map((m) => [m.name, m.value]));
const evaluate = async (s, expression) => {
  const r = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }, s);
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
  return r.result.value;
};
// frames over a window: count, mean and worst gap, share of gaps over 25 ms (a dropped frame at 60 Hz)
const FRAMES = (ms, scroll) => `new Promise((resolve) => {
  const gaps = []; let last = performance.now(); const start = last; let y = 0;
  const max = document.documentElement.scrollHeight - innerHeight;
  function tick(now) {
    gaps.push(now - last); last = now;
    if (${scroll}) { y = Math.min(max, y + 40); window.scrollTo(0, y); if (y >= max) y = 0; }
    if (now - start < ${ms}) requestAnimationFrame(tick);
    else { gaps.shift(); const sum = gaps.reduce((a, b) => a + b, 0);
      resolve({ frames: gaps.length, fps: Math.round(1000 * gaps.length / sum), worst: Math.round(Math.max(...gaps)), slow: gaps.filter((g) => g > 25).length }); }
  }
  requestAnimationFrame(tick);
})`;

const rows = [];
for (const path of PAGES) {
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId: s } = await send("Target.attachToTarget", { targetId, flatten: true });
  await send("Page.enable", {}, s);
  await send("Performance.enable", {}, s);
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false }, s);
  await send("Page.addScriptToEvaluateOnNewDocument", { source: `window.__long = []; new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__long.push(e.duration); }).observe({ type: "longtask", buffered: true });` }, s);
  const loaded = once("Page.loadEventFired", s);
  await send("Page.navigate", { url: BASE + path }, s);
  await loaded;
  if (INJECT) await evaluate(s, INJECT);
  await sleep(3500); // entrance animations and count-ups finish
  if (process.env.INJECT_LATE) { console.log('late:', JSON.stringify(await evaluate(s, process.env.INJECT_LATE))); await sleep(600); }
  const load = await evaluate(s, `(() => { const n = performance.getEntriesByType("navigation")[0];
    const long = performance.getEntriesByType("longtask");
    return { dcl: Math.round(n.domContentLoadedEventEnd), load: Math.round(n.loadEventEnd), transferKB: Math.round(performance.getEntriesByType("resource").reduce((a, r) => a + (r.encodedBodySize || 0), n.encodedBodySize) / 1024),
      blockedMs: Math.round(window.__long.reduce((x, d) => x + Math.max(0, d - 50), 0)), longest: Math.round(Math.max(0, ...window.__long)),
      nodes: document.getElementsByTagName("*").length, animations: document.getAnimations().filter((a) => a.playState === "running").length }; })()`);
  const afterLoad = await metrics(s);
  // idle: nothing is touched for 3 s. Main-thread time here is the price of whatever keeps animating.
  const idleFrames = await evaluate(s, FRAMES(3000, false));
  const afterIdle = await metrics(s);
  const scrollFrames = await evaluate(s, FRAMES(3000, true));
  const afterScroll = await metrics(s);
  const row = {
    page: path, ...load,
    loadTaskMs: Math.round(afterLoad.TaskDuration * 1000), loadScriptMs: Math.round(afterLoad.ScriptDuration * 1000),
    idleTaskMs: Math.round((afterIdle.TaskDuration - afterLoad.TaskDuration) * 1000),
    idleFps: idleFrames.fps, idleWorst: idleFrames.worst, idleSlow: idleFrames.slow,
    scrollTaskMs: Math.round((afterScroll.TaskDuration - afterIdle.TaskDuration) * 1000),
    scrollFps: scrollFrames.fps, scrollWorst: scrollFrames.worst, scrollSlow: scrollFrames.slow,
  };
  // moving a control: thirty arrow presses on the first slider of the Scenario Lab, or the oxygen range on the explorer
  if (path === "/scenario/" || path === "/flex/") {
    await evaluate(s, `window.scrollTo(0, 0); document.querySelector('input[type="range"]')?.focus(); window.__long.length = 0; true`);
    const before = await metrics(s);
    const t0 = Date.now();
    const steps = [];
    for (let i = 0; i < 30; i++) {
      await send("Input.dispatchKeyEvent", { type: "keyDown", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 }, s);
      await send("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 }, s);
      const t1 = Date.now();
      await evaluate(s, `new Promise((r) => requestAnimationFrame(r))`);
      steps.push(Date.now() - t1);   // how long the page took to paint the next frame after the key press
      await sleep(40);               // a steady drag: about 25 steps a second
    }
    steps.sort((x, y) => x - y);
    row.stepMedianMs = steps[Math.floor(steps.length / 2)];
    row.stepWorstMs = steps[steps.length - 1];
    row.stepsOver50 = steps.filter((x) => x > 50).length;
    await sleep(1500);   // let the last deferred update finish
    const long = await evaluate(s, `window.__long.slice()`);
    row.dragLongTasks = long.length; row.dragWorstTaskMs = Math.round(Math.max(0, ...long)); row.dragBlockedMs = Math.round(long.reduce((x, d) => x + Math.max(0, d - 50), 0));
    const after = await metrics(s);
    row.slider30TaskMs = Math.round((after.TaskDuration - before.TaskDuration) * 1000);
    row.slider30ScriptMs = Math.round((after.ScriptDuration - before.ScriptDuration) * 1000);
    row.slider30WallMs = Date.now() - t0;
    row.sliderMoved = await evaluate(s, `document.querySelector('input[type="range"]')?.value`);
  }
  rows.push(row);
  await send("Target.closeTarget", { targetId });
}
console.log(`== ${LABEL} (${BASE})`);
console.table(rows.map(({ page, load, blockedMs, longest, nodes, animations, loadTaskMs, loadScriptMs }) => ({ page, load, blockedMs, longest, nodes, animations, loadTaskMs, loadScriptMs })));
console.table(rows.map(({ page, idleTaskMs, idleFps, idleWorst, idleSlow, scrollTaskMs, scrollFps, scrollWorst, scrollSlow }) => ({ page, idleTaskMs, idleFps, idleWorst, idleSlow, scrollTaskMs, scrollFps, scrollWorst, scrollSlow })));
console.table(rows.filter((r) => r.slider30TaskMs !== undefined).map(({ page, dragLongTasks, dragWorstTaskMs, dragBlockedMs, slider30TaskMs, sliderMoved }) => ({ page, dragLongTasks, dragWorstTaskMs, dragBlockedMs, slider30TaskMs, sliderMoved })));
ws.close();
chrome.kill();
