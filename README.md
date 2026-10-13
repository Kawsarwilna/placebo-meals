# Placebo meals

**Does a heart rate "meal response" actually come from the meal? A placebo test on public wearable data.**

Wellness wearables often describe how your body responds to food, and the change in heart rate after eating is a common way to measure it. This project checks whether that change belongs to the meal at all.

It scores real meals and *placebo moments* in exactly the same way. A placebo moment is a food-free time at the same time of day, on a different day, for the same person. If the response is about food, real meals should score clearly higher.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/figure-dark.png">
  <img alt="Glucose rises after real meals but not after placebo moments. Heart rate looks the same after both, and real meals outscore placebos about half the time." src="results/figure-light.png">
</picture>

## Result

**Glucose passes the placebo test. Heart rate does not.**

| Score | After real meals | After placebo moments | Difference | Real meal scores higher |
|---|---|---|---|---|
| Glucose peak: highest in the 3 h after, minus the 30 min before | +44 mg/dL | +11 mg/dL | +35.0 mg/dL | 84% of the time |
| Heart rate peak: same definition | +48 bpm | +52 bpm | -3.0 bpm | 45% of the time |
| Heart rate average: 30 to 120 min after, minus the 30 min before | +1.5 bpm | +0.4 bpm | -0.6 bpm | 49% of the time |

How to read the table:

- **Every value is a median across 15 people.** Each person is summarized first.
- **"Difference"** is each person's average after real meals minus their average after placebo moments.
- **"Real meal scores higher"** is the chance that one of a person's real meals beats one of their placebo moments. 50% is a coin flip.

Across people:

- **Glucose** is higher after real meals for 13 of 15 people (p < 0.001, Wilcoxon signed-rank test).
- **Heart rate peak** is higher after real meals for 5 of 15 (p = 0.12).
- **Heart rate average** is higher after real meals for 7 of 15 (p = 0.89).

**What it means.** In everyday wrist data, the heart rate peak after a meal is about +48 bpm, which looks like a strong response. Food-free moments show +52 bpm. The likely reason is that a peak over 3 hours picks up movement, such as walking or standing up, plus sensor noise. The movement check below tests this directly.

Without a placebo comparison, a heart rate meal response can look convincing while measuring something else. Glucose, scored the same way, separates meals from placebos easily, which shows the test itself works.

## Movement check

The wristband also records motion, so I repeated the test in two ways that take movement out of the picture. Both were planned and written down before running them. See "Movement check" in [CLAUDE.md](CLAUDE.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/movement-dark.png">
  <img alt="After removing movement, heart rate after real meals and after placebo moments still looks similar, and real meals outscore placebos only a little more often than a coin flip." src="results/movement-light.png">
</picture>

1. **Movement removed.**
   - For each person, a simple model predicts heart rate from wrist movement over the current and previous 15 minutes.
   - It is fitted only on minutes at least 3 hours after eating, so a meal effect can't leak in.
   - Movement explains a median 35% of minute-to-minute heart rate variation (range 0% to 60%). The lowest is participant 013, whose heart rate has frequent sensor spikes.
   - The placebo test then runs on what movement doesn't explain:
     - Heart rate peak: a real meal scores higher 55% of the time (7 of 15 people higher, p = 0.98).
     - Heart rate average: 57% of the time (11 of 15 people higher, median difference +1.8 bpm, p = 0.07).
2. **Still periods only** (exploratory).
   - The plan was to keep meals and placebo moments where at least 80% of minutes were still, both in the 30 min before and from 30 to 120 min after.
   - **People rarely sit still after eating.** Even with the loosest planned threshold (0.1 g), only 27 of 167 meals (16%) passed, compared with 241 of 644 placebo moments (37%).
   - That leaves only 7 people with enough data, below the planned minimum of 8, so this comparison is exploratory only:
     - Heart rate average: a real meal scores higher 48% of the time.
     - Glucose in the same windows, as a check: 89%.

**What it means.** Removing movement doesn't rescue the peak metric, so the large peak "response" was never about the meal. The calmer average shows a hint: with movement removed, heart rate after real meals was higher for 11 of 15 people, by a median of +1.8 bpm. A small rise after eating is expected physiology, so the hint is plausible.

The evidence is weak, though (p = 0.07), and a single real meal beats a placebo moment only 57% of the time. Any real heart rate effect here is small on average, and far too small next to everyday movement to say anything about one meal.

## What I'd do next

- **Test the small average effect properly.** Use the same standardized meal on several days, with people seated for 2 hours afterward, against matched no-meal sessions. That is the cleanest way to confirm or rule out the small heart rate rise hinted at above.
- **Score every meal response against a personal placebo baseline.** Use the same person, the same time of day and no food. It costs little and flags responses that aren't about food.
- **Run the same test on other signals.** Candidates include skin temperature and EDA, both in this dataset, and sensors placed closer to digestion.

## How it works

1. **Data.** According to the dataset description:
   - 16 adults aged 35 to 65, with HbA1c in the high-normal to prediabetic range, recorded for 8 to 10 days each.
   - Heart rate from an Empatica E4 wristband, averaged per minute here.
   - Glucose from a Dexcom G6, every 5 minutes.
   - Timestamped food logs.
2. **Meals.** Food items logged within 30 minutes of each other form one meal. A meal counts as *clean* when nothing else was eaten from 2 hours before to 3 hours after it starts. That leaves 167 clean meals.
3. **Placebo moments.** For each clean meal, 5 moments that pass the same food-free rule, on other days, within 60 minutes of the meal's clock time. That gives 644 placebo moments.
4. **Scores.** Each moment is compared with the 30 minutes before it in two ways:
   - Peak: the highest value in the next 3 hours.
   - Average: the mean from 30 to 120 minutes after.
5. **Statistics.** Each person's real meals are compared with their own placebo moments first. Then the results are summarized across people.
6. **Checks.**
   - Every included participant's heart rate is lowest between 3 and 7 am, so the device clocks are in local time.
   - Glucose peaks a median of 63 minutes after logged meals, so meal times line up with the sensors.

15 of 16 people are included, meaning they have at least 3 clean meals with usable heart rate and glucose. Participant 015 is excluded: their food log and glucose recording overlap for 0 hours.

The analysis rules were written down before looking at any heart rate result. They are listed under "Analysis decisions" in [CLAUDE.md](CLAUDE.md), and the commit history shows when they were added.

## Robustness

- **Leaving out the 2 people whose glucose check failed** (012, 016): real meals outscore placebos 86% of the time for glucose, 46% for heart rate peak and 47% for heart rate average.
- **Exploratory checks** (not part of the fixed rules):
  - Smoothing heart rate over 5 minutes before taking the peak: 51%.
  - Large meals only (the top third, at least 617 kcal, 12 people): 97% for glucose, 48% for heart rate peak and 32% for heart rate average.

## Limitations

- **Wrist, not torso.** The E4 derives heart rate from an optical sensor that is noisy during movement.
- **Approximate movement control.** A linear model of wrist motion can't remove everything that moves heart rate, such as posture, stress or caffeine. Wrist motion also misses movement the wrist doesn't make.
- **Self-reported food logs.** An unlogged snack would make a placebo moment look more like a meal. That would blur glucose too, and glucose still separates clearly, so the logs look mostly reliable.
- **Small sample.** 15 people, about a week each.
- **No repeatability measure.** The dataset's repeated standard breakfast couldn't be used for this. Only 3 of them passed the clean-window rule, from 2 people.
- **Not medical advice.** This is an analysis of a public research dataset for general wellness interest. It makes no claim about any specific product.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/download.py
.venv/bin/python src/motion.py
.venv/bin/python run_all.py
```

`src/motion.py` streams the 13 GB of raw accelerometer files once, checks each against its published checksum and keeps only a per-minute movement summary (about 7 MB). `run_all.py` writes `results/metrics.json`, `results/per_participant.csv`, all figures and this README. Every result above comes from that run. To run the tests: `.venv/bin/python -m pytest -q`.

## Data and credit

- Cho P, Kim J, Bent B, Dunn J. *BIG IDEAs Lab Glycemic Variability and Wearable Device Data* (version 1.1.3). PhysioNet, 2026. https://doi.org/10.13026/aw6y-fc44
- Bent B, Cho PJ, Henriquez M, et al. Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches. *npj Digital Medicine* 4, 89 (2021).
- Goldberger A, et al. PhysioBank, PhysioToolkit, and PhysioNet. *Circulation* 101(23): e215-e220 (2000).

The data is under the Open Data Commons Attribution License v1.0 and is not included in this repository. The code is MIT licensed.

Built by Kawsar Nabawi.
