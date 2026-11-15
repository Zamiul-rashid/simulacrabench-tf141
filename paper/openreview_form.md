# OpenReview form answers (SimulacraBench write-up)

Paste these into the form at
<https://openreview.net/group?id=NeurIPS.cc/2026/Competition/SimulacraBench>.
Due 2026-11-20 10:59 UTC (16:59 Bangladesh time). The field marked TODO (authors) needs the authors' OpenReview profiles.

**title**
SimulacraBench Technical Report: A Time-Budgeted Blend of Tabular Learners for Per-Cell Survey Completion

**authors**
1. Zamiul Rashid (zamiul.rashid@g.bracu.ac.bd)
2. Azra Humayra Alam Prova (TODO: email)

TODO: affiliations; every author needs an OpenReview profile.

**team_id**
TF141

**keywords**
survey completion, conditional probability estimation, tabular foundation models, TabICL, ensemble, linear pool, log score, calibration

**TLDR**
Per-question blend of five run-time-fitted tabular learners (incl. TabICL v2) with EM weights, a split-half-gated similarity layer and floor correction, under one shared time budget.

**abstract**
Each hidden cell is scored on its own, so we estimate, for every question, the distribution of the answer given a respondent's GIVEN columns and the visible respondents, inside the hosted run. Five model families are fitted at run time (a shared multi-head network, a wider network, a similarity model with learned column weights, per-question logistic regression, and the pretrained in-context learner TabICL v2) and blended per question: a linear pool with weights fitted by expectation-maximisation on a held-back fold, averaged with a logarithmic pool. A last similarity layer, which adds about 0.001 skill locally where visible rows contain near-duplicates of hidden ones (not significant on held-out data), is kept for a survey only if a split-half check on the held-back fold supports it. "Not asked" is an ordinary answer option, a closing step adapts the vectors to the grader's probability floor, and one clock is shared by the three surveys. The design was chosen on locally built proxy datasets (no SimulacraBench data); the local numbers we report come from those same data unless marked held-out. Best development-leaderboard score: 0.4893 (UNICEF 0.3499, World Bank 0.2335, UNHCR 0.8843). Test-phase score: 0.49 (UNICEF 0.34, World Bank 0.23, UNHCR 0.88; as displayed, two decimals).

**pdf**
paper/main.pdf (after filling the red placeholders and rebuilding with `make -C paper`).

**code_url**
https://github.com/Zamiul-rashid/simulacrabench-tf141 (tag `test-submission`; switch the repository to public before submitting this form)

**code_license**
MIT

**base_models**
TabICL v2 classifier (Hugging Face jingang/TabICL, revision 4dcd344ece2c00be9e831fdd35bed57b5ad83e19, file tabicl-classifier-v2-20260212.ckpt, SHA-256 bdc7dbd5e4ff21f8f0456fcf90c6b7cdf72dbea960f2d05b19bec19f9b3d4ed0)

**external_data**
None of the following is used by the submitted model; it reads only the frame passed to `predict()`. These public datasets were used **offline only**, reshaped into the competition's format, to compare model designs locally (scored with the organisers' `score.py`). Rows are those of each local dataset built from the source.

- freeCodeCamp New Coder Surveys 2016 and 2021 (Kaggle freecodecamp/2016-new-coder-survey-, ODbL-1.0; fccuser/2021-new-coder-survey, CC-BY-SA-4.0): 4 samples of 6,927 rows; World-Bank-shaped tests.
- Kaggle ML & Data Science Survey 2017 (Kaggle kaggle/kaggle-survey-2017, ODbL-1.0): 2 samples of 6,927 rows; World-Bank-shaped tests.
- Stack Overflow Developer Survey 2018 (Kaggle stackoverflow/stack-overflow-2018-developer-survey, ODbL-1.0): 3 samples of 6,927 rows; World-Bank-shaped tests.
- US Current Population Survey, basic monthly public-use files Jan + Feb 2024 (census.gov, public domain): 10,349 rows; repeat-household tests.
- Afrobarometer Round 8 merged release 2023-03-01 (afrobarometer.org, free with citation): 20,000 rows; memory and run-time tests.
- IPIP Big-Five (BIG5) and DASS 2017-2019 (openpsychometrics.org; no licence named, released for public use): 19,719 and 20,000 rows; generic tests.
- OpenML kdd_internet_usage (1997 GVU survey; OpenML, licence field "Public"): 10,108 rows; generic tests.
- Imperial College London / YouGov COVID-19 Behaviour Tracker (github.com/YouGov-Data/covid-19-tracker; "provided to the public strictly for educational and academic research purposes"): 20,000 rows; internal evaluation only, not redistributed.

**data_use_attestation**
We confirm that we complied with the SimulacraBench data-use agreement. In particular, we made no attempt to re-identify respondents or link records to external sources, and did not redistribute microdata.

**email_sharing / data_release**
Tick both.
