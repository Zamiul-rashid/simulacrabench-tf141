# OpenReview form answers (SimulacraBench write-up)

Paste these into the form at
<https://openreview.net/group?id=NeurIPS.cc/2026/Competition/SimulacraBench>.
Due 2026-11-20 10:59 UTC (16:59 Bangladesh time). Fields marked TODO need the test-phase
result or the public repo URL.

**title**
SimulacraBench Technical Report: A Self-Validating, Time-Budgeted Blend of Tabular Learners

**authors**
TODO: every author needs an OpenReview profile.

**team_id**
TF141

**keywords**
survey completion, conditional probability estimation, tabular foundation models, TabICL, ensemble, linear pool, log score, calibration

**TLDR**
Per-question blend of five run-time-fitted tabular learners (incl. TabICL v2) with EM weights, a self-validating similarity layer and floor correction, under one shared time budget.

**abstract**
Every hidden cell is scored on its own, so the target is $P(\text{answer}\mid\text{GIVEN columns})$ for each question, estimated from the visible respondents inside the hosted run. Our submission fits five model families at run time (a shared multi-head network, a wider second network, a similarity model with learned column weights, per-question logistic regression, and the pretrained in-context learner TabICL v2) and blends them per question. Blend weights come from expectation--maximisation on held-back rows, averaged with a geometric pool. A final similarity layer is switched on per survey only when a split-half check on held-back rows shows a gain of more than two standard errors. "Not asked" is an ordinary answer option, and a closing step corrects for the grader's probability floor. Everything runs under one clock shared by the three surveys. Local test data were used only to choose the design. On the development leaderboard the submission scores 0.4893 (UNICEF 0.3499, World Bank 0.2335, UNHCR 0.8843). Test-phase score: TODO.

**pdf**
paper/main.pdf (after filling the red placeholders and rebuilding with `make -C paper`).

**code_url**
TODO: https://github.com/<account>/simulacrabench-tf141

**code_license**
MIT

**base_models**
TabICL v2 classifier (Hugging Face jingang/TabICL, revision 4dcd344ece2c00be9e831fdd35bed57b5ad83e19, file tabicl-classifier-v2-20260212.ckpt, SHA-256 bdc7dbd5e4ff21f8f0456fcf90c6b7cdf72dbea960f2d05b19bec19f9b3d4ed0)

**external_data**
None of the following is used by the submitted model; it reads only the frame passed to `predict()`. These public datasets were used **offline only**, reshaped into the competition's format, to compare model designs locally (scored with the organisers' `score.py`):

- freeCodeCamp 2016 New Coder Survey (Kaggle freecodecamp/2016-new-coder-survey-, ODbL-1.0): two samples of 6,927 rows; World-Bank-shaped tests.
- freeCodeCamp 2021 New Coder Survey (Kaggle fccuser/2021-new-coder-survey, CC-BY-SA-4.0): two samples of 6,927 rows; World-Bank-shaped tests.
- Kaggle ML & Data Science Survey 2017 (Kaggle kaggle/kaggle-survey-2017, ODbL-1.0): two samples of 6,927 rows; World-Bank-shaped tests.
- Stack Overflow Developer Survey 2018 (Kaggle stackoverflow/stack-overflow-2018-developer-survey, ODbL): three samples of 6,927 rows; World-Bank-shaped tests.
- US Current Population Survey, basic monthly public-use files Jan + Feb 2024 (census.gov, public domain): repeat-household tests.
- Afrobarometer Round 8 merged release 2023-03-01 (afrobarometer.org, free with citation): memory and run-time tests.
- Open-Source Psychometrics Project BIG5 (IPIP) and DASS 2017-2019 (openpsychometrics.org, released for public use): generic tests.
- OpenML kdd_internet_usage (1997 GVU survey, 10,108 rows): generic tests.
- Imperial College London / YouGov COVID-19 Behaviour Tracker, 10 countries (github.com/YouGov-Data/covid-19-tracker, academic research use only): evaluation only, not redistributed.

**data_use_attestation**
We confirm that we complied with the SimulacraBench data-use agreement. In particular, we made no attempt to re-identify respondents or link records to external sources, and did not redistribute microdata.

**email_sharing / data_release**
Tick both.
