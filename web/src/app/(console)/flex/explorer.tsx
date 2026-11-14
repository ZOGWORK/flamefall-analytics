"use client";

import { Download, RotateCcw } from "lucide-react";
import { useMemo } from "react";

import { AXIS_LABEL, D2Chart, MixChart, RateChart, ShareChart, type RateColumn } from "@/components/charts/flex-charts";
import { OutcomeStrip } from "@/components/charts/outcome-strip";
import { Chips, Field, Pick, RangeField, Segments } from "@/components/console/controls";
import { DataTable, n, type Column } from "@/components/console/data-table";
import { Callout, KV, Kicker, NoData, Num, OutcomeBadge, Panel, Quote, Readout, Section, Source, Tag } from "@/components/console/primitives";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { flex, TABLE_SOURCE } from "@/lib/data";
import { fmt, fuelName, pct } from "@/lib/format";
import { d2Line, nearestTests, wilson, type GasColumn } from "@/lib/stats";
import type { FlexRow, Outcome } from "@/lib/types";
import { list, range, useUrlState } from "@/lib/use-url-state";

const ROWS = flex.rows;
const S = flex.summary;
const REPORT = flex.meta.report;
const O2: [number, number] = [Math.floor(S.ranges.o2[0] * 100), Math.ceil(S.ranges.o2[1] * 100)];
const P: [number, number] = [0.65, 3.1];
const FAMILY: Record<string, string> = Object.fromEntries(
  flex.families.map((f) => [f.startsWith("Air") ? "air" : f.startsWith("CO2") ? "co2" : f.startsWith("He") ? "he" : "n2", f]),
);
const FAMILY_OPTIONS = Object.entries(FAMILY).map(([value, label]) => ({ value, label }));
const DEFAULTS = {
  fuel: "Methanol,Heptane",
  o2: `${O2[0]}~${O2[1]}`,
  p: `${P[0]}~${P[1]}`,
  atm: Object.keys(FAMILY).join(","),
  out: flex.outcomes.join(","),
  x: "o2_pct",
  view: "share",
  kx: "d0_mm",
  test: "",
};
const COOL: Record<string, [string, "amber" | "data" | "dim"]> = {
  indicated: ["cool-flame evidence reported", "amber"],
  not_indicated: ["no cool-flame evidence", "data"],
  unclear: ["cool flame unclear", "dim"],
};

const COLUMNS: Column<FlexRow>[] = [
  { key: "test_id", header: "Test", sort: (r) => r.test_no, cell: (r) => <Num>{r.test_id}</Num>, className: "whitespace-nowrap" },
  { key: "date", header: "Date", sort: (r) => r.date_iso, cell: (r) => <Num>{r.date_iso}</Num>, className: "whitespace-nowrap" },
  { key: "fuel", header: "Fuel", sort: (r) => r.fuel, cell: (r) => fuelName(r.fuel), className: "whitespace-nowrap" },
  { key: "p", header: "Pressure, mmHg", numeric: true, sort: (r) => r.pressure_mmhg, cell: (r) => n(r.pressure_mmhg, 1) },
  { key: "o2", header: "O2", numeric: true, sort: (r) => r.o2, cell: (r) => n(r.o2) },
  { key: "n2", header: "N2", numeric: true, sort: (r) => r.n2, cell: (r) => n(r.n2) },
  { key: "co2", header: "CO2", numeric: true, sort: (r) => r.co2, cell: (r) => n(r.co2) },
  { key: "he", header: "He", numeric: true, sort: (r) => r.he, cell: (r) => n(r.he) },
  { key: "d0", header: "D0, mm", numeric: true, sort: (r) => r.d0_mm, cell: (r) => n(r.d0_mm) },
  {
    key: "dend",
    header: "End diameter, mm",
    numeric: true,
    sort: (r) => r.extinction_diameter_mm,
    cell: (r) => n(r.extinction_diameter_mm),
    title: `The value Table IX prints in its extinction-diameter column. It is an extinction diameter only when the outcome is Extinction; ${flex.printed_end_diameter.Disruption} Disruption and ${flex.printed_end_diameter.Completion} Completion rows also print one.`,
  },
  { key: "k", header: "K, mm²/s", numeric: true, sort: (r) => r.burning_rate_mm2_s, cell: (r) => n(r.burning_rate_mm2_s) },
  { key: "t", header: "Burn time, s", numeric: true, sort: (r) => r.burn_time_s, cell: (r) => n(r.burn_time_s, 1) },
  { key: "outcome", header: "Outcome", sort: (r) => r.outcome, cell: (r) => <OutcomeBadge outcome={r.outcome} /> },
  {
    key: "cool",
    header: "Cool flame (caption)",
    sort: (r) => r.cool_flame_label,
    cell: (r) => (r.cool_flame_label ? r.cool_flame_label.replace("_", " ") : ""),
    title: "From the Appendix B caption; blank means the caption is silent.",
    className: "whitespace-nowrap",
  },
  { key: "support", header: "Support", sort: (r) => r.support, cell: (r) => r.support.replace("_", " "), className: "whitespace-nowrap" },
  { key: "notes", header: "Cleaning note", cell: (r) => r.notes, className: "min-w-56 text-muted-foreground" },
  { key: "source", header: "Source", cell: (r) => <span className="text-note text-muted-foreground">{r.source}</span>, className: "min-w-72" },
];

function csv(rows: FlexRow[]): string {
  const cols: (keyof FlexRow)[] = [
    "test_no", "test_id", "cir_id", "date_iso", "fuel", "pressure_mmhg", "o2", "n2", "co2", "he", "d0_mm",
    "extinction_diameter_mm", "burning_rate_mm2_s", "burn_time_s", "outcome", "cool_flame_label", "support", "notes", "source",
  ];
  const cell = (v: unknown) => (v === null || v === undefined ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  return [cols.join(","), ...rows.map((r) => cols.map((c) => cell(r[c])).join(","))].join("\n");
}

function download(rows: FlexRow[]) {
  const url = URL.createObjectURL(new Blob([csv(rows)], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = "flex_table_ix_filtered.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export function Explorer() {
  const [q, set, reset] = useUrlState(DEFAULTS);
  const fuels = list(q.fuel);
  const o2 = range(q.o2);
  const pressure = range(q.p);
  const atm = list(q.atm);
  const outcomes = list(q.out);
  const xcol = q.x as GasColumn;
  const kx = q.kx as RateColumn;
  const fullPressure = pressure[0] <= P[0] && pressure[1] >= P[1];

  const d = useMemo(() => {
    const families = new Set(atm.map((a) => FAMILY[a]));
    return ROWS.filter(
      (r) =>
        fuels.includes(r.fuel) &&
        r.o2_pct >= o2[0] &&
        r.o2_pct <= o2[1] &&
        // FLEX-114 has no pressure in the source: it is kept only when the pressure filter is at its full range
        (r.pressure_atm === null ? fullPressure : r.pressure_atm >= pressure[0] && r.pressure_atm <= pressure[1]) &&
        families.has(r.atmosphere) &&
        outcomes.includes(r.outcome),
    );
    // the filter values are strings in the address bar: depend on those
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q.fuel, q.o2, q.p, q.atm, q.out]);

  const filters = (
    <Panel
      title="Filter the tests"
      aside={
        <Button variant="outline" size="sm" onClick={reset} className="rounded-sm">
          <RotateCcw aria-hidden /> Reset
        </Button>
      }
    >
      <div className="grid grid-cols-1 gap-x-8 gap-y-5 md:grid-cols-2 xl:grid-cols-3">
        <Field label="Fuel">
          <Chips label="Fuel" value={fuels} onChange={(v) => set({ fuel: v.join(",") })} options={[{ value: "Methanol", label: "Methanol" }, { value: "Heptane", label: "n-Heptane" }]} />
        </Field>
        <RangeField label="Ambient O2, mol %" min={O2[0]} max={O2[1]} step={1} value={o2} onChange={(v) => set({ o2: v.join("~") })} format={(v) => `${v}%`} />
        <RangeField
          label="Ambient pressure, atm"
          min={P[0]}
          max={P[1]}
          step={0.05}
          value={pressure}
          onChange={(v) => set({ p: v.map((x) => Number(x.toFixed(2))).join("~") })}
          format={(v) => v.toFixed(2)}
          hint="FLEX-114 has no pressure in the source and is kept only at the full range."
        />
        <Field label="Diluent" className="xl:col-span-2">
          <Chips label="Diluent" value={atm} onChange={(v) => set({ atm: v.join(",") })} options={FAMILY_OPTIONS} />
        </Field>
        <Field label="Outcome">
          <Chips label="Outcome" value={outcomes} onChange={(v) => set({ out: v.join(",") })} options={flex.outcomes.map((o) => ({ value: o, label: o }))} />
        </Field>
      </div>
    </Panel>
  );

  if (d.length === 0) {
    const pool = fuels.length ? ROWS.filter((r) => fuels.includes(r.fuel)) : ROWS;
    const near = nearestTests(pool, (o2[0] + o2[1]) / 2, (pressure[0] + pressure[1]) / 2);
    return (
      <>
        {filters}
        <NoData title="No FLEX test matches these filters">
          Nothing in Table IX was run at this combination. The closest tests by oxygen and pressure are listed below so you can see what
          was actually tried.
        </NoData>
        <div>
          <DataTable rows={near} columns={COLUMNS.filter((c) => ["test_id", "fuel", "o2", "co2", "he", "p", "d0", "outcome", "source"].includes(c.key))} rowKey={(r) => r.test_id} caption="Nearest FLEX tests by oxygen and pressure" minWidth={900} />
          <Source href={flex.meta.pdf_url}>{`${TABLE_SOURCE}. A test with no printed pressure is not ranked.`}</Source>
        </div>
      </>
    );
  }

  const total = d.length;
  const k = d.reduce((s, r) => s + r.extinguished, 0);
  const [lo, hi] = wilson(k, total);
  const counts = { Extinction: k, Disruption: 0, Completion: 0 } as Record<Outcome, number>;
  for (const r of d) if (r.outcome !== "Extinction") counts[r.outcome] += 1;
  const heTests = d.filter((r) => r.he > 0).length;
  const drawn = d.filter((r) => r.burning_rate_mm2_s !== null && r[kx] !== null).length;
  const row = d.find((r) => r.test_id === q.test) ?? d[0];
  const line = d2Line(row, flex.meta.end_marker_extinction, flex.meta.end_marker_other);
  const missing = ([["d0_mm", "initial diameter"], ["burning_rate_mm2_s", "burning rate"], ["burn_time_s", "burn time"]] as const)
    .filter(([col]) => row[col] === null)
    .map(([, label]) => label);
  const cool = COOL[row.cool_flame_label];

  return (
    <>
      {filters}

      <section className="grid grid-cols-1 gap-px border border-line bg-line xl:grid-cols-12">
        <div className="bg-surface p-4 sm:p-5 xl:col-span-5">
          <Kicker className="text-dim">Ended in extinction</Kicker>
          <p className="num mt-2 text-[clamp(3.5rem,9vw,6rem)] leading-none font-bold tracking-tight text-ext">{pct(k / total)}</p>
          <p className="mt-3 text-body text-foreground">
            <Num>{k}</Num> of <Num>{total}</Num> matching tests ended with the visible flame going out.
          </p>
          <p className="mt-1 text-note text-muted-foreground">
            95% interval <Num>{pct(lo, 0)}</Num>–<Num>{pct(hi, 0)}</Num> (Wilson). Source: {TABLE_SOURCE}.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-px bg-line sm:grid-cols-3 xl:col-span-7">
          <Readout className="border-0" value={total} unit={`of ${ROWS.length}`} label="tests match the filters" source={TABLE_SOURCE} tone="amber" />
          <Readout className="border-0" value={counts.Disruption} label="ended in Disruption (not an extinction)" source={`${REPORT} §5.2: may reflect needle contamination`} tone="disrupt" />
          <Readout className="border-0" value={counts.Completion} label="burned to Completion" source={TABLE_SOURCE} tone="done" />
        </div>
      </section>

      <Section
        title="Did the flame go out?"
        explainer="Share of tests that ended in Extinction at each tested gas level. Bigger dots mean more tests; bars are 95% intervals."
      >
        <Panel>
          <Tabs value={q.view} onValueChange={(v) => set({ view: v as string })}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <TabsList className="h-8 max-w-full rounded-sm">
                <TabsTrigger value="share" className="rounded-sm px-3">Share + trend</TabsTrigger>
                <TabsTrigger value="mix" className="rounded-sm px-3">All three outcomes</TabsTrigger>
              </TabsList>
              <Segments label="Compare against" value={xcol} onChange={(v) => set({ x: v })} options={[{ value: "o2_pct", label: "Oxygen" }, { value: "co2_pct", label: "Carbon dioxide" }, { value: "he_pct", label: "Helium" }]} />
            </div>
            <TabsContent value="share" className="mt-4">
              <ShareChart rows={d} xcol={xcol} />
            </TabsContent>
            <TabsContent value="mix" className="mt-4">
              <MixChart rows={d} xcol={xcol} />
            </TabsContent>
          </Tabs>
          <Source href={flex.meta.pdf_url}>
            {`${TABLE_SOURCE}. The dashed trend is a one-variable logistic fit per fuel; pressure, droplet size and the other gases also vary between tests, so it describes these tests and is not a causal effect.`}
          </Source>
        </Panel>
        {xcol === "he_pct" && (
          <Callout title="Helium: effect unclear" tone="data" className="mt-4">
            {`Only ${heTests} of the filtered tests contain helium (${S.he_tests} in the whole table), and they were run at different oxygen levels and pressures than the CO2 series. Treat the helium trend as uncertain, not as evidence that helium suppresses or sustains a flame.`}
          </Callout>
        )}
        {xcol === "co2_pct" && (
          <Callout title="CO2 and helium were never combined" tone="data" className="mt-4">
            No FLEX test contains both diluents, so nothing here says what a CO2 + He mixture would do.
          </Callout>
        )}
      </Section>

      <Section
        title="How fast did the droplet burn, and how did the tests end?"
        explainer="No single burning rate per fuel: it moves with droplet size, oxygen and diluent."
      >
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel
            className="xl:col-span-3"
            title="Average burning-rate constant K, one point per test"
            aside={
              <div className="w-64 max-w-full">
                <Pick label="Plot K against" value={kx} onChange={(v) => set({ kx: v })} options={Object.entries(AXIS_LABEL).map(([value, label]) => ({ value, label }))} />
              </div>
            }
          >
            <RateChart rows={d} xcol={kx} />
            <Source href={flex.meta.pdf_url}>
              {`${TABLE_SOURCE}. K is the report's linear fit of D² against time from shortly after ignition to extinction. ${drawn} of ${total} filtered tests drawn; the rest have no K or no x value in the source and are left out, not set to zero.`}
            </Source>
          </Panel>
          <Panel className="xl:col-span-2" title="How the matching tests ended">
            <OutcomeStrip counts={counts} height={36} />
            <Source href={flex.meta.pdf_url}>
              {`${TABLE_SOURCE}. Disruption is not Extinction: ${REPORT} §5.2 links minor disruptions to needle coating contamination.`}
            </Source>
          </Panel>
        </div>
      </Section>

      <Section
        title="One test, start to finish"
        explainer="The line is rebuilt from three printed numbers. It is not the measured trace."
      >
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel className="xl:col-span-3" aside={<div className="w-40"><Pick mono label="Test" value={row.test_id} onChange={(v) => set({ test: v })} options={d.map((r) => ({ value: r.test_id, label: r.test_id }))} /></div>} title={`${row.test_id} · ${fuelName(row.fuel)}`}>
            {line ? (
              <D2Chart line={line} row={row} />
            ) : (
              <NoData title={`${row.test_id} cannot be drawn`}>
                {`Table IX prints no ${missing.join(", ")} for this test, and a missing value is not filled in.`}
              </NoData>
            )}
            <Source href={flex.meta.pdf_url}>
              {`${row.source}${row.caption_figure !== null ? `; measured trace: Appendix B, Figure ${row.caption_figure}` : ""}. Line = D0² − K·t over the printed burn time (d²-law reconstruction).`}
            </Source>
          </Panel>
          <Panel className="xl:col-span-2" title="As printed">
            <p className="flex flex-wrap gap-1.5">
              <OutcomeBadge outcome={row.outcome} />
              {cool && <Tag tone={cool[1]}>{cool[0]}</Tag>}
              {row.support && <Tag>{row.support.replace("_", " ")}</Tag>}
            </p>
            <KV
              className="mt-3"
              rows={[
                ["Date", <Num key="d">{row.date_iso}</Num>],
                ["Atmosphere", <Num key="a">{`O2 ${row.o2.toFixed(2)} · N2 ${row.n2.toFixed(2)} · CO2 ${row.co2.toFixed(2)} · He ${row.he.toFixed(2)}`}</Num>],
                ["Pressure", <Num key="p">{`${fmt(row.pressure_mmhg, 1, "mmHg")} (${fmt(row.pressure_atm, 2, "atm")})`}</Num>],
                ["D0", <Num key="d0">{fmt(row.d0_mm, 2, "mm")}</Num>],
                [row.end_diameter_label, <Num key="de">{fmt(row.extinction_diameter_mm, 2, "mm")}</Num>],
                ["K", <Num key="k">{fmt(row.burning_rate_mm2_s, 2, "mm²/s")}</Num>],
                ["Burn time", <Num key="t">{fmt(row.burn_time_s, 1, "s")}</Num>],
              ]}
            />
            {row.cool_flame_quote && (
              <div className="mt-4">
                <Quote>{row.cool_flame_quote}</Quote>
                <p className="mt-1.5 text-note text-muted-foreground">
                  Source: {REPORT}, Appendix B, Figure <Num>{row.caption_figure}</Num> caption.
                </p>
              </div>
            )}
            {row.notes && <p className="mt-3 text-note text-muted-foreground">Cleaning note: {row.notes}</p>}
            {row.caption_atmosphere_differs && (
              <p className="mt-3 text-note text-muted-foreground">
                The report&apos;s figure caption words this atmosphere as <Num>{row.caption_atmosphere}</Num>; Table IX prints{" "}
                <Num>{row.table_atmosphere}</Num>. Table IX is used.
              </p>
            )}
          </Panel>
        </div>
      </Section>

      <Section title="Every matching test" explainer="Sortable. Empty cells are empty in the source and stay empty here.">
        <DataTable rows={d} columns={COLUMNS} rowKey={(r) => r.test_id} caption="FLEX tests matching the filters" minWidth={1900} />
        <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
          <Source href={flex.meta.record_url} className="mt-0 max-w-3xl">
            {`${flex.meta.report_title}. Gas columns are mole fractions as printed; ${S.gas_sum_not_1.length} rows do not sum to exactly 1.00 because the source prints two decimals.`}
          </Source>
          <Button variant="outline" size="sm" className="rounded-sm" onClick={() => download(d)}>
            <Download aria-hidden /> Download these rows (CSV)
          </Button>
        </div>
      </Section>
    </>
  );
}
