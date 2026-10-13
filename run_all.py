"""Run the whole analysis: windows, statistics, figures, metrics.json and README.md."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from analyze import all_windows, curves
from figure import DARK, LIGHT, make_figure
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
    write_outputs(metrics, per)
    print(f"done: {metrics['participants']} participants, {metrics['meals']} meals, {metrics['placebos']} placebos")


if __name__ == "__main__":
    main()
