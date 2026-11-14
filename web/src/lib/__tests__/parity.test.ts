// The browser repeats a handful of Python calculations so that filters and sliders respond at once.
// golden.json holds the Python answers (written by scripts/export_web.py). Every test here compares.

import { describe, expect, it } from "vitest";

import catalogueJson from "@/data/catalogue.json";
import flexJson from "@/data/flex.json";
import coolCard from "@/data/model_droplet_cool_flame.json";
import extinctionCard from "@/data/model_droplet_extinction.json";
import searchJson from "@/data/search.json";
import solidJson from "@/data/solid.json";
import golden from "../__fixtures__/golden.json";
import { rankInvestigations, RELEVANCE_KEYS } from "../catalogue";
import { predict } from "../model";
import { nearestFlex, nearestSolid } from "../nearest";
import { hazard, R, rank, sensitivity, terms, TERM_KEYS } from "../ranking";
import { SearchIndex } from "../search";
import { d2Line, logisticTrend, nearestTests, shareByLevel, wilson, type GasColumn } from "../stats";
import type { CatalogueData, FlexData, Fuel, ModelCard, ScenarioInput, SearchData, SolidData, TermKey } from "../types";

const flex = flexJson as unknown as FlexData;
const catalogue = catalogueJson as unknown as CatalogueData;
const solid = solidJson as unknown as SolidData;
const index = new SearchIndex(searchJson as unknown as SearchData);
const cards: Record<string, ModelCard> = {
  droplet_extinction: extinctionCard as unknown as ModelCard,
  droplet_cool_flame: coolCard as unknown as ModelCard,
};
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const G = golden as any;
const close = (a: number, b: number, digits = 9) => expect(a).toBeCloseTo(b, digits);

describe("FLEX aggregates", () => {
  it("Wilson interval", () => {
    for (const c of G.wilson) {
      const [lo, hi] = wilson(c.k, c.n);
      close(lo, c.lo);
      close(hi, c.hi);
    }
  });

  it("extinction share by level, for the whole table and for filtered subsets", () => {
    const frames: Record<string, typeof flex.rows> = {
      all: flex.rows,
      methanol: flex.rows.filter((r) => r.fuel === "Methanol"),
      air_1atm: flex.rows.filter(
        (r) => r.atmosphere.startsWith("Air") && r.pressure_atm !== null && r.pressure_atm >= 0.9 && r.pressure_atm <= 1.1,
      ),
    };
    for (const [key, expected] of Object.entries(G.share_by_level) as [string, typeof G.wilson][]) {
      const [label, xcol] = key.split(":");
      const got = shareByLevel(frames[label], xcol as GasColumn);
      expect(got.length, key).toBe(expected.length);
      got.forEach((row, i) => {
        const e = expected[i];
        expect([row.fuel, row.n, row.k, row.disruption, row.completion], key).toEqual([
          e.fuel,
          e.n,
          e.k,
          e.disruption,
          e.completion,
        ]);
        close(row.level, e.level);
        close(row.share, e.share);
        close(row.lo, e.lo);
        close(row.hi, e.hi);
      });
    }
    expect(shareByLevel([], "o2_pct")).toEqual([]);
  });

  it("the totals behind every headline", () => {
    const all = shareByLevel(flex.rows, "o2_pct");
    expect(all.reduce((s, r) => s + r.n, 0)).toBe(276);
    expect(all.reduce((s, r) => s + r.k, 0)).toBe(186);
    expect(all.reduce((s, r) => s + r.disruption, 0)).toBe(62);
    expect(all.reduce((s, r) => s + r.completion, 0)).toBe(28);
    expect(flex.summary.by_fuel.Methanol).toMatchObject({ n: 157, Extinction: 126 });
    expect(flex.summary.by_fuel.Heptane).toMatchObject({ n: 119, Extinction: 60 });
    expect(flex.summary.cool_flame.indicated).toBe(39);
  });

  it("one-variable logistic trend", () => {
    for (const c of G.logistic_trend) {
      const sub = flex.rows.filter((r) => r.fuel === c.fuel);
      const got = logisticTrend(
        sub.map((r) => r[c.xcol as GasColumn]),
        sub.map((r) => r.extinguished),
        c.grid,
      );
      expect(got).not.toBeNull();
      (got as number[]).forEach((p, i) => close(p, c.p[i], 6));
    }
    expect(logisticTrend([1, 2, 3], [0, 1, 0], [1])).toBeNull(); // too few tests
    expect(logisticTrend(Array(10).fill(5), [0, 1, 0, 1, 0, 1, 0, 1, 0, 1], [5])).toBeNull(); // one level only
  });

  it("nearest tests never use an imputed pressure", () => {
    for (const c of G.nearest_tests) {
      const pool = flex.rows.filter((r) => c.fuels.includes(r.fuel));
      expect(nearestTests(pool, c.o2_pct, c.pressure_atm).map((r) => r.test_id)).toEqual(c.ids);
    }
    const everything = nearestTests(flex.rows, 21, 1, 276);
    expect(everything.length).toBe(275);
    expect(everything.some((r) => r.test_id === "FLEX-114")).toBe(false);
  });

  it("d²-law line and the name of its end marker", () => {
    for (const c of G.d2_line) {
      const row = flex.rows.find((r) => r.test_id === c.test_id)!;
      const got = d2Line(row, flex.meta.end_marker_extinction, flex.meta.end_marker_other);
      if (c.line === null) {
        expect(got).toBeNull(); // no diameters printed: no line, never a guess
        continue;
      }
      close(got!.d2_start, c.line.d2_start);
      close(got!.d2_end, c.line.d2_end);
      close(got!.t_line_end, c.line.t_line_end);
      if (c.line.t_zero === null) expect(got!.t_zero).toBeNull();
      else close(got!.t_zero as number, c.line.t_zero);
      expect(got!.d2_end).toBeGreaterThanOrEqual(0); // a diameter squared is never drawn below zero
      expect(got!.marker?.name).toBe(c.line.marker?.name);
      // a marker exists only when Table IX prints an end diameter; when it does, its name follows the outcome
      if (got!.marker) expect(got!.marker.name === flex.meta.end_marker_extinction).toBe(row.outcome === "Extinction");
      else expect(row.extinction_diameter_mm).toBeNull();
    }
  });
});

describe("catalogue", () => {
  it("relevance ranking against each preset scenario", () => {
    for (const c of G.rank_investigations) {
      const s = c.scenario;
      const got = rankInvestigations(
        catalogue.investigations,
        { o2_pct: s.o2_pct, pressure_kpa: s.pressure_kpa, flow_cm_s: s.flow_cm_s, evidence_class: "solid", gravity_g: s.gravity_g },
        catalogue.relevance_weights,
      );
      expect(got.length).toBeGreaterThan(25); // every combustion investigation, the planned one included
      expect(got.map((r) => r.row.investigation_id)).toEqual(c.top.map((t: { id: string }) => t.id));
      got.forEach((r, i) => {
        close(r.rel.score, c.top[i].relevance);
        for (const k of RELEVANCE_KEYS) {
          close(r.rel.terms[k], c.top[i].terms[k]);
          expect(r.rel.why[k]).toBe(c.top[i].why[k]);
        }
      });
    }
  });

  it("a planned investigation earns no closeness at all", () => {
    const ranked = rankInvestigations(
      catalogue.investigations,
      { o2_pct: 34, pressure_kpa: 56.5, flow_cm_s: 5, evidence_class: "solid", gravity_g: 0.16 },
      catalogue.relevance_weights,
    );
    const fm2 = ranked.find((r) => r.row.investigation_id === "FM2")!;
    expect(fm2.rel.score).toBe(0);
    for (const k of RELEVANCE_KEYS) {
      expect(fm2.rel.terms[k]).toBe(0);
      expect(fm2.rel.why[k]).toBe("planned, not tested");
    }
    expect(ranked.find((r) => r.row.investigation_id === "LUCI")!.rel.terms.gravity).toBe(1); // flown
  });

  it("a question naming two fuel classes is not filtered to one; an oxygen limit filters investigations too", () => {
    expect(index.parseFilters("Which materials did the smoke detector miss?")).toEqual({});
    const got = index.answer("Which materials did the smoke detector miss?");
    expect(got.statements.some((s) => s.doc.doc_id === "same-detector-misses")).toBe(true);
    const high = index.answer("Which experiments ran above 80% oxygen?");
    expect(high.investigations).not.toContain("FM2");
    for (const h of high.hits.filter((x) => x.doc.kind === "investigation")) {
      expect(searchJson.investigation_o2[h.doc.investigation_id as keyof typeof searchJson.investigation_o2]![1]).toBeGreaterThanOrEqual(80);
    }
  });

  it("retrieval: expansion, filters, statements and their order", () => {
    for (const c of G.answer) {
      expect(index.expand(c.query), c.query).toBe(c.expanded);
      const got = index.answer(c.query);
      expect(got.filters, c.query).toEqual(c.filters);
      expect(got.statements.map((s) => s.doc.doc_id), c.query).toEqual(c.statements.map((s: { doc_id: string }) => s.doc_id));
      expect(got.hits.map((h) => h.doc.doc_id), c.query).toEqual(c.hits.map((h: { doc_id: string }) => h.doc_id));
      got.statements.forEach((s, i) => close(s.score, c.statements[i].score, 4));
      expect(got.investigations, c.query).toEqual(c.investigations);
      expect(got.n_hits, c.query).toBe(c.n_hits);
    }
  });

  it("CO2 in a question is not read as an oxygen limit, and a burner feed is never matched", () => {
    expect(index.parseFilters("which droplets burned in CO2 above 30%?")).toEqual({ evidence_class: "droplet" });
    expect(index.parseFilters("tests with o2 above 30%")).toEqual({ o2_at_least: 30 });
    const high = index.answer("tests with oxygen above 60%");
    expect(high.statements.every((s) => s.doc.o2_is_ambient === true)).toBe(true);
    expect(high.statements.some((s) => s.doc.doc_id === "inverse-flame-85")).toBe(false);
  });
});

describe("nearest real tests", () => {
  it("droplets", () => {
    for (const c of G.nearest_flex) {
      const [fuel, o2, p, co2, he, d0] = c.args;
      const got = nearestFlex(flex.rows, fuel as Fuel, o2, p, co2, he, d0, c.k);
      expect(got.map((n) => n.row.test_id)).toEqual(c.ids);
      expect(got.map((n) => n.not_compared)).toEqual(c.not_compared);
      got.forEach((n, i) => close(n.distance, c.distance[i]));
    }
  });

  it("a missing value is never a perfect match: such a test is ranked last and says what was left out", () => {
    const methanol = flex.rows.filter((r) => r.fuel === "Methanol");
    const noPressure = flex.rows.filter((r) => r.pressure_kpa === null);
    expect(noPressure.map((r) => r.test_id)).toEqual(["FLEX-114"]);
    const { fuel, o2_pct, co2_pct, he_pct } = noPressure[0];
    const all = nearestFlex(flex.rows, fuel, o2_pct, 101.3, co2_pct, he_pct, null, flex.rows.length);
    expect(all.at(-1)).toMatchObject({ not_compared: "pressure" });
    expect(all.at(-1)!.row.test_id).toBe("FLEX-114"); // identical on every stated input, still last
    expect(all.slice(0, -1).every((n) => n.not_compared === "")).toBe(true);
    expect(nearestFlex(methanol, "Methanol", 21, 101.3, 0, 0, 3).every((n) => n.not_compared === "")).toBe(true);
    const pmma = nearestSolid(solid.points, "PMMA", 17, 101.3, 10, 400);
    const firstMissing = pmma.findIndex((n) => n.not_compared !== "");
    expect(firstMissing).toBeGreaterThan(0);
    expect(pmma.slice(firstMissing).every((n) => n.not_compared === "flow" && n.point.flow_cm_s === null)).toBe(true);
  });

  it("solids: same material first, other materials marked", () => {
    for (const c of G.nearest_solid) {
      const [mat, o2, p, flow] = c.args;
      const got = nearestSolid(solid.points, mat, o2, p, flow, c.k);
      expect(got.map((n) => n.point.point_id)).toEqual(c.ids);
      expect(got.map((n) => n.not_compared)).toEqual(c.not_compared);
      expect(got.map((n) => n.same_material)).toEqual(c.same_material);
      got.forEach((n, i) => close(n.distance, c.distance[i]));
    }
  });
});

describe("triage score", () => {
  it("the worked example: 0.637 in microgravity, 0.687 lunar, 0.337 at the oxygen limit", () => {
    expect(G.worked_example).toEqual({ base: 0.637, lunar: 0.687, limit: 0.337 });
    const base: ScenarioInput = G.hazard[0].scenario;
    const lunar: ScenarioInput = G.hazard[1].scenario;
    const limit: ScenarioInput = G.hazard[2].scenario;
    expect(Number(hazard(base).toFixed(3))).toBe(0.637);
    expect(Number(hazard(lunar).toFixed(3))).toBe(0.687);
    expect(Number(hazard(limit).toFixed(3))).toBe(0.337);
    expect(terms(limit).values.M_O2).toBeCloseTo(0, 12);
  });

  it("every term, reason and flag", () => {
    for (const c of G.hazard) {
      const got = terms(c.scenario);
      for (const k of TERM_KEYS) {
        close(got.values[k], c.terms.values[k]);
        expect(got.why[k], `${c.scenario.name} ${k}`).toBe(c.terms.why[k]);
      }
      expect(got.flags).toEqual(c.terms.flags);
      close(hazard(c.scenario), c.hazard);
    }
  });

  it("weights sum to 1 and the ordering and its sensitivity match", () => {
    close(
      TERM_KEYS.reduce((s, k) => s + R.weights[k], 0),
      1,
    );
    for (const c of G.rank) {
      const w = c.weights as Record<TermKey, number>;
      const order = rank(R.presets, w);
      expect(order.map(([n]) => n)).toEqual(c.order.map(([n]: [string, number]) => n));
      order.forEach(([, s], i) => close(s, c.order[i][1]));
      expect(sensitivity(R.presets, w)).toEqual(c.sensitivity);
    }
  });
});

describe("model estimate from a stored card", () => {
  it("probability, bootstrap interval and distance to data", () => {
    for (const c of G.predict) {
      const got = predict(cards[c.model], c.x);
      close(got.p, c.out.p, 8);
      close(got.lo as number, c.out.lo, 8);
      close(got.hi as number, c.out.hi, 8);
      close(got.nn_distance, c.out.nn_distance, 8);
      expect(got.far_from_data).toBe(c.out.far_from_data);
      expect(got.extrapolating).toBe(c.out.extrapolating);
      expect(got.outside_envelope).toEqual(c.out.outside_envelope);
      expect(got.nearest.map((n) => n.row_id)).toEqual(c.out.nearest.map((n: { row_id: string }) => n.row_id));
    }
  });

  it("a query outside the training envelope is flagged", () => {
    const out = predict(cards.droplet_extinction, {
      o2_pct: 45, pressure_kpa: 56.5, o2_partial_kpa: 25.4, co2_pct: 0, he_pct: 0, d0_mm: 3, fuel_heptane: 1,
    });
    expect(out.extrapolating).toBe(true);
    expect(out.outside_envelope.map((o) => o.feature)).toContain("o2_pct");
  });
});
