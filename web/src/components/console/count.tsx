"use client";

import { useReducedMotion } from "motion/react";
import CountUp from "react-countup";

const NUMBER = /^(\d+(?:\.\d+)?)(%?)$/;

/**
 * A big number that counts up to its value when it scrolls into view (react-countup).
 * Decoration only. The real value is always in the page for a screen reader and for a reader
 * without scripts, it is what the count ends on, and readers who ask for reduced motion see it
 * at once (a count of zero seconds). The markup is the same either way, so the page the server
 * rendered is the page the browser hydrates. Text that is not a single number ("39 of 60") is
 * shown as it is.
 */
export function Count({ text, className }: { text: string; className?: string }) {
  const reduce = useReducedMotion();
  const m = NUMBER.exec(text);
  if (!m) return <span className={className}>{text}</span>;
  const decimals = m[1].includes(".") ? m[1].split(".")[1].length : 0;
  return (
    <span className={className}>
      <span className="sr-only">{text}</span>
      <span aria-hidden>
        <CountUp end={Number(m[1])} decimals={decimals} suffix={m[2]} duration={reduce ? 0 : 1.4} enableScrollSpy scrollSpyOnce preserveValue>
          {({ countUpRef }) => <span ref={countUpRef}>{text}</span>}
        </CountUp>
      </span>
    </span>
  );
}
