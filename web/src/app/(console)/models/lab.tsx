"use client";

import { Activity, Database, ShieldAlert } from "lucide-react";
import { useMemo, useState } from "react";

import { CalibrationChart, CoefficientChart, ConfusionMatrix, RocChart } from "@/components/charts/model-charts";
import { Field, Pick, Segments } from "@/components/console/controls";
import { DataTable, n, type Column } from "@/components/console/data-table";
import { Callout, HeroBand, KV, Num, Panel, Prose, Readout, Section, Source } from "@/components/console/primitives";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import coolJson from "@/data/model_droplet_cool_flame.json";
import extinctionJson from "@/data/model_droplet_extinction.json";
import solidJson from "@/data/model_solid_sustained.json";
import { flex } from "@/lib/data";
import { capitalise, g, g3 } from "@/lib/format";
import { predict } from "@/lib/model";
import type { ModelCard } from "@/lib/types";
import { useUrlState } from "@/lib/use-url-state";

const CARDS: Record<string, ModelCard> = {
  droplet_extinction: extinctionJson as unknown as ModelCard,
  droplet_cool_flame: coolJson as unknown as ModelCard,
  solid_sustained: solidJson as unknown as ModelCard,
};
const LABELS = [
  { value: "droplet_extinction", label: "Droplets: does the visible flame go out?" },
  { value: "droplet_cool_flame", label: "Droplets: cool-flame evidence (exploratory)" },
  { value: "solid_sustained", label: "Solids: is the flame sustained? (failed)" },
];
const NICE: Record<string, string> = {
  o2_pct: "Oxygen, %", pressure_kpa: "Pressure (log)", o2_partial_kpa: "O2 partial pressure", co2_pct: "CO2, %", he_pct: "Helium, %",
  d0_mm: "Droplet diameter (log)", fuel_heptane: "Fuel is n-heptane", flow_cm_s: "Flow (log)", thickness_mm: "Thickness (log)",
  is_quiescent: "Still gas", "o2_pct x flow_cm_s": "Oxygen × flow",
};
const UNITS: Record<string, string> = { o2_pct: "%", pressure_kpa: "kPa", o2_partial_kpa: "kPa", co2_pct: "%", he_pct: "%", d0_mm: "mm", flow_cm_s: "cm/s", thickness_mm: "mm" };
const QUERY_DEFAULTS: Record<string, number> = { o2_pct: 45, pressure_kpa: 56.5, co2_pct: 0, he_pct: 0, d0_mm: 3, flow_cm_s: 10, thickness_mm: 3 };
const nice = (f: string) => NICE[f] ?? f.replace("=", ": ").replaceAll("_", " ");
const plain = (f: string) => nice(f).replace(" (log)", "");
const f2 = (v: number | null | undefined, digits = 2) => (v === null || v === undefined || Number.isNaN(v) ? "n/a" : v.toFixed(digits));
const pc = (v: number | null | undefined) => (v === null || v === undefined ? "n/a" : `${(v * 100).toFixed(0)}%`);

type GroupRow = ModelCard["metrics"]["per_group"][number];
const GROUP_COLS: Column<GroupRow>[] = [
  { key: "group", header: "Group", sort: (r) => r.group, cell: (r) => <span className="num text-note">{r.group}</span>, className: "min-w-64" },
  { key: "n", header: "Rows", numeric: true, sort: (r) => r.n, cell: (r) => r.n },
  { key: "pos", header: "Positive", numeric: true, sort: (r) => r.positives, cell: (r) => r.positives },
  { key: "auc", header: "AUC", numeric: true, sort: (r) => r.auc, cell: (r) => n(r.auc), title: "Blank when the group has only one outcome: AUC is then undefined." },
  { key: "pred", header: "Mean predicted", numeric: true, sort: (r) => r.mean_predicted, cell: (r) => n(r.mean_predicted) },
  { key: "obs", header: "Observed share", numeric: true, sort: (r) => r.observed_share, cell: (r) => n(r.observed_share) },
];

function Query({ card, failed }: { card: ModelCard; failed: boolean }) {
  const inputs = card.continuous.filter((c) => c !== "o2_partial_kpa");
  const [values, setValues] = useState<Record<string, number>>(() => Object.fromEntries(inputs.map((c) => [c, QUERY_DEFAULTS[c] ?? 1])));
  const [flags, setFlags] = useState<Record<string, boolean>>(() => Object.fromEntries(card.binary.map((c) => [c, true])));
  const [cats, setCats] = useState<Record<string, string>>(() => Object.fromEntries(Object.entries(card.categorical).map(([c, list]) => [c, list.find((x) => x !== "rare") ?? list[0]])));

  const out = useMemo(() => {
    const x: Record<string, number | string> = { ...values, ...cats };
    if (card.continuous.includes("o2_partial_kpa")) x.o2_partial_kpa = ((values.o2_pct ?? 0) / 100) * (values.pressure_kpa ?? 0);
    for (const c of card.binary) x[c] = flags[c] ? 1 : 0;
    return predict(card, x);
  }, [card, values, flags, cats]);

  const why = [
    ...out.outside_envelope.map((o) => `${plain(o.feature)} ${g(o.value)} is outside the tested ${g3(o.tested_min)} to ${g3(o.tested_max)}`),
    ...(out.far_from_data ? [`distance to the nearest training row is ${out.nn_distance.toFixed(2)}, beyond the ${out.train_nn_p95.toFixed(2)} that covers 95% of training rows`] : []),
  ];

  return (
    <Panel title="Try a query" explainer="It starts outside the envelope on purpose.">
      <div className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
        {inputs.map((c) => (
          <div key={c}>
            <Label htmlFor={`q-${card.name}-${c}`} className="text-note text-muted-foreground">
              {plain(c)}
              {UNITS[c] && !plain(c).includes(UNITS[c]) ? `, ${UNITS[c]}` : ""}
            </Label>
            <Input
              id={`q-${card.name}-${c}`}
              type="number"
              step="any"
              min={card.log_features.includes(c) ? 0.01 : 0}
              value={values[c]}
              onChange={(e) => setValues((v) => ({ ...v, [c]: Math.max(card.log_features.includes(c) ? 0.01 : 0, Number(e.target.value) || 0) }))}
              className="num mt-1 h-8 rounded-sm border-input bg-background"
            />
          </div>
        ))}
        {card.binary.map((c) => (
          <div key={c} className="flex items-end gap-2 pb-1.5">
            <Switch id={`q-${card.name}-${c}`} checked={flags[c]} onCheckedChange={(v) => setFlags((f) => ({ ...f, [c]: v }))} />
            <Label htmlFor={`q-${card.name}-${c}`} className="text-body text-foreground">
              {nice(c)}
            </Label>
          </div>
        ))}
        {Object.entries(card.categorical).map(([c, options]) => (
          <Field key={c} label={capitalise(c.replaceAll("_", " "))} className="col-span-2 sm:col-span-1">
            <Pick label={c} value={cats[c]} onChange={(v) => setCats((s) => ({ ...s, [c]: v }))} options={options.filter((x) => x !== "rare").map((x) => ({ value: x, label: x }))} />
          </Field>
        ))}
      </div>
      {out.extrapolating ? (
        <Callout title="Distance-to-data warning: this query is an extrapolation" tone="ext" className="mt-4">
          {`${capitalise(why.join("; "))}. Any output is a DEMO value, not an estimate to act on.`}
        </Callout>
      ) : (
        <Callout title="Inside the training envelope" tone="data" className="mt-4">
          {`Distance to the nearest training row is ${out.nn_distance.toFixed(2)} (95% of training rows are within ${out.train_nn_p95.toFixed(2)} of another).`}
        </Callout>
      )}
      <p className="mt-3 text-body text-foreground" aria-live="polite">
        {failed ? (
          <span className="text-muted-foreground">No probability is shown for this model because it failed validation.</span>
        ) : (
          <>
            Model output: <Num className="text-panel text-amber">{pc(out.p)}</Num>{" "}
            <span className="text-muted-foreground">
              (95% interval <Num>{pc(out.lo)}</Num> to <Num>{pc(out.hi)}</Num>)
            </span>
            {out.extrapolating && <span className="num ml-2 text-ext">DEMO</span>}
          </>
        )}
      </p>
      <p className="mt-1 text-note text-muted-foreground">
        Nearest training rows: <Prose text={out.nearest.slice(0, 4).map((r) => `${r.row_id} (${r.distance.toFixed(2)})`).join(", ")} />
      </p>
    </Panel>
  );
}

export function ModelLab() {
  const [q, set] = useUrlState({ model: "droplet_extinction" });
  const name = q.model in CARDS ? q.model : "droplet_extinction";
  const r = CARDS[name];
  const m = r.metrics;
  const lomo = r.leave_one_material_out;
  const cy = m.confusion_at_youden;
  const failed = r.headline_auc !== null && r.headline_auc < 0.6;
  const isDroplet = name.startsWith("droplet");
  const stress = isDroplet ? "leave-one-fuel-out" : "leave-one-material-out";
  const sens90 = m.burning_sensitivity_at_90_specificity;
  const caveats = [
    "These are associations in the tests that were run, not causes.",
    "Gas fractions sum to one, and oxygen fraction, pressure and oxygen partial pressure are tied together, so their effects cannot be separated cleanly.",
    ...(isDroplet ? [`Helium appears in only ${flex.summary.he_tests} tests, run at their own oxygen levels and pressures: its bar is not evidence that helium suppresses or sustains a flame.`] : []),
  ];

  return (
    <>
      <Panel title="Model">
        <Segments label="Model" value={name} onChange={(v) => set({ model: v })} options={LABELS} />
        <p className="mt-3 text-note text-muted-foreground">
          Positive class: <Prose text={r.target_label} />.
        </p>
      </Panel>

      {failed && (
        <Callout
          title="This model failed validation and is not used anywhere in the console"
          tone="ext"
          note="Why: each test series has its own oxygen limit (13.5% for a rod in concurrent flow, about 17% for fabric, 17.5% for a rod in opposed flow), extinction happens at both low and high flow, and most recorded extinctions are given as fan settings with no velocity. A single straight boundary cannot carry over from one series to another."
        >
          {`On test series it had not seen, it ranks a sustained flame above an extinguished one only ${pc(m.roc_auc)} of the time: no better than a coin. The Scenario Lab therefore shows the nearest real tests for solid materials and no probability.`}
        </Callout>
      )}

      <HeroBand
        key={name}
        kicker={`Headline AUC · ${r.headline_is === "leave-one-material-out" ? stress : r.headline_is}`}
        value={f2(r.headline_auc)}
        dial={{ value: r.headline_auc ?? 0, tick: 0.5, caption: "mark: coin flip" }}
        tone={failed ? "ext" : "amber"}
        source={`scripts/train_models.py → data/models/${name}.json; fold membership in data/cv_splits.json`}
        readouts={
          <>
            <Readout className="border-0" icon={Activity} meter={m.roc_auc ?? 0} tone="data" value={f2(m.roc_auc)} label="grouped-CV ROC-AUC" source={`95% interval ${f2(m.roc_auc_ci[0])} to ${f2(m.roc_auc_ci[1])} · cluster bootstrap over ${r.n_split_groups} groups`} />
            <Readout className="border-0" icon={ShieldAlert} meter={cy.false_positive_rate ?? 0} tone="ext" value={pc(cy.false_positive_rate)} label="false-positive rate at the working threshold" source={`${cy.fp} of ${cy.fp + cy.tn} negatives called positive at threshold ${cy.threshold.toFixed(2)} (Youden's J)`} />
            <Readout className="border-0" icon={Database} meter={r.positive_share} tone="done" value={r.n_rows} label="rows after exclusions" source={`${r.n_positive} positive (${pc(r.positive_share)}) · ${r.n_groups} groups · class weights ${r.class_weight_balanced ? "balanced" : "not needed"}`} />
          </>
        }
      >
        is the worse of grouped cross-validation (<Num>{f2(m.roc_auc)}</Num>) and the {stress} stress test (<Num>{f2(lomo.pooled_auc)}</Num>). 0.5 is a
        coin flip; 1 is perfect.
      </HeroBand>

      <Section title="Can it tell the two outcomes apart, and what does it get wrong?" explainer="Every point was scored by a model that never saw its group.">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Panel title="ROC curve, out-of-fold predictions only">
            <RocChart card={r} failed={failed} />
            <KV
              className="mt-4"
              rows={[
                ["PR-AUC", <Num key="a">{f2(m.pr_auc)}</Num>],
                ["Brier score", <Num key="b">{f2(m.brier, 3)}</Num>],
                ["Majority-class accuracy", <span key="c"><Num>{pc(m.baseline_majority_accuracy)}</Num> <span className="text-muted-foreground">(the bar to beat)</span></span>],
                [`Sensitivity for “${r.burning_label}” at 90% specificity`, <Num key="d">{pc(sens90.sensitivity)}</Num>],
                ["Row-wise CV AUC", <span key="e"><Num>{f2(m.rowwise_cv_auc_for_comparison_only)}</Num> <span className="text-muted-foreground">(leaky; shown only for contrast)</span></span>],
              ]}
            />
          </Panel>
          <Panel title="Confusion matrices">
            <div className="space-y-4">
              <ConfusionMatrix c={m["confusion_at_0.5"]} title="Threshold 0.50" />
              <ConfusionMatrix c={cy} title={`Threshold ${cy.threshold.toFixed(2)} (Youden's J, used by the console)`} />
            </div>
            {name === "droplet_extinction" && (
              <p className="mt-3 text-note text-muted-foreground">
                The costly error is top right: <Num>{cy.fp}</Num> tests where the flame did not go out but the model said it would. A model like
                this must not be relied on by itself for a fire-protection decision.
              </p>
            )}
          </Panel>
        </div>
        <Source>{`Pooled out-of-fold predictions, outer GroupKFold with 5 folds; inner GroupKFold with 3 folds chooses C from [${r.C_grid.join(", ")}] (chosen for the final fit: ${r.C_final}).`}</Source>
      </Section>

      <Section title="Are the probabilities honest, and does it hold up group by group?" explainer="On the dashed line means well calibrated. A blank AUC means the group has only one outcome.">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Panel title="Calibration, in ten bins">
            <CalibrationChart card={r} />
            <p className="mt-3 text-note text-muted-foreground">
              Calibration slope <Num>{f2(m.calibration.slope)}</Num> (1 is ideal; below 1 means over-confident), intercept{" "}
              <Num>{f2(m.calibration.intercept)}</Num>. Bin sizes are small; read the shape, not single points.
            </p>
          </Panel>
          <Panel title={`Per group, and the ${stress} stress test`}>
            <DataTable rows={m.per_group} columns={GROUP_COLS} rowKey={(row) => row.group} caption="Out-of-fold results per group" maxHeight={250} minWidth={640} />
            <p className="mt-4 text-body text-foreground">Stress test: train on the others, test on the one left out</p>
            <ul className="mt-1">
              {lomo.per_material.map((row) => (
                <li key={row.material} className="grid grid-cols-[1fr_auto_auto] gap-x-4 border-b border-line py-1.5 text-body last:border-b-0">
                  <span className="text-foreground">{row.material}</span>
                  <span className="num text-muted-foreground">{row.positives} of {row.n} positive</span>
                  <span className="num text-foreground">AUC {f2(row.auc)}</span>
                  {row.note && <span className="col-span-3 text-note text-muted-foreground">{row.note}</span>}
                </li>
              ))}
            </ul>
          </Panel>
        </div>
        <Source>Out-of-fold predictions per group; the stress test is reported separately and never averaged into the grouped-CV figure.</Source>
      </Section>

      <Section title="What moved the prediction?" explainer="Each bar is a change in log-odds for a one-standard-deviation increase, with a 95% bootstrap interval.">
        <Panel>
          <CoefficientChart card={r} label={nice} />
        </Panel>
        <Callout title="How to read this chart" tone="data" className="mt-4">
          {caveats.join(" ")}
        </Callout>
        <Source>{`Final model refitted on all ${r.n_rows} rows; intervals from ${r.bootstrap.n} cluster-bootstrap refits.`}</Source>
      </Section>

      <Section title="Where does the model stop?" explainer="The ranges it was trained on, and a live check of how far any query sits from that data.">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel className="xl:col-span-2" title="Training-data envelope">
            <ul>
              {Object.entries(r.envelope).map(([k, [lo, hi]]) => (
                <li key={k} className="grid grid-cols-[1fr_auto] gap-x-4 border-b border-line py-1.5 text-body last:border-b-0">
                  <span className="text-muted-foreground">{plain(k)}</span>
                  <span className="num text-foreground">
                    {lo.toFixed(2)} to {hi.toFixed(2)} {UNITS[k] ?? ""}
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-note text-muted-foreground">
              Nearest-neighbour distance between training rows: median <Num>{r.distance.train_nn_median.toFixed(2)}</Num>, 95th percentile{" "}
              <Num>{r.distance.train_nn_p95.toFixed(2)}</Num> (standardised units).
            </p>
          </Panel>
          <div className="xl:col-span-3">
            <Query key={name} card={r} failed={failed} />
          </div>
        </div>
      </Section>

      <Section title="How it was built" explainer="The protocol, the features left out, and the features added with their written reason.">
        <Accordion className="border border-line bg-surface">
          <AccordionItem value="protocol" className="px-4">
            <AccordionTrigger className="rounded-sm py-2.5 hover:no-underline">
              <span className="text-body font-normal text-muted-foreground">
                <span className="num mr-2 text-panel font-medium text-amber">{Object.keys(r.dropped_features).length + Object.keys(r.added_features).length}</span>
                feature decisions and the full protocol
              </span>
            </AccordionTrigger>
            <AccordionContent>
        <div className="grid grid-cols-1 gap-4 pb-2 xl:grid-cols-3">
          <Panel title="Protocol">
            <ul className="list-disc space-y-1.5 pl-5 text-body text-muted-foreground marker:text-dim">
              <li><Prose text={`Model: L2-penalised logistic regression (lbfgs, up to 5,000 iterations); C chosen from [${r.C_grid.join(", ")}] by inner grouped CV.`} /></li>
              <li><Prose text={`Validation: outer grouped 5-fold. A group (${isDroplet ? "a tested atmosphere" : "an investigation or test series"}) is never split between training and test. Folds are fixed by seed 42 and saved.`} /></li>
              <li>No leakage: burning rate, burn time, extinction diameter, heat release and spread rate are outcomes and are never inputs. Medians, means and standard deviations are learned on the training fold only.</li>
              <li>{`Headline: the worse of grouped-CV AUC and the ${stress} stress test.`}</li>
              {r.notes.map((note) => (
                <li key={note}><Prose text={note} /></li>
              ))}
            </ul>
          </Panel>
          <Panel title="Specified features not used, and why">
            <ul className="space-y-1.5 text-body text-muted-foreground">
              {Object.entries(r.dropped_features).map(([k, v]) => (
                <li key={k}><Num className="text-foreground">{k}</Num>: {v}</li>
              ))}
            </ul>
          </Panel>
          <Panel title="Features added to the specified list, with the reason">
            <ul className="space-y-1.5 text-body text-muted-foreground">
              {Object.keys(r.added_features).length ? Object.entries(r.added_features).map(([k, v]) => <li key={k}><Num className="text-foreground">{k}</Num>: <Prose text={v} /></li>) : <li>None.</li>}
            </ul>
          </Panel>
        </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
        {r.sensitivity_without_disruption && (
          <Callout title="Sensitivity check: leave the disrupted tests out" tone="data" className="mt-4">
            {`Refitted on Extinction against Completion only (${r.sensitivity_without_disruption.n_rows} rows), grouped-CV AUC is ${r.sensitivity_without_disruption.roc_auc.toFixed(2)} (95% interval ${r.sensitivity_without_disruption.roc_auc_ci[0].toFixed(2)} to ${r.sensitivity_without_disruption.roc_auc_ci[1].toFixed(2)}). Disruption is never counted as extinction in either version; the main model simply keeps those rows as “did not extinguish”.`}
          </Callout>
        )}
        <Source>Research specification §7.3, adapted where the data forced it; every adaptation is listed in DECISIONS.md in the repository.</Source>
      </Section>
    </>
  );
}
