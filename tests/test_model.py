"""Models: no leakage, grouped splits, the metrics the specification asks for, and distance-to-data."""
from __future__ import annotations

import json

import numpy as np
import pytest

from flamefall import model

OUTCOME_COLUMNS = {"burning_rate_mm2_s", "burn_time_s", "extinction_diameter_mm", "outcome", "extinguished",
                   "cool_flame_label", "K_hot_mm2_s", "sustained", "hrr", "spread_rate"}


@pytest.fixture(scope="module")
def cards() -> dict:
    return {name: json.loads((model.MODEL_DIR / f"{name}.json").read_text(encoding="utf-8")) for name in model.SPECS}


@pytest.fixture(scope="module")
def splits() -> dict:
    return json.loads((model.DATA / "cv_splits.json").read_text(encoding="utf-8"))


def test_bootstrap_counts_match_what_the_provenance_file_says():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    kept = {name: json.loads((root / "data" / "models" / f"{name}.json").read_text(encoding="utf-8"))["bootstrap"]["n"]
            for name in ("droplet_extinction", "droplet_cool_flame", "solid_sustained")}
    assert kept == {"droplet_extinction": 1000, "droplet_cool_flame": 992, "solid_sustained": 1000}
    text = (root / "data" / "PROVENANCE.md").read_text(encoding="utf-8")
    assert "1,000 for droplet extinction, 992 for droplet cool-flame evidence, 1,000 for solids" in " ".join(text.split())


def test_three_models_and_they_never_pool_droplets_with_solids():
    assert set(model.SPECS) == {"droplet_extinction", "droplet_cool_flame", "solid_sustained"}
    droplet = set(model.frame_for("droplet_extinction")["row_id"])
    solid = set(model.frame_for("solid_sustained")["row_id"])
    assert all(r.startswith("FLEX-") for r in droplet)
    assert not any(r.startswith("FLEX-") for r in solid)
    assert not droplet & solid


def test_no_outcome_is_used_as_a_feature():
    for spec in model.SPECS.values():
        used = set(spec.continuous) | set(spec.binary) | set(spec.categorical)
        assert not used & OUTCOME_COLUMNS, spec.name
        assert "o2_partial_kpa" in spec.continuous            # the specified operative variable


def test_rows_and_class_balance(cards):
    d, c, s = cards["droplet_extinction"], cards["droplet_cool_flame"], cards["solid_sustained"]
    assert (d["n_rows"], d["n_positive"]) == (275, 185)       # FLEX-114 has no pressure and is dropped
    assert (c["n_rows"], c["n_positive"]) == (47, 39)
    assert (s["n_rows"], s["n_positive"]) == (179, 135)
    assert d["class_weight_balanced"] is False and c["class_weight_balanced"] and s["class_weight_balanced"]
    for card in cards.values():
        assert card["seed"] == 42 and card["C_final"] in [0.01, 0.1, 1.0, 10.0]


def test_folds_never_split_a_group(splits):
    for name, sp in splits.items():
        groups = sp["groups"]
        seen = set()
        for fold in sp["outer"]:
            train = {groups[r] for r in fold["train_rows"]}
            test = {groups[r] for r in fold["test_rows"]}
            assert not train & test, (name, fold["fold"])
            assert not seen & set(fold["test_rows"])           # each row is tested exactly once
            seen |= set(fold["test_rows"])
        assert seen == set(groups)
        assert sp["seed"] == 42 and sp["k"] == 5


def test_every_specified_metric_is_reported(cards):
    for card in cards.values():
        m = card["metrics"]
        for key in ["roc_auc", "roc_auc_ci", "pr_auc", "brier", "calibration", "confusion_at_0.5", "youden_threshold",
                    "confusion_at_youden", "burning_sensitivity_at_90_specificity", "per_group", "roc"]:
            assert key in m, key
        assert {"slope", "intercept", "bins"} <= set(m["calibration"])
        for cm in (m["confusion_at_0.5"], m["confusion_at_youden"]):
            assert cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"] == card["n_rows"]
        assert all({"feature", "log_odds", "odds_ratio", "ci_low", "ci_high"} <= set(c) for c in card["coef_table"])
        assert card["leave_one_material_out"]["per_material"]
        assert len(card["oof"]) == card["n_rows"]


def test_headline_is_the_worse_of_the_two_validations(cards):
    for card in cards.values():
        grouped, lomo = card["metrics"]["roc_auc"], card["leave_one_material_out"]["pooled_auc"]
        candidates = [v for v in (grouped, lomo) if v is not None]
        assert card["headline_auc"] == pytest.approx(min(candidates))


def test_droplet_model_generalises_and_solid_model_does_not(cards):
    d, s = cards["droplet_extinction"], cards["solid_sustained"]
    assert d["metrics"]["roc_auc"] > 0.8 and d["metrics"]["roc_auc_ci"][0] > 0.7
    assert d["headline_auc"] < d["metrics"]["roc_auc"]         # an unseen fuel is harder than an unseen atmosphere
    assert s["headline_auc"] < 0.6                             # reported as a failure, not hidden
    # row-wise CV is never the headline: it flatters the solid model by more than 0.1, and for the
    # droplet model it is no more than 0.02 below grouped CV
    assert d["metrics"]["rowwise_cv_auc_for_comparison_only"] >= d["metrics"]["roc_auc"] - 0.02
    assert s["metrics"]["rowwise_cv_auc_for_comparison_only"] > s["metrics"]["roc_auc"] + 0.1


def test_disruption_is_never_the_positive_class():
    f = model.frame_for("droplet_extinction")
    assert f.loc[f["outcome"] == "Disruption", "y"].sum() == 0
    assert f.loc[f["outcome"] == "Extinction", "y"].all()


def test_cool_flame_model_uses_only_stated_labels():
    f = model.frame_for("droplet_cool_flame")
    assert set(f["cool_flame_label"]) == {"indicated", "not_indicated"}
    assert set(f["fuel"]) == {"Heptane"} and set(f["outcome"]) == {"Extinction"}


def test_preprocessing_statistics_come_from_the_training_rows_only():
    spec = model.SPECS["droplet_extinction"]
    df = model.frame_for("droplet_extinction").reset_index(drop=True)
    prep_a = model.fit_prep(df.iloc[:100], spec)
    prep_b = model.fit_prep(df.iloc[100:], spec)
    assert prep_a["mean"]["o2_pct"] != prep_b["mean"]["o2_pct"]
    X = model.transform(df.iloc[:100], spec, prep_a)
    assert np.allclose(X[:, 0].mean(), 0, atol=1e-9) and np.allclose(X[:, 0].std(), 1, atol=1e-9)
    assert not np.isnan(model.transform(df, spec, prep_a)).any()   # missing diameters are imputed, not dropped


def test_cross_validation_never_learns_preprocessing_from_the_rows_it_scores(monkeypatch):
    """Inside nested CV every scaler is fitted on training rows only, and never on the whole frame."""
    spec = model.SPECS["droplet_extinction"]
    df = model.frame_for("droplet_extinction").reset_index(drop=True)
    fitted_on, scored = {}, []
    real_fit, real_transform = model.fit_prep, model.transform

    def spy_fit(frame, s):
        prep = real_fit(frame, s)
        fitted_on[id(prep)] = (prep, set(frame["row_id"]))
        return prep

    def spy_transform(frame, s, prep):
        scored.append((set(frame["row_id"]), id(prep)))
        return real_transform(frame, s, prep)

    monkeypatch.setattr(model, "fit_prep", spy_fit)
    monkeypatch.setattr(model, "transform", spy_transform)
    cv = model.nested_cv(df, spec)

    ids = df["row_id"].to_numpy()
    everything = frozenset(ids)
    assert len(everything) == len(df)

    # The only (fitted on, applied to) pairs the protocol allows, worked out from the fold membership
    # alone: an outer scaler is fitted on a fold's training rows and applied to those rows and to that
    # fold's test rows; an inner scaler is fitted on an inner training split of one outer training set
    # and applied to that split and to its inner test split. A scaler fitted on a test fold, or on
    # the whole frame, is in neither list.
    allowed, outer_scoring = set(), []
    index = {row: i for i, row in enumerate(ids)}
    for fold in cv["folds"]:
        train, test = frozenset(fold["train_rows"]), frozenset(fold["test_rows"])
        assert not train & test and train | test == everything
        allowed |= {(train, train), (train, test)}
        outer_scoring.append((train, test))
        tr = np.array(sorted(index[r] for r in train))
        groups = cv["split_groups"][tr]
        for inner_train, inner_test in model._splits(groups, min(3, len(np.unique(groups)))):
            a, b = frozenset(ids[tr[inner_train]]), frozenset(ids[tr[inner_test]])
            assert not a & b and a | b == train
            allowed |= {(a, a), (a, b)}

    seen = {(frozenset(fitted_on[key][1]), frozenset(rows)) for rows, key in scored}
    assert seen <= allowed, "a scaler was fitted on, or applied to, rows the protocol does not allow"
    assert all(pair in seen for pair in outer_scoring)             # every outer test fold was scored by its own fold's scaler
    assert all(rows != everything for _, rows in fitted_on.values())
    assert not any(fitted == test for fitted, _ in seen for _, test in outer_scoring)   # never fitted on a test fold
    whole = real_fit(df, spec)
    assert all(prep["mean"]["o2_pct"] != whole["mean"]["o2_pct"] for prep, _ in fitted_on.values())


def test_the_preprocessing_test_catches_a_scaler_fitted_on_the_test_fold(monkeypatch):
    """The check above must fail for the classic leak, or it proves nothing."""
    spec = model.SPECS["droplet_extinction"]
    df = model.frame_for("droplet_extinction").reset_index(drop=True)
    cv = model.nested_cv(df, spec)
    ids = df["row_id"].to_numpy()
    allowed = set()
    for fold in cv["folds"]:
        train, test = frozenset(fold["train_rows"]), frozenset(fold["test_rows"])
        allowed |= {(train, train), (train, test)}
    for fold in cv["folds"]:
        test = frozenset(fold["test_rows"])
        assert (test, test) not in allowed                          # fitted on the test fold, applied to it
        assert (frozenset(ids), test) not in allowed                # fitted on everything, applied to the test fold


def test_cards_state_where_they_depart_from_the_protocol(cards):
    solid, cool = cards["solid_sustained"], cards["droplet_cool_flame"]
    s = model.solid_frame()
    moved = s[s["o2_initial_pct"] != s["o2_pct"]]
    assert len(s) == 179 and len(moved) == 13 and set(moved["y"]) == {0}
    assert any("moves 13 of the 179 rows, 13 of them not sustained" in note for note in solid["notes"])
    assert any("oxygen partial pressure and the oxygen-flow interaction" in note for note in solid["notes"])
    spec = model.SPECS["solid_sustained"]
    assert "o2_partial_kpa" in spec.continuous and ("o2_pct", "flow_cm_s") in spec.interactions   # the two that carry it
    assert (s["o2_partial_kpa"] == s["o2_pct"] / 100 * s["pressure_kpa"]).all()
    assert cool["leave_one_material_out"]["pooled_auc"] is None and cool["headline_is"] == "grouped cross-validation"
    assert "alone, not the worse of two" in cool["headline_note"]
    for name in ("droplet_extinction", "solid_sustained"):
        assert cards[name]["headline_note"].startswith("The worse of")


def test_prediction_inside_the_envelope():
    fm = model.Fitted("droplet_extinction")
    out = fm.predict(dict(o2_pct=21, pressure_kpa=101.3, o2_partial_kpa=21.3, co2_pct=0, he_pct=0, d0_mm=3.0,
                          fuel_heptane=1.0))
    assert 0 < out["lo"] <= out["p"] <= out["hi"] < 1
    assert out["extrapolating"] is False and out["outside_envelope"] == []
    assert len(out["nearest"]) == 5 and out["nearest"][0]["row_id"].startswith("FLEX-")


def test_distance_to_data_warning_outside_the_envelope():
    fm = model.Fitted("droplet_extinction")
    out = fm.predict(dict(o2_pct=45, pressure_kpa=56.5, o2_partial_kpa=25.4, co2_pct=30, he_pct=30, d0_mm=3.0,
                          fuel_heptane=1.0))
    assert out["extrapolating"] and out["far_from_data"]
    flagged = {o["feature"] for o in out["outside_envelope"]}
    assert {"o2_pct", "pressure_kpa"} <= flagged
    assert out["nn_distance"] > out["train_nn_p95"]


def test_more_oxygen_means_less_extinction_and_more_co2_means_more():
    fm = model.Fitted("droplet_extinction")
    base = dict(pressure_kpa=101.3, co2_pct=0, he_pct=0, d0_mm=3.0, fuel_heptane=0.0)
    low = fm.predict({**base, "o2_pct": 15, "o2_partial_kpa": 15.2})["p"]
    high = fm.predict({**base, "o2_pct": 30, "o2_partial_kpa": 30.4})["p"]
    assert low > high
    with_co2 = fm.predict({**base, "o2_pct": 21, "o2_partial_kpa": 21.3, "co2_pct": 30})["p"]
    without = fm.predict({**base, "o2_pct": 21, "o2_partial_kpa": 21.3})["p"]
    assert with_co2 > without


def test_model_cards_are_strict_json():
    """No bare NaN or Infinity token: the cards must load in any JSON parser, not only Python's."""
    def reject(token):
        raise ValueError(f"non-finite token {token}")

    for name in model.SPECS:
        text = (model.MODEL_DIR / f"{name}.json").read_text(encoding="utf-8")
        json.loads(text, parse_constant=reject)
    json.loads((model.DATA / "cv_splits.json").read_text(encoding="utf-8"), parse_constant=reject)
    rows = json.loads((model.MODEL_DIR / "droplet_extinction.json").read_text(encoding="utf-8"))["training_rows"]
    missing = [r for r in rows if r["d0_mm"] is None]
    assert len(missing) == 12                                   # the 12 tests with no printed diameter
    fm = model.Fitted("droplet_extinction")
    assert 0 < fm.predict(dict(o2_pct=21, pressure_kpa=101.3, o2_partial_kpa=21.3, co2_pct=0, he_pct=0, d0_mm=None,
                               fuel_heptane=0.0))["p"] < 1     # a missing diameter is imputed, not an error


def test_each_model_names_its_burning_class(cards):
    assert cards["droplet_extinction"]["burning_label"] == "the visible flame did not go out"
    assert "cool-flame evidence" in cards["droplet_cool_flame"]["burning_label"]
    assert cards["solid_sustained"]["burning_label"] == "the flame was sustained"


def test_auc_helper():
    y = np.array([0, 0, 1, 1])
    assert model.auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == 1.0
    assert model.auc(y, np.array([0.9, 0.8, 0.2, 0.1])) == 0.0
    assert model.auc(y, np.array([0.5, 0.5, 0.5, 0.5])) == 0.5
    assert model.auc(np.array([1, 1]), np.array([0.2, 0.3])) is None
