// The stated relevance rule: how closely an investigation's tested conditions match a scenario.
// Mirrors flamefall/catalogue.py (relevance, rank_investigations). It measures closeness of test
// conditions. It says nothing about how dangerous a scenario is.

import { g, num } from "./format";
import type { Investigation } from "./types";

export const RELEVANCE_KEYS = ["oxygen", "pressure", "fuel type", "flow", "gravity"] as const;
export type RelevanceKey = (typeof RELEVANCE_KEYS)[number];

type Match = [number, string];

function rangeMatch(value: number, loRaw: number | string, hiRaw: number | string, fade: number): Match {
  const lo = num(loRaw);
  const hi = num(hiRaw);
  if (lo === null || hi === null) return [0, "not stated for this investigation"];
  if (lo <= value && value <= hi) return [1, `inside the tested range ${g(lo)} to ${g(hi)}`];
  const gap = value < lo ? lo - value : value - hi;
  return [Math.max(0, 1 - gap / fade), `${gap.toFixed(1)} outside the tested range ${g(lo)} to ${g(hi)}`];
}

export interface Relevance {
  score: number;
  terms: Record<RelevanceKey, number>;
  why: Record<RelevanceKey, string>;
}

export interface ScenarioConditions {
  o2_pct: number;
  pressure_kpa: number;
  flow_cm_s: number;
  evidence_class: string;
  gravity_g: number;
}

export function relevance(row: Investigation, s: ScenarioConditions, weights: Record<string, number>): Relevance {
  const t = {} as Record<RelevanceKey, Match>;
  t.oxygen = rangeMatch(s.o2_pct, row.o2_min_pct, row.o2_max_pct, 10);
  t.pressure = rangeMatch(s.pressure_kpa, row.pressure_min_kPa, row.pressure_max_kPa, 40);
  t.flow =
    row.flow_regime === "quiescent" && s.flow_cm_s === 0
      ? [1, "still gas, as tested"]
      : rangeMatch(s.flow_cm_s, row.flow_min_cm_s, row.flow_max_cm_s, 20);
  const cls = row.evidence_class;
  if (cls === s.evidence_class || (cls === "partial_g" && s.evidence_class === "solid")) {
    t["fuel type"] = [1, "same kind of fuel"];
  } else if (cls === "smoke") {
    t["fuel type"] = [0.5, "smoke and detection evidence applies to any burning or overheating material"];
  } else {
    t["fuel type"] = [0, "different kind of fuel: physics does not transfer"];
  }
  const grav = num(row.gravity_g);
  if (grav === null) t.gravity = [0, "not a flight test"];
  else if (Math.abs(grav - s.gravity_g) < 0.02) t.gravity = [1, "same gravity level"];
  else t.gravity = [0, `tested at ${g(grav)} g, scenario is ${g(s.gravity_g)} g`];

  const terms = {} as Record<RelevanceKey, number>;
  const why = {} as Record<RelevanceKey, string>;
  let score = 0;
  for (const k of RELEVANCE_KEYS) {
    terms[k] = t[k][0];
    why[k] = t[k][1];
    score += weights[k] * t[k][0];
  }
  return { score, terms, why };
}

export interface RankedInvestigation {
  row: Investigation;
  rel: Relevance;
}

/** Combustion investigations ordered by closeness, highest first; ties broken by identifier. */
export function rankInvestigations(
  investigations: Investigation[],
  s: ScenarioConditions,
  weights: Record<string, number>,
): RankedInvestigation[] {
  return investigations
    .filter((r) => r.is_combustion)
    .map((row) => ({ row, rel: relevance(row, s, weights) }))
    .sort(
      (a, b) =>
        b.rel.score - a.rel.score ||
        (a.row.investigation_id < b.row.investigation_id ? -1 : a.row.investigation_id > b.row.investigation_id ? 1 : 0),
    );
}

/** A tested range as text; an unstated range says so. */
export function rangeText(lo: number | string, hi: number | string, unit: string): string {
  const a = num(lo);
  const b = num(hi);
  if (a === null || b === null) return "not stated";
  return a === b ? `${g(a)} ${unit}` : `${g(a)} to ${g(b)} ${unit}`;
}
