"use client";

// Charts of how a model was validated. Every curve comes from out-of-fold predictions.

import { Bar, BarChart, CartesianGrid, Cell, ComposedChart, ErrorBar, Line, LineChart, ReferenceDot, ReferenceLine, Scatter, Tooltip, XAxis, YAxis } from "recharts";

import type { Confusion, ModelCard } from "@/lib/types";
import { AXIS, axisLabel, Chart, GRID, Legend, Tip } from "./base";

const UNIT = { domain: [0, 1] as [number, number], ticks: [0, 0.25, 0.5, 0.75, 1] };

/** ROC curve against the coin-flip diagonal, with the working threshold marked. */
export function RocChart({ card, failed }: { card: ModelCard; failed: boolean }) {
  const roc = card.metrics.roc.map(([fpr, tpr]) => ({ fpr, tpr }));
  const cy = card.metrics.confusion_at_youden;
  const color = failed ? "var(--ext)" : "var(--data)";
  return (
    <div>
      <Chart height={320} label="ROC curve from out-of-fold predictions">
        <LineChart data={roc} margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="fpr" {...UNIT} {...AXIS} label={axisLabel("False-positive rate", "x")} />
          <YAxis type="number" {...UNIT} {...AXIS} label={axisLabel("Sensitivity", "y")} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) =>
              active && payload?.length ? (
                <Tip title={`False-positive rate ${Number(payload[0].payload.fpr).toFixed(2)}`} lines={[`Sensitivity ${Number(payload[0].payload.tpr).toFixed(2)}`]} />
              ) : null
            }
          />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--dim)" strokeDasharray="3 3" />
          <Line dataKey="tpr" type="stepAfter" stroke={color} strokeWidth={2.5} dot={false} animationDuration={500} />
          {cy.false_positive_rate !== null && cy.sensitivity !== null && (
            <ReferenceDot x={cy.false_positive_rate} y={cy.sensitivity} r={5} fill="var(--amber)" stroke="var(--background)" strokeWidth={1.5} />
          )}
        </LineChart>
      </Chart>
      <Legend
        items={[
          { label: "Model", color, shape: "line" },
          { label: "Coin flip", color: "var(--dim)", shape: "dash" },
          { label: "Working threshold", color: "var(--amber)" },
        ]}
      />
    </div>
  );
}

/** Predicted probability against what happened, in bins. On the dashed line means well calibrated. */
export function CalibrationChart({ card }: { card: ModelCard }) {
  const bins = card.metrics.calibration.bins.map((b) => ({ ...b, x: b.mean_predicted, y: b.observed_share }));
  return (
    <div>
      <Chart height={320} label="Calibration: mean predicted probability against observed share">
        <ComposedChart margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <CartesianGrid {...GRID} />
          <XAxis type="number" dataKey="x" {...UNIT} {...AXIS} label={axisLabel("Mean predicted probability", "x")} />
          <YAxis type="number" dataKey="y" {...UNIT} {...AXIS} label={axisLabel("Observed share", "y")} />
          <Tooltip
            cursor={{ stroke: "var(--input)" }}
            content={({ active, payload }) => {
              const p = payload?.find((x) => x.payload && "n" in x.payload)?.payload;
              return active && p ? <Tip title={`Predicted ${p.x.toFixed(2)}`} lines={[`Observed ${p.y.toFixed(2)}`, `${p.n} tests in this bin`]} /> : null;
            }}
          />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--dim)" strokeDasharray="3 3" />
          <Line data={bins} dataKey="y" stroke="var(--data)" strokeWidth={1.5} dot={false} activeDot={false} tooltipType="none" />
          <Scatter
            data={bins}
            fill="var(--data)"
           
            shape={(props: { cx?: number; cy?: number; payload?: { n: number } }) => (
              <circle cx={props.cx} cy={props.cy} r={3 + 1.25 * Math.sqrt(props.payload?.n ?? 1)} fill="var(--data)" stroke="var(--background)" strokeWidth={1} />
            )}
          />
        </ComposedChart>
      </Chart>
      <Legend
        items={[
          { label: "Model, one dot per bin (bigger = more tests)", color: "var(--data)" },
          { label: "Perfect calibration", color: "var(--dim)", shape: "dash" },
        ]}
      />
    </div>
  );
}

/** Log-odds change per one standard deviation, with 95% bootstrap intervals. Associations, not causes. */
export function CoefficientChart({ card, label }: { card: ModelCard; label: (feature: string) => string }) {
  const rows = card.coef_table
    .filter((c) => c.feature !== "(intercept)")
    .map((c) => ({ ...c, name: label(c.feature), err: [c.log_odds - c.ci_low, c.ci_high - c.log_odds] }));
  return (
    <div>
      <Chart height={90 + 34 * rows.length} label="Model coefficients with 95% bootstrap intervals">
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, bottom: 18, left: 8 }} barCategoryGap="28%">
          <CartesianGrid {...GRID} horizontal={false} />
          <XAxis type="number" {...AXIS} domain={["auto", "auto"]} label={axisLabel("Change in log-odds per one standard deviation", "x")} />
          <YAxis type="category" dataKey="name" width={150} {...AXIS} tick={{ fill: "var(--foreground)", fontFamily: "var(--font-plex)", fontSize: 12 }} />
          <Tooltip
            cursor={{ fill: "var(--accent)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload;
              return active && p ? (
                <Tip title={p.name} lines={[`log-odds ${p.log_odds.toFixed(2)} [${p.ci_low.toFixed(2)}, ${p.ci_high.toFixed(2)}]`, `odds ratio ${p.odds_ratio.toFixed(2)}`]} />
              ) : null;
            }}
          />
          <ReferenceLine x={0} stroke="var(--input)" />
          <Bar dataKey="log_odds">
            {rows.map((r) => (
              <Cell key={r.feature} fill={r.log_odds > 0 ? "var(--ext)" : "var(--data)"} />
            ))}
            <ErrorBar dataKey="err" direction="x" width={4} strokeWidth={1} stroke="var(--foreground)" />
          </Bar>
        </BarChart>
      </Chart>
      <Legend
        items={[
          { label: "raises the odds of the positive class", color: "var(--ext)" },
          { label: "lowers them", color: "var(--data)" },
          { label: "95% bootstrap interval", color: "var(--foreground)", shape: "line" },
        ]}
      />
    </div>
  );
}

/** A confusion matrix as real text, not an image. */
export function ConfusionMatrix({ c, title }: { c: Confusion; title: string }) {
  const max = Math.max(c.tn, c.fp, c.fn, c.tp, 1);
  const cell = (value: number, label: string, costly = false) => (
    <div className="relative border border-line p-3">
      <span aria-hidden className={`absolute inset-0 ${costly ? "bg-ext" : "bg-amber"}`} style={{ opacity: 0.04 + 0.26 * (value / max) }} />
      <p className="num relative text-heading font-medium text-foreground">{value}</p>
      <p className="relative text-note text-muted-foreground">{label}</p>
    </div>
  );
  return (
    <figure>
      <figcaption className="text-body text-foreground">{title}</figcaption>
      <div className="mt-2 grid grid-cols-2 gap-px">
        {cell(c.tn, "actual 0, predicted 0")}
        {cell(c.fp, "actual 0, predicted 1", true)}
        {cell(c.fn, "actual 1, predicted 0")}
        {cell(c.tp, "actual 1, predicted 1")}
      </div>
    </figure>
  );
}
