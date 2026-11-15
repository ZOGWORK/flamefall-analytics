"use client";

// Shared chart frame and axis styling, so every chart reads the same way.

import { useEffect, useRef, useState } from "react";
import { ChartContainer, type ChartConfig } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

const EMPTY: ChartConfig = {};
/** How many charts have asked for a timer slot, so that timers are spread out. */
let waiting = 0;

export function Chart({
  children,
  height = 320,
  className,
  label,
}: {
  children: React.ComponentProps<typeof ChartContainer>["children"];
  height?: number;
  className?: string;
  label: string;
}) {
  // A chart on screen is built at once. One further down is built in an idle moment after the page
  // has loaded, or as soon as it comes near the viewport, whichever is first. Building every chart
  // of a long page in one go kept the page busy for a second or more while it loaded; building one
  // only when it scrolls into view makes scrolling hitch. The box keeps its height, so nothing
  // moves when the chart appears, and it keeps its label, so a screen reader finds it either way.
  const box = useRef<HTMLDivElement>(null);
  const [built, setBuilt] = useState(false);
  useEffect(() => {
    const el = box.current;
    if (!el || built) return;
    const build = () => setBuilt(true);
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) build();
      },
      { rootMargin: "300px 0px" },
    );
    observer.observe(el);
    // one chart per idle period: a callback that overruns its period pushes the rest to the next one.
    // Where there is no idle callback (Safari), the charts are spaced out on a timer instead.
    const idle =
      typeof window.requestIdleCallback === "function"
        ? window.requestIdleCallback(build, { timeout: 4000 })
        : window.setTimeout(build, 400 + 150 * waiting++);
    window.addEventListener("beforeprint", build); // a printed page shows every chart
    return () => {
      window.removeEventListener("beforeprint", build);
      observer.disconnect();
      if (typeof window.cancelIdleCallback === "function") window.cancelIdleCallback(idle);
      else window.clearTimeout(idle);
    };
  }, [built]);
  return (
    <div ref={box} role="img" aria-label={label} className={cn("w-full", className)} style={{ height }}>
      {built && (
        <ChartContainer config={EMPTY} className="aspect-auto h-full w-full">
          {children}
        </ChartContainer>
      )}
    </div>
  );
}

export const GRID = { stroke: "var(--line)", strokeDasharray: "0" } as const;
export const AXIS = {
  stroke: "var(--line)",
  tick: { fill: "var(--muted-foreground)" },
  tickLine: false,
  axisLine: { stroke: "var(--input)" },
} as const;

export function axisLabel(value: string, axis: "x" | "y") {
  return axis === "x"
    ? ({ value, position: "insideBottom", offset: -2, fill: "var(--muted-foreground)", fontSize: 12 } as const)
    : ({ value, angle: -90, position: "insideLeft", offset: 12, fill: "var(--muted-foreground)", fontSize: 12, style: { textAnchor: "middle" } } as const);
}

/** Tooltip box. Content is supplied by each chart, so the wording is always specific. */
export function Tip({ title, lines }: { title: React.ReactNode; lines: React.ReactNode[] }) {
  return (
    <div className="max-w-64 border border-input bg-popover px-3 py-2 text-note text-muted-foreground">
      <p className="num text-foreground">{title}</p>
      {lines.map((line, i) => (
        <p key={i} className="num">
          {line}
        </p>
      ))}
    </div>
  );
}

/** A legend written as text, so the colours are named and not just shown. */
export function Legend({ items, className }: { items: { label: string; color: string; shape?: "dot" | "line" | "dash" | "x" | "diamond" | "ring" }[]; className?: string }) {
  return (
    <ul className={cn("flex flex-wrap gap-x-5 gap-y-1 text-note text-muted-foreground", className)}>
      {items.map((it) => (
        <li key={it.label} className="flex items-center gap-1.5">
          <svg aria-hidden width="14" height="10" viewBox="0 0 14 10">
            {it.shape === "line" && <line x1="0" y1="5" x2="14" y2="5" stroke={it.color} strokeWidth="2" />}
            {it.shape === "dash" && <line x1="0" y1="5" x2="14" y2="5" stroke={it.color} strokeWidth="2" strokeDasharray="3 2" />}
            {it.shape === "x" && <path d="M3 1 L11 9 M11 1 L3 9" stroke={it.color} strokeWidth="2" />}
            {it.shape === "diamond" && <path d="M7 0 L12 5 L7 10 L2 5 Z" fill={it.color} />}
            {it.shape === "ring" && <circle cx="7" cy="5" r="3.5" fill="none" stroke={it.color} strokeWidth="1.5" />}
            {(!it.shape || it.shape === "dot") && <circle cx="7" cy="5" r="4" fill={it.color} />}
          </svg>
          {it.label}
        </li>
      ))}
    </ul>
  );
}
