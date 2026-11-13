# SimulacraBench 2026: team TF141

Our entry to [SimulacraBench](https://simulacrabench.org), the NeurIPS 2026 competition on
completing survey responses. For every hidden cell of three surveys (UNICEF, World Bank,
UNHCR), the submission returns a probability vector over the answer options, using only the
respondent's GIVEN columns and the fully visible respondents.

| | Mean skill | UNICEF | World Bank | UNHCR |
|---|---|---|---|---|
| Development leaderboard (noised, rounded) | 0.4893 | 0.3499 | 0.2335 | 0.8843 |
| Test phase | *to be added* | | | |

The technical report is [`paper/main.pdf`](paper/main.pdf).

## Method in one paragraph

Each cell is scored on its own with a proper log score, so the target is
P(answer | GIVEN columns) for every question, fitted at run time on the visible rows.
Five model families are fitted inside `predict()`: a shared multi-head network, a wider
network, a similarity model with learned column weights, per-question logistic regression,
and the pretrained in-context learner TabICL v2 (inference only). They are blended per
question by a linear pool with EM weights, averaged with a geometric pool. A similarity layer
is applied on top only when a split-half test on held-back rows shows a clear gain. "Not
asked" is learned as an ordinary answer, exact skip rules are applied where the data never
break them, and a last step corrects for the grader's probability floor. One clock is shared
by the three surveys, and time a survey does not use flows to the next.

## Repository

| Path | What |
|---|---|
| `submission/` | The submitted `main.py` (byte-identical to the uploaded archive) and `requirements.txt`. |
| `scripts/fetch_tabicl.py` | Downloads the TabICL v2 checkpoint from a pinned Hugging Face revision and checks its SHA-256. |
| `scripts/build_zip.sh` | Rebuilds the exact archive that was uploaded. |
| `experiments/eval/` | Local scoring tools (organisers' scorer), the rehearsal of the hosted run, the gap analysis, and `results.csv`, the log of every local run. See [`experiments/README.md`](experiments/README.md). |
| `experiments/datasets/` | Builders for every local test dataset and a README per dataset with source and licence. No data is committed. |
| `paper/` | The technical report (LaTeX source, official template). |
| `starter-kit/` | The organisers' starter kit, as a submodule pinned at `aa03186`. |

## Reproduce

```bash
git clone --recurse-submodules https://github.com/Zamiul-rashid/simulacrabench-tf141 && cd simulacrabench-tf141
conda create -y -p .venv python=3.13 && conda activate ./.venv     # or any Python 3.13
pip install -r requirements-dev.txt

# 1. rebuild the submitted archive (downloads and verifies the checkpoint)
bash scripts/build_zip.sh                     # -> tf141_submission.zip

# 2. check it the way the hosted ingestion does
python starter-kit/tools/check_submission_zip.py tf141_submission.zip

# 3. run it on practice data in the official format
python starter-kit/make_sandbox.py --schema starter-kit/data/world_bank.json \
       --config starter-kit/config.yml --out _sandbox/world_bank
python starter-kit/score.py --submission submission --data _sandbox/world_bank \
       --schema starter-kit/data/world_bank.json --config starter-kit/config.yml --phase 2
```

The real survey microdata are held by the organisers and never leave their servers; test-phase
predictions are produced by their runner calling `submission/main.py`.

The number of TabICL rounds completed depends on the machine's speed, so results can vary
slightly between machines. Set `SB_FULL_PASSES` (rounds) and `SB_CLOCK_SECONDS` (time
budget) to pin them.

## Data use

The submission reads only the frame the organisers pass to `predict()`. External public
datasets (listed in [`experiments/datasets/README.md`](experiments/datasets/README.md)) were
used offline, only to compare model designs. We made no attempt to re-identify respondents
or link records to external sources, and we redistribute no microdata.

## Licence

MIT (see `LICENSE`). The TabICL checkpoint is BSD-3-Clause and is downloaded, not
redistributed here. Each external dataset keeps its own licence.
