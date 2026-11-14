"""Build data/flex_droplets.csv: FLEX Table IX normalised into the 24-column research schema.

Inputs : data/flex-table-ix.csv, data/flex_caption_annotations.csv
Output : data/flex_droplets.csv (24 schema columns, then clearly separated extras)

Run from the repo root:  python scripts/build_flex_droplets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flamefall import flex, schema  # noqa: E402


def main() -> int:
    df = flex.build_schema_frame()
    out = flex.DATA / "flex_droplets.csv"
    df.to_csv(out, index=False, lineterminator="\n")
    print(f"wrote {out.name}: {len(df)} rows x {len(df.columns)} columns")
    print("extinction_mode:", df["extinction_mode"].value_counts().to_dict())
    print("cool_flame_observed:", df["cool_flame_observed"].value_counts(dropna=False).to_dict())
    print("support:", df["support"].value_counts(dropna=False).to_dict())
    print("vocabulary problems:", schema.check_vocabulary(df))
    print("(a) no_ignition with K:", schema.rule_a_no_ignition_has_no_K(df))
    print("(a) ignited, K missing in source:", len(schema.rule_a_missing_K_but_ignited(df)))
    print("(b) cool flame without radiative diameter:", schema.rule_b_cool_flame_needs_radiative_diameter(df))
    print("(c) diameter ordering:", schema.rule_c_diameters_ordered(df))
    print("(c) with zero tolerance:", schema.rule_c_diameters_ordered(df, tol=0.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
