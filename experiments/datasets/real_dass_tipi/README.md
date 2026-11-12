# real_dass_tipi — Open-Source Psychometrics Project: DASS-42 + TIPI + vocabulary check list, 2017-2019

Built by `experiments/datasets/builders/real_dass_tipi.py` (raw files in `experiments/datasets/raw/`).

- **Source:** https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip
- **Licence / terms:** No licence named; the raw-data page releases the data 'for general public edification', anonymous, collected with research consent. No registration.
- **Citation:** Open-Source Psychometrics Project, DASS (Depression Anxiety Stress Scales) online data, collected 2017-2019, https://openpsychometrics.org/_rawdata/.

## Shape

| rows | GIVEN | PREDICT | gated | gated cells (mean share over PREDICT) | split train/dev/test |
|---|---|---|---|---|---|
| 20000 | 13 | 80 | 0 | 0.000 | 15000 / 1500 / 3500 |

## What was done

- One row per respondent, random 20,000 of 39,775.
- Derived PREDICT items mimic the World Bank file's score bands: DASS-42 severity bands (standard cut-offs), TIPI trait quintiles, vocabulary-score band, test-duration quintile.
- No routed items in this instrument, so no gates (the World Bank file has 40).
- Every cell is a string; no NaN. Item non-response has its own level. Levels under 1% of answers are folded into 'Other'. Roles assigned at random with a fixed seed (75/7.5/17.5%).
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Gates

None.

## Scores (phase 2: TRAIN+DEV visible, TEST scored; `experiments/eval/run.py`)

| submission | skill | s.e. | seconds |
|---|---|---|---|
| external_model | 0.0138 | 0.0017 | 1.9 |
| v1_learned_gates | 0.0309 | 0.0016 | 86.5 |
| v2_joint | 0.0336 | 0.0016 | 96.8 |

`external_model` is the organisers' baseline as shipped; on datasets with chained gates it returns -2.2e-16 in the NA_GATED slot and the scorer rejects it (FAIL). `external_model_clipped` is the same code with outputs clipped at 0 (scratchpad wrapper). v1/v2 have run-time guards, so on a busy machine they may fit fewer questions; see the dataset notes in the hand-off report.
