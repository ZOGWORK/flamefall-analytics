"use client";

// Charts of the FLEX droplet tests. Droplet data only: never drawn with solid-fuel data.

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  ErrorBar,
  Line,
  LineChart,
  ReferenceDot,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { FUEL_COLOR, OUTCOME_COLOR } from "@/components/console/primitives";
import { fmt, fuelName } from "@/lib/format";
import { logisticTrend, shareByLevel, type D2Line, type GasColumn } from "@/lib/stats";
import type { FlexRow, Outcome } from "@/lib/types";
import { AXIS, axisLabel, Chart, GRID, Legend, Tip } from "./base";

export const AXIS_LABEL: Record<string, string> = {
  o2_pct: "Ambient O2, mol %",
  co2_pct: "Ambient CO2, mol %",
  he_pct: "Ambient He, mol %",
  pressure_atm: "Ambient pressure, atm",
  d0_mm: "Initial droplet diameter D0, mm",
};

const FUELS = ["Methanol", "Heptane"] as const;
const OUTCOMES: Outcome[] = ["Extinction", "Disruption", "Completion"];

type DotProps = { cx?: number; cy?: number; payload?: Record<string, number> };

/** Share of tests ending in Extinction at each tested gas level, with Wilson intervals and a per-fuel trend. */
export function ShareChart({ rows, xcol }: { rows: FlexRow[]; xcol: GasColumn }) {
  const { points, trends } = useMemo(() => {
    const agg = shareByLevel(rows, xcol);
    const points = FUELS.map((fuel) => ({
      fuel,
      data: agg
        .filter((a) => a.fuel === fuel)
        .map((a) => ({ ...a, x: a.level, y: a.share * 100, err: [(a.share - a.lo) * 100, (a.hi - a.share) * 100] })),
    }));
    const trends = FUELS.map((fuel) => {
      const sub = rows.filter((r) => r.fuel === fuel);
      if (!sub.length) return { fuel, data: [] as { x: number; y: number }[] };
      const xs = sub.map((r) => r[xcol]);
      const lo = Math.min(...xs);
      const hi = Math.max(...xs);
      const grid = Array.from({ length: 60 }, (_, i) => lo + ((hi - lo) * i) / 59);
      const p = logisticTrend(xs, sub.map((r) => r.extinguished), grid);
      return { fuel, data: p ? grid.map((x, i) => ({ x, y: p[i] * 100 })) : [] };
    });
    return { points, trends };
  }, [rows, xcol]);

  return (
    <div>
      <Chart height={360} label={`Share of tests ending in Extinction against ${AXIS_LABEL[xcol]}`}>
        <ComposedChart margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="x" domain={["dataMin - 1", "dataMax + 1"]} {...AXIS} label={axisLabel(AXIS_LABEL[xcol], "x")} allowDecimals={false} />
          <YAxis type="number" dataKey="y" domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} unit="%" {...AXIS} label={axisLabel("Tests ending in Extinction", "y")} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) => {
              const p = payload?.find((x) => x.payload && "k" in x.payload)?.payload;
              if (!active || !p) return null;
              return (
                <Tip
                  title={`${fuelName(p.fuel)} at ${p.level}%`}
                  lines={[
                    `Extinction ${p.k} of ${p.n} tests = ${p.y.toFixed(0)}%`,
                    `95% interval ${(p.lo * 100).toFixed(0)}–${(p.hi * 100).toFixed(0)}%`,
                    `Disruption ${p.disruption} · Completion ${p.completion}`,
                  ]}
                />
              );
            }}
          />
          {trends.map((t) =>
            t.data.length ? (
              <Line key={`trend-${t.fuel}`} data={t.data} dataKey="y" type="monotone" stroke={FUEL_COLOR[t.fuel]} strokeWidth={1.5} strokeDasharray="3 3" dot={false} activeDot={false} isAnimationActive={false} tooltipType="none" />
            ) : null,
          )}
          {points.map((s) => (
            <Scatter
              key={s.fuel}
              data={s.data}
              fill={FUEL_COLOR[s.fuel]}
              shape={(props: DotProps) => (
                <circle cx={props.cx} cy={props.cy} r={3 + 1.6 * Math.sqrt(props.payload?.n ?? 1)} fill={FUEL_COLOR[s.fuel]} fillOpacity={0.85} stroke="var(--background)" strokeWidth={1} />
              )}
            >
              <ErrorBar dataKey="err" direction="y" width={0} strokeWidth={1} stroke={FUEL_COLOR[s.fuel]} />
            </Scatter>
          ))}
        </ComposedChart>
      </Chart>
      <Legend
        items={[
          { label: "Methanol, share per tested level", color: FUEL_COLOR.Methanol },
          { label: "n-Heptane, share per tested level", color: FUEL_COLOR.Heptane },
          { label: "one-variable trend per fuel", color: "var(--muted-foreground)", shape: "dash" },
        ]}
      />
    </div>
  );
}

/** Counts of the three outcomes at each tested level. The three stay separate. */
export function MixChart({ rows, xcol }: { rows: FlexRow[]; xcol: GasColumn }) {
  const data = useMemo(() => {
    const byLevel = new Map<number, Record<string, number>>();
    for (const r of rows) {
      const level = r[xcol];
      const entry = byLevel.get(level) ?? { level, Extinction: 0, Disruption: 0, Completion: 0 };
      entry[r.outcome] += 1;
      byLevel.set(level, entry);
    }
    return [...byLevel.values()].sort((a, b) => a.level - b.level);
  }, [rows, xcol]);

  return (
    <div>
      <Chart height={360} label={`Number of tests by outcome against ${AXIS_LABEL[xcol]}`}>
        <BarChart data={data} margin={{ top: 8, right: 12, bottom: 18, left: 4 }} barCategoryGap="22%">
          <CartesianGrid {...GRID} vertical={false} />
          <XAxis dataKey="level" {...AXIS} label={axisLabel(AXIS_LABEL[xcol], "x")} />
          <YAxis allowDecimals={false} {...AXIS} label={axisLabel("Number of tests", "y")} />
          <Tooltip
            cursor={{ fill: "var(--accent)" }}
            content={({ active, payload, label }) =>
              active && payload?.length ? (
                <Tip title={`${label}%`} lines={payload.map((p) => `${p.name}: ${p.value} tests`)} />
              ) : null
            }
          />
          {OUTCOMES.map((o) => (
            <Bar key={o} dataKey={o} stackId="a" fill={OUTCOME_COLOR[o]} isAnimationActive={false} />
          ))}
        </BarChart>
      </Chart>
      <Legend items={OUTCOMES.map((o) => ({ label: o, color: OUTCOME_COLOR[o] }))} />
    </div>
  );
}

const SHAPE: Record<Outcome, "dot" | "x" | "diamond"> = { Extinction: "dot", Disruption: "x", Completion: "diamond" };

function Mark({ cx = 0, cy = 0, outcome, color }: { cx?: number; cy?: number; outcome: Outcome; color: string }) {
  if (outcome === "Disruption") {
    return <path d={`M${cx - 3.5} ${cy - 3.5} L${cx + 3.5} ${cy + 3.5} M${cx + 3.5} ${cy - 3.5} L${cx - 3.5} ${cy + 3.5}`} stroke={color} strokeWidth={1.75} />;
  }
  if (outcome === "Completion") {
    return <path d={`M${cx} ${cy - 5} L${cx + 5} ${cy} L${cx} ${cy + 5} L${cx - 5} ${cy} Z`} fill={color} fillOpacity={0.85} />;
  }
  return <circle cx={cx} cy={cy} r={4} fill={color} fillOpacity={0.8} />;
}

export type RateColumn = "d0_mm" | "o2_pct" | "co2_pct" | "he_pct" | "pressure_atm";

/** Average burning-rate constant K against a chosen condition. Rows without K or x are not drawn. */
export function RateChart({ rows, xcol }: { rows: FlexRow[]; xcol: RateColumn }) {
  const series = useMemo(
    () =>
      FUELS.flatMap((fuel) =>
        OUTCOMES.map((outcome) => ({
          fuel,
          outcome,
          data: rows
            .filter((r) => r.fuel === fuel && r.outcome === outcome && r.burning_rate_mm2_s !== null && r[xcol] !== null)
            .map((r) => ({ ...r, x: r[xcol] as number, y: r.burning_rate_mm2_s as number })),
        })),
      ).filter((s) => s.data.length),
    [rows, xcol],
  );

  return (
    <div>
      <Chart height={360} label={`Average burning rate K against ${AXIS_LABEL[xcol]}`}>
        <ScatterChart margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="x" domain={["auto", "auto"]} {...AXIS} label={axisLabel(AXIS_LABEL[xcol], "x")} />
          <YAxis type="number" dataKey="y" domain={[0, "auto"]} {...AXIS} label={axisLabel("Average burning rate K, mm²/s", "y")} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload as (FlexRow & { x: number; y: number }) | undefined;
              if (!active || !p) return null;
              return (
                <Tip
                  title={`${p.test_id} · ${fuelName(p.fuel)}`}
                  lines={[
                    `O2 ${p.o2_pct}% · CO2 ${p.co2_pct}% · He ${p.he_pct}%`,
                    `P ${fmt(p.pressure_atm, 2, "atm")} · D0 ${fmt(p.d0_mm, 2, "mm")}`,
                    `K ${fmt(p.burning_rate_mm2_s, 2, "mm²/s")} · ${p.outcome}`,
                  ]}
                />
              );
            }}
          />
          {series.map((s) => (
            <Scatter
              key={`${s.fuel}-${s.outcome}`}
              data={s.data}
              fill={FUEL_COLOR[s.fuel]}
              isAnimationActive={false}
              shape={(props: { cx?: number; cy?: number }) => <Mark cx={props.cx} cy={props.cy} outcome={s.outcome} color={FUEL_COLOR[s.fuel]} />}
            />
          ))}
        </ScatterChart>
      </Chart>
      <Legend
        items={[
          { label: "Methanol", color: FUEL_COLOR.Methanol },
          { label: "n-Heptane", color: FUEL_COLOR.Heptane },
          ...OUTCOMES.map((o) => ({ label: o, color: "var(--muted-foreground)", shape: SHAPE[o] })),
        ]}
      />
    </div>
  );
}

/** The d²-law line of one test, rebuilt from three printed numbers. Not the measured trace. */
export function D2Chart({ line, row }: { line: D2Line; row: FlexRow }) {
  const color = FUEL_COLOR[row.fuel];
  const data = [
    { t: 0, d2: line.d2_start },
    { t: line.t_end, d2: line.d2_end },
  ];
  const top = Math.max(line.d2_start, line.marker?.d2 ?? 0);
  return (
    <div>
      <Chart height={320} label={`Droplet diameter squared against time for ${row.test_id}, rebuilt from Table IX`}>
        <LineChart data={data} margin={{ top: 12, right: 16, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="t" domain={[0, "dataMax"]} {...AXIS} label={axisLabel("Time from ignition, s", "x")} />
          <YAxis type="number" domain={[0, Math.ceil(top * 1.08)]} {...AXIS} label={axisLabel("Droplet diameter², mm²", "y")} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) =>
              active && payload?.length ? (
                <Tip title={`t = ${Number(payload[0].payload.t).toFixed(1)} s`} lines={[`D² = ${Number(payload[0].payload.d2).toFixed(2)} mm²`]} />
              ) : null
            }
          />
          <Line dataKey="d2" stroke={color} strokeWidth={2.5} dot={false} animationDuration={500} />
          <ReferenceDot x={0} y={line.d2_start} r={5} fill="var(--background)" stroke="var(--foreground)" strokeWidth={1.5} />
          {line.marker && (
            <ReferenceDot
              x={line.marker.t}
              y={line.marker.d2}
              shape={(props: { cx?: number; cy?: number }) => <Mark cx={props.cx} cy={props.cy} outcome="Disruption" color={OUTCOME_COLOR[row.outcome]} />}
            />
          )}
        </LineChart>
      </Chart>
      <Legend
        items={[
          { label: "d²-law line: D0² − K·t", color, shape: "line" },
          { label: "Initial diameter² (Table IX)", color: "var(--foreground)", shape: "ring" },
          ...(line.marker ? [{ label: line.marker.name, color: OUTCOME_COLOR[row.outcome], shape: "x" as const }] : []),
        ]}
      />
    </div>
  );
}
