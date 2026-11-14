// Shapes of the JSON files written by scripts/export_web.py. A missing source value is null, never 0.

export type Outcome = "Extinction" | "Disruption" | "Completion";
export type Fuel = "Methanol" | "Heptane";
export type Verification = "verified_live" | "index" | "unverified";

export interface FlexRow {
  test_no: number;
  test_id: string;
  cir_id: string;
  date_iso: string;
  fuel: Fuel;
  pressure_mmhg: number | null;
  pressure_atm: number | null;
  pressure_kpa: number | null;
  o2: number;
  n2: number;
  co2: number;
  he: number;
  o2_pct: number;
  co2_pct: number;
  he_pct: number;
  o2_partial_kpa: number | null;
  d0_mm: number | null;
  extinction_diameter_mm: number | null;
  burning_rate_mm2_s: number | null;
  burn_time_s: number | null;
  outcome: Outcome;
  extinguished: number;
  atmosphere: string;
  cool_flame_label: "" | "indicated" | "not_indicated" | "unclear";
  cool_flame_quote: string;
  caption_figure: number | null;
  support: string;
  notes: string;
  source: string;
  caption_atmosphere: string;
  caption_atmosphere_differs: boolean;
  table_atmosphere: string;
  end_diameter_label: string;
}

export interface FuelSummary {
  n: number;
  Extinction: number;
  Disruption: number;
  Completion: number;
  extinction_share: number;
}

export interface FlexSummary {
  n: number;
  first_test: string;
  last_test: string;
  absent_numbers: number[];
  outcomes: Record<Outcome, number>;
  extinction_share: number;
  by_fuel: Record<Fuel, FuelSummary>;
  ranges: Record<string, [number, number, number, number]>;
  he_tests: number;
  co2_tests: number;
  co2_and_he: number;
  gas_sum_not_1: string[];
  noted_rows: string[];
  missing_gmt: number;
  heptane_extinctions: number;
  cool_flame: { indicated: number; not_indicated: number; unclear: number; "": number };
  captions: number;
}

export interface FlexData {
  meta: {
    report: string;
    report_title: string;
    record_url: string;
    pdf_url: string;
    psi_id: string;
    table_source: string;
    end_marker_extinction: string;
    end_marker_other: string;
  };
  summary: FlexSummary;
  outcomes: Outcome[];
  families: string[];
  caption_conflicts: number;
  printed_end_diameter: Record<Outcome, number>;
  rows: FlexRow[];
}

export interface Investigation {
  investigation_id: string;
  full_name: string;
  programme: string;
  platform: string;
  facility: string;
  facility_group: string;
  status: string;
  date_start: string;
  date_end: string;
  pi: string;
  objective: string;
  materials: string;
  sample_geometry: string;
  o2_min_pct: number | string;
  o2_max_pct: number | string;
  pressure_min_kPa: number | string;
  pressure_max_kPa: number | string;
  flow_min_cm_s: number | string;
  flow_max_cm_s: number | string;
  flow_regime: string;
  gravity_g: number | string;
  n_tests: number | string;
  key_result: string;
  key_result_value: number | string;
  key_result_unit: string;
  psi_url: string;
  primary_source_url: string;
  primary_source_ref: string;
  verification: string;
  psi_id: string;
  doi: string;
  in_psi_search: boolean;
  psi_research_area: string;
  fuel_type: string;
  evidence_class: string;
  range_source: string;
  n_tests_source: string;
  psi_tables: string[];
  psi_file_count: number | string;
  objective_full: string;
  note: string;
  environments: string[];
  is_combustion: boolean;
}

export interface CatalogueData {
  counts: {
    search_hits: number;
    combustion_science: number;
    other_areas: { psi_id: string; title: string; research_area: string }[];
    with_experimental_table: number;
    tables: number;
    retrieved: string;
    catalogue_rows: number;
    outside_psi_search: number;
    evidence: number;
    evidence_verified: number;
    evidence_unverified: number;
    evidence_index: number;
  };
  search_url: string;
  env_rules: Record<string, string>;
  fuel_type_label: Record<string, string>;
  evidence_class_label: Record<string, string>;
  relevance_weights: Record<string, number>;
  investigations: Investigation[];
}

export interface Evidence {
  id: string;
  investigation_id: string;
  evidence_class: string;
  pillar: string;
  statement: string;
  value: number | null;
  unit: string | null;
  o2_min_pct: number | null;
  o2_max_pct: number | null;
  o2_is_ambient: boolean;
  pressure_kpa: number | null;
  gravity_g: number | null;
  material: string | null;
  source_ref: string;
  source_url: string;
  verification: Verification;
  read_level: string;
  quote: string | null;
}

export type SolidOutcome = "sustained" | "quenched" | "blowoff" | "no_ignition" | "ambiguous";

export interface SolidPoint {
  point_id: string;
  investigation_id: string;
  test_no: string;
  material_class: string;
  material_verbatim: string;
  geometry: string;
  flow_direction: string;
  flow_cm_s: number | null;
  o2_at_outcome_pct: number | null;
  pressure_kPa: number | null;
  /** false: the source does not print a pressure for this test and the value is assumed. */
  pressure_stated: boolean;
  outcome: SolidOutcome;
  outcome_quote: string;
  source_ref: string;
  source_url: string;
  verification: string;
  usable_for_model: boolean;
}

export interface SolidEnvelope {
  n: number;
  o2?: [number, number];
  pressure?: [number, number];
  flow?: [number, number];
  sustained_o2_max?: number | null;
}

export interface SolidData {
  points: SolidPoint[];
  envelope_all: SolidEnvelope;
  envelopes: Record<string, SolidEnvelope>;
  n_decided: number;
  n_pressure_stated: number;
  pressure_note: string;
  n_total: number;
}

export interface SearchDoc {
  doc_id: string;
  kind: "evidence" | "investigation";
  investigation_id: string;
  title: string;
  text: string;
  source_ref: string;
  source_url: string;
  verification: string;
  evidence_class: string | null;
  o2_min_pct: number | null;
  o2_max_pct: number | null;
  o2_is_ambient: boolean | null;
}

export interface SearchData {
  docs: SearchDoc[];
  vocab: string[];
  idf: number[];
  vectors: [number, number][][];
  stop_words: string[];
  synonyms: Record<string, string>;
  class_words: Record<string, string>;
  min_score: number;
  investigation_class: Record<string, string>;
  investigation_o2: Record<string, [number, number] | null>;
}

export interface ScenarioInput {
  name: string;
  material: string;
  o2_pct: number;
  pressure_kpa: number;
  flow_cm_s: number;
  gravity_g: number;
  hrr_scale: string;
  free_volume_m3: number;
  is_droplet: boolean;
  droplet_d0_mm: number;
  n_alkane: boolean;
}

export interface RankingData {
  weights: Record<TermKey, number>;
  term_label: Record<TermKey, string>;
  p_o2_ref_kpa: number;
  p_o2_min_kpa: Record<string, { value: number; why: string }>;
  p_o2_floor_kpa: number;
  flow_band: [number, number];
  flow_zero_at: number;
  quiescent_score: number;
  hrr_scale_w: Record<string, { watts: number; why: string }>;
  detection: Record<string, { score: number; why: string }>;
  detection_default: { score: number; why: string };
  large_volume_m3: number;
  large_volume_bonus: number;
  hrr_log_range_w: [number, number];
  cool_flame_min_d0_mm: number;
  gravity_score: { g: number; score: number; name: string }[];
  presets: ScenarioInput[];
}

export type TermKey = "M_O2" | "M_flow" | "H" | "D" | "G" | "C";

export interface Confusion {
  threshold: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  sensitivity: number | null;
  specificity: number | null;
  false_positive_rate: number | null;
  [key: string]: number | null;
}

export interface ModelCard {
  name: string;
  title: string;
  target_label: string;
  burning_is_y1: boolean;
  burning_label: string;
  seed: number;
  n_rows: number;
  n_positive: number;
  positive_share: number;
  class_weight_balanced: boolean;
  C_grid: number[];
  C_final: number;
  outer_folds: number;
  n_groups: number;
  n_split_groups: number;
  features: string[];
  continuous: string[];
  log_features: string[];
  log1p_features: string[];
  binary: string[];
  categorical: Record<string, string[]>;
  interactions: [string, string][];
  squares: string[];
  dropped_features: Record<string, string>;
  added_features: Record<string, string>;
  notes: string[];
  prep: { median: Record<string, number>; mean: Record<string, number>; sd: Record<string, number> };
  coef: number[];
  coef_table: { feature: string; log_odds: number; odds_ratio: number; ci_low: number; ci_high: number }[];
  bootstrap: { n: number; coef: number[][] };
  metrics: {
    roc_auc: number | null;
    roc_auc_ci: [number | null, number | null];
    pr_auc: number | null;
    brier: number;
    calibration: {
      slope: number | null;
      intercept: number | null;
      bins: { mean_predicted: number; observed_share: number; n: number }[];
    };
    "confusion_at_0.5": Confusion;
    youden_threshold: number;
    confusion_at_youden: Confusion;
    burning_sensitivity_at_90_specificity: { sensitivity: number | null; [key: string]: number | null };
    per_group: {
      group: string;
      n: number;
      positives: number;
      auc: number | null;
      mean_predicted: number;
      observed_share: number;
    }[];
    roc: [number, number][];
    baseline_majority_accuracy: number;
    rowwise_cv_auc_for_comparison_only: number | null;
  };
  leave_one_material_out: {
    pooled_auc: number | null;
    per_material: { material: string; n: number; positives: number; auc: number | null; brier?: number | null; note?: string }[];
  };
  headline_auc: number | null;
  headline_is: string;
  headline_note: string;
  envelope: Record<string, [number, number]>;
  distance: { columns: string[]; train_nn_median: number; train_nn_p95: number; train_nn_max: number };
  training_rows: ({ row_id: string; y: number } & Record<string, number | string | null>)[];
  sensitivity_without_disruption?: { n_rows: number; roc_auc: number; roc_auc_ci: [number, number] };
}

export interface PanelsData {
  luci: {
    title: string;
    unit: string;
    source_ref: string;
    source_url: string;
    verification: Verification;
    rows: { label: string; lunar: number; earth: number; quote: string; slides: string; note?: string }[];
  };
  smoke: {
    unit: string;
    threshold_nm: number;
    note: string;
    flights: {
      id: string;
      label: string;
      evidence_id: string;
      rows: { material: string; fresh: number; aged: number }[];
    }[];
  };
  other_gaps: { gap: string; status: string; source: string }[];
  blue_flame_quote: { quote: string; source_ref: string; source_url: string; verification: Verification };
  partial_gravity_wording: string;
}
