# real_afrobarometer_r8 — Afrobarometer Round 8 merged file, part-2 countries (2021-2022, with COVID-19 module)

Built by `experiments/datasets/builders/real_afrobarometer_r8.py` (raw files in `experiments/datasets/raw/`).

- **Source:** https://www.afrobarometer.org/wp-content/uploads/2023/03/afrobarometer_release-dataset_merge-34ctry_r8_en_2023-03-01.sav (codebook https://www.afrobarometer.org/wp-content/uploads/2025/07/R8_Merge-Codebook_28May24.final_.pdf)
- **Licence / terms:** Afrobarometer data are free to use with citation (afrobarometer.org/data); direct download, no registration. (The same rounds are mirrored on Hugging Face as electricsheepafrica/africa-afrobarometer-<country>, CC-BY-4.0, but that mirror unions columns across rounds, so the official merged file was used.)
- **Citation:** Afrobarometer Data, Round 8 merged data set (34 countries), 2019-2022, release 2023-03-01, available at www.afrobarometer.org.

## Shape

| rows | GIVEN | PREDICT | gated | gated cells (mean share over PREDICT) | split train/dev/test |
|---|---|---|---|---|---|
| 20000 | 9 | 203 | 84 | 0.113 | 15001 / 1500 / 3499 |

## What was done

- Face-to-face, one adult per household; restricted to R8 part-2 countries (the ones carrying the COVID-19 module), random 20,000 respondents; roles stratified by country.
- Codes labelled 'Not applicable ...' (routed past) or 'Not asked in this country' -> NA_GATED when a gate was inferred; 'Missing', 'Refused', 'Don't know' are ordinary levels.
- Dropped: interviewer/admin fields, verbatims, weights, party/ethnic-group lists, the election-specific block, Q10-Q19 (dropped by a prefix rule), tax, media-regulation, China/external-influence blocks (to keep PREDICT near 200).
- Many gates are country-level (an item not fielded in some countries), like UNICEF's Q01 on Country.
- Every cell is a string; no NaN. Item non-response has its own level. Levels under 1% of answers are folded into 'Other'. Roles assigned at random with a fixed seed (75/7.5/17.5%).
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Gates

Inferred from the data: for each item with not-asked cells, the single other item and value set S (values at which most rows hold an answer) that best predicts who was asked; a sibling with exactly the same not-asked rows is not allowed as parent, and the gate graph is acyclic. Accepted if agreement >= 0.6; otherwise the not-asked cells become the ordinary level 'Not asked'. Gates are not a constraint the rows satisfy exactly.

Agreement (share of rows where `answered == parent in observed_if`): median 1.0000, min 0.8845, max 1.0000, 84 gates; 3 below 0.95.

| item | parent | #observed_if | agreement |
|---|---|---|---|
| Q26 | COUNTRY | 2 | 1.0000 |
| Q27 | COUNTRY | 2 | 1.0000 |
| Q29 | COUNTRY | 15 | 1.0000 |
| Q30 | COUNTRY | 15 | 1.0000 |
| Q31 | COUNTRY | 3 | 1.0000 |
| Q35B | Q35A | 1 | 1.0000 |
| Q35D | Q35C | 1 | 0.9999 |
| Q38A | COUNTRY | 15 | 1.0000 |
| Q38B | COUNTRY | 15 | 1.0000 |
| Q38C | COUNTRY | 15 | 1.0000 |
| Q40A | REGION | 46 | 1.0000 |
| Q40B | COUNTRY | 15 | 1.0000 |
| Q40C | COUNTRY | 15 | 1.0000 |
| Q41B | COUNTRY | 15 | 1.0000 |
| Q41D | COUNTRY | 15 | 1.0000 |
| Q41E | COUNTRY | 14 | 1.0000 |
| Q41F | REGION | 46 | 1.0000 |
| Q41K | COUNTRY | 15 | 1.0000 |
| Q42B | COUNTRY | 15 | 1.0000 |
| Q42D | COUNTRY | 15 | 1.0000 |
| Q42H | COUNTRY | 15 | 1.0000 |
| Q44B | Q44A | 1 | 1.0000 |
| Q44C | Q44A | 1 | 1.0000 |
| Q44E | Q44D | 1 | 1.0000 |
| Q44F | Q44D | 1 | 1.0000 |
| Q44H | Q44G | 1 | 1.0000 |
| Q44I | Q44G | 1 | 1.0000 |
| Q44K | Q44J | 1 | 1.0000 |
| Q44L | Q44J | 1 | 1.0000 |
| Q44N | Q44M | 3 | 1.0000 |
| Q51B | COUNTRY | 15 | 1.0000 |
| Q51C | COUNTRY | 14 | 1.0000 |
| Q51D | Q87A | 6 | 0.8845 |
| Q52A | COUNTRY | 14 | 1.0000 |
| Q52B | REGION | 46 | 1.0000 |
| Q53A | COUNTRY | 4 | 1.0000 |
| Q53C | REGION | 46 | 1.0000 |
| Q54C | COUNTRY | 6 | 1.0000 |
| Q72B | Q72A | 1 | 1.0000 |
| Q82A | Q41E | 6 | 0.9865 |
| Q82B | Q41E | 6 | 0.9865 |
| Q82D | Q82C | 3 | 0.9539 |
| Q86E | COUNTRY | 2 | 1.0000 |
| Q87A | COUNTRY | 15 | 1.0000 |
| Q87B | COUNTRY | 15 | 1.0000 |
| Q87C | COUNTRY | 15 | 1.0000 |
| Q87D | COUNTRY | 15 | 1.0000 |
| Q87E | COUNTRY | 15 | 1.0000 |
| Q88 | COUNTRY | 15 | 1.0000 |
| Q89A | COUNTRY | 15 | 1.0000 |
| Q89B | COUNTRY | 2 | 1.0000 |
| Q90 | COUNTRY | 15 | 1.0000 |
| COV1 | COUNTRY | 15 | 1.0000 |
| COV2 | COV1 | 4 | 1.0000 |
| COV3 | COV1 | 4 | 1.0000 |
| COV4 | COUNTRY | 2 | 0.9999 |
| COV5 | COUNTRY | 12 | 0.9379 |
| COV6 | COUNTRY | 12 | 0.9379 |
| COV8 | COV1 | 4 | 1.0000 |
| COV9 | COV1 | 4 | 1.0000 |
| COV10 | COUNTRY | 14 | 0.9845 |
| COV11 | COUNTRY | 14 | 0.9845 |
| COV12 | COV1 | 4 | 1.0000 |
| COV13 | COV1 | 4 | 1.0000 |
| COV14 | COV1 | 4 | 1.0000 |
| COV15 | COV1 | 4 | 1.0000 |
| COV16 | COV1 | 4 | 1.0000 |
| COV17 | COV1 | 4 | 1.0000 |
| COV18 | COV1 | 4 | 1.0000 |
| COV19 | COV1 | 4 | 1.0000 |
| COV20 | COV1 | 4 | 1.0000 |
| COV21 | COV1 | 4 | 1.0000 |
| COV22 | COV1 | 4 | 1.0000 |
| COV23 | COV1 | 4 | 1.0000 |
| COV24 | COV1 | 4 | 1.0000 |
| Q91A | REGION | 46 | 1.0000 |
| Q92G | Q92F | 1 | 1.0000 |
| Q94B | Q94A | 1 | 1.0000 |
| Q94D | Q94C | 1 | 1.0000 |
| Q94E | Q94C | 1 | 1.0000 |
| Q95B | Q95A | 2 | 1.0000 |
| Q95D | Q95C | 10 | 0.9964 |
| Q96C | Q96B | 11 | 1.0000 |
| Q98B | Q98A | 20 | 0.9954 |

Items with not-asked cells but no accepted gate (not-asked kept as ordinary level 'Not asked'; None = fewer than 1% of cells): Q82C (None), Q96A (None), DemandDemo (None), SupplyDemo (None)

## Scores (phase 2: TRAIN+DEV visible, TEST scored; `experiments/eval/run.py`)

| submission | skill | s.e. | seconds |
|---|---|---|---|
| external_model | FAIL |  | 3.4 |
| external_model_clipped | 0.1501 | 0.0021 | 4.6 |
| v1_learned_gates | 0.1235 | 0.0019 | 240.7 |
| v2_joint | 0.1761 | 0.002 | 845.0 |

`external_model` is the organisers' baseline as shipped; on datasets with chained gates it returns -2.2e-16 in the NA_GATED slot and the scorer rejects it (FAIL). `external_model_clipped` is the same code with outputs clipped at 0 (scratchpad wrapper). v1/v2 have run-time guards, so on a busy machine they may fit fewer questions; see the dataset notes in the hand-off report.
