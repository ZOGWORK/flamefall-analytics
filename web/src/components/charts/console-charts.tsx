"use client";

// Charts added so that each page leads with a picture of the numbers, not a paragraph.

import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

import { FUEL_COLOR, OUTCOME_COLOR } from "@/components/console/primitives";
import { g, num, pct } from "@/lib/format";
import type { FlexRow, FlexSummary, Investigation, SolidPoint } from "@/lib/types";
import { AXIS, axisLabel, Chart, GRID, Legend, Tip } from "./base";

/** Extinction share by fuel, as two bars with their counts. */
export function FuelBars({ summary }: { summary: FlexSummary }) {
  const rows = (["Methanol", "Heptane"] as const).map((fuel) => ({ fuel, ...summary.by_fuel[fuel] }));
  return (
    <ul className="space-y-4">
      {rows.map((r) => (
        <li key={r.fuel}>
          <div className="flex items-baseline justify-between gap-3">
            <span className="text-body text-foreground">{r.fuel === "Heptane" ? "n-Heptane" : r.fuel}</span>
            <span className="num text-heading font-medium" style={{ color: FUEL_COLOR[r.fuel] }}>
              {pct(r.extinction_share)}
            </span>
          </div>
          <div className="mt-1.5 h-3 bg-secondary" role="img" aria-label={`${r.Extinction} of ${r.n} tests ended in Extinction`}>
            <div className="h-full" style={{ width: `${100 * r.extinction_share}%`, background: FUEL_COLOR[r.fuel] }} />
          </div>
          <p className="num mt-1 text-note text-muted-foreground">
            {r.Extinction} of {r.n} ended in Extinction · {r.Disruption} Disruption · {r.Completion} Completion
          </p>
        </li>
      ))}
    </ul>
  );
}

const CLASS_ORDER = ["droplet", "gas", "solid", "smoke", "partial_g"];

interface RangeRow {
  id: string;
  cls: string;
  lo: number;
  hi: number;
  base: number;
  span: number;
}

/**
 * The ambient-oxygen range each investigation actually tested. Unstated ranges are not drawn.
 * One chart per kind of evidence: droplets, gas flames, solids and smoke are never put on one chart.
 * `exploration` is the oxygen level the challenge brief expects in future cabins.
 */
export function OxygenRangeChart({ investigations, classLabel, exploration }: { investigations: Investigation[]; classLabel: Record<string, string>; exploration: number }) {
  const groups = useMemo(() => {
    const rows: RangeRow[] = investigations
      .map((r) => ({ id: r.investigation_id, cls: r.evidence_class, lo: num(r.o2_min_pct), hi: num(r.o2_max_pct) }))
      .filter((r): r is { id: string; cls: string; lo: number; hi: number } => r.lo !== null && r.hi !== null)
      .sort((a, b) => b.hi - a.hi || a.lo - b.lo)
      .map((r) => ({ ...r, base: r.lo, span: Math.max(r.hi - r.lo, 0.35) }));
    const order = (cls: string) => (CLASS_ORDER.includes(cls) ? CLASS_ORDER.indexOf(cls) : CLASS_ORDER.length);
    return [...new Set(rows.map((r) => r.cls))]
      .sort((a, b) => order(a) - order(b))
      .map((cls) => ({ cls, rows: rows.filter((r) => r.cls === cls) }));
  }, [investigations]);
  return (
    <div className="space-y-6">
      {groups.map(({ cls, rows }) => (
        <OxygenRangeGroup key={cls} title={classLabel[cls] ?? cls} rows={rows} exploration={exploration} />
      ))}
      <Legend
        items={[
          { label: `tested range reaches ${exploration}% O2 or more`, color: "var(--amber)" },
          { label: `stays below ${exploration}%`, color: "var(--data)" },
          { label: "air, 21% (grey dashed line)", color: "var(--dim)", shape: "line" },
        ]}
      />
    </div>
  );
}

function OxygenRangeGroup({ title, rows, exploration }: { title: string; rows: RangeRow[]; exploration: number }) {
  const reaches = (hi: number) => hi >= exploration;
  return (
    <div>
      <p className="kicker mb-1 text-dim">
        {title} · {rows.length} with a stated range
      </p>
      <Chart height={60 + 22 * rows.length} label={`Ambient oxygen range tested by each investigation: ${title}`}>
        <BarChart data={rows} layout="vertical" margin={{ top: 16, right: 16, bottom: 18, left: 8 }} barCategoryGap="30%">
          <CartesianGrid {...GRID} horizontal={false} />
          <XAxis type="number" domain={[10, 42]} ticks={[10, 15, 21, 25, 30, 35, 40]} unit="%" {...AXIS} label={axisLabel("Ambient O2 tested, % by volume", "x")} />
          <YAxis type="category" dataKey="id" width={132} interval={0} {...AXIS} tick={{ fill: "var(--foreground)", fontSize: 11 }} />
          <ReferenceLine x={21} stroke="var(--dim)" strokeDasharray="3 3" />
          <ReferenceLine x={exploration} stroke="var(--amber)" strokeDasharray="3 3" label={{ value: `exploration ${exploration}%+`, position: "top", fill: "var(--amber)", fontSize: 11 }} />
          <Tooltip
            cursor={{ fill: "var(--accent)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload;
              return active && p ? <Tip title={p.id} lines={[p.lo === p.hi ? `${g(p.lo)}% O2` : `${g(p.lo)} to ${g(p.hi)}% O2`, title]} /> : null;
            }}
          />
          <Bar dataKey="base" stackId="r" fill="transparent" />
          <Bar dataKey="span" stackId="r" animationDuration={500}>
            {rows.map((r) => (
              <Cell key={r.id} fill={reaches(r.hi) ? "var(--amber)" : "var(--data)"} />
            ))}
          </Bar>
        </BarChart>
      </Chart>
    </div>
  );
}

/** Solid-fuel outcomes. Amber: the flame was sustained. Red: it went out (quenched, or blown off). Grey: it never lit. */
export const SOLID_STYLE: Record<string, { label: string; color: string; shape: "dot" | "x" | "ring" }> = {
  sustained: { label: "sustained", color: "var(--amber)", shape: "dot" },
  quenched: { label: "quenched", color: "var(--ext)", shape: "dot" },
  blowoff: { label: "blown off", color: "var(--ext)", shape: "x" },
  no_ignition: { label: "no ignition", color: "var(--dim)", shape: "ring" },
};

export function SolidMark({ cx = 0, cy = 0, outcome }: { cx?: number; cy?: number; outcome: string }) {
  const s = SOLID_STYLE[outcome];
  if (s.shape === "x") return <path d={`M${cx - 3.5} ${cy - 3.5} L${cx + 3.5} ${cy + 3.5} M${cx + 3.5} ${cy - 3.5} L${cx - 3.5} ${cy + 3.5}`} stroke={s.color} strokeWidth={1.75} />;
  if (s.shape === "ring") return <circle cx={cx} cy={cy} r={3.5} fill="none" stroke={s.color} strokeWidth={1.5} />;
  return <circle cx={cx} cy={cy} r={4} fill={s.color} fillOpacity={0.7} />;
}

function Crosshair({ cx = 0, cy = 0 }: { cx?: number; cy?: number }) {
  return (
    <g>
      <circle cx={cx} cy={cy} r={9} fill="none" stroke="var(--foreground)" strokeWidth={1.5} />
      <path d={`M${cx - 15} ${cy} H${cx - 4} M${cx + 4} ${cy} H${cx + 15} M${cx} ${cy - 15} V${cy - 4} M${cx} ${cy + 4} V${cy + 15}`} stroke="var(--foreground)" strokeWidth={1.5} />
    </g>
  );
}

/** Where a scenario sits among the tests that were actually run: oxygen against pressure. */
export function ScenarioMap({
  o2,
  pressure,
  flexRows,
  solidPoints,
}: {
  o2: number;
  pressure: number;
  flexRows?: FlexRow[];
  solidPoints?: SolidPoint[];
}) {
  const series = useMemo(() => {
    if (flexRows) {
      return (["Extinction", "Disruption", "Completion"] as const).map((o) => ({
        key: o as string,
        name: o as string,
        color: OUTCOME_COLOR[o],
        shape: "dot" as "dot" | "x" | "ring",
        solid: false,
        data: flexRows.filter((r) => r.outcome === o && r.pressure_kpa !== null).map((r) => ({ x: r.o2_pct, y: r.pressure_kpa as number, id: r.test_id, what: o as string })),
      }));
    }
    return Object.entries(SOLID_STYLE).map(([o, style]) => ({
      key: o,
      name: style.label,
      color: style.color,
      shape: style.shape,
      solid: true,
      data: (solidPoints ?? [])
        .filter((p) => p.outcome === o && p.o2_at_outcome_pct !== null && p.pressure_kPa !== null)
        .map((p) => ({ x: p.o2_at_outcome_pct as number, y: p.pressure_kPa as number, id: `${p.investigation_id} ${p.test_no}`, what: style.label })),
    }));
  }, [flexRows, solidPoints]);
  const xs = series.flatMap((s) => s.data.map((d) => d.x));
  const ys = series.flatMap((s) => s.data.map((d) => d.y));
  const xDomain: [number, number] = [Math.floor(Math.min(o2, ...xs) - 2), Math.ceil(Math.max(o2, ...xs) + 2)];
  const yDomain: [number, number] = [Math.floor(Math.min(pressure, ...ys) / 10) * 10 - 10, Math.ceil(Math.max(pressure, ...ys) / 10) * 10 + 10];
  return (
    <div>
      <Chart height={340} label="The scenario's oxygen and pressure against every test of this kind">
        <ScatterChart margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="x" domain={xDomain} unit="%" {...AXIS} label={axisLabel("Ambient O2, % by volume", "x")} allowDecimals={false} />
          <YAxis type="number" dataKey="y" domain={yDomain} {...AXIS} label={axisLabel("Pressure, kPa", "y")} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload;
              return active && p ? <Tip title={p.id} lines={[`O2 ${g(p.x)}% at ${p.y.toFixed(1)} kPa`, p.what]} /> : null;
            }}
          />
          {series.map((s) =>
            s.solid ? (
              <Scatter key={s.key} data={s.data} fill={s.color} shape={(props: { cx?: number; cy?: number }) => <SolidMark cx={props.cx} cy={props.cy} outcome={s.key} />} />
            ) : (
              <Scatter key={s.key} data={s.data} fill={s.color} fillOpacity={0.6} />
            ),
          )}
          <Scatter data={[{ x: o2, y: pressure, id: "Your scenario", what: "not a test" }]} shape={(props: { cx?: number; cy?: number }) => <Crosshair cx={props.cx} cy={props.cy} />} />
        </ScatterChart>
      </Chart>
      <Legend items={[...series.map((s) => ({ label: s.name, color: s.color, shape: s.shape })), { label: "your scenario (not a test)", color: "var(--foreground)", shape: "ring" as const }]} />
    </div>
  );
}
