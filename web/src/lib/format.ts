// Number formatting. A missing value prints as a dash, never as 0.

export const DASH = "—";

/** Fixed decimals with an optional unit; null, undefined and NaN print as a dash. */
export function fmt(value: number | null | undefined, digits = 2, unit = ""): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return unit ? `${value.toFixed(digits)} ${unit}` : value.toFixed(digits);
}

/** A share (0..1) as a percentage. */
export function pct(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return DASH;
  return `${(100 * x).toFixed(digits)}%`;
}

/** Python's "{:g}": up to six significant digits, no trailing zeros. */
export function g(value: number): string {
  if (!Number.isFinite(value)) return String(value);
  return String(Number(value.toPrecision(6)));
}

/** Python's "{:.3g}". */
export function g3(value: number): string {
  if (!Number.isFinite(value)) return String(value);
  return String(Number(value.toPrecision(3)));
}

export function capitalise(text: string): string {
  return text ? text[0].toUpperCase() + text.slice(1) : text;
}

/** A catalogue cell that may be a number or an empty string. */
export function num(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const f = Number(value);
  return Number.isNaN(f) ? null : f;
}

export function fuelName(fuel: string): string {
  return fuel === "Heptane" ? "n-Heptane" : fuel;
}
