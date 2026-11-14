"use client";

import { Gauge, Orbit, RotateCcw, Wind } from "lucide-react";
import { useMemo, useState } from "react";

import { Field, Pick, Segments, SliderField } from "@/components/console/controls";
import { DataTable, n, type Column } from "@/components/console/data-table";
import { Callout, HeroBand, NoData, Num, OutcomeBadge, Panel, Prose, Quote, Readout, Section, Source, Tag } from "@/components/console/primitives";
import { ScenarioMap } from "@/components/charts/console-charts";
import { EvidenceGroup } from "@/components/console/evidence-group";
import { Dial, Meter } from "@/components/console/viz";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import coolJson from "@/data/model_droplet_cool_flame.json";
import extinctionJson from "@/data/model_droplet_extinction.json";
import solidModelJson from "@/data/model_solid_sustained.json";
import { evidence, flex, panels, solid } from "@/lib/data";
import { capitalise, g, g3 } from "@/lib/format";
import { predict } from "@/lib/model";
import { nearestFlex, nearestSolid, type NearFlex, type NearSolid } from "@/lib/nearest";
import { normalise, R, rank, sensitivity, terms, TERM_KEYS } from "@/lib/ranking";
import { DEFAULT_STATE, FEATURED, gaps as findGaps, MATERIALS, toScenario, YOUR_SCENARIO, type LabState, type MaterialKey } from "@/lib/scenario";
import type { Fuel, ModelCard, TermKey } from "@/lib/types";
import { useUrlState } from "@/lib/use-url-state";

const EXT = extinctionJson as unknown as ModelCard;
const COOL = coolJson as unknown as ModelCard;
const SOLID = solidModelJson as unknown as ModelCard;
const KPA_PER_PSI = 6.894757;
const GRAVITY = [
  { value: "0", label: "0 g (orbit)" },
  { value: "0.16", label: "Lunar, 0.16 g" },
  { value: "0.38", label: "Mars, 0.38 g" },
  { value: "1", label: "Earth, 1 g" },
];
const PARTIAL_G_SOURCES = ["LUCI", "Lunar-g drop-tower centrifuge", "KC-135 partial-gravity flights", "Parabolic-flight wire tests", "FM2"];
const DECIDED = solid.points.filter((p) => p.outcome !== "ambiguous");
const PARTIAL_G = evidence.filter((e) => e.evidence_class === "partial_g" && PARTIAL_G_SOURCES.includes(e.investigation_id));
const URL_DEFAULTS = Object.fromEntries(Object.entries(DEFAULT_STATE).map(([k, v]) => [k, String(v)])) as Record<keyof LabState, string>;
const pc = (v: number | null) => (v === null ? "n/a" : `${(v * 100).toFixed(0)}%`);

const FLEX_COLS: Column<NearFlex>[] = [
  { key: "id", header: "Test", cell: (x) => x.row.test_id, numeric: true },
  { key: "o2", header: "O2, %", numeric: true, cell: (x) => n(x.row.o2_pct, 0) },
  { key: "co2", header: "CO2, %", numeric: true, cell: (x) => n(x.row.co2_pct, 0) },
  { key: "he", header: "He, %", numeric: true, cell: (x) => n(x.row.he_pct, 0) },
  { key: "p", header: "Pressure, kPa", numeric: true, cell: (x) => n(x.row.pressure_kpa, 1) },
  { key: "d0", header: "D0, mm", numeric: true, cell: (x) => n(x.row.d0_mm) },
  { key: "k", header: "K, mm²/s", numeric: true, cell: (x) => n(x.row.burning_rate_mm2_s) },
  { key: "out", header: "Outcome", cell: (x) => <OutcomeBadge outcome={x.row.outcome} /> },
  { key: "cool", header: "Cool flame (caption)", cell: (x) => x.row.cool_flame_label.replace("_", " "), className: "whitespace-nowrap" },
  {
    key: "dist",
    header: "Distance",
    numeric: true,
    cell: (x) => n(x.distance),
    title: "0 = identical conditions. Scaled: 5 points of O2, 50 kPa, 15 points of CO2, 10 of helium, 0.8 mm each count as 1.",
  },
  { key: "src", header: "Source", cell: (x) => <span className="text-note text-muted-foreground">{x.row.source}</span>, className: "min-w-64" },
];

const SOLID_COLS: Column<NearSolid>[] = [
  { key: "inv", header: "Investigation", cell: (x) => <Num>{x.point.investigation_id}</Num>, className: "whitespace-nowrap" },
  { key: "test", header: "Test", cell: (x) => <Num>{x.point.test_no}</Num>, className: "whitespace-nowrap" },
  { key: "mat", header: "Material (as printed)", cell: (x) => <Prose text={x.point.material_verbatim} />, className: "min-w-48" },
  { key: "o2", header: "O2, %", numeric: true, cell: (x) => n(x.point.o2_at_outcome_pct, 1) },
  { key: "p", header: "Pressure, kPa", numeric: true, cell: (x) => n(x.point.pressure_kPa, 1) },
  { key: "flow", header: "Flow, cm/s", numeric: true, cell: (x) => n(x.point.flow_cm_s, 1) },
  { key: "dir", header: "Flow direction", cell: (x) => x.point.flow_direction },
  { key: "out", header: "Outcome", cell: (x) => <Tag tone={x.point.outcome === "sustained" ? "amber" : x.point.outcome === "no_ignition" ? "dim" : "ext"}>{x.point.outcome.replace("_", " ")}</Tag> },
  {
    key: "dist",
    header: "Distance",
    numeric: true,
    cell: (x) => n(x.distance),
    title: "0 = identical conditions. Scaled: 2 points of O2, 30 kPa, and a factor of e in flow each count as 1.",
  },
  { key: "same", header: "Same material", cell: (x) => (x.same_material ? "yes" : <span className="text-amber">no</span>) },
  { key: "quote", header: "What the source says", cell: (x) => <span className="text-note text-muted-foreground"><Prose text={x.point.outcome_quote} /></span>, className: "min-w-64" },
  { key: "src", header: "Source", cell: (x) => <span className="text-note text-muted-foreground"><Prose text={x.point.source_ref} /></span>, className: "min-w-56" },
];

export function Lab() {
  const [q, set, reset] = useUrlState(URL_DEFAULTS);
  const [rawWeights, setRawWeights] = useState<Record<TermKey, number>>({ ...R.weights });
  const s: LabState = useMemo(
    () => ({
      material: (q.material in MATERIALS ? q.material : "pmma") as MaterialKey,
      o2: Number(q.o2), p: Number(q.p), flow: Number(q.flow), g: Number(q.g), co2: Number(q.co2), he: Number(q.he), d0: Number(q.d0),
      hrr: q.hrr in R.hrr_scale_w ? q.hrr : DEFAULT_STATE.hrr,
      volume: Number(q.volume),
    }),
    [q],
  );
  const apply = (next: Partial<LabState>) => set(Object.fromEntries(Object.entries(next).map(([k, v]) => [k, String(v)])) as Partial<typeof URL_DEFAULTS>);

  const m = MATERIALS[s.material];
  const droplet = m.kind === "droplet";
  const po2 = (s.o2 / 100) * s.p;
  const gravityLabel = GRAVITY.find((x) => Number(x.value) === s.g)?.label ?? `${s.g} g`;
  const gaps = useMemo(() => findGaps(s, flex.rows, solid), [s]);
  const nearF = useMemo(() => (droplet ? nearestFlex(flex.rows, m.code as Fuel, s.o2, s.p, s.co2, s.he, s.d0) : []), [droplet, m.code, s]);
  const nearS = useMemo(() => (droplet ? [] : nearestSolid(solid.points, m.code, s.o2, s.p, s.flow)), [droplet, m.code, s]);
  const fuelRows = useMemo(() => flex.rows.filter((r) => r.fuel === m.code), [m.code]);

  // ---- model estimate (droplets in microgravity only)
  const x = { o2_pct: s.o2, pressure_kpa: s.p, o2_partial_kpa: po2, co2_pct: s.co2, he_pct: s.he, d0_mm: s.d0, fuel_heptane: m.code === "Heptane" ? 1 : 0 };
  const out = useMemo(() => (droplet && s.g === 0 ? predict(EXT, x) : null), [droplet, s]); // eslint-disable-line react-hooks/exhaustive-deps
  const cool = useMemo(() => (droplet && s.g === 0 && m.code === "Heptane" ? predict(COOL, x) : null), [droplet, s, m.code]); // eslint-disable-line react-hooks/exhaustive-deps
  const demo = out ? out.extrapolating || gaps.length > 0 : false;
  const em = EXT.metrics;
  const thr = em.youden_threshold;

  // ---- triage score
  const weights = normalise(rawWeights);
  const mine = toScenario(s);
  const t = terms(mine);
  const score = TERM_KEYS.reduce((sum, k) => sum + weights[k] * t.values[k], 0);
  const all = [mine, ...R.presets];
  const order = rank(all, weights);
  const sens = sensitivity(all, weights);
  const disagreement = !droplet && t.values.M_O2 === 0 && nearS.some((x) => x.point.outcome === "sustained") && nearS.length > 0 && Math.min(...nearS.map((x) => x.distance)) < 1;
  const tally = (list: string[]) => {
    const counts = new Map<string, number>();
    for (const o of list) counts.set(o, (counts.get(o) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  };

  return (
    <>
      <Panel
        title="Scenario"
        explainer="Every result below updates as you move a control."
        aside={
          <Button variant="outline" size="sm" className="rounded-sm" onClick={reset}>
            <RotateCcw aria-hidden /> Reset
          </Button>
        }
      >
        <div className="flex flex-wrap gap-1.5">
          {FEATURED.map((f) => (
            <Button key={f.label} variant="outline" size="sm" className="rounded-sm" title={f.note} onClick={() => apply(f.state)}>
              {f.label}
            </Button>
          ))}
        </div>
        <div className="mt-5 grid grid-cols-1 gap-x-8 gap-y-6 md:grid-cols-2">
          <Field label="Fuel or material">
            <Pick label="Fuel or material" value={s.material} onChange={(v) => apply({ material: v as MaterialKey })} options={Object.entries(MATERIALS).map(([value, v]) => ({ value, label: v.label }))} />
          </Field>
          <Field label="Gravity">
            <Segments label="Gravity" value={String(s.g)} onChange={(v) => apply({ g: Number(v) })} options={GRAVITY} />
          </Field>
          <SliderField label="Oxygen, % by volume" min={10} max={60} step={0.5} value={s.o2} onChange={(v) => apply({ o2: v })} format={(v) => `${g(v)}%`} />
          <SliderField label="Pressure, kPa" min={20} max={310} step={0.1} value={s.p} onChange={(v) => apply({ p: Number(v.toFixed(1)) })} format={(v) => `${v.toFixed(1)} kPa`} hint="101.3 kPa = 14.7 psi (sea level). 70.3 kPa = 10.2 psi. 56.5 kPa = 8.2 psi." />
          <SliderField label="Ventilation flow, cm/s" min={0} max={80} step={0.5} value={s.flow} onChange={(v) => apply({ flow: v })} format={(v) => `${g(v)} cm/s`} />
          {droplet && (
            <>
              <SliderField label="Droplet diameter, mm" min={0.5} max={8} step={0.1} value={s.d0} onChange={(v) => apply({ d0: Number(v.toFixed(1)) })} format={(v) => `${v.toFixed(1)} mm`} />
              <SliderField label="CO2 in the atmosphere, %" min={0} max={80} step={5} value={s.co2} onChange={(v) => apply({ co2: v })} format={(v) => `${g(v)}%`} />
              <SliderField label="Helium in the atmosphere, %" min={0} max={80} step={5} value={s.he} onChange={(v) => apply({ he: v })} format={(v) => `${g(v)}%`} />
            </>
          )}
        </div>
      </Panel>

      <HeroBand
        kicker="Oxygen partial pressure"
        value={
          <>
            {po2.toFixed(1)}
            <span className="ml-2 text-heading font-medium text-muted-foreground">kPa</span>
          </>
        }
        dial={{ value: po2 / 65, tick: 21.2 / 65, caption: "mark: sea-level air" }}
        source={`computed from the inputs: ${g(s.o2)}% × ${g(s.p)} kPa. Sea-level air is 21.2 kPa. Dial scale 0 to 65 kPa, the highest in the droplet tests.`}
        readouts={
          <>
            <Readout className="border-0" icon={Gauge} meter={s.p / 310} value={(s.p / KPA_PER_PSI).toFixed(1)} unit="psi" tone="data" label="total pressure" source={`${g(s.p)} kPa = ${(s.p / 101.325).toFixed(2)} atm`} />
            <Readout className="border-0" icon={Wind} meter={s.flow / 80} value={g(s.flow)} unit="cm/s" tone="data" label="ventilation flow" source={s.flow === 0 ? "still gas" : "forced flow past the fuel"} />
            <Readout className="border-0" icon={Orbit} meter={s.g} value={`${g(s.g)} g`} tone={s.g === 0 ? "done" : "disrupt"} label="gravity" source={gravityLabel} />
          </>
        }
      >
        of oxygen for {droplet ? (m.code === "Heptane" ? "an n-heptane droplet" : "a methanol droplet") : m.label} in this atmosphere.
      </HeroBand>

      {(s.g === 0.16 || s.g === 0.38) && (
        <Section title="Partial gravity" explainer="This gravity has never been tested in the repository. Nothing below is scaled or adjusted for it.">
          <NoData title={`No combustion test at ${gravityLabel.split(",")[0]} gravity exists in the PSI repository`} note="Source: official challenge brief: “there is currently no partial-gravity combustion data available in PSI.”">
            Everything below is from microgravity. The closest real evidence for partial gravity is listed next; none of it is a repository dataset.
          </NoData>
          <div className="mt-3">
            <EvidenceGroup entries={PARTIAL_G} label="sourced statements: the nearest real evidence for partial gravity" lead />
          </div>
          <div className="mt-4">
            <Quote>
              <Prose text={panels.partial_gravity_wording} />
            </Quote>
          </div>
        </Section>
      )}
      {s.g === 1 && (
        <NoData title="Normal-gravity tests are not part of this dataset">
          The data here are microgravity experiments. Normal-gravity values appear only where a source quotes one for comparison, so the
          nearest tests below are microgravity tests.
        </NoData>
      )}

      <Section
        title="Nearest real tests"
        explainer={
          droplet
            ? `The eight FLEX ${m.code === "Heptane" ? "n-heptane" : "methanol"} droplet burns closest to this atmosphere and droplet size.`
            : "The eight solid-fuel test points closest to this oxygen level, pressure and flow, same material first."
        }
      >
        <Panel className="mb-4" title="Where the scenario sits among the real tests" explainer={droplet ? "Every FLEX burn of this fuel, by oxygen and pressure. The crosshair is your scenario." : "Every solid-fuel test point with a stated outcome. The crosshair is your scenario."}>
          {droplet ? <ScenarioMap o2={s.o2} pressure={s.p} flexRows={fuelRows} /> : <ScenarioMap o2={s.o2} pressure={s.p} solidPoints={DECIDED} />}
          <Source>{droplet ? `${flex.meta.report}, Table IX. A test with no printed pressure is not drawn.` : "NASA/TM-20210011385 (BASS-II); PSI-99; Olson et al. 2023; ICES-2024-365; ICES-2025-156; NTRS 20240007628. Solid fuels only."}</Source>
        </Panel>
        {droplet ? (
          <>
            <DataTable rows={nearF} columns={FLEX_COLS} rowKey={(x) => x.row.test_id} caption="Nearest FLEX tests" minWidth={1200} maxHeight={380} />
            <Source href={flex.meta.pdf_url}>{`${flex.meta.report}, Table IX; cool-flame column from Appendix B captions.`}</Source>
          </>
        ) : (
          <>
            {nearS.some((x) => !x.same_material) && (
              <p className="mb-2 text-note text-amber">
                Fewer than three {m.label} test points have a stated outcome, so other materials are included and marked.
              </p>
            )}
            <DataTable rows={nearS} columns={SOLID_COLS} rowKey={(x) => x.point.point_id} caption="Nearest solid-fuel test points" minWidth={1500} maxHeight={380} />
            <Source href="https://ntrs.nasa.gov/citations/20210011385">
              BASS-II summary memo NASA/TM-20210011385 (Tables 5.1, 7.1, A.1 to A.6); PSI Saffire tables; ICES-2024-365; NTRS 20240007628. Each row names its own source.
            </Source>
          </>
        )}
      </Section>

      <Section title="Model estimate" explainer="A probability from a small logistic model, shown only where that model passed validation.">
        {s.g !== 0 ? (
          <NoData title="No estimate at this gravity">
            Every model here was trained on microgravity tests only. None is applied to another gravity level.
          </NoData>
        ) : out ? (
          <>
            <div className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2 xl:grid-cols-4">
              <Readout className="border-0" tone={demo ? "dim" : "ext"} value={pc(out.p)} label="estimated chance the visible flame goes out" source={`95% interval ${pc(out.lo)} to ${pc(out.hi)} (cluster bootstrap)${demo ? " · DEMO: extrapolated" : ""}`} />
              <Readout className="border-0" tone="data" value={out.p >= thr ? "above" : "below"} label={`the decision threshold of ${thr.toFixed(2)}`} source="Youden's J threshold on out-of-fold predictions; this console uses it and says so" />
              <Readout className="border-0" tone={out.far_from_data ? "dim" : "done"} value={out.nn_distance.toFixed(2)} label="distance to the nearest training test" source={`typical ${out.train_nn_median.toFixed(2)}; 95% of training tests are within ${out.train_nn_p95.toFixed(2)} of another`} />
              <Readout className="border-0" tone="amber" value={(EXT.headline_auc as number).toFixed(2)} label="headline AUC of this model" source={`worse of grouped CV (${(em.roc_auc as number).toFixed(2)}) and leave-one-fuel-out; false-positive rate ${pc(em.confusion_at_youden.false_positive_rate)}`} />
            </div>
            {demo && (
              <Callout title="DEMO estimate: this scenario is outside what the model has seen" tone="ext" className="mt-4">
                {`Treat the number above as an illustration of the model's shape, not as a prediction. Reasons: ${[
                  ...out.outside_envelope.map((o) => `${o.feature} = ${g(o.value)} is outside the tested ${g3(o.tested_min)} to ${g3(o.tested_max)}`),
                  ...(out.far_from_data ? ["the scenario is farther from every training test than 95% of training tests are from each other"] : []),
                  ...gaps,
                ].join("; ")}.`}
              </Callout>
            )}
            <p className="mt-3 text-note text-muted-foreground">
              “Flame goes out” means the visible flame. It includes radiative extinctions after which a cool flame can keep burning, and it
              does not include disruptions.
            </p>
            {cool && (
              <Callout title="If the visible flame goes out, is the fire out?" tone="ext" className="mt-4" note={`Source: ${flex.meta.report}, Appendix B captions; model card in the Model Lab.`}>
                {`Not necessarily. In ${flex.summary.cool_flame.indicated} of the ${flex.summary.heptane_extinctions} n-heptane tests logged as Extinction, the report describes evidence of cool-flame burning afterwards. ` +
                  (cool.extrapolating || gaps.length > 0
                    ? `This scenario is outside what the exploratory cool-flame model has seen (${[
                        ...cool.outside_envelope.map((o) => `${o.feature} = ${g(o.value)} is outside the ${g3(o.tested_min)} to ${g3(o.tested_max)} covered by the labelled tests`),
                        ...(cool.far_from_data ? ["the scenario is far from every labelled test"] : []),
                        ...gaps,
                      ].join("; ")}), so its output, ${pc(cool.p)}, is a DEMO value and not an estimate.`
                    : `An exploratory model on the ${COOL.n_rows} labelled tests puts the chance of cool-flame evidence for this scenario at ${pc(cool.p)} (95% interval ${pc(cool.lo)} to ${pc(cool.hi)}; grouped-CV AUC ${(COOL.metrics.roc_auc as number).toFixed(2)} with an interval of ${(COOL.metrics.roc_auc_ci[0] as number).toFixed(2)} to ${(COOL.metrics.roc_auc_ci[1] as number).toFixed(2)}, so treat it as a sketch).`)}
              </Callout>
            )}
            <Source href={flex.meta.pdf_url}>Logistic model trained on FLEX Table IX initial conditions only; full metrics in the Model Lab.</Source>
          </>
        ) : (
          <>
            <NoData title="No model estimate for solid materials" note="Why it fails, and every metric, are in the Model Lab. The nearest real tests above are the answer.">
              {`A logistic model was trained on the ${SOLID.n_rows} verified solid-fuel test points exactly as specified, and it failed validation: on test series it had not seen, its AUC is ${(SOLID.metrics.roc_auc as number).toFixed(2)} (95% interval ${(SOLID.metrics.roc_auc_ci[0] as number).toFixed(2)} to ${(SOLID.metrics.roc_auc_ci[1] as number).toFixed(2)}), no better than a coin. Showing its probabilities would be inventing confidence, so none is shown.`}
            </NoData>
            {nearS.length > 0 && (
              <p className="mt-3 text-body text-foreground">
                <span className="text-muted-foreground">What the nearest tests did: </span>
                <Prose text={tally(nearS.map((x) => x.point.outcome)).map(([k, v]) => `${v} ${k.replace("_", " ")}`).join(" · ")} />.{" "}
                <span className="text-muted-foreground">
                  Their distance from your scenario ranges from <Num>{Math.min(...nearS.map((x) => x.distance)).toFixed(2)}</Num> to{" "}
                  <Num>{Math.max(...nearS.map((x) => x.distance)).toFixed(2)}</Num>; a distance above about <Num>2</Num> means a different
                  regime, not a comparable test.
                </span>
              </p>
            )}
          </>
        )}
      </Section>

      {gaps.length > 0 && (
        <NoData title="This scenario is outside the tested envelope" note="The nearest real tests are listed above. Nothing has been filled in by interpolation.">
          {`No experiment in the data was run at these conditions. ${gaps.map(capitalise).join(" · ")}.`}
        </NoData>
      )}

      <Section title="Triage score" explainer="A stated formula for ordering scenarios by how much attention they deserve. It is not a risk rating.">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel className="xl:col-span-2" title="Your scenario">
            <div className="flex items-center gap-5">
              <Dial value={score} tone="amber" size={148} label={`Triage score ${score.toFixed(3)} on a scale of 0 to 1`}>
                <span className="glow num text-heading font-bold text-amber">{score.toFixed(3)}</span>
                <span className="kicker text-dim">of 1</span>
              </Dial>
              <p className="text-body text-foreground">triage score, from 0 to 1</p>
            </div>
            <p className="mt-1 text-note text-muted-foreground">Hazard = Σ weight × term. A design choice, for ordering only.</p>
            {t.flags.map((flag) => (
              <p key={flag} className="mt-2 text-note text-amber">
                Flag: {flag}.
              </p>
            ))}
            <div className="mt-4 space-y-4">
              <Field label="Size of the burning item">
                <Segments label="Size of the burning item" value={s.hrr} onChange={(v) => apply({ hrr: v })} options={Object.keys(R.hrr_scale_w).map((k) => ({ value: k, label: capitalise(k) }))} />
              </Field>
              <Field label="Free volume of the cabin, m³">
                <Input type="number" min={1} max={1000} step={1} value={s.volume} onChange={(e) => apply({ volume: Math.min(1000, Math.max(1, Number(e.target.value) || 1)) })} className="num h-8 w-32 rounded-sm border-input bg-background" aria-label="Free volume of the cabin, cubic metres" />
              </Field>
            </div>
          </Panel>
          <Panel className="xl:col-span-3" title="Term by term" explainer="Each term is between 0 and 1. Its contribution is its weight times its value.">
            <ul>
              {TERM_KEYS.map((k) => (
                <li key={k} className="border-b border-line py-2 last:border-b-0">
                  <div className="grid grid-cols-[1fr_auto] items-baseline gap-x-4 sm:grid-cols-[11rem_1fr_auto]">
                    <span className="text-body text-foreground">{R.term_label[k]}</span>
                    <Meter value={t.values[k]} tone="amber" segments={28} label={`${R.term_label[k]}: ${t.values[k].toFixed(2)}`} className="col-span-2 row-start-2 mt-1 sm:col-span-1 sm:row-start-1 sm:mt-0" />
                    <span className="num text-note text-muted-foreground">
                      {weights[k].toFixed(2)} × <span className="text-foreground">{t.values[k].toFixed(2)}</span> = {(weights[k] * t.values[k]).toFixed(3)}
                    </span>
                  </div>
                  <p className="mt-1 text-note text-muted-foreground">
                    <Prose text={t.why[k]} />
                  </p>
                </li>
              ))}
            </ul>
          </Panel>
        </div>

        {disagreement && (
          <Callout title="The formula and the data disagree here" tone="ext" className="mt-4">
            The oxygen term scores this scenario 0 because its oxygen partial pressure is below the minimum measured at 1 atm, yet a real
            test close to it sustained a flame. A limit measured at one pressure does not transfer to another by partial pressure alone.
            This is why the score is for triage only.
          </Callout>
        )}

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel
            className="xl:col-span-2"
            title="Adjust the weights"
            explainer="They are a design choice. Whatever you type is renormalised to sum to 1."
            aside={
              <Button variant="outline" size="sm" className="rounded-sm" onClick={() => setRawWeights({ ...R.weights })}>
                <RotateCcw aria-hidden /> Defaults
              </Button>
            }
          >
            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
              {TERM_KEYS.map((k) => (
                <div key={k}>
                  <Label htmlFor={`w-${k}`} className="text-note text-muted-foreground">
                    {R.term_label[k]}
                  </Label>
                  <Input id={`w-${k}`} type="number" min={0} max={1} step={0.05} value={rawWeights[k]} onChange={(e) => setRawWeights((w) => ({ ...w, [k]: Math.max(0, Number(e.target.value) || 0) }))} className="num mt-1 h-8 rounded-sm border-input bg-background" />
                </div>
              ))}
            </div>
            <p className="mt-3 text-note text-muted-foreground">
              Defaults: <Prose text={TERM_KEYS.map((k) => `${R.term_label[k]} ${R.weights[k].toFixed(2)}`).join(", ")} />.
            </p>
          </Panel>
          <Panel className="xl:col-span-3" title="Order of scenarios under these weights">
            <ol>
              {order.map(([name, value], i) => (
                <li key={name} className="grid grid-cols-[1.5rem_1fr_auto] items-baseline gap-x-3 border-b border-line py-1.5 last:border-b-0">
                  <span className="num text-note text-dim">{i + 1}</span>
                  <span className={name === YOUR_SCENARIO ? "text-body font-medium text-amber" : "text-body text-foreground"}>{name}</span>
                  <span className="num text-body text-foreground">{value.toFixed(3)}</span>
                </li>
              ))}
            </ol>
            {sens.weight_sensitive ? (
              <Callout title="Ranking is weight-sensitive" tone="ext" className="mt-4" note="Do not read the order as settled. It depends on a choice of weights that no experiment fixes.">
                {`Moving a single weight by 0.10 changes the top three: ${sens.changes.slice(0, 4).map((c) => `${c.change} → ${c.top.join(", ")}`).join("; ")}.`}
              </Callout>
            ) : (
              <Callout title="Top three is stable" tone="data" className="mt-4">
                Moving any single weight by ±0.10 (then renormalising) leaves the top three in the same order.
              </Callout>
            )}
          </Panel>
        </div>
        <Source>Formula, lookup values and their sources: flamefall/ranking.py, exported to the app unchanged. Weights are a design choice, not a measurement.</Source>
      </Section>

      <Section title="What the data says, and what is unknown" explainer="The two lists a reader should leave with.">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Panel title="What the data says">
            <ul className="list-disc space-y-1.5 pl-5 text-body text-muted-foreground marker:text-dim">
              {droplet ? (
                <>
                  <li>
                    <Prose text={`Of the ${nearF.length} nearest FLEX tests, ${nearF.filter((x) => x.row.outcome === "Extinction").length} ended in visible-flame extinction, ${nearF.filter((x) => x.row.outcome === "Disruption").length} in disruption and ${nearF.filter((x) => x.row.outcome === "Completion").length} burned to completion.`} />
                  </li>
                  {m.code === "Heptane" && (
                    <li>
                      <Prose text={`${nearF.filter((x) => x.row.cool_flame_label === "indicated").length} of those carry cool-flame evidence after the visible flame went out.`} />
                    </li>
                  )}
                </>
              ) : (
                <>
                  <li>
                    <Prose text={`${tally(nearS.map((x) => x.point.outcome)).map(([k, v]) => `${v} of the ${nearS.length} nearest test points: ${k.replace("_", " ")}`).join("; ")}.`} />
                  </li>
                  <li>
                    <Prose text={`Oxygen partial pressure here is ${po2.toFixed(1)} kPa. Saffire VI burned fabric and acrylic at about 16.8 kPa (31% O2, 54 kPa).`} />
                  </li>
                </>
              )}
              <li>Smoke from overheated wire insulation can be too fine for a light-scattering detector: see What We Don&apos;t Know.</li>
            </ul>
          </Panel>
          <Panel title="What is unknown">
            <ul className="list-disc space-y-1.5 pl-5 text-body text-muted-foreground marker:text-dim">
              {(gaps.length ? gaps : ["nothing flagged for these inputs: the scenario sits inside the tested ranges"]).map((item) => (
                <li key={item}>
                  <Prose text={`${capitalise(item)}.`} />
                </li>
              ))}
              <li>How any of this changes in partial gravity: no repository dataset exists yet.</li>
            </ul>
          </Panel>
        </div>
      </Section>
    </>
  );
}
