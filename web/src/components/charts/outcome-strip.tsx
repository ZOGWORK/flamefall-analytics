"use client";

import { motion } from "motion/react";

import { OUTCOME_COLOR } from "@/components/console/primitives";
import { pct } from "@/lib/format";
import type { Outcome } from "@/lib/types";

const ORDER: Outcome[] = ["Extinction", "Disruption", "Completion"];

/** How a set of tests ended, as one bar. The three outcomes are never merged. */
export function OutcomeStrip({ counts, height = 28 }: { counts: Record<Outcome, number>; height?: number }) {
  const total = ORDER.reduce((s, o) => s + (counts[o] ?? 0), 0);
  if (total === 0) return null;
  return (
    <div>
      <div
        className="flex w-full gap-px"
        style={{ height }}
        role="img"
        aria-label={ORDER.map((o) => `${o} ${counts[o] ?? 0}`).join(", ")}
      >
        {ORDER.map((o, i) =>
          counts[o] ? (
            <motion.div
              key={o}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ delay: 0.08 * i, duration: 0.45 }}
              style={{ flexGrow: counts[o], flexBasis: 0, background: OUTCOME_COLOR[o], originX: 0 }}
            />
          ) : null,
        )}
      </div>
      <dl className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-body">
        {ORDER.map((o) => (
          <div key={o} className="flex items-baseline gap-2">
            <span aria-hidden className="size-2 shrink-0 self-center" style={{ background: OUTCOME_COLOR[o] }} />
            <dt className="text-muted-foreground">{o}</dt>
            <dd className="num text-foreground">
              {counts[o] ?? 0}
              <span className="ml-1.5 text-note text-muted-foreground">{pct((counts[o] ?? 0) / total)}</span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
