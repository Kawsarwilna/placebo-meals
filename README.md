# Placebo meals

**A placebo test for heart rate meal responses, run on public wearable data.**

Wearables that report meal responses need a way to check that the response comes from the meal. To check heart rate, I scored real meals and *placebo moments* the same way. A placebo moment is a time when the same person ate nothing, at the same time of day as a real meal but on a different day. If heart rate responds to food, real meals should score higher.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/figure-dark.png">
  <img alt="Glucose rises after real meals but not after placebo moments. Heart rate looks the same after both, and real meals outscore placebos about half the time." src="results/figure-light.png">
</picture>

## Result

**Glucose rises far more after real meals than after placebo moments. Heart rate shows no difference.**

| Score | After real meals | After placebo moments | Difference | Real meal scores higher |
|---|---|---|---|---|
| Glucose peak: highest in the 3 h after, minus the 30 min before | +44 mg/dL | +11 mg/dL | +35.0 mg/dL | 85% of the time |
| Heart rate peak: same definition | +48 bpm | +50 bpm | -0.5 bpm | 49% of the time |
| Heart rate average: 30 to 120 min after, minus the 30 min before | +1.5 bpm | -0.8 bpm | -1.4 bpm | 49% of the time |

How to read the table:

- **Every value is a median across 15 people**, taken after summarizing each person.
- **"Difference"** is a person's average after real meals minus their average after placebo moments.
- **"Real meal scores higher"** is the chance that one of a person's real meals beats one of their placebo moments. 50% is a coin flip.

Across people:

- **Glucose** is higher after real meals for 14 of 15 people (p < 0.001, Wilcoxon signed-rank test).
- **Heart rate peak** is higher for 6 of 15 (p = 0.23).
- **Heart rate average** is higher for 6 of 15 (p = 0.80).

**What it means.** In everyday wrist data, the heart rate peak after a meal reaches about +48 bpm, which looks like a strong response. Placebo moments reach +50 bpm. A 3-hour peak catches movement, like walking or standing up, along with sensor noise. The movement check below tests that.

Without a placebo comparison, you would read that +48 bpm as a meal response. Glucose, scored the same way, separates meals from placebo moments, so the test can detect a real effect.

These results rule out a large heart rate response to meals in this data. A smaller one could still hide below the detection limits listed under Limitations.

## Movement check

The wristband also records motion, so I repeated the test in two ways that take movement out of the picture. I wrote both down in [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) before running them.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/movement-dark.png">
  <img alt="With movement removed, heart rate after real meals and after placebo moments still looks similar, and real meals outscore placebos a little more often than a coin flip." src="results/movement-light.png">
</picture>

1. **Movement removed.**
   - For each person, I fit a model that predicts heart rate from wrist movement over the current and previous 15 minutes.
   - I fit it on minutes at least 3 hours after eating, so a meal effect can't leak in.
   - Movement explains a median 35% of minute-to-minute heart rate variation (range 0% to 60%). The lowest is participant 013, whose heart rate has frequent sensor spikes.
   - I then ran the placebo test on the heart rate that movement doesn't explain:
     - Heart rate peak: a real meal scores higher 48% of the time (7 of 15 people higher, p = 0.89).
     - Heart rate average: 61% of the time (11 of 15 people higher, median difference +1.9 bpm, p = 0.28).
2. **Still periods** (exploratory).
   - I planned to keep meals and placebo moments where at least 80% of minutes were still, both in the 30 min before and from 30 to 120 min after.
   - **People kept moving after most meals.** With the loosest planned threshold (0.1 g), 27 of 167 meals (16%) passed, against 193 of 504 placebo moments (38%).
   - That left 7 people with enough data, under the planned minimum of 8, so I report this comparison as exploratory:
     - Heart rate average: a real meal scores higher 51% of the time.
     - Glucose in the same windows, as a check: 88%.

**What it means.** With movement removed, the peak still can't tell meals from placebo moments, so the large peak comes from something other than the meal.

The average leans toward real meals. With movement removed, heart rate after real meals was higher for 11 of 15 people, by a median of +1.9 bpm, and a real meal wins 61% of the time.

The evidence is weak (p = 0.28). The lean also shrinks to 54% when you restrict the test to lunch and dinner, so early-morning and late-night timing around sleep may explain it better than food does. Either way, an effect this small can't tell you anything about a single meal.

## What I'd do next

- **Look for a small heart rate effect under controlled conditions.** Give people the same standardized meal on several days, keep them seated for 2 hours afterward and compare against matched no-meal sessions. That would confirm or rule out the small lean seen above.
- **Score each meal response against a personal placebo baseline.** Use food-free moments from the same person at the same time of day. The comparison costs little and catches responses that have nothing to do with food.
- **Run the same test on other signals.** Skin temperature and EDA sit in this dataset already, and sensors closer to digestion are the obvious next candidates.

## How it works

1. **Data.** From the dataset description:
   - 16 adults aged 35 to 65, with HbA1c in the high-normal to prediabetic range, recorded for 8 to 10 days each.
   - Heart rate from an Empatica E4 wristband, which I averaged per minute.
   - Glucose from a Dexcom G6, every 5 minutes.
   - Timestamped food logs.
2. **Meals.** Food items logged within 30 minutes of each other form one meal. A meal counts as *clean* when the person ate nothing else from 2 hours before to 3 hours after it started. That leaves 167 clean meals.
3. **Placebo moments.** For each clean meal, I picked 5 moments that pass the same food-free rule, on other days, within 60 minutes of the meal's clock time. That gives 504 placebo moments.
4. **Scores.** I compared each moment with the 30 minutes before it in two ways:
   - Peak: the highest value in the next 3 hours.
   - Average: the mean from 30 to 120 minutes after.
5. **Statistics.** I compared each person's real meals with their own placebo moments, then summarized across people.
6. **Checks.**
   - Every included participant's heart rate bottoms out between 3 and 7 am, so the device clocks run on local time.
   - Glucose peaks a median of 63 minutes after logged meals, so the meal times line up with the sensors.

I included 15 of 16 people, the ones with at least 3 clean meals with usable heart rate and glucose. I left out participant 015, whose food log and glucose recording overlap for 0 hours.

I wrote the analysis rules down before looking at any heart rate result. They are in [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md), with links to the commits that added them.

## Robustness

- **Leaving out the 1 person whose glucose check failed** (012): real meals outscore placebos 85% of the time for glucose, 49% for heart rate peak and 47% for heart rate average.
- **Exploratory checks**, outside the fixed rules:
  - Different random draws of placebo moments (10 draws): real meals outscore placebos 80% to 85% of the time for glucose, 47% to 52% for heart rate peak, 48% to 56% for heart rate average and 54% to 63% for the movement-removed average.
  - Lunch and dinner (moments starting between 11:00 and 21:00, 12 people): 77% for glucose, 42% for heart rate peak, 46% for heart rate average and 54% for the movement-removed average.
  - Smoothing heart rate over 5 minutes before taking the peak: 51%.
  - Large meals (the top third, at least 617 kcal, 12 people): 97% for glucose, 46% for heart rate peak and 32% for heart rate average.

## Limitations

- **One dataset, built for another question.** The BIG IDEAs study collected these recordings to estimate glucose from wearables, so the meals were free-living and uncontrolled. The participants, adults aged 35 to 65 with HbA1c in the high-normal to prediabetic range, don't represent everyone. I haven't repeated this test on a second dataset yet.
- **Detection limits.**
  - The test has 15 people with a median of 11 clean meals each (range 4 to 17).
  - At 80% power, it can reliably detect average differences of about 13 mg/dL for glucose, 7 bpm for heart rate peak, 4 bpm for heart rate average and 5 bpm for the movement-removed average.
  - Glucose cleared its limit by a wide margin. A heart rate effect from digestion of a few beats per minute would fall below these limits, so measuring one takes a bigger or controlled study.
- **Wrist sensor.** The E4 measures heart rate optically at the wrist, and the signal gets noisy during movement.
- **Approximate movement control.** A linear model of wrist motion leaves in other things that change heart rate, like posture, stress or caffeine. It also misses movement that doesn't involve the wrist.
- **Self-reported food logs.** An unlogged snack would make a placebo moment look more like a meal. Snacks like that would blur the glucose result too, and glucose still separates meals from placebo moments, so the logs hold up well enough for this test.
- **Sleep around placebo moments.** 18% of placebo moments started while the person lay still, probably asleep, against 8% of meals. Leaving those moments out gives 48% for heart rate peak and 44% for heart rate average.
- **No repeatability measure.** I couldn't use the dataset's repeated standard breakfast for this, because 3 of them passed the clean-window rule, from 2 people.
- **Not medical advice.** This is an analysis of a public research dataset for general wellness interest. It makes no claim about any specific product.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/download.py
.venv/bin/python src/motion.py
.venv/bin/python run_all.py
```

`src/motion.py` streams the 13 GB of raw accelerometer files once, checks each against its published checksum and keeps a per-minute movement summary of about 7 MB.

`run_all.py` writes `results/metrics.json`, `results/per_participant.csv`, the figures and this README. Every result above comes from that run. To run the tests: `.venv/bin/python -m pytest -q`.

## Data and credit

- Cho P, Kim J, Bent B, Dunn J. *BIG IDEAs Lab Glycemic Variability and Wearable Device Data* (version 1.1.3). PhysioNet, 2026. https://doi.org/10.13026/aw6y-fc44
- Bent B, Cho PJ, Henriquez M, et al. Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches. *npj Digital Medicine* 4, 89 (2021).
- Goldberger A, et al. PhysioBank, PhysioToolkit, and PhysioNet. *Circulation* 101(23): e215-e220 (2000).

The data is under the Open Data Commons Attribution License v1.0 and is not included in this repository. The code is MIT licensed.

Built by [Kawsar Nabawi](https://kawsarnabawi.com).
