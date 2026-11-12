# Local evaluation

The hosted grader never shows logs and returns dev scores noised and rounded, so every
modelling choice was made on local datasets with known answers, scored with the
organisers' own functions (`starter-kit/score.py`, pinned as a submodule at `aa03186`).

```bash
git submodule update --init          # organisers' starter kit
pip install -r requirements-dev.txt
python scripts/fetch_tabicl.py       # checkpoint into submission/

# build a dataset (see experiments/datasets/README.md), then score a submission on it
python experiments/eval/run.py submission experiments/datasets/wb_realistic --phase 2
# rehearse the hosted run: import once, call predict() for several surveys under one clock
python experiments/eval/run_three.py submission 2 rehearsal unicef_realistic wb_realistic unhcr_full
# where a submission loses against the true generating probabilities (fabricated UNHCR-like data)
python experiments/eval/gap_unhcr.py submission --phase 1
```

| File | What it does |
|---|---|
| `eval/run.py` | Scores one submission on one dataset and phase; appends a row to `results.csv`. |
| `eval/run_three.py` | Imports a submission once and calls `predict()` for several datasets in turn, as the hosted orchestrator does; reports the total wall-clock from import. |
| `eval/run_matrix.py` | Runs `run.py` over a list of datasets, one at a time under a memory cap (Linux: `flock` + `systemd-run`). |
| `eval/by_item.py` | Per-question skill of a submission, next to the best possible where it is known. |
| `eval/gap_unhcr.py` | Regenerates a fabricated UNHCR-like dataset from its builder, computes the true P(answer given GIVEN) per cell, and splits the submission's shortfall by row and question type. |
| `eval/results.csv` | Every local run we made (submission version, dataset, phase, skill, standard error, seconds). The tables in the paper come from this file. |

Submission versions in `results.csv` are named `vN_*`; the final one is `v13_top`, whose
code is `submission/main.py`. Rows tagged `callK_of_N` come from `run_three.py`.
