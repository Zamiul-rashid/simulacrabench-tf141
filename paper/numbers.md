# Where every number in the report comes from

Paths are relative to the repository root. `results.csv` = `experiments/eval/results.csv`;
`logs/` = `experiments/eval/logs/`. "Last default run" = the last `PASS` row for that
submission, dataset and phase whose tag is not a budget, clock, gate-variant or review-check tag.

## Abstract, Table 3 (leaderboard)

| Number | Source |
|---|---|
| 0.4893 / 0.3499 / 0.2335 / 0.8843 | Development leaderboard, `v13_top` upload of 2026-11-12; `experiments/eval/dev_submissions.csv` |
| "adds about 0.001 skill locally" | Table 7 replicate pairs (+0.0012, `logs/review_paired.log`) and Table 6 fresh draw (+0.0018, +0.0014) |
| Test-phase scores 0.49 / 0.34 / 0.23 / 0.88 | Test-phase leaderboard, submission 1053552 (2026-11-15), displayed to two decimals; `experiments/eval/dev_submissions.csv` |
| Commit a4b0588 | `git rev-parse test-submission` |

## Section 1

| Number | Source |
|---|---|
| ε = 10⁻³, scoring and skill formula | `starter-kit/config.yml` (`scoring.floor`), `starter-kit/score.py` |
| 20% blend fold, 5 folds | `submission/main.py` (`N_FOLDS`, `blend_rows = fold == 0`) |
| UNHCR gate agreement 29–98% | UNHCR schema notes in the organisers' starter kit |
| 128 / 384×384 units, 40 pseudo-rows, exponents in [0, 3], strengths {0, 0.5, 1, 1.5}, n ≥ 20 | `submission/main.py` (see Table 5 for line-level detail) |
| 2 SE threshold, 2.5 variant tried | `submission/main.py` (`TOP_Z`); `results.csv` tag `v13d_z2.5` |

## Section 2

| Number | Source |
|---|---|
| Checkpoint revision and SHA-256 | `scripts/fetch_tabicl.py` |
| 2778 s full test-phase rehearsal | `logs/v13_crash_time_memory_checks.log` (`TOTAL 2778s`); `results.csv` tag `v13_final_rehearsal` |
| 3.5 GB peak, 20,000-row 203-question survey | `logs/v13_crash_time_memory_checks.log` (`peak 3.53 GB`, Afrobarometer); `experiments/datasets/real_afrobarometer_r8/README.md` |
| Table 2 rows and licences | each `experiments/datasets/<name>/README.md` |

## Section 3

| Number | Source |
|---|---|
| 0.2486 top World Bank step | Codabench "Best scores by instrument" page, snapshot 2026-10-27, anonymised in `experiments/eval/leaderboard_steps_2026-10-27.md` |
| 0.015 step | difference of adjacent published World Bank values (0.2486 − 0.2335) |
| 0.0033 World Bank-like gap | `experiments/datasets/wb_realistic/ceiling.json` (phase 2: 0.1805) minus `results.csv` v13 `wb_realistic` phase 2 (0.1772) |

## Section 4

| Number | Source |
|---|---|
| main.py SHA-256 | `README.md` table; recompute with `sha256sum submission/main.py` |
| UNHCR-like 0.7005–0.7023, World Bank-like 0.1656–0.1660 across survey orders | `results.csv` tags `v12b_*` (three orders of the three-survey run) |

## Appendix B

| Number | Source |
|---|---|
| Table 4 v0 row | `results.csv` `external_model` rows (the organisers' baseline) |
| Table 4 cells | `results.csv`, last default run per version; v13 UNHCR-like `v13e_honest`; footnoted exceptions: v7 UNHCR (`v7test_longbudget`), v12 (`v12b_*` three-survey runs; CPS `v12_same_clock`), v13 UNICEF (`v13test`) |
| Table 4 Dev board column | `experiments/eval/dev_submissions.csv` |
| Table 6 (held-out), incl. v1 column | `results.csv` tags `heldout_wb`, `heldout_fresh`, `heldout_fresh_top0`, `heldout_fresh_r2`, `heldout_fresh_top0_r2`; deltas from `experiments/eval/paired.py` on the `--dump` files; printout in `logs/review_paired.log` |
| Stack Overflow 2018 s3: LR dropped on 17 of 79 questions | `logs/review_runs.log` (`[heldout_wb v13_top real_wb_so2018_s3 p1] [v13] dropped:`) |
| fCC 2016 z = 2.6, SO s3 z = −2.9 | `logs/review_paired.log` (`# real_wb_fcc2016_s2`, `# real_wb_so2018_s3`) |
| Table 7 (gate): off/on, Δ | UNHCR-like and CPS: mean of `results.csv` tags `gate_*_r2`, `gate_*_r3` (UNHCR-like) and `gate_*`, `gate_*_r2` (CPS); other rows `gate_off`, `gate_on`; Δ from `logs/review_paired.log` (section "Replicates") |
| First UNHCR-like pair 0.7630 / 0.7612 / +0.0018; LR dropped on 158 and 163 of 213 questions | `results.csv` tags `gate_on`, `gate_off`; `dropped:` lines in `logs/review_runs.log` |
| Arms of the two clean pairs differ by 0.0002; replicates had nothing dropped | `logs/review_paired.log` ("Run-to-run, same arm"); `logs/review_replicates.log` |
| Run-to-run 0.001–0.003; v13 clean runs 0.7649–0.7659 | `results.csv` v13 `unhcr_repeats` phase 1 tags `v13e_honest` (0.7659), `gate_on_r2` (0.7651), `gate_on_r3` (0.7649), `gate_on` (0.7630, LR dropped) |
| Table 7 permissive column | `results.csv`: UNHCR-like repeats `v13test`; CPS and fCC 2021 `v13b`; World Bank-like `v13c_top1`; GVU sets `v13b` (same as `v13c_top1`) |
| Table 7 Gate column | the `[gate_on …] similarity layer` lines in `logs/review_runs.log` (e.g. UNHCR-like repeats 0.1893/0.0769 = 2.5; CPS 0.0635/0.0292 = 2.2) and `logs/review_replicates.log` (0.1907/0.0758 = 2.5, 0.1976/0.0758 = 2.6; CPS 0.0649/0.0294 = 2.2). An earlier run of the same code gave 2.6 and 2.2 (`logs/v13_similarity_gate_runs.log`) |
| Table 7 "run-to-run noise < 0.00002" | per-cell means of `v13on_*` minus `v13off_*` dumps on the four closed-gate sets (−0.000014, +0.000013, −0.000009, +0.000019) |
| Fresh UNHCR-like gate 3.7 | `[heldout_fresh v13_top …]` line in `logs/review_runs.log` (0.3347/0.0901) and `logs/review_replicates.log` (0.3318/0.0898) |
| UNHCR-like gap: 0.7081, 0.7401, 0.032 (0.006), +0.015 (0.004), 0.047 (0.004), 0.023, median 0.0001, max 0.0058, 24% | `logs/gap_v13_top_unhcr_full_p1.log` (run with `SB_CLOCK_SECONDS=1400`; see the `[unhcr_full gap]` line in `logs/v13_similarity_gate_runs.log`) and `logs/gap_v13_top_unhcr_full_p1.csv` |
| World Bank-like per-question median and max (0.00025) | `experiments/datasets/wb_realistic/ceiling.json` vs. the v13 per-question skills in `logs/wb_items_v13_p2.json` |
| Per-country skill and SEs | `logs/review_paired.log` (section "Per-country skill with respondent-clustered SEs") |
| Linked rows: v12 +0.013 above the GIVEN-only reference, layer adds about 0.002 | `logs/gap_v12_clock_unhcr_full_p1.log` (sum of the three `linked household` gap->GIVEN values: −0.0130) vs. the v13 log (−0.0150) |
| Link-aware reference 0.7700, gap 0.062 (0.004) | `logs/gap_v13_top_unhcr_full_p1.log` (`best possible with household link`, `all` row gap->link 0.0619) |
| CatBoost 16% weight, ≤ 0.0001 | `logs/catboost_member_x_cat.log` (weights line; 0.2089 vs 0.2090, 0.2243 vs 0.2243) |
| +0.0002 with eight TabICL estimators at the same clock | `results.csv`: `x_time` `wb_realistic` phase 1 `time_total2000_members8` 0.1662 vs `time_total2000_members4` 0.1660 |
| Sandboxes 0.4037–0.4040 / 0.2854–0.2858 / 0.2361–0.2363 | `results.csv`, `sandbox_*` rows of v8–v13 |
| Afrobarometer 0.1834–0.1835 | `results.csv` `real_afrobarometer_r8` phase 2, v10/v11/v13 |
| YouGov 0.2798 (v1), 0.2900 (v8) | `results.csv` `real_yougov_vaccine` phase 2 |

## Appendix C

| Number | Source |
|---|---|
| Upload list | `experiments/eval/dev_submissions.csv` |
