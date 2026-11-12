# unicef_realistic

Fabricated respondents on the **real UNICEF schema** (`starter-kit/data/unicef.json`, unchanged;
`gated_value` added). 19,846 rows, roles drawn at random in the schema's counts
(TRAIN 14,885 / DEV 1,488 / TEST 3,473). Builder: `builders/unicef_build.py realistic` (seed 101).

What is planted (replacing the sandbox's single trait):
- **GIVEN block** with realistic dependencies: country shares 8-12%; religion (Q05) strongly
  country-specific (Nepal Hindu, Pakistan/Iraq/Mali/Egypt Muslim, Nigeria split, Latin America /
  Zambia / Kenya Christian; Jewish, Baha'i, Sikh very rare); role (Q04) depends on religion;
  age (Q01) country-dependent and **NA_GATED exactly when Country = Egypt** (GIVEN item gated on GIVEN);
  child under 5 (Q13) depends on country, age, gender.
- **Three correlated latent traits** (vaccine confidence, deference to religious leaders,
  child-vaccine support; correlations .2-.5), whose means depend on country, role, age, urban,
  with **country x demographic interactions** (urban effect larger in Nigeria/Pakistan; gender effect on
  deference reversed in Iraq/Mali/Pakistan; country-specific age slope on Q08; country x gender on Q11).
- **Strong country effects** on every PREDICT item (country x option offsets, sd .45-1.05 on the logit scale).
- **Skewed / ordinal items**: Q14 ordered logit over Very / Somehow / Not at all (+ separate Not sure);
  Q16 ~80% Yes; rare "Prefer not to answer" / "No response" levels in Q06 (No response concentrated in
  Mali and Nigeria) and Q17 (No response concentrated in Pakistan).
- **Exact gates**: Q09, Q10 asked iff Q08 = No (PREDICT parent); Q14-Q18 asked iff Q13 = Yes
  (GIVEN parent: free points if applied as a hard rule).

`ceiling.json`: skill of the true generating conditional P(item | GIVEN) (300-replicate
Rao-Blackwellised Monte Carlo) scored with the organisers' functions, phase 1 and phase 2.

## Results (2026-11-11, `experiments/eval/run.py`; post-processing in the analysis scratchpad)
| phase | baseline | v1 | v2 | v2 + hard gates* | ceiling |
|---|---|---|---|---|---|
| 1 | 0.3286 | 0.3410 | 0.3426 | 0.3428 | 0.3480 |
| 2 | 0.3291 | 0.3404 | 0.3424 | 0.3427 | 0.3463 |

*GIVEN-parent gates applied as exact rules, and PREDICT-parent gates by recursion (P(child asked) =
P(parent in observed_if)), only where the visible rows obey the gate 100%. v2's learned gates already
leak < 0.0003 NA_GATED mass here, so the rule gains only about 0.0002.
