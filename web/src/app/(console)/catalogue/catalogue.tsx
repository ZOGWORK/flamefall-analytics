"use client";

import { ArrowUpRight, FlaskConical, Search, Table2, Telescope, X } from "lucide-react";
import { useMemo, useState } from "react";

import { OxygenRangeChart } from "@/components/charts/console-charts";
import { Chips, Field, Pick } from "@/components/console/controls";
import { DataTable, type Column } from "@/components/console/data-table";
import { Callout, HeroBand, KV, NoData, Num, Panel, Prose, Readout, Section, Source, Tag, VerificationBadge } from "@/components/console/primitives";
import { Statement } from "@/components/console/statement";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import searchJson from "@/data/search.json";
import { rangeText, rankInvestigations, RELEVANCE_KEYS, type RankedInvestigation } from "@/lib/catalogue";
import { catalogue, ev, evidence } from "@/lib/data";
import { capitalise, g } from "@/lib/format";
import { R } from "@/lib/ranking";
import { SearchIndex } from "@/lib/search";
import type { Investigation, SearchData } from "@/lib/types";
import { list, useUrlState } from "@/lib/use-url-state";

const INDEX = new SearchIndex(searchJson as unknown as SearchData);
const INV = catalogue.investigations;
const COMBUSTION = INV.filter((r) => r.is_combustion);
const N = catalogue.counts;
const EXAMPLES = [
  "Which experiments tested solid materials above 25% oxygen?",
  "Did the smoke detector miss anything?",
  "What do we know about fire in lunar gravity?",
  "Does turning off ventilation put a flame out?",
];
const HARDWARE = [...new Set(COMBUSTION.map((r) => r.facility_group))].sort().map((v) => ({ value: v, label: v }));
const FUELS = ["droplet", "gas", "solid", "smoke", "model"].map((v) => ({ value: v, label: catalogue.fuel_type_label[v] }));
const ENVS = Object.keys(catalogue.env_rules).map((v) => ({ value: v, label: v }));
const NO_RANK = "none";
const RANK_OPTIONS = [{ value: NO_RANK, label: "No ranking (catalogue order)" }, ...R.presets.map((p, i) => ({ value: String(i), label: p.name }))];
const DEFAULTS = { q: "", hw: "", fuel: "", env: "", rank: NO_RANK };
const GRAVITY_NAME = Object.fromEntries(R.gravity_score.map((x) => [x.g, x.name]));

function tableFile(name: string): string {
  return `/psi/${name.replace(".csv", ".json").replaceAll(" ", "_")}`;
}

function PsiTable({ tables }: { tables: string[] }) {
  const [name, setName] = useState(tables[0]);
  const [state, setState] = useState<{ name: string; columns: string[]; rows: string[][] } | "loading" | "error" | null>(null);
  const load = async (which: string) => {
    setState("loading");
    try {
      const res = await fetch(tableFile(which));
      if (!res.ok) throw new Error(String(res.status));
      setState(await res.json());
    } catch {
      setState("error");
    }
  };
  const shown = state && typeof state === "object" && state.name === name ? state : null;
  const columns: Column<string[]>[] = shown ? shown.columns.map((c, i) => ({ key: `${i}`, header: c || `column ${i + 1}`, cell: (row) => row[i], className: "num whitespace-nowrap" })) : [];
  return (
    <div className="mt-4">
      <p className="kicker text-dim">Experimental table, as PSI publishes it</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-2">
        {tables.length > 1 ? (
          <div className="w-full max-w-md">
            <Pick label="PSI experimental table" value={name} onChange={(v) => { setName(v); setState(null); }} options={tables.map((t) => ({ value: t, label: t }))} />
          </div>
        ) : (
          <Num className="text-note text-muted-foreground">{name}</Num>
        )}
        <Button variant="outline" size="sm" className="rounded-sm" onClick={() => (shown ? setState(null) : load(name))}>
          {shown ? "Hide this table" : "Show this table"}
        </Button>
      </div>
      {state === "loading" && <p className="mt-2 text-note text-muted-foreground">Loading the table…</p>}
      {state === "error" && <p className="mt-2 text-note text-ext">The table could not be loaded. It is in the repository under data/psi/experimental_tables.</p>}
      {shown && (
        <div className="mt-2">
          <DataTable rows={shown.rows} columns={columns} rowKey={(r) => String(shown.rows.indexOf(r))} maxHeight={300} caption={shown.name} />
          <p className="mt-1.5 text-note text-muted-foreground">
            <Num>{shown.rows.length}</Num> rows, exactly as PSI publishes them (<Num>{shown.name}</Num>). Padding rows that hold no test are dropped.
          </p>
        </div>
      )}
    </div>
  );
}

function Detail({ item }: { item: RankedInvestigation | { row: Investigation; rel?: undefined } }) {
  const r = item.row;
  const more = evidence.filter((e) => e.investigation_id === r.investigation_id);
  const links: [string, string][] = [];
  if (r.psi_id) links.push([`PSI record ${r.psi_id}`, r.psi_url]);
  if (r.doi) links.push([`DOI ${r.doi}`, `https://doi.org/${r.doi}`]);
  if (r.primary_source_url && r.primary_source_url !== r.psi_url) links.push(["primary source", r.primary_source_url]);
  return (
    <div className="pb-2">
      <p className="flex flex-wrap gap-1.5">
        <VerificationBadge level={r.verification} />
        <Tag tone="data">{catalogue.fuel_type_label[r.fuel_type] ?? r.fuel_type}</Tag>
        {r.environments.map((e) => (
          <Tag key={e}>{e}</Tag>
        ))}
        {r.status !== "complete" && <Tag tone="amber">{r.status.replaceAll("_", " ")}</Tag>}
      </p>
      <div className="mt-3">
        <p className="kicker text-dim">Key finding</p>
        {r.key_result ? (
          <>
            <p className="mt-1 text-body text-foreground">
              <Prose text={r.key_result} />
            </p>
            <Source href={r.primary_source_url} className="mt-1">
              {r.primary_source_ref}
            </Source>
          </>
        ) : (
          <p className="mt-1 text-body text-muted-foreground">
            None recorded: no quantitative result for this investigation was checked against a primary source during the build.
          </p>
        )}
      </div>
      <KV
        className="mt-3"
        rows={[
          ["Objective", r.objective || "not stated"],
          ["Fuels / materials", r.materials || "not stated"],
          ["Samples", r.sample_geometry ? <Prose key="s" text={r.sample_geometry} /> : "not stated"],
          ["Ambient O2", <Num key="o2">{rangeText(r.o2_min_pct, r.o2_max_pct, "%")}</Num>],
          ["Pressure", <Num key="p">{rangeText(r.pressure_min_kPa, r.pressure_max_kPa, "kPa")}</Num>],
          ["Flow", <span key="f"><Num>{rangeText(r.flow_min_cm_s, r.flow_max_cm_s, "cm/s")}</Num>{r.flow_regime ? ` · ${r.flow_regime}` : ""}</span>],
          ["Tests", <span key="n"><Num>{r.n_tests !== "" ? r.n_tests : "not stated"}</Num>{r.n_tests_source ? <span className="text-muted-foreground"> ({<Prose text={r.n_tests_source} />})</span> : null}</span>],
          ["Hardware", `${r.facility || r.facility_group} · ${r.platform}`],
          ["Lead", r.pi || "not stated in the record"],
          ["Record dates", <Num key="d">{`${r.date_start || "?"} to ${r.date_end || "?"}`}</Num>],
        ]}
      />
      {r.range_source && (
        <p className="mt-2 text-note text-muted-foreground">
          Where the ranges come from: <Prose text={r.range_source} />.
        </p>
      )}
      {r.note && (
        <p className="mt-2 text-note text-muted-foreground">
          <Prose text={r.note} />
        </p>
      )}
      {item.rel && (
        <p className="mt-2 text-note text-muted-foreground">
          Closeness terms:{" "}
          {RELEVANCE_KEYS.map((k, i) => (
            <span key={k}>
              {i > 0 && " · "}
              {k} <Num>{item.rel.terms[k].toFixed(2)}</Num> (<Prose text={item.rel.why[k]} />)
            </span>
          ))}
        </p>
      )}
      {links.length > 0 && (
        <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-note">
          {links.map(([label, href]) => (
            <a key={href} href={href} target="_blank" rel="noopener" className="inline-flex items-center gap-0.5 text-foreground underline decoration-line hover:decoration-amber">
              <Prose text={label} />
              <ArrowUpRight aria-hidden className="size-3" />
            </a>
          ))}
        </p>
      )}
      {more.length > 0 && (
        <div className="mt-4">
          <p className="kicker text-dim">
            All sourced statements for this investigation (<Num>{more.length}</Num>)
          </p>
          {more.map((e) => (
            <Statement key={e.id} entry={e} />
          ))}
        </div>
      )}
      {r.psi_tables.length > 0 && <PsiTable tables={r.psi_tables} />}
    </div>
  );
}

export function Catalogue() {
  const [q, set] = useUrlState(DEFAULTS);
  const [draft, setDraft] = useState<string | null>(null);
  const text = draft ?? q.q;
  const hardware = list(q.hw);
  const fuel = list(q.fuel);
  const env = list(q.env);
  const preset = q.rank === NO_RANK ? null : R.presets[Number(q.rank)];

  const answer = useMemo(() => (q.q.trim() ? INDEX.answer(q.q) : null), [q.q]);
  const shown = useMemo(() => {
    let items: (RankedInvestigation | { row: Investigation; rel?: undefined })[] = preset
      ? rankInvestigations(INV, { o2_pct: preset.o2_pct, pressure_kpa: preset.pressure_kpa, flow_cm_s: preset.flow_cm_s, evidence_class: "solid", gravity_g: preset.gravity_g }, catalogue.relevance_weights)
      : COMBUSTION.map((row) => ({ row }));
    if (hardware.length) items = items.filter((x) => hardware.includes(x.row.facility_group));
    if (fuel.length) items = items.filter((x) => fuel.includes(x.row.fuel_type));
    if (env.length) items = items.filter((x) => x.row.environments.some((e) => env.includes(e)));
    return items;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q.hw, q.fuel, q.env, q.rank]);
  const others = INV.filter((r) => !r.is_combustion);
  const filterText: string[] = [];
  if (answer?.filters.o2_at_least !== undefined) filterText.push(`ambient O2 of ${g(answer.filters.o2_at_least)}% or more`);
  if (answer?.filters.o2_at_most !== undefined) filterText.push(`ambient O2 of ${g(answer.filters.o2_at_most)}% or less`);
  if (answer?.filters.evidence_class) filterText.push(`${catalogue.evidence_class_label[answer.filters.evidence_class].toLowerCase()} only`);
  const submit = (value: string) => {
    setDraft(null);
    set({ q: value });
  };

  return (
    <>
      <HeroBand
        kicker="Repository search"
        value={N.search_hits}
        dial={{ value: N.combustion_science / N.search_hits, caption: `${N.combustion_science} combustion` }}
        source={`PSI repository search, retrieved ${N.retrieved.slice(0, 10)}`}
        readouts={
          <>
            <Readout className="border-0" icon={FlaskConical} meter={N.combustion_science / N.search_hits} value={N.combustion_science} tone="data" label="of those are Combustion Science" source="The other two are a solder study (PSI-181) and a fluid-physics experiment (PSI-108)" />
            <Readout className="border-0" icon={Table2} meter={N.with_experimental_table / N.search_hits} value={N.with_experimental_table} unit={`of ${N.search_hits}`} tone="data" label="records attach a per-test experimental table" source={`${N.tables} tables in all, every one copied into this repository`} />
            <Readout className="border-0" icon={Telescope} meter={N.outside_psi_search / N.catalogue_rows} value={N.outside_psi_search} tone="amber" label="related investigations that the search does not return" source="Saffire IV to VI, SoFIE-GEL, FLARE, LUCI, FM2: added from their own papers and marked as such" />
          </>
        }
      >
        records come back from a PSI search for “combustion”.
      </HeroBand>

      <Section title="Oxygen tested, by investigation" explainer="The ambient-oxygen range each investigation actually ran, one chart per kind of evidence. An investigation with no stated range is not drawn.">
        <Panel>
          <OxygenRangeChart investigations={COMBUSTION} classLabel={catalogue.evidence_class_label} exploration={ev("brief-atmospheres").value as number} />
          <Source href={catalogue.search_url}>
            Ranges computed from each record&apos;s PSI experimental table or its cited paper; the source of every range is in the investigation&apos;s detail below. Burner-feed oxygen is never counted as ambient.
          </Source>
        </Panel>
      </Section>

      <Section
        title="Ask the evidence"
        explainer="The answer is the matching measured statements themselves. Retrieval and extraction only: it cannot make up a number."
      >
        <Panel>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              submit(text);
            }}
          >
            <div className="relative flex-1">
              <Search aria-hidden className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-dim" />
              <Input aria-label="Question" value={text} onChange={(e) => setDraft(e.target.value)} placeholder={EXAMPLES[0]} className="h-9 rounded-sm border-input bg-background pl-8" />
            </div>
            {q.q && (
              <Button type="button" variant="outline" size="icon-lg" className="rounded-sm" aria-label="Clear the question" onClick={() => submit("")}>
                <X aria-hidden />
              </Button>
            )}
            <Button type="submit" size="lg" className="rounded-sm">
              Ask
            </Button>
          </form>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {EXAMPLES.map((ex) => (
              <Button key={ex} variant="outline" size="sm" className="h-auto max-w-full shrink rounded-sm py-1 text-left whitespace-normal text-muted-foreground" onClick={() => submit(ex)}>
                {ex}
              </Button>
            ))}
          </div>

          {answer && (
            <div className="mt-4 border-t border-line pt-3" aria-live="polite">
              {filterText.length > 0 && (
                <p className="text-note text-muted-foreground">
                  Filter read from your question: <Prose text={filterText.join("; ")} />. Burner-feed oxygen values are never matched.
                </p>
              )}
              {answer.statements.length === 0 && answer.hits.length === 0 ? (
                <NoData title="Nothing in the catalogue matches that question" className="mt-2">
                  No sourced statement or investigation record contains those terms. Try a material, a hardware name, or a condition such
                  as oxygen, pressure, flow or gravity.
                </NoData>
              ) : (
                <>
                  <p className="mt-1 text-body text-foreground">
                    <Num>{answer.statements.length}</Num> sourced statements from <Num>{answer.investigations.length}</Num> investigations:
                  </p>
                  {answer.statements.map((s) => (
                    <div key={s.doc.doc_id} className="border-b border-line py-3 last:border-b-0">
                      <p className={s.doc.verification === "unverified" ? "text-body text-muted-foreground" : "text-body text-foreground"}>
                        <span className="num mr-2 text-amber">{s.doc.investigation_id}</span>
                        <Prose text={s.doc.text} />
                      </p>
                      <Source href={s.doc.source_url} verification={s.doc.verification} className="mt-1.5">
                        {s.doc.source_ref}
                      </Source>
                    </div>
                  ))}
                  {answer.investigations.some((i) => INV.some((r) => r.investigation_id === i)) && (
                    <p className="mt-2 text-note text-muted-foreground">
                      Investigations to open below:{" "}
                      <Num>{answer.investigations.filter((i) => INV.some((r) => r.investigation_id === i)).slice(0, 8).join(", ")}</Num>
                    </p>
                  )}
                </>
              )}
            </div>
          )}
        </Panel>
      </Section>

      <Section title="Browse and rank" explainer="Filter by hardware, fuel and environment, or rank every investigation against a scenario.">
        <Panel>
          <div className="grid grid-cols-1 gap-x-8 gap-y-5 lg:grid-cols-2">
            <Field label="Hardware" hint="CIR = Combustion Integrated Rack; MDCA = droplet apparatus; MSG = glovebox." className="lg:col-span-2">
              <Chips label="Hardware" value={hardware} onChange={(v) => set({ hw: v.join(",") })} options={HARDWARE} />
            </Field>
            <Field label="Fuel type">
              <Chips label="Fuel type" value={fuel} onChange={(v) => set({ fuel: v.join(",") })} options={FUELS} />
            </Field>
            <Field label="Environment" hint={Object.entries(catalogue.env_rules).map(([k, v]) => `${k}: ${v}`).join(" · ")}>
              <Chips label="Environment" value={env} onChange={(v) => set({ env: v.join(",") })} options={ENVS} />
            </Field>
            <Field label="Rank by closeness to a scenario" className="lg:col-span-2">
              <div className="max-w-xl">
                <Pick label="Rank by closeness to a scenario" value={q.rank} onChange={(v) => set({ rank: v })} options={RANK_OPTIONS} />
              </div>
            </Field>
          </div>
        </Panel>

        {preset && (
          <Callout title="Ranking rule (a design choice, shown in full)" tone="data" className="mt-4">
            <p className="num text-foreground">
              closeness = {RELEVANCE_KEYS.map((k) => `${catalogue.relevance_weights[k].toFixed(2)} × ${k}`).join(" + ")}
            </p>
            <p className="mt-1.5">
              <Prose text={`Scenario: ${g(preset.o2_pct)}% O2 at ${g(preset.pressure_kpa)} kPa, ${g(preset.flow_cm_s)} cm/s, ${GRAVITY_NAME[preset.gravity_g]}, solid material.`} />{" "}
              Each term is 1 when the scenario lies inside the investigation&apos;s tested range, fades with distance outside it, and is 0
              when the repository does not state the range. It measures how close the test conditions are. It says nothing about how
              dangerous the scenario is.
            </p>
          </Callout>
        )}

        {shown.length === 0 ? (
          <NoData title="No investigation matches these filters" className="mt-4">
            {`Remove a filter to see the rest. The full catalogue has ${COMBUSTION.length} combustion investigations.`}
          </NoData>
        ) : (
          <div className="mt-4">
            <p className="text-body text-foreground">
              <Num>{shown.length}</Num> investigations
              {preset && <span className="text-muted-foreground"> · ordered by closeness; open one for the reason behind each term</span>}
            </p>
            <Accordion multiple className="mt-2 border border-line">
              {shown.map((item) => (
                <AccordionItem key={item.row.investigation_id} value={item.row.investigation_id} className="border-line px-3">
                  <AccordionTrigger className="rounded-sm py-2 hover:no-underline">
                    <span className="grid min-w-0 flex-1 grid-cols-1 gap-x-4 sm:grid-cols-[10rem_1fr_auto] sm:items-baseline">
                      <span className="num text-foreground">{item.row.investigation_id}</span>
                      <span className="min-w-0 text-body font-normal text-muted-foreground">{item.row.full_name}</span>
                      <span className="num text-note font-normal text-dim">
                        {item.row.psi_id || "not in the PSI search"}
                        {item.rel && <span className="ml-3 text-data">closeness {item.rel.score.toFixed(2)}</span>}
                      </span>
                    </span>
                  </AccordionTrigger>
                  <AccordionContent>
                    <Detail item={item} />
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        )}
      </Section>

      {others.length > 0 && !hardware.length && !fuel.length && !env.length && (
        <Section title="Returned by the search, but not combustion" explainer="Listed for completeness and left out of every ranking.">
          <ul className="border border-line">
            {others.map((r) => (
              <li key={r.psi_id} className="grid grid-cols-1 gap-x-4 border-b border-line px-3 py-2 last:border-b-0 sm:grid-cols-[6rem_1fr_10rem_auto]">
                <Num className="text-foreground">{r.psi_id}</Num>
                <span className="text-body text-muted-foreground">{r.full_name}</span>
                <span className="text-body text-muted-foreground">{capitalise(r.psi_research_area)}</span>
                <a href={r.psi_url} target="_blank" rel="noopener" className="inline-flex items-center gap-0.5 text-note text-foreground underline decoration-line">
                  record <ArrowUpRight aria-hidden className="size-3" />
                </a>
              </li>
            ))}
          </ul>
          <Source href={catalogue.search_url}>PSI Data Repository search “combustion”</Source>
        </Section>
      )}
    </>
  );
}
