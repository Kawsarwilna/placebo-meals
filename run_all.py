"""Run the whole analysis: windows, statistics, figures, metrics.json and README.md."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from analyze import all_windows, curves
from figure import DARK, LIGHT, make_figure, make_movement_figure
from report import RESULTS, build_metrics, write_outputs


def main():
    table = all_windows()
    metrics, per = build_metrics(table)
    curve_table = curves(table)

    RESULTS.mkdir(exist_ok=True)
    subtitle = (
        f"{metrics['participants']} adults, {metrics['meals']} clean meals vs {metrics['placebos']} "
        "time-matched placebo moments. Lines: mean across people. Bands: ±1 standard error."
    )
    make_figure(curve_table, per, subtitle, LIGHT, RESULTS / "figure-light.png")
    make_figure(curve_table, per, subtitle, DARK, RESULTS / "figure-dark.png")

    move = metrics["movement"]
    movement_subtitle = (
        f"Movement model fitted per person on food-free minutes. Still periods: {move['still_meals']} meals, "
        f"{move['still_placebos']} placebo moments. Lines: mean across people. Bands: ±1 standard error."
    )
    make_movement_figure(curve_table, per, movement_subtitle, LIGHT, RESULTS / "movement-light.png")
    make_movement_figure(curve_table, per, movement_subtitle, DARK, RESULTS / "movement-dark.png")
    write_outputs(metrics, per)
    print(f"done: {metrics['participants']} participants, {metrics['meals']} meals, {metrics['placebos']} placebos")


if __name__ == "__main__":
    main()
