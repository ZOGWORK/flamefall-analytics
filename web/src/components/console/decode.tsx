"use client";

import { useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

/**
 * A number that "decodes" into place: its digits flicker, then settle left to right.
 * Decoration only: it starts from the real value and ends on it, the real value is what a
 * screen reader gets, and readers who ask for reduced motion see it at once.
 */
export function Decode({ text, className }: { text: string; className?: string }) {
  const reduce = useReducedMotion();
  const [frame, setFrame] = useState<{ of: string; shown: string } | null>(null);

  useEffect(() => {
    if (reduce) return;
    const total = 16;
    let step = 0;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      step += 1;
      const settled = Math.floor((step / total) * text.length);
      const shown = [...text].map((ch, i) => (i < settled || !/\d/.test(ch) ? ch : String(Math.floor(Math.random() * 10)))).join("");
      setFrame(step < total ? { of: text, shown } : null);
      if (step < total) timer = setTimeout(tick, 38);
    };
    timer = setTimeout(tick, 38);
    return () => clearTimeout(timer);
  }, [text, reduce]);

  const display = !reduce && frame && frame.of === text ? frame.shown : text;
  return (
    <span className={className}>
      <span className="sr-only">{text}</span>
      <span aria-hidden>{display}</span>
    </span>
  );
}
