"use client";

// Charts for the gaps page. Each one draws real tests and marks the region where none exist.

import { Bar, BarChart, CartesianGrid, ReferenceArea, ReferenceLine, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

import { FUEL_COLOR } from "@/components/console/primitives";
import { fmt, fuelName } from "@/lib/format";
import type { FlexRow, PanelsData, SolidPoint } from "@/lib/types";
import { AXIS, axisLabel, Chart, GRID, Legend, Tip } from "./base";
import { SOLID_STYLE, SolidMark } from "./console-charts";

const LUNAR = "var(--amber)";
const EARTH = "var(--dim)";

/** Spread rate in simulated lunar gravity against normal gravity, same hardware. */
export function LuciChart({ rows, unit }: { rows: PanelsData["luci"]["rows"]; unit: string }) {
  return (
    <div>
      <Chart height={250} label="Flame spread rate in simulated lunar gravity against normal gravity">
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, bottom: 18, left: 8 }} barCategoryGap="24%" barGap={2}>
          <CartesianGrid {...GRID} horizontal={false} />
          <XAxis type="number" {...AXIS} label={axisLabel(`Flame spread rate, ${unit}`, "x")} />
          <YAxis type="category" dataKey="label" width={170} {...AXIS} tick={{ fill: "var(--foreground)", fontFamily: "var(--font-plex)", fontSize: 12 }} />
          <Tooltip
            cursor={{ fill: "var(--accent)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload;
              return active && p ? <Tip title={p.label} lines={[`${p.lunar} ${unit} in simulated lunar gravity`, `${p.earth} ${unit} in normal gravity`, `slides ${p.slides}`]} /> : null;
            }}
          />
          <Bar dataKey="lunar" fill={LUNAR} animationDuration={500} />
          <Bar dataKey="earth" fill={EARTH} animationDuration={500} />
        </BarChart>
      </Chart>
      <Legend items={[{ label: "Simulated lunar gravity", color: LUNAR }, { label: "Normal gravity, same hardware", color: EARTH }]} />
    </div>
  );
}

/** Every solid-fuel test point with a stated outcome, and the region no test reaches. */
export function SolidEnvelopeChart({ points, limit }: { points: SolidPoint[]; limit: number }) {
  const series = Object.keys(SOLID_STYLE).map((outcome) => ({
    outcome,
    data: points.filter((p) => p.outcome === outcome && p.o2_at_outcome_pct !== null && p.pressure_kPa !== null).map((p) => ({ ...p, x: p.o2_at_outcome_pct, y: p.pressure_kPa })),
  }));
  return (
    <div>
      <Chart height={400} label="Solid-fuel test points by ambient oxygen and pressure, with the untested region marked">
        <ScatterChart margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="x" domain={[12, 42]} ticks={[...new Set([15, 20, 25, 30, limit, 40])].sort((a, b) => a - b)} {...AXIS} label={axisLabel("Ambient O2 at the outcome, % by volume", "x")} />
          <YAxis type="number" dataKey="y" domain={[40, 115]} {...AXIS} label={axisLabel("Pressure, kPa", "y")} />
          <ReferenceArea x1={limit} x2={42} fill="var(--foreground)" fillOpacity={0.06} stroke="var(--dim)" strokeDasharray="4 3" label={{ value: `NO DATA above ${limit}% O2`, position: "insideTop", fill: "var(--foreground)", fontSize: 11, fontFamily: "var(--font-jetbrains)" }} />
          <ReferenceArea x1={30} x2={42} y1={40} y2={70.3} fill="none" stroke="var(--amber)" strokeDasharray="2 3" label={{ value: "expected Moon-base and rover atmospheres", position: "insideBottom", fill: "var(--amber)", fontSize: 11 }} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload as (SolidPoint & { x: number; y: number }) | undefined;
              return active && p ? (
                <Tip title={`${p.investigation_id} ${p.test_no} · ${p.material_class}`} lines={[`O2 ${p.x.toFixed(1)}% at ${p.y.toFixed(1)} kPa`, `flow ${fmt(p.flow_cm_s, 1, "cm/s")}`, p.outcome.replace("_", " ")]} />
              ) : null;
            }}
          />
          {series.map((s) => (
            <Scatter key={s.outcome} data={s.data} fill={SOLID_STYLE[s.outcome].color} shape={(props: { cx?: number; cy?: number }) => <SolidMark cx={props.cx} cy={props.cy} outcome={s.outcome} />} />
          ))}
        </ScatterChart>
      </Chart>
      <Legend items={Object.values(SOLID_STYLE).map((s) => ({ label: s.label, color: s.color, shape: s.shape }))} />
    </div>
  );
}

/** Every FLEX test lies on one of the two axes: no test contains both diluents. */
export function DiluentChart({ rows, both }: { rows: FlexRow[]; both: number }) {
  const series = (["Methanol", "Heptane"] as const).map((fuel) => ({ fuel, data: rows.filter((r) => r.fuel === fuel).map((r) => ({ ...r, x: r.co2_pct, y: r.he_pct })) }));
  return (
    <div>
      <Chart height={340} label="FLEX tests by CO2 and helium fraction: none contains both">
        <ScatterChart margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="x" domain={[0, 75]} {...AXIS} label={axisLabel("CO2 in the atmosphere, mol %", "x")} />
          <YAxis type="number" dataKey="y" domain={[0, 50]} {...AXIS} label={axisLabel("Helium in the atmosphere, mol %", "y")} />
          <ReferenceArea x1={2.5} x2={75} y1={2.5} y2={50} fill="var(--foreground)" fillOpacity={0.06} stroke="var(--dim)" strokeDasharray="4 3" label={{ value: `NO DATA · ${both} of ${rows.length} tests contain both gases`, fill: "var(--foreground)", fontSize: 11, fontFamily: "var(--font-jetbrains)" }} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload as FlexRow | undefined;
              return active && p ? <Tip title={`${p.test_id} · ${fuelName(p.fuel)}`} lines={[`O2 ${p.o2_pct}%`, `CO2 ${p.co2_pct}% · He ${p.he_pct}%`]} /> : null;
            }}
          />
          {series.map((s) => (
            <Scatter key={s.fuel} data={s.data} fill={FUEL_COLOR[s.fuel]} fillOpacity={0.55} />
          ))}
        </ScatterChart>
      </Chart>
      <Legend items={[{ label: "Methanol", color: FUEL_COLOR.Methanol }, { label: "n-Heptane", color: FUEL_COLOR.Heptane }]} />
    </div>
  );
}

/** Geometric mean smoke particle diameter, fresh and aged, against the mark the smoke panel states. */
export function SmokeChart({ rows, threshold, unit }: { rows: { material: string; fresh: number; aged: number }[]; threshold: number; unit: string }) {
  return (
    <div>
      <Chart height={320} label="Smoke particle diameter by material, fresh and after ageing">
        <BarChart data={rows} margin={{ top: 16, right: 12, bottom: 8, left: 4 }} barCategoryGap="24%" barGap={2}>
          <CartesianGrid {...GRID} vertical={false} />
          <XAxis dataKey="material" {...AXIS} tick={{ fill: "var(--foreground)", fontFamily: "var(--font-plex)", fontSize: 12 }} interval={0} />
          <YAxis domain={[0, 560]} {...AXIS} label={axisLabel(`Geometric mean diameter, ${unit}`, "y")} />
          <ReferenceLine y={threshold} stroke="var(--ext)" strokeDasharray="4 3" label={{ value: `${threshold} ${unit}`, position: "insideTopRight", fill: "var(--ext)", fontSize: 11, fontFamily: "var(--font-jetbrains)" }} />
          <Tooltip
            cursor={{ fill: "var(--accent)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload;
              return active && p ? <Tip title={p.material} lines={[`${p.fresh} ${unit} fresh`, `${p.aged} ${unit} after 720 s`]} /> : null;
            }}
          />
          <Bar dataKey="fresh" fill="var(--data)" animationDuration={500} />
          <Bar dataKey="aged" fill="var(--amber)" animationDuration={500} />
        </BarChart>
      </Chart>
      <Legend items={[{ label: "Fresh smoke", color: "var(--data)" }, { label: "After 720 s", color: "var(--amber)" }]} />
    </div>
  );
}

/** Horizontal bars of counts, as real text. */
export function CountBars({ rows, total }: { rows: { label: string; value: number; color: string }[]; total: number }) {
  return (
    <ul className="space-y-2">
      {rows.map((r) => (
        <li key={r.label} className="grid grid-cols-[9.5rem_1fr_2.5rem] items-center gap-x-3 text-body">
          <span className="text-muted-foreground">{r.label}</span>
          <span className="h-4 bg-secondary" aria-hidden>
            <span className="block h-full" style={{ width: `${(100 * r.value) / total}%`, background: r.color }} />
          </span>
          <span className="num text-right text-foreground">{r.value}</span>
        </li>
      ))}
    </ul>
  );
}
