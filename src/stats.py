"""Compare real meals with placebo moments, within each participant first."""

import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon


def auc(meal_values, placebo_values):
    """Chance that a random real meal scores higher than a random placebo moment (ties count half)."""
    return mannwhitneyu(meal_values, placebo_values).statistic / (len(meal_values) * len(placebo_values))


def per_participant(table, metric, meal_filter=None):
    rows = []
    for pid, d in table.groupby("pid"):
        meals = d[d["kind"] == "meal"]
        if meal_filter is not None:
            meals = meals[meal_filter(meals)]
        meal_values = meals[metric].dropna()
        placebo_values = d.loc[d["kind"] == "placebo", metric].dropna()
        if len(meal_values) < 2 or len(placebo_values) < 2:
            continue
        rows.append({
            "pid": pid,
            "meals": len(meal_values),
            "placebos": len(placebo_values),
            "meal_mean": meal_values.mean(),
            "placebo_mean": placebo_values.mean(),
            "difference": meal_values.mean() - placebo_values.mean(),
            "auc": auc(meal_values, placebo_values),
        })
    return pd.DataFrame(rows)


def summarize(per):
    return {
        "participants": len(per),
        "median_meal": float(per["meal_mean"].median()),
        "median_placebo": float(per["placebo_mean"].median()),
        "median_difference": float(per["difference"].median()),
        "participants_positive": int((per["difference"] > 0).sum()),
        "wilcoxon_p": float(wilcoxon(per["difference"]).pvalue),
        "median_auc": float(per["auc"].median()),
        "mean_auc": float(per["auc"].mean()),
    }
