// Scenario triage score. A stated, auditable rule; never a verdict.
//
//   Hazard = 0.30 M_O2 + 0.20 M_flow + 0.15 H + 0.15 D + 0.10 G + 0.10 C
//
// Mirrors flamefall/ranking.py. Every constant comes from ranking.json, which Python exports,
// so the two cannot drift apart. Every weight and lookup value is a design choice.

import rankingJson from "@/data/ranking.json";
import { g } from "./format";
import type { RankingData, ScenarioInput, TermKey } from "./types";

export const R = rankingJson as unknown as RankingData;
export const TERM_KEYS: TermKey[] = ["M_O2", "M_flow", "H", "D", "G", "C"];
export const DEFAULT_HRR = "small sample (glovebox scale)";

export function scenario(partial: Partial<ScenarioInput> & Pick<ScenarioInput, "name" | "material">): ScenarioInput {
  return {
    o2_pct: 21,
    pressure_kpa: 101.3,
    flow_cm_s: 0,
    gravity_g: 0,
    hrr_scale: DEFAULT_HRR,
    free_volume_m3: 1,
    is_droplet: false,
    droplet_d0_mm: 0,
    n_alkane: false,
    ...partial,
  };
}

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

function mO2(s: ScenarioInput): { value: number; why: string; flagged: boolean } {
  const p = (s.o2_pct / 100) * s.pressure_kpa;
  const known = R.p_o2_min_kpa[s.material];
  const pMin = known ? known.value : R.p_o2_floor_kpa;
  const why = known ? known.why : "no measured minimum for this material: cross-material floor used";
  const value = clamp01((p - pMin) / (R.p_o2_ref_kpa - pMin));
  return {
    value,
    why: `O2 partial pressure ${p.toFixed(1)} kPa against a minimum of ${pMin.toFixed(1)} kPa (${why})`,
    flagged: !known,
  };
}

function mFlow(s: ScenarioInput): [number, string] {
  const v = s.flow_cm_s;
  const [lo, hi] = R.flow_band;
  const q = R.quiescent_score;
  if (v <= 0) return [q, "still gas: scored 0.4, not 0, because flames have burned in still gas at raised oxygen"];
  if (v < lo) return [q + ((1 - q) * v) / lo, `${g(v)} cm/s, below the ${g(lo)}-${g(hi)} cm/s band`];
  if (v <= hi) return [1, `${g(v)} cm/s, inside the ${g(lo)}-${g(hi)} cm/s ventilation band`];
  if (v < R.flow_zero_at) return [(R.flow_zero_at - v) / (R.flow_zero_at - hi), `${g(v)} cm/s, towards the blowoff side`];
  return [0, `${g(v)} cm/s, at or beyond ${g(R.flow_zero_at)} cm/s`];
}

function hTerm(s: ScenarioInput): [number, string] {
  const { watts, why } = R.hrr_scale_w[s.hrr_scale];
  return [clamp01(Math.log10(watts / 10) / Math.log10(3200 / 10)), why];
}

function dTerm(s: ScenarioInput): [number, string] {
  const base = R.detection[s.material] ?? R.detection_default;
  if (s.free_volume_m3 > R.large_volume_m3) {
    return [
      Math.min(1, base.score + 0.1),
      `${base.why}; +0.1 for a free volume above 15 m3 (far-field alarm took 981 s in Saffire VI)`,
    ];
  }
  return [base.score, base.why];
}

function gTerm(s: ScenarioInput): [number, string] {
  let best = R.gravity_score[0];
  for (const cand of R.gravity_score) {
    if (Math.abs(cand.g - s.gravity_g) < Math.abs(best.g - s.gravity_g)) best = cand;
  }
  const note = best.g === 0 || best.g === 1 ? "" : " No combustion test in this gravity exists in PSI.";
  return [best.score, `${best.name}.${note}`];
}

function cTerm(s: ScenarioInput): [number, string] {
  if (s.is_droplet && s.n_alkane && s.droplet_d0_mm >= 2.0) {
    return [1, "large n-alkane droplet: can keep burning as a cool flame after the visible flame goes out"];
  }
  return [0, "solid fuel, or a droplet outside the cool-flame regime"];
}

export interface Terms {
  values: Record<TermKey, number>;
  why: Record<TermKey, string>;
  flags: string[];
}

export function terms(s: ScenarioInput): Terms {
  const o2 = mO2(s);
  const parts: Record<TermKey, [number, string]> = {
    M_O2: [o2.value, o2.why],
    M_flow: mFlow(s),
    H: hTerm(s),
    D: dTerm(s),
    G: gTerm(s),
    C: cTerm(s),
  };
  const values = {} as Record<TermKey, number>;
  const why = {} as Record<TermKey, string>;
  for (const k of TERM_KEYS) {
    values[k] = parts[k][0];
    why[k] = parts[k][1];
  }
  return {
    values,
    why,
    flags: o2.flagged ? ["oxygen minimum is a cross-material floor, not measured for this material"] : [],
  };
}

export function hazard(s: ScenarioInput, weights: Record<TermKey, number> = R.weights): number {
  const v = terms(s).values;
  return TERM_KEYS.reduce((sum, k) => sum + weights[k] * v[k], 0);
}

/** Scenarios ordered by score, highest first; ties broken by name. */
export function rank(scenarios: ScenarioInput[], weights: Record<TermKey, number> = R.weights): [string, number][] {
  return scenarios
    .map((s): [string, number] => [s.name, hazard(s, weights)])
    .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
}

export interface Sensitivity {
  base_top: string[];
  weight_sensitive: boolean;
  changes: { change: string; top: string[] }[];
}

/** Does the top-`top` order survive moving each weight by +/- `step` (then renormalising)? */
export function sensitivity(
  scenarios: ScenarioInput[],
  weights: Record<TermKey, number> = R.weights,
  top = 3,
  step = 0.1,
): Sensitivity {
  const baseTop = rank(scenarios, weights)
    .slice(0, top)
    .map(([n]) => n);
  const changes: Sensitivity["changes"] = [];
  for (const key of TERM_KEYS) {
    for (const sign of [1, -1]) {
      const w = { ...weights };
      w[key] = Math.max(0, w[key] + sign * step);
      const total = TERM_KEYS.reduce((s, k) => s + w[k], 0);
      for (const k of TERM_KEYS) w[k] = w[k] / total;
      const order = rank(scenarios, w)
        .slice(0, top)
        .map(([n]) => n);
      if (order.some((n, i) => n !== baseTop[i])) {
        changes.push({ change: `${R.term_label[key]} weight ${sign > 0 ? "+" : "-"}${step.toFixed(2)}`, top: order });
      }
    }
  }
  return { base_top: baseTop, weight_sensitive: changes.length > 0, changes };
}

/** Weights typed by a reader, renormalised to sum to 1. All zero falls back to the defaults. */
export function normalise(raw: Record<TermKey, number>): Record<TermKey, number> {
  const total = TERM_KEYS.reduce((s, k) => s + Math.max(0, raw[k]), 0);
  if (total <= 0) return { ...R.weights };
  const out = {} as Record<TermKey, number>;
  for (const k of TERM_KEYS) out[k] = Math.max(0, raw[k]) / total;
  return out;
}
