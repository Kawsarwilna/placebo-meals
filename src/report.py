import json
import re
from pathlib import Path
from statistics import median

import pandas as pd

from analyze import MIN_MEALS, food_glucose_overlap_hours, lowest_hr_hour
from load import PARTICIPANTS
from meals import CLEAN_AFTER_MIN, CLEAN_BEFORE_MIN, MEAL_GAP_MIN, PLACEBO_CLOCK_WINDOW_MIN, PLACEBOS_PER_MEAL
from movement import FIT_MIN_SINCE_FOOD, MIN_STILL_PARTICIPANTS, STILL_SHARE, STILL_THRESHOLD
from response import POST_MIN, PRE_MIN, SUSTAINED_FROM_MIN, SUSTAINED_TO_MIN
from stats import per_participant, summarize

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
METRICS = {"glucose": "glucose_peak", "hr_peak": "hr_peak", "hr_sustained": "hr_sustained"}


def still_windows(table):
    return table[(table["still_before"] >= STILL_SHARE) & (table["still_after"] >= STILL_SHARE)]


def movement_per_participant(table):
    still = still_windows(table)
    return {
        "adj_hr_peak": per_participant(table, "hr_adj_peak"),
        "adj_hr_sustained": per_participant(table, "hr_adj_sustained"),
        "still_hr_sustained": per_participant(still, "hr_sustained"),
        "still_glucose": per_participant(still, "glucose_peak"),
    }


def build_metrics(table):
    per = {key: per_participant(table, column) for key, column in METRICS.items()}
    per_movement = movement_per_participant(table)
    still = still_windows(table)
    failed = sorted(per["glucose"].loc[per["glucose"]["difference"] <= 0, "pid"])
    meals = table[table["kind"] == "meal"]
    standard = meals[meals["standard_breakfast"].astype(bool)]
    big_cutoff = float(meals["calories"].quantile(2 / 3))
    included = sorted(table["pid"].unique())
    excluded = sorted(set(PARTICIPANTS) - set(included))

    def big(m):
        return m["calories"] >= big_cutoff

    metrics = {
        "participants_total": len(PARTICIPANTS),
        "participants": len(included),
        "excluded": excluded,
        "excluded_food_glucose_overlap_hours": {pid: food_glucose_overlap_hours(pid) for pid in excluded},
        "lowest_hr_hour": {pid: lowest_hr_hour(pid) for pid in included},
        "meals": int(len(meals)),
        "placebos": int((table["kind"] == "placebo").sum()),
        "glucose_time_to_peak_median_min": float(meals["glucose_time_to_peak"].median()),
        "glucose_check_failed": failed,
        "main": {key: summarize(p) for key, p in per.items()},
        "sensitivity": {key: summarize(p[~p["pid"].isin(failed)]) for key, p in per.items()},
        "exploratory": {
            "hr_peak_smoothed": summarize(per_participant(table, "hr_peak_smooth")),
            "big_meal_kcal_cutoff": big_cutoff,
            "big_meals": {key: summarize(per_participant(table, column, big)) for key, column in METRICS.items()},
        },
        "standard_breakfasts_clean": int(len(standard)),
        "standard_breakfast_participants": int(standard["pid"].nunique()),
        "movement": {
            "model_r2_by_participant": table.groupby("pid")["movement_r2"].first().to_dict(),
            "still_threshold_g": STILL_THRESHOLD,
            "still_meals": int((still["kind"] == "meal").sum()),
            "still_placebos": int((still["kind"] == "placebo").sum()),
            "results": {key: summarize(p) for key, p in per_movement.items()},
        },
    }
    return metrics, {**per, **per_movement}


def display_values(m):
    main, sens, explore = m["main"], m["sensitivity"], m["exploratory"]

    def pct(x):
        return f"{x:.0%}"

    def pvalue(x):
        return "p < 0.001" if x < 0.001 else f"p = {x:.2f}"

    low_hours = m["lowest_hr_hour"].values()
    overlap = m["excluded_food_glucose_overlap_hours"]
    values = {
        "participants_total": m["participants_total"],
        "participants": m["participants"],
        "excluded": ", ".join(m["excluded"]),
        "excluded_overlap_hours": ", ".join(f"{overlap[pid]:.0f}" for pid in m["excluded"]),
        "min_meals": MIN_MEALS,
        "low_hour_min": min(low_hours),
        "low_hour_max": max(low_hours),
        "meals": m["meals"],
        "placebos": m["placebos"],
        "glucose_ttp": f"{m['glucose_time_to_peak_median_min']:.0f}",
        "failed_count": len(m["glucose_check_failed"]),
        "failed_list": ", ".join(m["glucose_check_failed"]),
        "smooth_auc": pct(explore["hr_peak_smoothed"]["median_auc"]),
        "big_cut": f"{explore['big_meal_kcal_cutoff']:.0f}",
        "big_participants": explore["big_meals"]["glucose"]["participants"],
        "sb_count": m["standard_breakfasts_clean"],
        "sb_participants": m["standard_breakfast_participants"],
        "meal_gap": MEAL_GAP_MIN,
        "clean_before_h": f"{CLEAN_BEFORE_MIN / 60:g}",
        "clean_after_h": f"{CLEAN_AFTER_MIN / 60:g}",
        "placebos_per_meal": PLACEBOS_PER_MEAL,
        "clock_window": PLACEBO_CLOCK_WINDOW_MIN,
        "pre_min": PRE_MIN,
        "post_h": f"{POST_MIN / 60:g}",
        "sustained_from": SUSTAINED_FROM_MIN,
        "sustained_to": SUSTAINED_TO_MIN,
    }
    move = m["movement"]
    r2_by_pid = move["model_r2_by_participant"]
    r2 = list(r2_by_pid.values())
    values.update({
        "fit_gap_h": f"{FIT_MIN_SINCE_FOOD / 60:g}",
        "r2_median": pct(median(r2)),
        "r2_min": pct(min(r2)),
        "r2_max": pct(max(r2)),
        "r2_min_pid": min(r2_by_pid, key=r2_by_pid.get),
        "still_threshold": f"{move['still_threshold_g']:g}",
        "still_share": pct(STILL_SHARE),
        "still_min_participants": MIN_STILL_PARTICIPANTS,
        "still_meals": move["still_meals"],
        "still_placebos": move["still_placebos"],
        "still_meal_share": pct(move["still_meals"] / m["meals"]),
        "still_placebo_share": pct(move["still_placebos"] / m["placebos"]),
    })
    for key, s in move["results"].items():
        values[f"{key}_participants"] = s["participants"]
        if s["participants"]:
            values[f"{key}_diff"] = f"{s['median_difference']:+.1f}"
            values[f"{key}_positive"] = s["participants_positive"]
            values[f"{key}_p"] = pvalue(s["wilcoxon_p"])
            values[f"{key}_auc"] = pct(s["median_auc"])
    for key, digits in [("glucose", 0), ("hr_peak", 0), ("hr_sustained", 1)]:
        s = main[key]
        values[f"{key}_meal"] = f"{s['median_meal']:+.{digits}f}"
        values[f"{key}_placebo"] = f"{s['median_placebo']:+.{digits}f}"
        values[f"{key}_diff"] = f"{s['median_difference']:+.1f}"
        values[f"{key}_positive"] = s["participants_positive"]
        values[f"{key}_p"] = pvalue(s["wilcoxon_p"])
        values[f"{key}_auc"] = pct(s["median_auc"])
        values[f"sens_{key}_auc"] = pct(sens[key]["median_auc"])
        values[f"big_{key}_auc"] = pct(explore["big_meals"][key]["median_auc"])
    return values


def render_readme(values):
    template = (ROOT / "README.template.md").read_text()
    readme = re.sub(r"\{\{(\w+)\}\}", lambda match: str(values[match.group(1)]), template)
    (ROOT / "README.md").write_text(readme)


def write_outputs(metrics, per):
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    table = pd.concat([p.assign(metric=key) for key, p in per.items() if len(p)], ignore_index=True)
    table.round(4).to_csv(RESULTS / "per_participant.csv", index=False)
    render_readme(display_values(metrics))
