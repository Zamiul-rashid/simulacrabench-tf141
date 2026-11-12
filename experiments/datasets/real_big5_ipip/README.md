# real_big5_ipip — Open-Source Psychometrics Project BIG5: 50-item IPIP Big-Five markers, c. 2012

Built by `experiments/datasets/builders/real_big5_ipip.py` (raw files in `experiments/datasets/raw/`).

- **Source:** http://openpsychometrics.org/_rawdata/BIG5.zip
- **Licence / terms:** No licence named; released 'for general public edification', anonymous, research consent at collection; IPIP items are public domain. No registration.
- **Citation:** Open-Source Psychometrics Project, BIG5 data (IPIP Big-Five Factor Markers), c. 2012, https://openpsychometrics.org/_rawdata/.

## Shape

| rows | GIVEN | PREDICT | gated | gated cells (mean share over PREDICT) | split train/dev/test |
|---|---|---|---|---|---|
| 19719 | 7 | 55 | 0 | 0.000 | 14789 / 1479 / 3451 |

## What was done

- One row per respondent, all 19,719.
- Derived PREDICT items: quintile bands of the five trait scores (mean of 10 items, reverse-keyed).
- No routed items, so no gates.
- Every cell is a string; no NaN. Item non-response has its own level. Levels under 1% of answers are folded into 'Other'. Roles assigned at random with a fixed seed (75/7.5/17.5%).
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Gates

None.

## Scores (phase 2: TRAIN+DEV visible, TEST scored; `experiments/eval/run.py`)

| submission | skill | s.e. | seconds |
|---|---|---|---|
| external_model | -0.0025 | 0.0017 | 1.5 |
| v1_learned_gates | 0.0151 | 0.0015 | 240.8 |
| v2_joint | 0.0195 | 0.0015 | 118.9 |

`external_model` is the organisers' baseline as shipped; on datasets with chained gates it returns -2.2e-16 in the NA_GATED slot and the scorer rejects it (FAIL). `external_model_clipped` is the same code with outputs clipped at 0 (scratchpad wrapper). v1/v2 have run-time guards, so on a busy machine they may fit fewer questions; see the dataset notes in the hand-off report.
