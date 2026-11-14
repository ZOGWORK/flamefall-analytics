// Nearest real tests to a scenario. Mirrors flamefall/catalogue.py (nearest_flex, nearest_solid).
// A distance is a ranking aid over stated initial conditions. Nothing is interpolated.

import type { FlexRow, Fuel, SolidPoint } from "./types";

export interface NearFlex {
  row: FlexRow;
  distance: number;
}

/** Scaled so that 5 points of O2, 50 kPa, 15 points of CO2, 10 of helium and 0.8 mm each count as 1. */
export function nearestFlex(
  rows: FlexRow[],
  fuel: Fuel,
  o2Pct: number,
  pressureKpa: number,
  co2Pct: number,
  hePct: number,
  d0Mm: number | null,
  k = 8,
): NearFlex[] {
  return rows
    .filter((r) => r.fuel === fuel)
    .map((row, i) => {
      // a test with no printed pressure or diameter is ranked on the inputs it does have
      const p = row.pressure_kpa ?? pressureKpa;
      let d2 = ((row.o2_pct - o2Pct) / 5) ** 2 + ((row.co2_pct - co2Pct) / 15) ** 2 + ((row.he_pct - hePct) / 10) ** 2;
      d2 += ((p - pressureKpa) / 50) ** 2;
      if (d0Mm !== null) d2 += (((row.d0_mm ?? d0Mm) - d0Mm) / 0.8) ** 2;
      return { row, distance: Math.sqrt(d2), i };
    })
    .sort((a, b) => a.distance - b.distance || a.i - b.i)
    .slice(0, k)
    .map(({ row, distance }) => ({ row, distance }));
}

export interface NearSolid {
  point: SolidPoint;
  distance: number;
  same_material: boolean;
}

/**
 * Same material first; other materials only when fewer than three points of that material
 * have a stated outcome. Scaled so that 2 points of O2, 30 kPa and a factor of e in flow count as 1.
 */
export function nearestSolid(
  points: SolidPoint[],
  materialClass: string,
  o2Pct: number,
  pressureKpa: number,
  flowCmS: number,
  k = 8,
): NearSolid[] {
  const decided = points.filter((p) => p.outcome !== "ambiguous");
  const same = decided.filter((p) => p.material_class === materialClass);
  const pool = same.length >= 3 ? same : decided;
  return pool
    .filter((p) => p.o2_at_outcome_pct !== null && p.pressure_kPa !== null) // no oxygen or pressure: not ranked
    .map((point, i) => {
      const flow = point.flow_cm_s ?? flowCmS;
      const d2 =
        (((point.o2_at_outcome_pct as number) - o2Pct) / 2) ** 2 +
        (((point.pressure_kPa as number) - pressureKpa) / 30) ** 2 +
        (Math.log1p(flow) - Math.log1p(flowCmS)) ** 2;
      return { point, distance: Math.sqrt(d2), same_material: point.material_class === materialClass, i };
    })
    .sort((a, b) => a.distance - b.distance || a.i - b.i)
    .slice(0, k)
    .map(({ point, distance, same_material }) => ({ point, distance, same_material }));
}
