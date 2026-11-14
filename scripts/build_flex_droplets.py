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


def problems(df) -> list[str]:
    """Everything that must be empty before the file may be written.

    The documented source gaps are not problems: the 16 ignited tests with no printed burning rate,
    FLEX-212 (rule b) and the 0.01 mm rounding step of FLEX-129 (inside rule (c)'s tolerance).
    """
    found = list(schema.check_vocabulary(df))
    found += [f"rule (a): {t} has a burning rate but did not ignite" for t in schema.rule_a_no_ignition_has_no_K(df)]
    unexpected_b = set(schema.rule_b_cool_flame_needs_radiative_diameter(df)) - set(schema.KNOWN_SOURCE_GAPS["b"])
    found += [f"rule (b): {t} has cool-flame evidence but no radiative-extinction diameter" for t in sorted(unexpected_b)]
    found += [f"rule (c): {t} has diameters out of order" for t in schema.rule_c_diameters_ordered(df)]
    return found


def main() -> int:
    df = flex.build_schema_frame()
    out = flex.DATA / "flex_droplets.csv"
    found = problems(df)
    if found:
        print(f"NOT written: {out.name} would break {len(found)} schema rule(s):")
        for line in found:
            print("  ", line)
        return 1
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
