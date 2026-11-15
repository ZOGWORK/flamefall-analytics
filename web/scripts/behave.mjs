// Behaviour checks in a real browser: controls, shared links, in-place navigation, the glass card.
// usage: node scripts/behave.mjs <base url>     (serve the built site first; see measure.mjs)
// Set CHROME_PATH to the Chrome or Chromium executable if it is not in the default Windows location.
// Exits with an error if any check fails.
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:3211";
const PORT = 9335;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = spawn(process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "beh-"))}`,
  "--window-size=1440,900", "--no-first-run", "about:blank"], { stdio: "ignore" });
let version;
for (let i = 0; i < 50; i++) { try { version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); break; } catch { await sleep(200); } }
const ws = new WebSocket(version.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let nextId = 1; const pending = new Map(); const listeners = [];
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.reject(new Error(m.error.message)) : p.resolve(m.result); } else for (const l of listeners) l(m); });
const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => { const id = nextId++; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params, sessionId })); });
const once = (method, sessionId) => new Promise((resolve) => { const l = (m) => { if (m.method === method && m.sessionId === sessionId) { listeners.splice(listeners.indexOf(l), 1); resolve(m.params); } }; listeners.push(l); });

async function open(path) {
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId: s } = await send("Target.attachToTarget", { targetId, flatten: true });
  await send("Page.enable", {}, s); await send("Runtime.enable", {}, s);
  const errors = [];
  listeners.push((m) => { if (m.sessionId === s && m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description?.slice(0, 200) ?? m.params.exceptionDetails.text);
    if (m.sessionId === s && m.method === "Runtime.consoleAPICalled" && m.params.type === "error") errors.push("console.error: " + m.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 200)); });
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false }, s);
  const loaded = once("Page.loadEventFired", s);
  await send("Page.navigate", { url: BASE + path }, s); await loaded; await sleep(2500);
  const ev = async (expression) => { const r = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }, s);
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text); return r.result.value; };
  const key = async (k, code, vk, n = 1) => { for (let i = 0; i < n; i++) { await send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, windowsVirtualKeyCode: vk }, s); await send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: vk }, s); } };
  return { s, ev, key, errors, close: () => send("Target.closeTarget", { targetId }) };
}
const results = [];
const check = (name, ok, detail = "") => { results.push(ok); console.log(`${ok ? "ok  " : "FAIL"} ${name}${detail ? "  " + detail : ""}`); };
const HERO = `document.querySelector("section.beam p.num, .beam p.num")?.innerText.replace(/\\s+/g, " ")`;

// 1. Scenario Lab: move the oxygen slider; the results and the address bar follow
{
  const p = await open("/scenario/");
  const before = await p.ev(HERO);
  await p.ev(`document.querySelector('input[type="range"]').focus(); true`);
  await p.key("ArrowRight", "ArrowRight", 39, 10);
  const label = await p.ev(`document.querySelector('input[type="range"]').value`);
  await sleep(900);
  const after = await p.ev(HERO);
  const search = await p.ev(`location.search`);
  check("scenario: slider value changes at once", label === "26", `value=${label}`);
  check("scenario: the result follows the slider", before !== after && after.startsWith("26.3"), `${before} -> ${after}`);
  check("scenario: the address bar follows, once", search === "?o2=26", search);
  check("scenario: no page errors", p.errors.length === 0, p.errors.join(" | "));
  await p.close();
}
// 2. a shared link still sets the state, and the deferred results show it
{
  const p = await open("/scenario/?g=0.16&material=sibal&o2=34&p=56.5");
  const text = await p.ev(`document.body.innerText`);
  check("scenario: a link sets the scenario", text.includes("No combustion test at Lunar gravity") && text.includes("a plan, not evidence") && /19\.2\s*kPa/.test(text));
  check("scenario link: no page errors", p.errors.length === 0, p.errors.join(" | "));
  await p.close();
}
// 3. FLEX Explorer: narrow the oxygen range; the count follows
{
  const p = await open("/flex/");
  const count = `[...document.querySelectorAll("p,span,dd")].map((e) => e.innerText).find((t) => /^\\d+\\s*of 276$/.test(t.replace(/\\s+/g, " ").trim()))`;
  const before = await p.ev(count);
  await p.ev(`document.querySelector('input[type="range"]').focus(); true`);
  await p.key("ArrowRight", "ArrowRight", 39, 12);
  await sleep(900);
  const after = await p.ev(count);
  const search = await p.ev(`location.search`);
  const rows = await p.ev(`document.querySelectorAll("tbody tr").length`);
  check("flex: the results follow the filter", before !== after && !!after, `${String(before).replace(/\s+/g, " ")} -> ${String(after).replace(/\s+/g, " ")}; table rows ${rows}`);
  check("flex: the address bar follows", /o2=/.test(search), search);
  check("flex: no page errors", p.errors.length === 0, p.errors.join(" | "));
  await p.close();
}
// 4. Overview: the glass distortion is off while scrolling and back when it stops; nothing animates at rest
{
  const p = await open("/");
  const glass = `(() => { const el = [...document.querySelectorAll("*")].find((e) => (e.style.backdropFilter || "").includes("url(") || e.style.backdropFilter === "none"); return el ? el.style.backdropFilter : "not found"; })()`;
  const atRest = await p.ev(glass);
  await p.ev(`window.scrollTo(0, 200); new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => r(true))))`);
  const moving = await p.ev(glass);
  await sleep(500);
  const settled = await p.ev(glass);
  const running = await p.ev(`document.getAnimations().filter((a) => a.playState === "running").length`);
  check("overview: liquid glass is on at rest", atRest.includes("url("), atRest.slice(0, 50));
  check("overview: distortion is off while scrolling", moving === "none", moving);
  check("overview: distortion returns when scrolling stops", settled.includes("url("), settled.slice(0, 50));
  check("overview: nothing animates at rest", running === 0, `running=${running}`);
  check("overview: no page errors", p.errors.length === 0, p.errors.join(" | "));
  await p.close();
}
// 5. every page: no errors, no animation left running, client-side navigation still works
{
  const p = await open("/");
  await p.ev(`window.__marker = 42; true`);
  for (const path of ["/flex/", "/catalogue/", "/scenario/", "/models/", "/unknowns/"]) {
    await p.ev(`document.querySelector('a[href="${path}"]').click(); true`);
    await sleep(3200);
    const state = await p.ev(`({ path: location.pathname, marker: window.__marker, running: document.getAnimations().filter((a) => a.playState === "running").length, h1: document.querySelector("h1")?.innerText })`);
    check(`navigate to ${path} in place`, state.path === path && state.marker === 42 && state.running === 0, JSON.stringify(state));
  }
  check("navigation: no page errors", p.errors.length === 0, p.errors.join(" | "));
  await p.close();
}
console.log(results.every(Boolean) ? "ALL OK" : "SOME FAILED");
ws.close(); chrome.kill();
process.exit(results.every(Boolean) ? 0 : 1);
