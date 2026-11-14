// Typed access to the JSON that scripts/export_web.py writes. The app reads nothing else.
// The large files used by one page only (search index, model cards) are imported by that page.

import catalogueJson from "@/data/catalogue.json";
import evidenceJson from "@/data/evidence.json";
import flexJson from "@/data/flex.json";
import panelsJson from "@/data/panels.json";
import solidJson from "@/data/solid.json";
import type { CatalogueData, Evidence, FlexData, PanelsData, SolidData } from "./types";

export const flex = flexJson as unknown as FlexData;
export const catalogue = catalogueJson as unknown as CatalogueData;
export const evidence = evidenceJson as unknown as Evidence[];
export const solid = solidJson as unknown as SolidData;
export const panels = panelsJson as unknown as PanelsData;

const byId = new Map(evidence.map((e) => [e.id, e]));

/** One sourced statement by its identifier. Throws at build time if a page cites one that does not exist. */
export function ev(id: string): Evidence {
  const e = byId.get(id);
  if (!e) throw new Error(`evidence entry not found: ${id}`);
  return e;
}

/**
 * The top of the oxygen range any solid-fuel investigation states (SoFIE-GEL, up to 34% O2).
 * Above it there is no solid-material test point at all, so the app answers NO DATA.
 */
export const SOLID_O2_LIMIT = ev("sofie-gel-envelope").o2_max_pct as number;

export const TABLE_SOURCE = flex.meta.table_source;
export const SRC_RECOMPUTED = `${flex.meta.report}, Table IX · recomputed from the data`;
