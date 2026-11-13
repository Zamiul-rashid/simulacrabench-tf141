# Response to the simulated review (round 1)

This answers the revision roadmap (REV-01 to REV-37) and the reviewers' questions. Section and table numbers refer to the revised `paper/main.tex`. Every new number is mapped to its source in `paper/numbers.md`.

One constraint applies throughout: `submission/main.py` must stay byte-identical to the archive uploaded for the test phase. Suggestions that would edit it are declined, and the reason is given in each case. All new analyses run the submitted code unchanged.

Status key: **Done**; **Partly done** (the minimum fix is done, the fuller fix is not); **Pending** (it can only be done after the test phase); **Authors** (only the authors can answer); **Declined**.

## Roadmap items

| Item | Status | What changed |
|---|---|---|
| REV-01 Traceable numbers | Done | `paper/numbers.md` maps every number to a file. Added to `experiments/eval/logs/`: the gap-analysis outputs, gate log lines, rehearsal timing and memory log, CatBoost log, review-run log and paired comparisons. `experiments/eval/dev_submissions.csv` holds the upload history. The 0.7081 analysis is named (`unhcr_full`, DP1, 1400 s clock). |
| REV-02 Section 3 compliance | Done | Section 3 holds leaderboard numbers only. The version table, gap analysis, CatBoost and other local checks moved to App. B, "Local development evidence (not leaderboard)". |
| REV-03 Data-use disclosure | Partly done | A new "Data use" paragraph in Section 2 covers GIVEN-only matching, no identifiers or keys, the likely source of the UNHCR gain in re-interviewed households, and switching the layer off (`SB_TOP=0`) before any release as microdata. **Authors:** whether the organisers were consulted (red placeholder). |
| REV-04 Reproducibility statement | Done | "Pin it" is removed. Section 4 says results depend on wall-clock time, tells organisers to leave all `SB_*` unset, explains how the phase is detected, and reports the spread over three survey orders. Declined: an `SB_DETERMINISTIC` mode and a hosted log file, because both would edit `main.py`. |
| REV-05 Checklist labels | Done | The template labels are restored verbatim. |
| REV-06 Checkpoint name | Done | Table 1 gives the full file name. The caption gives the revision and a SHA-256 prefix; the full value is in the README and `scripts/fetch_tabicl.py`. |
| REV-07 Table 2 | Done | Every row has a source, licence or terms, and row count. The table matches the form's `external_data`. YouGov is labelled "evaluation only, not redistributed" under its terms, and its numbers are reported in App. B. |
| REV-08 Scoring command | Done | Section 4 points to the full command in `README.md`, which avoids the broken inline command. |
| REV-09 Run-time switches | Done | A "Switches" row in Table 5 lists the switches, their defaults, and that they were unset in the submitted run. |
| REV-10 Table 4 selection rule | Partly done | The rule is "last run at the default budget". Exceptions are footnoted (a: longer budget, b: three-survey/shared-clock runs, c: earlier gate setting). Missing versions are explained. The upload history, including the organisers' baseline, is in App. C rather than as a v0 row in Table 4, which has no local runs of that baseline. |
| REV-11 Abstract sentence | Done | The abstract now says the design was chosen on locally built proxy data (no SimulacraBench data), and that local numbers come from the same data unless marked held-out. The form matches. |
| REV-12 Where the method does worst | Partly done | Section 3.2 defines the rounding step and states the World Bank result both ways: the proxy is near its true conditional while the board is one step lower, and the shortfall is unexplained. **Pending:** the per-survey comment on test scores. |
| REV-13 Estimand | Done | Section 1.2 states the exchangeability assumption and the target P(answer \| GIVEN, visible rows) when units repeat. App. B explains the +0.015. Section 5 says repeat-household gains will not carry over to fresh cross-sections. "As the scoring rule implies" is removed. |
| REV-14 Commit, archive, repo | Partly done | The README has an SHA-256 table for archive members. Section 4 names the `test-submission` tag and links `numbers.md`. **Pending:** create the tag, fill the commit hash and test submission ID, make the repo public and check it logged out, then do the final grep and rebuild. |
| REV-15 Small fixes | Done | Fig. 1 uses `\S\ref`. "(if applicable)" is restored. The form uses a single hyphen. Section 2 states which splits were used (hosted DEV feedback, sandboxes) and mirrors the form's "reads only the frame passed to `predict()`". |
| REV-16 Post-selection and held-out | Done | App. B and Section 5 label local evidence as post-selection. **New Table 6** runs v1, v10 and v13 on data never used for a design decision: a fresh-seed UNHCR-like draw and five World Bank-shaped samples last touched at v8. Result: v1→v10 gains hold (+0.008 to +0.014, each z > 4). The similarity layer adds +0.0018 (SE 0.0011) on the fresh UNHCR-like draw. On the World Bank-shaped samples v13 is within 0.0007 of v10, with both signs. Sandboxes, Afrobarometer and YouGov are reported. |
| REV-17 "Paired" claim | Partly done | The Table 4 caption says its SEs are for absolute skills. The run-to-run spread is reported (about 0.002), and the late steps are called within noise. `run.py --dump` and `paired.py` add respondent-clustered paired SEs, which Tables 6 and 7 use. Not done: three replicates per version with a Holm correction for Table 4, for lack of time before the deadline. |
| REV-18 Gate description | Done | Section 1.7 discloses that β is shared across halves, that the SE assumes independent rows, and that the threshold was fixed after a 2.5 variant was tried. It defines "per-row gain summed over questions". **New Table 7** gives same-code layer off (`SB_TOP=0`) vs on for all six gate datasets, with paired SEs. The layer opens only on UNHCR-like repeats (+0.0018, SE 0.0008) and CPS (+0.0012, SE 0.0006). Elsewhere off and on differ by under 0.00002 (run noise). Declined for the submission: moving β inside the halves. Not done: a sensitivity run on a copy. |
| REV-19 Text matches code | Done | The blend-fold nesting is described accurately: out-of-fold networks and TabICL, leave-one-out similarity model tuned on all visible rows, LR penalty on the fold, later stages unnested. So are hidden-row averaging, TabICL rounds and the log-pool member set. Declined: editing stale docstrings in `main.py`. |
| REV-20 "Self-validating" | Done | The term is dropped from the title and text. The new title is in both the paper and the form. |
| REV-21 Gap analysis | Partly done | "Evenly" is replaced by per-question median and maximum (UNHCR-like 0.0001 / 0.0058; World Bank-like 0.00005 / 0.00025). The Monte Carlo oracle is disclosed. Row-bootstrap SEs are given for the 0.032 / 0.047 / +0.015 decomposition (0.006 / 0.004 / 0.004). Not done: a Rao-Blackwellised oracle. |
| REV-22 Dev-board column | Done | The caption and App. C say one board step is about 0.005 of the mean and cannot rank versions, and that 0.4828→0.4893 cannot be credited to the layer alone. App. C lists all uploads, and Table 3's caption says "best of our uploads". |
| REV-23 Floor correction | Partly done | Strength 1 is called the Bayes act; the others are an in-sample recalibration. The output is described as shaped for the grader, not beliefs. The strengths chosen in hosted runs cannot be reported, because hosted stdout is not shown. |
| REV-24 "Proper" claim | Done | Now reads: "The unfloored log score is strictly proper; the floor makes reporting beliefs slightly suboptimal, which §1.7 undoes." |
| REV-25 TabICL v2 attribution | Done | Cites the TabICLv2 paper (arXiv:2602.11139, checked), v1 and the checkpoint. A sentence explains the choice over TabPFN v2 (10-class native limit). |
| REV-26 Forecast combination | Done | The logarithmic pool cites Genest & Zidek and Heskes. EM cites Dempster and Raftery (BMA). Sharpening cites Ranjan & Gneiting. Stacking and optimal pools cite Wolpert, Hall & Mitchell, Geweke & Amisano and Yao et al. 0.5/0.5 is marked "an empirical choice". |
| REV-27 Similarity model positioning | Done | Section 1.4 positions it with NCA, TabR and ModernNCA, and as a model-assisted hot deck (Andridge & Little). Fellegi–Sunter is not cited, because the method does no record linkage. |
| REV-28 "Strong single learner" | Done (minimum) | The claim is removed. No single-member row was added. |
| REV-29 Dataset and tool citations | Done | Bib entries added for Afrobarometer (as the provider asks), IPIP, OpenML, YouGov, CPS, fCC, Kaggle, Stack Overflow, SciPy and L-BFGS-B. |
| REV-30 Competition context | Done | One sentence after the checklist contrasts the method with LLM silicon samples and MICE. |
| REV-31 Fitness for use | Done | Section 5 says how to use the vectors for domain estimates: pre-correction probabilities, renormalised over substantive answers, with design weights. |
| REV-32 Routing and DK/refused | Done | Section 5 names routing breaks under PREDICT-parent gates and suggests drawing in questionnaire order. Section 1.3 states that DK and refused are ordinary options, distinct from `NA_GATED`. |
| REV-33 Population breakdown | Partly done | App. B gives per-country skill (against the whole-set reference loss; not the gap to the true conditional, which would need the oracle per row) on simulated UNHCR-like data (Egypt 0.698 to Lebanon 0.808) and World Bank-like data (Nigeria 0.023, n = 13, to unanswered 0.202). Section 5 uses "shrunk toward the pooled, majority-dominated distribution". The Section 3.2 heading is unchanged (template text). |
| REV-34 Wording | Done | "Fabricated" became "simulated". *n* in 1/(n+2) is defined. "Per GIVEN profile" was removed. |
| REV-35 Proxy representativeness | Done | Section 5 says the evidence rests on simulators we built, which plant the features the method targets, and mostly uses DP1 visibility. |
| REV-36 Response letter | Done | This file. |
| REV-37 Hidden-split premise | Done | Section 5: "Blend-fold choices assume hidden rows are drawn like visible ones." |

## Answers to reviewers' questions

**EIC**

1. The 0.7081 vs 0.7401 analysis comes from `unhcr_full`, DP1, run with `SB_CLOCK_SECONDS=1400`. The output is in `experiments/eval/logs/gap_v13_top_unhcr_full_p1.{log,csv}`.
2. **Authors to answer** (organiser consultation).
3. The dev scores come from the `v13_top` upload of 2026-11-12, built from `submission/main.py` (SHA-256 `08bdcec2…c1e4`). v5 and v7 were separate uploads and landed on the same rounded values. v10 (ID 1048594) displayed 0.48. See App. C.
4. Table 3 now uses the leaderboard's column names (`ave skill`, `skill_unicef`, `skill_world_bank`, `skill_unhcr`).
5. The "Organizer baseline (test)" row will be filled from the organisers' entry on the test leaderboard. The crowd marginal scores 0 by construction, and the caption says so.
6. We will upload v13 early in the test window (2026-11-15/16 BD time). Then we will fill Table 3, the abstract, the README and the form, and rebuild before 2026-11-20 10:59 UTC.

**R1**

1. There were ten development uploads, counting our upload of the organisers' baseline (App. C). 0.4893 is the best of them. v5 and v7 differ in code, not only in seed. v14 differs from v13 only in its clock.
2. Yes. The 2.5 variant had been seen on `real_cps_panel` and `unhcr_repeats` before 2.0 was fixed, and Section 1.7 now says so. No Table 7 dataset was held back. The fresh-seed UNHCR-like draw in Table 6, built after the design was frozen, is the confirmation (gate 3.7 SE, +0.0018).
3. Not available. Hosted stdout is not shown to participants. Local runs print these values, and the logs are in `experiments/eval/logs/`.
4. Not recomputed with a Rao-Blackwellised oracle. With row-bootstrap SEs, the linked-row +0.015 has SE 0.004, so it stays clear of zero. The World Bank-like gap was not bootstrapped.

**R3**

1. The hosted gate decisions are not visible. Locally, the gate opens on UNHCR-like data and stays closed on World Bank-like and UNICEF-like data. Within a single development upload, the UNHCR board gain cannot be attributed to the layer (App. C).
2. **Authors to answer.**
3. No. The submitted code returns only the floor-corrected vectors. The pre-correction probabilities exist inside the run, and Section 5 tells users to take those, which requires a copy of the code that returns them.
4. The wave is a GIVEN column, so the members can learn wave-specific `NA_GATED` patterns. We did not check `NA_GATED` error by wave separately.
5. We computed skill per country rather than the gap to the true conditional (App. B). Countries differ widely: on UNHCR-like data from 0.698 (Egypt) to 0.808 (Lebanon). On World Bank-like data, South Africa scores 0.111 and respondents with no country 0.202. The smallest groups (Nigeria, 13 hidden respondents; "Other", 9) score 0.023 and 0.045.
6. No design decision used YouGov. It was run at v1 and v8 only, as an extra check. Its terms permit academic research use. We do not redistribute it, and the builder is not in the public repo. Whether a prize-eligible entry counts as academic research is for the **authors** to confirm.

## Still open before the deadline

- Organiser consultation (REV-03, EIC Q2, R3 Q2).
- Author names and affiliations, and OpenReview profiles.
- Test-phase scores, the per-survey comment, the organiser-baseline row, the tag and commit hash, and making the repo public (REV-12, REV-14).
