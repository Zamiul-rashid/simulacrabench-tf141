# Response to the simulated review (rounds 1 and 2)

This answers the revision roadmap (REV-01 to REV-37) and the reviewers' questions. Section and table numbers refer to the revised `paper/main.tex`. Every new number is mapped to its source in `paper/numbers.md`.

One constraint applies throughout: `submission/main.py` must stay byte-identical to the archive uploaded for the test phase. Suggestions that would edit it are declined, and the reason is given in each case. All new analyses run the submitted code unchanged.

The round-1 table below has been corrected after the round-2 verification: rows that round 2 found overclaimed now state what is actually done, with the round-2 change marked *(r2)*. Round-2 new issues are answered in the last section.

Status key: **Done**; **Partly done** (the minimum fix is done, the fuller fix is not); **Pending** (it can only be done after the test phase); **Authors** (only the authors can answer); **Declined**.

## Roadmap items

| Item | Status | What changed |
|---|---|---|
| REV-01 Traceable numbers | Partly done | `paper/numbers.md` maps every number to a file. Added to `experiments/eval/logs/`: the gap-analysis outputs, gate log lines, rehearsal timing and memory log, CatBoost log, review-run and replicate logs, and paired comparisons. `experiments/eval/dev_submissions.csv` holds the upload history. The 0.7081 analysis is named (`unhcr_full`, DP1, 1400 s clock). *(r2)* The 0.2486 leaderboard snapshot is committed, anonymised, as `experiments/eval/leaderboard_steps_2026-10-27.md`. **Authors:** Codabench submission IDs are missing for 9 of the 10 development uploads, including the 0.4893 one. |
| REV-02 Section 3 compliance | Done *(r2)* | Section 3 holds leaderboard numbers only. The version table, gap analysis, CatBoost and other local checks moved to App. B, "Local development evidence (not leaderboard)". Round 1 had left the local 0.0033 figure in Section 3.2; it is now only in App. B. |
| REV-03 Data-use disclosure | Partly done | Section 2 "Data use" covers GIVEN-only matching and no identifiers or keys. *(r2)* It now says that the gain on re-interviewed households comes mostly from the members, not the layer, so switching the layer off is not enough, and that any release as imputed or synthetic microdata needs a disclosure-risk assessment. **Authors:** whether the organisers were consulted (red placeholder). |
| REV-04 Reproducibility statement | Done | "Pin it" is removed. Section 4 says results depend on wall-clock time, tells organisers to leave all `SB_*` unset, explains how the phase is detected, and reports the spread over three survey orders. Declined: an `SB_DETERMINISTIC` mode and a hosted log file, because both would edit `main.py`. |
| REV-05 Checklist labels | Done | The template labels are restored verbatim. |
| REV-06 Checkpoint name | Done | Table 1 gives the full file name. The caption gives the revision and a SHA-256 prefix; the full value is in the README and `scripts/fetch_tabicl.py`. |
| REV-07 Table 2 | Done *(r2)* | Every row has a source, licence or terms, and row count; the citations are in App. D. YouGov is labelled "evaluation only" and is not redistributed. *(r2)* The table is no longer scaled down, so it is readable, and the GVU licence ("none named; OpenML 'Public'") now matches the form. |
| REV-08 Scoring command | Done | Section 4 points to the full command in `README.md`, which avoids the broken inline command. |
| REV-09 Run-time switches | Done | A "Switches" row in Table 5 lists the switches, their defaults, and that they were unset in the submitted run. |
| REV-10 Table 4 selection rule | Partly done | The rule is "last run at the default budget". Exceptions are footnoted (a: longer budget, b: three-survey/shared-clock runs, c: earlier gate setting). Missing versions are explained. The upload history, including the organisers' baseline, is in App. C rather than as a v0 row in Table 4, which has no local runs of that baseline. |
| REV-11 Abstract sentence | Done | The abstract now says the design was chosen on locally built proxy data (no SimulacraBench data), and that local numbers come from the same data unless marked held-out. The form matches. |
| REV-12 Where the method does worst | Done | Section 3.2 defines the rounding step and states the World Bank result both ways: the proxy is near its true conditional while the board is one step lower, and the shortfall is unexplained. After the test phase it adds that the test scores (0.34, 0.23, 0.88) equal the development ones at two decimals, so World Bank stays the weakest survey. |
| REV-13 Estimand | Done | Section 1.2 states the exchangeability assumption and the target P(answer \| GIVEN, visible rows) when units repeat. App. B explains the +0.015. Section 5 says repeat-household gains will not carry over to fresh cross-sections. "As the scoring rule implies" is removed. |
| REV-14 Commit, archive, repo | Done | The README has an SHA-256 table for archive members. Section 4 names the `test-submission` tag (commit 276901c, the state at upload) and links `numbers.md`. Test scores and the submission ID (1053552) are filled in. Remaining step: switch the repository to public before the form is submitted. |
| REV-15 Small fixes | Done | Fig. 1 uses `\S\ref`. "(if applicable)" is restored. The form uses a single hyphen. Section 2 states which splits were used (hosted DEV feedback, sandboxes) and mirrors the form's "reads only the frame passed to `predict()`". |
| REV-16 Post-selection and held-out | Done *(r2)* | App. B and Section 5 label local evidence as post-selection. **Table 6** runs v1, v10 and v13 on data never used for a design decision: a fresh draw of the UNHCR-like simulator (new rows, same settings) and five World Bank-shaped samples last touched at v8. v1→v10 gains hold (+0.008 to +0.014, each z > 4). *(r2)* Round 1's reading was too strong. On the fresh draw the layer's share is +0.0018 and +0.0014 in two runs (z 1.7, 1.3): consistent with the design data but not significant alone. On the World Bank-shaped samples two differences exceed 2 SE (+0.0004, z 2.6; −0.0007, z −2.9, in a run that dropped logistic regression on 17 of 79 questions), so "neither helped nor hurt" is withdrawn. |
| REV-17 "Paired" claim | Partly done | The Table 4 caption says its SEs are for absolute skills. *(r2)* The run-to-run spread is now 0.001–0.003, from three survey orders and repeat runs of v13, and the late steps are called within noise. `run.py --dump` and `paired.py` add respondent-clustered paired SEs, which Tables 6 and 7 use. Not done: three replicates per version with a Holm correction for Table 4, for lack of time. |
| REV-18 Gate description | Done | Section 1.7 discloses that β is shared across halves, that the SE assumes independent rows, and that the threshold was fixed after a 2.5 variant was tried. **Table 7** gives same-code layer off (`SB_TOP=0`) vs on for all six gate datasets, with paired SEs. *(r2)* After the replicates the layer adds +0.0012 on UNHCR-like repeats (SE 0.0008, z 1.4, in two clean pairs) and +0.0012 on CPS (SE 0.0006, z 2.0, in two pairs); see NI-1. Elsewhere off and on differ by under 0.00002. Declined for the submission: moving β inside the halves. |
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
| REV-29 Dataset and tool citations | Done *(r2)* | Bib entries for Afrobarometer (as the provider asks), IPIP, OpenML, YouGov, CPS, fCC, Kaggle, Stack Overflow, SciPy and L-BFGS-B. *(r2)* DASS is now cited (Lovibond & Lovibond 1995); the Afrobarometer entry has the right years and its DOI; dataset titles keep their capitals. |
| REV-30 Competition context | Done | One sentence after the checklist contrasts the method with LLM silicon samples and MICE. |
| REV-31 Fitness for use | Done *(r2)* | Section 5 says the outputs suit per-cell prediction and model-assisted estimation, not release as data. For domain estimates it says to use the probabilities before the floor correction, and *(r2)* states that the submitted code does not return them. |
| REV-32 Routing and DK/refused | Done *(r2)* | Section 5 names routing breaks where a gate's parent is itself predicted. *(r2)* Round 1's advice was wrong (drawing in questionnaire order from per-cell vectors does not prevent breaks); it now says to condition each child on its drawn parent. Section 1.3 states that DK and refused are ordinary options, distinct from `NA_GATED`. |
| REV-33 Population breakdown | Partly done | App. B gives per-country skill (against the whole-set reference loss; not the gap to the true conditional, which would need the oracle per row) on simulated UNHCR-like data (Egypt 0.698 to Lebanon 0.808) and World Bank-like data (Nigeria 0.023, n = 13, to unanswered 0.202). Section 5 uses "shrunk toward the pooled, majority-dominated distribution". The Section 3.2 heading is unchanged (template text). |
| REV-34 Wording | Done | "Fabricated" became "simulated". *n* in 1/(n+2) is defined. "Per GIVEN profile" was removed. |
| REV-35 Proxy representativeness | Done *(r2)* | Section 5 says the evidence rests on simulators we built, *(r2)* tuned to resemble the leaderboard, which plant the features the method targets, and mostly uses DP1 visibility. |
| REV-36 Response letter | Done *(r2)* | This file. Round 2 found nine rows overclaimed; they are corrected above. |
| REV-37 Hidden-split premise | Done | Section 5: "Blend-fold choices assume hidden rows are drawn like visible ones." |

## Answers to reviewers' questions

**EIC**

1. The 0.7081 vs 0.7401 analysis comes from `unhcr_full`, DP1, run with `SB_CLOCK_SECONDS=1400`. The output is in `experiments/eval/logs/gap_v13_top_unhcr_full_p1.{log,csv}`.
2. **Authors to answer** (organiser consultation).
3. The dev scores come from the `v13_top` upload of 2026-11-12, built from `submission/main.py` (SHA-256 `08bdcec2…c1e4`). v5 and v7 were separate uploads and landed on the same rounded values. v10 (ID 1048594) displayed 0.48. See App. C.
4. *(r2, corrected)* Table 3 uses the column titles shown on the leaderboard page (Grand Prize, UNICEF, World Bank, UNHCR), and the caption says so. Round 1 wrongly said it used the result keys.
5. The "Organizer baseline (test)" row will be filled from the organisers' entry on the test leaderboard. The crowd marginal scores 0 by construction, and the caption says so.
6. We will upload v13 early in the test window (2026-11-15/16 BD time). Then we will fill Table 3, the abstract, the README and the form, and rebuild before 2026-11-20 10:59 UTC.

**R1**

1. There were ten development uploads, counting our upload of the organisers' baseline (App. C). 0.4893 is the best of them. v5 and v7 differ in code, not only in seed. v14 differs from v13 only in its clock.
2. Yes. The 2.5 variant had been seen on `real_cps_panel` and `unhcr_repeats` before 2.0 was fixed, and Section 1.7 now says so. No Table 7 dataset was held back. The fresh-seed UNHCR-like draw in Table 6, built after the design was frozen, is the confirmation: the gate opened in both runs (statistic 3.7) and the layer added +0.0018 and +0.0014, not significant alone (see REV-16).
3. Not available. Hosted stdout is not shown to participants. Local runs print these values, and the logs are in `experiments/eval/logs/`.
4. Not recomputed with a Rao-Blackwellised oracle. With row-bootstrap SEs, the linked-row +0.015 has SE 0.004, so it stays clear of zero. The World Bank-like gap was not bootstrapped.

**R3**

1. The hosted gate decisions are not visible. Locally, the gate opens on UNHCR-like data and stays closed on World Bank-like and UNICEF-like data. Within a single development upload, the UNHCR board gain cannot be attributed to the layer (App. C).
2. **Authors to answer.**
3. No. The submitted code returns only the floor-corrected vectors. The pre-correction probabilities exist inside the run, and Section 5 tells users to take those, which requires a copy of the code that returns them.
4. The wave is a GIVEN column, so the members can learn wave-specific `NA_GATED` patterns. We did not check `NA_GATED` error by wave separately.
5. We computed skill per country rather than the gap to the true conditional (App. B). Countries differ widely: on UNHCR-like data from 0.698 (Egypt) to 0.808 (Lebanon). On World Bank-like data, South Africa scores 0.111 and respondents with no country 0.202. The smallest groups (Nigeria, 13 hidden respondents; "Other", 9) score 0.023 and 0.045.
6. No design decision used YouGov. It was run at v1 and v8 only, as an extra check. Its terms permit academic research use. We do not redistribute it, and the builder is not in the public repo. Whether a prize-eligible entry counts as academic research is for the **authors** to confirm.

## Round 2: new issues

| Issue | Status | What changed |
|---|---|---|
| NI-1 Table 7 UNHCR-like row | Done | The first on/off pair overran the clock and dropped logistic regression on 158 and 163 of 213 questions; App. B now says so. Two more on/off pairs of the unchanged code dropped nothing and each gave +0.0012 (SE 0.0008, z 1.4); their arms differ by 0.0002 between pairs. Table 7 reports their mean (off 0.7638, on 0.7650). CPS was also repeated and gave +0.0012 again. Clean runs of v13 on this set score 0.7649–0.7659, which reconciles Table 5's 0.7659; the overrun run scored 0.7630. Logs: `logs/review_replicates.log`, `logs/review_paired.log`. |
| NI-2 Linked-row gain is the members' | Done | App. B: v12 (no layer, same clock) is already 0.013 above the GIVEN-only reference on linked rows, so the layer adds about 0.002. Section 2 "Data use" no longer says that `SB_TOP=0` suffices; it says the outputs carry information from visible respondents and that release as microdata needs a disclosure-risk assessment. |
| NI-3 Table 2 unreadable | Done | The table is no longer scaled: citations moved to App. D, rows merged, labels shortened. |
| NI-4 Held-out reading | Done | See REV-16. "Beats" and "neither helped nor hurt" are withdrawn; the two beyond-2-SE World Bank-shaped differences are reported, the −0.0007 one with its dropped member; 3.7 is called the gate's own blend-fold statistic; the fresh draw is described as new rows from the same simulator settings; a second fresh-draw run is in Table 6. |
| NI-5 Per-country claim | Done | Per-country skills now carry clustered SEs and hidden-respondent counts. The shrinkage reading is withdrawn: the small groups' SEs are too wide to tell. |
| NI-6 Routing advice | Done | See REV-32. |
| NI-7 TabICL estimators | Done | Now +0.0002 at the same clock (`x_time`, members 4 vs 8), within run-to-run noise. |
| NI-8 Permissive variant | Done | The losses are now 0.0000–0.0012 and are called unpaired. Both directions are treated alike: on UNHCR-like repeats its 0.7660 lies inside the 0.7649–0.7659 of v13's clean runs, so neither variant is ahead. |
| NI-9 Gap to the link-aware reference | Done | App. B reports 0.7700 and a gap of 0.062 (SE 0.004). |
| NI-10 Size in the abstract | Done | "Which helps" became "adds about 0.001 skill locally … (not significant on held-out data)", in the paper and the form. |
| NI-11 2026-11-14 re-upload | Done | Added to Table 8. Its score field is blank until the authors copy it from Codabench. |
| NI-12 Table 3 columns and baseline | Done | The caption says the columns are titled as on the leaderboard, that the development values are our best upload's unrounded, platform-noised result, and that the baseline row is the organisers' test entry. |
| NI-13 README | Done | "Geometric pool" became "logarithmic pool"; "exact archive" is reworded; the estimand matches the paper; the spread is 0.001–0.003, with a note that a run that overruns a member deadline drops that member. |
| NI-14 Lower-cased dataset titles | Done | Double braces in `refs.bib`. |
| NI-15 In-run gate z vs realised z | Done | App. B: the gate statistic (2.5–2.6 on UNHCR-like, 2.2 on CPS) exceeds the realised z (1.4, 2.0) because its SE treats rows as independent. |

Not done in round 2: the synthesis checker (`check_re_review_synthesis.py`) could not run, because round 1 produced no structured roadmap or adjudication artifacts. Round 2 was judged by the same model family that made the revisions.

## Still open before the deadline

- Organiser consultation (REV-03, EIC Q2, R3 Q2).
- Codabench submission IDs of the development uploads, especially the 0.4893 one, and the 2026-11-14 re-upload's score (REV-01, NI-11).
- Whether a prize-eligible entry counts as academic research under YouGov's terms (R3 Q6).
- Author names and affiliations, and OpenReview profiles.
- Making the repository public (REV-14). Test scores, the per-survey comment, the tag and commit hash are done; the organisers had no baseline entry on the test board on 2026-11-15.
