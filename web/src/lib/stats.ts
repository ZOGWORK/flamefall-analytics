// Calculations the browser repeats so that filters respond at once.
// Each one mirrors a Python function (named in its comment); src/lib/__tests__ compares the two.

import type { FlexRow } from "./types";

/** flamefall.flex.wilson_interval: Wilson score interval for a binomial share. */
export function wilson(k: number, n: number, z = 1.96): [number, number] {
  if (n === 0) return [NaN, NaN];
  const p = k / n;
  const denom = 1 + (z * z) / n;
  const centre = (p + (z * z) / (2 * n)) / denom;
  const half = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / denom;
  return [Math.max(0, centre - half), Math.min(1, centre + half)];
}

/** numpy.percentile with the default linear interpolation. q is 0..100. */
export function percentile(values: number[], q: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  if (sorted.length === 0) return NaN;
  const pos = ((sorted.length - 1) * q) / 100;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

export type GasColumn = "o2_pct" | "co2_pct" | "he_pct";

export interface ShareRow {
  fuel: string;
  level: number;
  n: number;
  k: number;
  share: number;
  lo: number;
  hi: number;
  disruption: number;
  completion: number;
}

/** flamefall.aggregates.share_by_level: extinction share at each tested level, per fuel. */
export function shareByLevel(rows: FlexRow[], xcol: GasColumn): ShareRow[] {
  const groups = new Map<string, FlexRow[]>();
  for (const r of rows) {
    const key = `${r.fuel}|${r[xcol]}`;
    const g = groups.get(key);
    if (g) g.push(r);
    else groups.set(key, [r]);
  }
  const out: ShareRow[] = [];
  for (const g of groups.values()) {
    const n = g.length;
    const k = g.reduce((s, r) => s + r.extinguished, 0);
    const [lo, hi] = wilson(k, n);
    out.push({
      fuel: g[0].fuel,
      level: g[0][xcol],
      n,
      k,
      share: k / n,
      lo,
      hi,
      disruption: g.filter((r) => r.outcome === "Disruption").length,
      completion: g.filter((r) => r.outcome === "Completion").length,
    });
  }
  // pandas groupby sorts by the keys: fuel, then level
  return out.sort((a, b) => (a.fuel === b.fuel ? a.level - b.level : a.fuel < b.fuel ? -1 : 1));
}

/**
 * flamefall.aggregates.logistic_trend: one-variable logistic fit by Newton iterations.
 * Returns null when it cannot be fitted (fewer than 8 tests, one outcome only, or one level only).
 */
export function logisticTrend(x: number[], y: number[], grid: number[]): number[] | null {
  const n = x.length;
  if (n < 8 || new Set(y).size < 2) return null;
  const min = Math.min(...x);
  const max = Math.max(...x);
  if (max - min === 0) return null;
  const mu = x.reduce((s, v) => s + v, 0) / n;
  const sd = Math.sqrt(x.reduce((s, v) => s + (v - mu) ** 2, 0) / n);
  const z = x.map((v) => (v - mu) / sd);
  let b0 = 0;
  let b1 = 0;
  const ridge = 1e-3;
  for (let iter = 0; iter < 50; iter++) {
    let h00 = ridge;
    let h01 = 0;
    let h11 = ridge;
    let g0 = -ridge * b0;
    let g1 = -ridge * b1;
    for (let i = 0; i < n; i++) {
      const p = 1 / (1 + Math.exp(-(b0 + b1 * z[i])));
      const w = Math.max(p * (1 - p), 1e-6);
      h00 += w;
      h01 += w * z[i];
      h11 += w * z[i] * z[i];
      g0 += y[i] - p;
      g1 += (y[i] - p) * z[i];
    }
    const det = h00 * h11 - h01 * h01;
    const s0 = (h11 * g0 - h01 * g1) / det;
    const s1 = (h00 * g1 - h01 * g0) / det;
    b0 += s0;
    b1 += s1;
    if (Math.max(Math.abs(s0), Math.abs(s1)) < 1e-8) break;
  }
  return grid.map((v) => 1 / (1 + Math.exp(-(b0 + (b1 * (v - mu)) / sd))));
}

/**
 * flamefall.aggregates.nearest_tests: the n tests closest to a target oxygen level and pressure.
 * A test with no printed pressure (FLEX-114) is not ranked: a missing value is never replaced.
 */
export function nearestTests(pool: FlexRow[], o2Pct: number, pressureAtm: number, n = 8): FlexRow[] {
  return pool
    .filter((r) => r.pressure_atm !== null)
    .map((r, i) => ({
      r,
      i,
      d: ((r.o2_pct - o2Pct) / 22) ** 2 + (((r.pressure_atm as number) - pressureAtm) / 2.4) ** 2,
    }))
    .sort((a, b) => a.d - b.d || a.i - b.i)
    .slice(0, n)
    .map((x) => x.r);
}

export interface D2Line {
  /** The printed burn time. */
  t_end: number;
  d2_start: number;
  /** Never below zero: a diameter squared cannot be negative. */
  d2_end: number;
  /** When the printed K and burn time take the line to zero before the burn ends: the time it gets there. */
  t_zero: number | null;
  /** Where the line stops: t_zero when it reaches zero early, otherwise the burn time. */
  t_line_end: number;
  marker: { name: string; t: number; d2: number; diameter_mm: number } | null;
}

/**
 * flamefall.aggregates.d2_line: the d²-law line rebuilt from D0, average K and burn time.
 * Not the measured trace. null when any of the three inputs is missing.
 */
export function d2Line(row: FlexRow, markerExtinction: string, markerOther: string): D2Line | null {
  const { d0_mm: d0, burning_rate_mm2_s: k, burn_time_s: tEnd } = row;
  if (d0 === null || k === null || tEnd === null) return null;
  const d2End = d0 ** 2 - k * tEnd;
  const tZero = d2End < 0 ? d0 ** 2 / k : null;
  const line: D2Line = {
    t_end: tEnd,
    d2_start: d0 ** 2,
    d2_end: Math.max(d2End, 0),
    t_zero: tZero,
    t_line_end: tZero ?? tEnd,
    marker: null,
  };
  const dext = row.extinction_diameter_mm;
  if (dext !== null) {
    // Table IX prints a value in this column for some Disruption and Completion tests too.
    // Only an Extinction outcome makes it an extinction diameter.
    const name = row.outcome === "Extinction" ? markerExtinction : markerOther.replace("{outcome}", row.outcome);
    line.marker = { name, t: tEnd, d2: dext ** 2, diameter_mm: dext };
  }
  return line;
}
