# wb_realistic

Fabricated respondents on the **real World Bank schema** (`starter-kit/data/world_bank.json`, unchanged;
`gated_value` added). 6,927 rows, roles drawn at random in the schema's counts (TRAIN 5,195 / DEV 520 /
TEST 1,212). Builder: `builders/wb_build.py realistic` (seed 303).

What is planted:
- **Platform version**: 61% of rows come from a "new" version in which country was not asked
  (`user.country` = 'Not answered' exactly for them). Version-specific structure: the post-survey module
  `user.plannedCourses`, `user.helpGetInterview`, `user.helpGetJobInDesiredSector` is shown only in the new
  version (98% 'Not answered' otherwise); in the new version `user.howLongUnemployed` /
  `user.howLongInCurrentPosition` use the coarse 'Under 6 months' level instead of the four fine bins.
- **Feedback experiment**: 17.7% randomised (mostly old-version rows) into yes1-yes4. All 19 tracer items
  are gated **exactly** on the GIVEN `group` (NA_GATED for 'Not randomised'); ~38% of randomised rows answer
  the tracer, the rest are 'Not answered' on every tracer item (block non-response). The control arm (yes4)
  gets no feedback: post-feedback items (`jobStrengthsAndWeaknesses`, `helpJobSearch`, `helpGettingJob`,
  `planToIncreaseJobSearch`) are 97% 'Not answered'; skills-report items (`plansToAttachSkillsReport`,
  `willSkillsAttachHelpGetInterview`) are 'Not answered' unless the arm got the skills report (yes1, yes2,
  Not randomised).
- **GIVEN-parent gates, exact**: 6 pre-survey items on `user.employmentStatus` (observed_if with 1, 2 and
  7 values; `howLongUnemployed` and `howLongInCurrentPosition` partition the statuses), 2 sector items on
  `user.age` (NA_GATED iff age 'Not answered'), 19 tracer items on `group`.
  PREDICT-parent gates, exact: `howManyHoursToUpskillPerWeek` <- `accessedLearningLinks`;
  `tr_job_number`, `tr_feel_work` <- `tr_job_full` (few asked rows: ~100 in TRAIN).
- **Monotone dropout** through the session (self-report scales -> Corsi -> digit span -> matrices -> CPT ->
  trail making -> mirror tracing -> BRET -> post-survey): every later item is 'Not answered'. Dropout
  propensity depends on education, any 'Not answered' in the GIVEN block, version and employment status
  (~7% miss the scales, ~50% miss the post-survey).
- **Derived score/band items**: each of the 16 self-report subscale bands is the band of the mean of 4
  simulated Likert items (latent Big Five / EI / RIASEC traits + acquiescence); trail-making log-time bands,
  error counts, CPT, BRET, matrices (binomial of 10 items) and span items are bands/counts of simulated
  task outcomes driven by a cognitive factor tied to education; `tr_riasec_target_sector` is a
  deterministic function of `tr_target_sector`; `tr_feel_work` is a mean of 8 items snapped to the schema
  levels; `tr_self_efficacy` the band of a mean of 5 items.
- **Near-duplicates**: `wageOfSimilarEmployeesAfter` / `lowestAcceptablePayAfter` repeat the GIVEN
  answers 55% of the time, otherwise a neighbouring band (ordinal); `tr_similar_wage_after` /
  `tr_low_pay_after` likewise on their 8-band scale; `tr_employment_status` keeps the GIVEN status 45%;
  `tr_job_full` agrees with `tr_employment_status` 93%; `expectsToFindJobInSixMonths` repeats the
  pre-survey answer 70%; post-survey search hours / applications follow the pre-survey effort trait.
- **25-option sector items** driven by RIASEC traits, gender and education; `appliedInThePastSector`
  mixes the preferred sector with entry-level sectors; `targetSector` repeats the preferred one 60%.
- Small n: 5,195 visible rows for 76 targets.

`ceiling.json`: skill of the true conditional given GIVEN (300-replicate Rao-Blackwellised Monte Carlo;
for derived band items the estimate is a frequency over replicates, so slightly pessimistic).

## Results
| phase | baseline | v1 | v2 | v2 + hard gates* | ceiling |
|---|---|---|---|---|---|
| 1 | 0.1423 | 0.1557 | 0.1594 | 0.1609 | 0.1703 |
| 2 | 0.1520 | 0.1646 | 0.1709 | 0.1723 | 0.1805 |

*as in unicef_realistic. Learned gates leak 1-4% NA mass on the rare employment-status levels and
about 19% (up to 56%) on the age 'Not answered' rows of the two sector items; the hard rule recovers +0.0015.
Phase 2 ran on a machine with load average about 30: v2 used 163 of its 177 s budget, fitted LR on only 73 of 76
questions, and the LR member got blend weight 0.
