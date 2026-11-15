"use client";

import { useEffect, useState } from "react";

/**
 * A value that follows `value` once it has stopped changing for `delay` milliseconds.
 *
 * A slider changes its value many times a second while it is dragged. The control shows each
 * change at once; the charts and tables computed from it are far heavier, and redrawing them for
 * every step made the drag stutter. They read the settled value instead, so they are redrawn
 * once, a moment after the pointer pauses. For a single click the delay is too short to notice.
 */
export function useSettled<T>(value: T, delay = 120): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setSettled(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);
  return settled;
}
