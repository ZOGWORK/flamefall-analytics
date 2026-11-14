// An estimate from a stored model card: probability, bootstrap interval and distance to the
// training data. Mirrors flamefall/model.py (Fitted). Nothing is fitted in the browser.

import { percentile } from "./stats";
import type { ModelCard } from "./types";

export type ModelInput = Record<string, number | string | null | undefined>;

export interface OutsideEnvelope {
  feature: string;
  value: number;
  tested_min: number;
  tested_max: number;
}

export interface Distance {
  nn_distance: number;
  train_nn_p95: number;
  train_nn_median: number;
  outside_envelope: OutsideEnvelope[];
  far_from_data: boolean;
  extrapolating: boolean;
  nearest: { row_id: string; distance: number; y: number }[];
}

export interface Prediction extends Distance {
  p: number;
  lo: number | null;
  hi: number | null;
}

const missing = (v: unknown): boolean => v === null || v === undefined || (typeof v === "number" && Number.isNaN(v));
const sigmoid = (z: number) => 1 / (1 + Math.exp(-z));

/** The design row [1, standardised continuous..., binary..., categories..., interactions..., squares...]. */
function featureRow(card: ModelCard, x: ModelInput): number[] {
  const { prep } = card;
  const vals = [1];
  const z: Record<string, number> = {};
  for (const col of card.continuous) {
    const v = x[col];
    let t: number;
    if (missing(v)) t = prep.median[col];
    else if (card.log_features.includes(col)) t = Math.log(v as number);
    else if (card.log1p_features.includes(col)) t = Math.log1p(v as number);
    else t = v as number;
    z[col] = (t - prep.mean[col]) / prep.sd[col];
    vals.push(z[col]);
  }
  for (const col of card.binary) vals.push(Number(x[col] ?? 0));
  for (const [col, cats] of Object.entries(card.categorical)) {
    const raw = x[col];
    const v = cats.includes(raw as string) ? raw : cats.includes("rare") ? "rare" : null;
    for (const c of cats) vals.push(v === c ? 1 : 0);
  }
  for (const [a, b] of card.interactions) vals.push(z[a] * z[b]);
  for (const c of card.squares ?? []) vals.push(z[c] ** 2);
  return vals;
}

const dot = (a: number[], b: number[]) => a.reduce((s, v, i) => s + v * b[i], 0);

/** How far a query sits from the rows the model was trained on (standardised continuous inputs). */
export function distance(card: ModelCard, x: ModelInput): Distance {
  const nCont = card.continuous.length;
  const zrow = (src: ModelInput) => featureRow(card, src).slice(1, 1 + nCont);
  const q = zrow(x);
  const d = card.training_rows.map((t) => {
    const r = zrow(t as ModelInput);
    return Math.sqrt(r.reduce((s, v, i) => s + (v - q[i]) ** 2, 0));
  });
  const order = d
    .map((v, i) => [v, i] as const)
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
    .slice(0, 5);
  const outside: OutsideEnvelope[] = [];
  for (const c of card.distance.columns) {
    const v = x[c];
    const [lo, hi] = card.envelope[c];
    if (!missing(v) && !(lo - 1e-9 <= (v as number) && (v as number) <= hi + 1e-9)) {
      outside.push({ feature: c, value: v as number, tested_min: lo, tested_max: hi });
    }
  }
  const nn = Math.min(...d);
  const p95 = card.distance.train_nn_p95;
  return {
    nn_distance: nn,
    train_nn_p95: p95,
    train_nn_median: card.distance.train_nn_median,
    outside_envelope: outside,
    far_from_data: nn > p95,
    extrapolating: outside.length > 0 || nn > p95,
    nearest: order.map(([dist, i]) => ({
      row_id: card.training_rows[i].row_id,
      distance: dist,
      y: card.training_rows[i].y,
    })),
  };
}

/** Probability with a 95% cluster-bootstrap interval, plus distance to the training data. */
export function predict(card: ModelCard, x: ModelInput): Prediction {
  const row = featureRow(card, x);
  const p = sigmoid(dot(row, card.coef));
  const ps = card.bootstrap.coef.map((c) => sigmoid(dot(c, row)));
  const lo = ps.length ? percentile(ps, 2.5) : null;
  const hi = ps.length ? percentile(ps, 97.5) : null;
  return { p, lo, hi, ...distance(card, x) };
}
