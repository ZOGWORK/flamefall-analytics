// Nearest real tests to a scenario. Mirrors flamefall/catalogue.py (nearest_flex, nearest_solid).
// A distance is a ranking aid over stated initial conditions. Nothing is interpolated.

import type { FlexRow, Fuel, SolidPoint } from "./types";

export interface NearFlex {
  row: FlexRow;
  distance: number;
  /** Quantities this test does not state, so they were left out of its distance. "" when it states them all. */
  not_compared: string;
}

/** Rows that state every compared quantity first, then by distance; ties keep table order. */
function statedFirst<T extends { distance: number; not_compared: string; i: number }>(rows: T[], k: number): T[] {
  return rows
    .filter((r) => Number.isFinite(r.distance))
    .sort((a, b) => Number(a.not_compared !== "") - Number(b.not_compared !== "") || a.distance - b.distance || a.i - b.i)
    .slice(0, k);
}

/**
 * Scaled so that 5 points of O2, 50 kPa, 15 points of CO2, 10 of helium and 0.8 mm each count as 1.
 * A test that does not state its pressure or initial diameter is compared on what it does state.
 * That is not a match on the missing quantity: such a test is ranked after every test that states
 * them all, and says what was left out.
 */
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
  const ranked = rows
    .filter((r) => r.fuel === fuel)
    .map((row, i) => {
      const left: string[] = [];
      let d2 = ((row.o2_pct - o2Pct) / 5) ** 2 + ((row.co2_pct - co2Pct) / 15) ** 2 + ((row.he_pct - hePct) / 10) ** 2;
      if (row.pressure_kpa === null) left.push("pressure");
      else d2 += ((row.pressure_kpa - pressureKpa) / 50) ** 2;
      if (d0Mm !== null) {
        if (row.d0_mm === null) left.push("initial diameter");
        else d2 += ((row.d0_mm - d0Mm) / 0.8) ** 2;
      }
      return { row, distance: Math.sqrt(d2), not_compared: left.join(", "), i };
    });
  return statedFirst(ranked, k).map(({ row, distance, not_compared }) => ({ row, distance, not_compared }));
}

export interface NearSolid {
  point: SolidPoint;
  distance: number;
  same_material: boolean;
  /** "flow" when the source gives no flow speed for this point, so flow was left out of its distance. */
  not_compared: string;
}

/**
 * Same material first; other materials only when fewer than three points of that material
 * have a stated outcome. Scaled so that 2 points of O2, 30 kPa and a factor of e in flow count as 1.
 * A point with no flow speed is compared on oxygen and pressure only and is ranked after every
 * point that states its flow.
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
  const ranked = pool
    .filter((p) => p.o2_at_outcome_pct !== null && p.pressure_kPa !== null) // no oxygen or pressure: not ranked
    .map((point, i) => {
      let d2 =
        (((point.o2_at_outcome_pct as number) - o2Pct) / 2) ** 2 +
        (((point.pressure_kPa as number) - pressureKpa) / 30) ** 2;
      if (point.flow_cm_s !== null) d2 += (Math.log1p(point.flow_cm_s) - Math.log1p(flowCmS)) ** 2;
      return {
        point,
        distance: Math.sqrt(d2),
        same_material: point.material_class === materialClass,
        not_compared: point.flow_cm_s === null ? "flow" : "",
        i,
      };
    });
  return statedFirst(ranked, k).map(({ point, distance, same_material, not_compared }) => ({
    point,
    distance,
    same_material,
    not_compared,
  }));
}
