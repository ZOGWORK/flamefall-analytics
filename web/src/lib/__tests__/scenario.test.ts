import { describe, expect, it } from "vitest";

import catalogueJson from "@/data/catalogue.json";
import flexJson from "@/data/flex.json";
import solidJson from "@/data/solid.json";
import { partialGravityRecords } from "../catalogue";
import { SOLID_O2_LIMIT } from "../data";
import { hazard, R, rank } from "../ranking";
import { DEFAULT_STATE, FEATURED, gaps, HRR_LARGE, LIMITS, MATERIALS, parseState, toScenario, YOUR_SCENARIO, type LabState } from "../scenario";
import type { CatalogueData, FlexData, SolidData } from "../types";
import { numberIn, oneOf, range } from "../url-values";

const catalogue = catalogueJson as unknown as CatalogueData;

const flex = (flexJson as unknown as FlexData).rows;
const solid = solidJson as unknown as SolidData;
const state = (patch: Partial<LabState>): LabState => ({ ...DEFAULT_STATE, ...patch });

describe("featured scenarios", () => {
  it("set every input the score reads, so each scores exactly as its ranking preset", () => {
    expect(FEATURED.length).toBe(4);
    for (const f of FEATURED) {
      const preset = R.presets.find((p) => p.name === f.preset)!;
      expect(hazard(toScenario(f.state)), f.label).toBeCloseTo(hazard(preset), 12);
    }
  });

  it("the vehicle scenario is scored at vehicle scale, not glovebox scale", () => {
    const vehicle = FEATURED.find((f) => f.label === "Large fire in a vehicle")!;
    expect(vehicle.state.hrr).toBe(HRR_LARGE);
    expect(vehicle.state.volume).toBe(16.7);
    const order = rank([toScenario(vehicle.state), ...R.presets]);
    const mine = order.find(([name]) => name === YOUR_SCENARIO)!;
    const twin = order.find(([name]) => name === vehicle.preset)!;
    expect(mine[1]).toBeCloseTo(twin[1], 12);
  });
});

describe("where the data stops", () => {
  it("a solid scenario in still gas is outside the tested flow range", () => {
    for (const material of ["pmma", "sibal"] as const) {
      const found = gaps(state({ material, flow: 0 }), flex, solid);
      const env = solid.envelopes[MATERIALS[material].code];
      expect(env.flow![0]).toBeGreaterThan(0); // no solid test was run in still gas
      expect(found.some((x) => x.startsWith("flow:") && x.includes("was tested from")), material).toBe(true);
    }
    expect(gaps(state({ material: "pmma", flow: 500 }), flex, solid).some((x) => x.startsWith("flow:"))).toBe(true);
    expect(gaps(state({ material: "pmma", flow: 10 }), flex, solid).some((x) => x.startsWith("flow:"))).toBe(false);
  });

  it("the station baseline sits inside the tested ranges", () => {
    expect(gaps(state({}), flex, solid)).toEqual([]);
  });

  it("partial gravity is always a gap, for every material", () => {
    for (const material of Object.keys(MATERIALS) as (keyof typeof MATERIALS)[]) {
      expect(gaps(state({ material, g: 0.16 }), flex, solid)[0]).toBe("gravity: no repository test at 0.16 g");
      expect(gaps(state({ material, g: 0.38 }), flex, solid)[0]).toBe("gravity: no repository test at 0.38 g");
    }
    expect(gaps(state({ g: 1 }), flex, solid)[0]).toBe("gravity: the data are microgravity tests");
  });

  it("solids above 34% oxygen have no test point at any pressure", () => {
    const found = gaps(state({ material: "sibal", o2: 40, p: 56.5 }), flex, solid);
    expect(found.some((x) => x.startsWith("oxygen above 34%"))).toBe(true);
  });

  it("droplets: flow, combined diluents and ranges are each reported", () => {
    const found = gaps(state({ material: "heptane", o2: 50, p: 20, flow: 5, co2: 10, he: 10, d0: 7.5 }), flex, solid);
    for (const start of ["oxygen:", "pressure:", "CO2 and helium together", "ventilation flow:", "droplet size:"]) {
      expect(found.some((x) => x.startsWith(start)), start).toBe(true);
    }
    expect(gaps(state({ material: "heptane", flow: 0, d0: 3 }), flex, solid)).toEqual([]);
  });

  it("a droplet scenario is scored as a droplet, a solid as a solid", () => {
    expect(toScenario(state({ material: "heptane", d0: 3 }))).toMatchObject({ is_droplet: true, n_alkane: true, droplet_d0_mm: 3 });
    expect(toScenario(state({ material: "methanol" }))).toMatchObject({ is_droplet: true, n_alkane: false });
    expect(toScenario(state({ material: "pmma" }))).toMatchObject({ is_droplet: false, material: "PMMA", droplet_d0_mm: 0 });
  });
});

describe("what the address bar can and cannot do", () => {
  const strings = (patch: Record<string, string> = {}) =>
    ({ ...Object.fromEntries(Object.entries(DEFAULT_STATE).map(([k, v]) => [k, String(v)])), ...patch }) as Record<keyof LabState, string>;

  it("round-trips a state the controls can produce", () => {
    expect(parseState(strings())).toEqual(DEFAULT_STATE);
    for (const f of FEATURED) {
      expect(parseState(strings(Object.fromEntries(Object.entries(f.state).map(([k, v]) => [k, String(v)])))), f.label).toEqual(f.state);
    }
  });

  it("a value that is not a number becomes the default, never NaN", () => {
    const s = parseState(strings({ material: "heptane", co2: "abc", he: "", o2: "NaN", p: "Infinity", flow: "1e999" }));
    expect(s).toMatchObject({ co2: DEFAULT_STATE.co2, he: DEFAULT_STATE.he, o2: DEFAULT_STATE.o2, p: DEFAULT_STATE.p, flow: DEFAULT_STATE.flow });
    for (const v of Object.values(s)) if (typeof v === "number") expect(Number.isFinite(v)).toBe(true);
  });

  it("a number outside a control's range is brought inside it", () => {
    expect(parseState(strings({ o2: "500", flow: "-3", d0: "0" }))).toMatchObject({ o2: LIMITS.o2[1], flow: LIMITS.flow[0], d0: LIMITS.d0[0] });
  });

  it("an unknown material, gravity or size becomes the default; an inherited key is not a material", () => {
    for (const material of ["toString", "constructor", "__proto__", "xyz", ""]) {
      expect(parseState(strings({ material })).material, material).toBe(DEFAULT_STATE.material);
    }
    expect(parseState(strings({ hrr: "toString" })).hrr).toBe(DEFAULT_STATE.hrr);
    for (const gravity of ["0.2", "abc", "", "-1", "2"]) expect(parseState(strings({ g: gravity })).g, gravity).toBe(DEFAULT_STATE.g);
    for (const level of R.gravity_score) expect(parseState(strings({ g: String(level.g) })).g).toBe(level.g);
  });

  it("any gravity other than microgravity is reported as a gap, whatever its value", () => {
    expect(gaps(state({ g: 0.2 }), flex, solid).some((x) => x.startsWith("gravity: no repository test at 0.2 g"))).toBe(true);
    expect(gaps(state({ g: 0.16 }), flex, solid).some((x) => x.startsWith("gravity: no repository test at 0.16 g"))).toBe(true);
    expect(gaps(state({ g: 1 }), flex, solid)).toContain("gravity: the data are microgravity tests");
    expect(gaps(state({ g: 0 }), flex, solid).some((x) => x.startsWith("gravity"))).toBe(false);
  });

  it("filter values from the address bar: ranges, choices and numbers", () => {
    expect(range("15~40", [10, 60])).toEqual([15, 40]);
    expect(range("5~99", [10, 60])).toEqual([10, 60]);
    expect(range("1~5", [10, 60])).toEqual([10, 60]); // wholly outside: the full range, not an inverted one
    for (const bad of ["", "abc", "40~15", "1~2~3", "~", "NaN~3"]) expect(range(bad, [10, 60]), bad).toEqual([10, 60]);
    expect(oneOf("co2_pct", ["o2_pct", "co2_pct"] as const, "o2_pct")).toBe("co2_pct");
    expect(oneOf("constructor", ["o2_pct", "co2_pct"] as const, "o2_pct")).toBe("o2_pct");
    expect(numberIn("12.5", 0, 80, 3)).toBe(12.5);
    expect(numberIn(" ", 0, 80, 3)).toBe(3);
  });
});

describe("numbers that pages used to type", () => {
  it("the partial-gravity count parses the gravity text, so a repository record would be counted", () => {
    const rows = catalogue.investigations;
    expect(rows.every((r) => typeof r.gravity_g === "string")).toBe(true); // why a number type check could never match
    expect(partialGravityRecords(rows)).toEqual([]); // LUCI is not a repository record; FM2 is planned
    const luci = rows.find((r) => r.investigation_id === "LUCI")!;
    expect(luci.gravity_g).toBe("0.16");
    expect(partialGravityRecords([...rows, { ...luci, in_psi_search: true }]).map((r) => r.investigation_id)).toEqual(["LUCI"]);
    const fm2 = rows.find((r) => r.investigation_id === "FM2")!;
    expect(partialGravityRecords([{ ...fm2, in_psi_search: true }])).toEqual([]); // a plan is not a test
  });

  it("the solid oxygen limit is the top of the widest stated range, and no test point is above it", () => {
    expect(SOLID_O2_LIMIT).toBe(34);
    expect(solid.points.filter((p) => (p.o2_at_outcome_pct ?? 0) > SOLID_O2_LIMIT)).toEqual([]);
    expect(gaps(state({ o2: SOLID_O2_LIMIT + 0.5 }), flex, solid).some((x) => x.startsWith(`oxygen above ${SOLID_O2_LIMIT}%`))).toBe(true);
    expect(gaps(state({ o2: SOLID_O2_LIMIT }), flex, solid).some((x) => x.startsWith("oxygen above"))).toBe(false);
  });

  it("every solid point says whether its pressure is stated", () => {
    expect(solid.points.filter((p) => p.pressure_stated).length).toBe(solid.n_pressure_stated);
    expect(solid.points.find((p) => p.point_id === "SAF6-1")!.pressure_stated).toBe(false);
  });
});
