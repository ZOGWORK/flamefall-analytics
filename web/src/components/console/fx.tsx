"use client";

// Decoration only: the status strip, the matrix of test cells and the embers in the backdrop. None of it moves.

import { OUTCOME_COLOR } from "@/components/console/primitives";
import { catalogue, flex, solid } from "@/lib/data";

/** One cell per FLEX test, in test order, coloured by how the test ended. */
export function TestMatrix() {
  return (
    <div
      role="img"
      aria-label={`${flex.rows.length} cells, one per test: ${flex.summary.outcomes.Extinction} Extinction, ${flex.summary.outcomes.Disruption} Disruption, ${flex.summary.outcomes.Completion} Completion`}
      className="grid grid-cols-[repeat(auto-fill,minmax(9px,1fr))] gap-[3px]"
    >
      {flex.rows.map((r) => (
        <span
          key={r.test_id}
          title={`${r.test_id} · ${r.outcome}`}
          className="aspect-square rounded-[2px]"
          style={{ background: OUTCOME_COLOR[r.outcome] }}
        />
      ))}
    </div>
  );
}

/** The strip along the top of the console: what the data snapshot holds. */
export function StatusBar() {
  const n = catalogue.counts;
  const items: [string, string | number][] = [
    ["Snapshot", n.retrieved.slice(0, 10)],
    ["Droplet tests", flex.summary.n],
    ["Solid test points", solid.n_total],
    ["Sourced statements", n.evidence],
    ["Verified", n.evidence_verified],
  ];
  return (
    <div className="glass-rail sticky top-0 z-20 hidden h-10 items-center gap-6 border-b border-line px-8 lg:flex">
      <span className="flex items-center gap-2.5">
        <span className="led" aria-hidden />
        <span className="kicker text-amber">Data locked</span>
      </span>
      {/* one line only: an item that does not fit wraps below it and is hidden whole, never cut mid-word */}
      <dl className="flex max-h-5 min-w-0 flex-1 flex-wrap items-baseline gap-x-6 gap-y-8 overflow-hidden">
        {items.map(([label, value]) => (
          <div key={label} className="flex shrink-0 items-baseline gap-2">
            <dt className="kicker text-dim">{label}</dt>
            <dd className="num text-note text-foreground">{value}</dd>
          </div>
        ))}
      </dl>
      <span className="kicker hidden text-dim 2xl:inline">Estimates, never verdicts</span>
    </div>
  );
}

/** Two still embers of light in the page backdrop. */
export function Ambient() {
  return (
    <div className="ambient" aria-hidden>
      <span />
      <span />
    </div>
  );
}
