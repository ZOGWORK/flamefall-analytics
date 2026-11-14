// Reading values out of the address bar. Plain functions, so any module can use them.
// Everything typed into a link is checked here: what is not valid falls back to a default.

export const list = (value: string): string[] => (value ? value.split(",") : []);
/** "lo~hi" from the address bar, kept inside the bounds; the bounds themselves when it is not two ordered numbers. */
export function range(value: string, bounds: [number, number]): [number, number] {
  const parts = value.split("~");
  const [lo, hi] = parts.map(Number);
  if (parts.length !== 2 || parts.some((p) => p.trim() === "") || !Number.isFinite(lo) || !Number.isFinite(hi) || lo > hi) return bounds;
  const inside: [number, number] = [Math.max(bounds[0], lo), Math.min(bounds[1], hi)];
  return inside[0] <= inside[1] ? inside : bounds; // a range wholly outside the bounds selects nothing real
}

/** A value from the address bar, or the fallback when it is not one of the allowed values. */
export function oneOf<T extends string>(value: string, allowed: readonly T[], fallback: T): T {
  return (allowed as readonly string[]).includes(value) ? (value as T) : fallback;
}

/** A number from the address bar kept inside [min, max], or the fallback when it is not a number. */
export function numberIn(value: string, min: number, max: number, fallback: number): number {
  const v = Number(value);
  return value.trim() !== "" && Number.isFinite(v) ? Math.min(max, Math.max(min, v)) : fallback;
}
