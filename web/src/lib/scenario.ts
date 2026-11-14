// The Scenario Lab's rules, kept apart from its page so they can be tested:
// which inputs a featured scenario sets, how a scenario is scored, and where the data stops.

import { SOLID_O2_LIMIT } from "./data";
import { g } from "./format";
import { R } from "./ranking";
import { numberIn } from "./url-values";
import type { FlexRow, Fuel, ScenarioInput, SolidData } from "./types";

export type MaterialKey = "pmma" | "sibal" | "nomex" | "silicone" | "heptane" | "methanol";

export const MATERIALS: Record<MaterialKey, { label: string; kind: "solid" | "droplet"; code: string }> = {
  pmma: { label: "PMMA (acrylic)", kind: "solid", code: "PMMA" },
  sibal: { label: "Cotton / fibreglass fabric (SIBAL)", kind: "solid", code: "SIBAL-cotton" },
  nomex: { label: "Nomex fabric", kind: "solid", code: "Nomex" },
  silicone: { label: "Silicone sheet", kind: "solid", code: "silicone" },
  heptane: { label: "n-Heptane droplet", kind: "droplet", code: "Heptane" },
  methanol: { label: "Methanol droplet", kind: "droplet", code: "Methanol" },
};

export interface LabState {
  material: MaterialKey;
  o2: number; // % by volume
  p: number; // kPa
  flow: number; // cm/s
  g: number; // 0, 0.16, 0.38 or 1
  co2: number; // %, droplets only
  he: number; // %, droplets only
  d0: number; // mm, droplets only
  hrr: string; // key of the heat-release scale
  volume: number; // m3
}

export const HRR_SMALL = "small sample (glovebox scale)";
export const HRR_LARGE = "large sample (vehicle scale)";

export const DEFAULT_STATE: LabState = {
  material: "pmma", o2: 21, p: 101.3, flow: 10, g: 0, co2: 0, he: 0, d0: 3, hrr: HRR_SMALL, volume: 50,
};

/** The range each control allows. A value from the address bar is kept inside it. */
export const LIMITS = {
  o2: [10, 60], p: [20, 310], flow: [0, 80], co2: [0, 80], he: [0, 80], d0: [0.5, 8], volume: [1, 1000],
} as const satisfies Partial<Record<keyof LabState, readonly [number, number]>>;

/**
 * The lab's state from the address bar. Anything that is not a known material, a gravity level
 * the formula has, a known size, or a number is replaced by the default, so a hand-typed link can
 * never produce an estimate for inputs the reader did not choose.
 */
export function parseState(q: Record<keyof LabState, string>): LabState {
  const d = DEFAULT_STATE;
  const number = (key: keyof typeof LIMITS) => numberIn(q[key], LIMITS[key][0], LIMITS[key][1], d[key]);
  const gravity = Number(q.g);
  return {
    material: Object.hasOwn(MATERIALS, q.material) ? (q.material as MaterialKey) : d.material,
    o2: number("o2"), p: number("p"), flow: number("flow"), co2: number("co2"), he: number("he"), d0: number("d0"),
    g: q.g.trim() !== "" && R.gravity_score.some((x) => x.g === gravity) ? gravity : d.g,
    hrr: Object.hasOwn(R.hrr_scale_w, q.hrr) ? q.hrr : d.hrr,
    volume: number("volume"),
  };
}

const CODE_TO_KEY: Record<string, MaterialKey> = { PMMA: "pmma", "SIBAL-cotton": "sibal", Nomex: "nomex", silicone: "silicone" };

const FEATURED_NOTES: [string, string][] = [
  ["Lunar-base cabin", "30% O2 or more at 10.2 psi or less, low ventilation, a fabric."],
  ["Pressurised rover", "Elevated oxygen at 10.2 psi with the cabin fan running, an acrylic panel."],
  ["Large fire in a vehicle", "The Saffire VI atmosphere: a fabric sheet in a 16.7 m3 cargo vehicle."],
  ["Station cabin", "Sea-level air in orbit, for comparison."],
];

/**
 * Featured scenarios are the first four ranking presets. Choosing one sets every input the score
 * reads, including the size of the burning item and the free volume, so "your scenario" scores
 * exactly as the same preset does in the ranking table.
 */
export const FEATURED: { label: string; note: string; preset: string; state: LabState }[] = FEATURED_NOTES.map(([label, note], i) => {
  const p = R.presets[i];
  return {
    label,
    note,
    preset: p.name,
    state: {
      ...DEFAULT_STATE,
      material: CODE_TO_KEY[p.material],
      o2: p.o2_pct,
      p: p.pressure_kpa,
      flow: p.flow_cm_s,
      g: p.gravity_g,
      hrr: p.hrr_scale,
      volume: p.free_volume_m3,
    },
  };
});

export const YOUR_SCENARIO = "Your scenario";

export function toScenario(s: LabState): ScenarioInput {
  const m = MATERIALS[s.material];
  const droplet = m.kind === "droplet";
  return {
    name: YOUR_SCENARIO,
    material: droplet ? `${m.code} droplet` : m.code,
    o2_pct: s.o2,
    pressure_kpa: s.p,
    flow_cm_s: s.flow,
    gravity_g: s.g,
    hrr_scale: s.hrr,
    free_volume_m3: s.volume,
    is_droplet: droplet,
    droplet_d0_mm: droplet ? s.d0 : 0,
    n_alkane: m.code === "Heptane",
  };
}

const inside = (v: number, lo: number, hi: number) => lo <= v && v <= hi;

/**
 * Every way the scenario falls outside what was tested. An empty list means it sits inside the
 * tested ranges. Each range is checked at both ends.
 */
export function gaps(s: LabState, flexRows: FlexRow[], solid: SolidData): string[] {
  const m = MATERIALS[s.material];
  const out: string[] = [];
  if (s.g === 1) out.push("gravity: the data are microgravity tests");
  else if (s.g !== 0) out.push(`gravity: no repository test at ${g(s.g)} g`);

  if (m.kind === "droplet") {
    const f = flexRows.filter((r) => r.fuel === (m.code as Fuel));
    const name = m.code === "Heptane" ? "n-heptane" : "methanol";
    const range = (get: (r: FlexRow) => number | null): [number, number] => {
      const vals = f.map(get).filter((v): v is number => v !== null);
      return [Math.min(...vals), Math.max(...vals)];
    };
    const o2 = range((r) => r.o2_pct);
    const p = range((r) => r.pressure_kpa);
    const d0 = range((r) => r.d0_mm);
    const co2Max = range((r) => r.co2_pct)[1];
    const heMax = range((r) => r.he_pct)[1];
    if (!inside(s.o2, o2[0], o2[1])) out.push(`oxygen: FLEX ${name} tests cover ${o2[0].toFixed(0)} to ${o2[1].toFixed(0)}%`);
    if (!inside(s.p, p[0], p[1])) out.push(`pressure: FLEX ${name} tests cover ${p[0].toFixed(0)} to ${p[1].toFixed(0)} kPa`);
    if (s.co2 > 0 && s.he > 0) out.push("CO2 and helium together: never combined in any FLEX test");
    if (s.co2 > co2Max) out.push(`CO2: tested up to ${co2Max.toFixed(0)}%`);
    if (s.he > heMax) out.push(`helium: tested up to ${heMax.toFixed(0)}%`);
    if (s.flow > 0) out.push("ventilation flow: every FLEX droplet burned in still gas");
    if (!inside(s.d0, d0[0], d0[1])) out.push(`droplet size: tested from ${d0[0].toFixed(2)} to ${d0[1].toFixed(2)} mm`);
    return out;
  }

  const env = solid.envelopes[m.code];
  if (!env || env.n === 0 || !env.o2 || !env.pressure || !env.flow) {
    out.push(`material: no ${m.label} test point with a stated outcome`);
  } else {
    if (!inside(s.o2, env.o2[0], env.o2[1])) out.push(`oxygen: ${m.label} was tested from ${env.o2[0].toFixed(1)} to ${env.o2[1].toFixed(1)}%`);
    if (!inside(s.p, env.pressure[0] - 1, env.pressure[1] + 1)) {
      out.push(`pressure: ${m.label} was tested from ${env.pressure[0].toFixed(0)} to ${env.pressure[1].toFixed(0)} kPa`);
    }
    // both ends: no solid test was run in still gas, so 0 cm/s is outside the range too
    if (!inside(s.flow, env.flow[0], env.flow[1])) out.push(`flow: ${m.label} was tested from ${g(env.flow[0])} to ${g(env.flow[1])} cm/s`);
  }
  if (s.o2 > SOLID_O2_LIMIT && solid.envelope_all.o2) {
    out.push(`oxygen above ${SOLID_O2_LIMIT}%: no solid-material test point exists at any pressure (highest with a stated outcome: ${solid.envelope_all.o2[1].toFixed(1)}%)`);
  }
  return out;
}
