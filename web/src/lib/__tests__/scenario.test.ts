import { describe, expect, it } from "vitest";

import flexJson from "@/data/flex.json";
import solidJson from "@/data/solid.json";
import { hazard, R, rank } from "../ranking";
import { DEFAULT_STATE, FEATURED, gaps, HRR_LARGE, MATERIALS, toScenario, YOUR_SCENARIO, type LabState } from "../scenario";
import type { FlexData, SolidData } from "../types";

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
