# real_wb_fcc2021_s2 — freeCodeCamp 2021 New Coder Survey (sample 2 of 2)

Built by `experiments/datasets/builders/real_wb_fcc2021.py` (raw files in `experiments/datasets/raw/`).

- **Source:** https://www.kaggle.com/datasets/fccuser/2021-new-coder-survey (file '2021 New Coder Survey.csv')
- **Licence / terms:** CC-BY-SA-4.0 (as listed on the Kaggle dataset page). Downloaded with the Kaggle CLI, no extra terms.
- **Citation:** freeCodeCamp (2021). 2021 New Coder Survey. Kaggle dataset fccuser/2021-new-coder-survey.

## Shape

| rows | GIVEN | PREDICT | gated | gates on a GIVEN column | gate agreement median (min-max) | Not answered (mean share over PREDICT) | NA_GATED (mean share) | ordered PREDICT items | split train/dev/test |
|---|---|---|---|---|---|---|---|---|---|
| 6927 | 9 | 70 | 17 | 17 | 0.9047 (0.7645-0.9718) | 0.059 | 0.108 | 30 | 5195 / 520 / 1212 |

Option counts of PREDICT items (NA_GATED included for gated items): {"min": 3, "median": 5.5, "max": 18, "2-3": 29, "4-7": 17, "8-12": 18, "13+": 6}.

## What was done

- One row per respondent; disjoint random samples of 6,927 rows (seed 20261115), `_s1` and `_s2`.
- Item names are the question numbers; the full question text is in schema.json.
- Last-year earnings (q22) collapsed from 22 USD bands to 11 (GIVEN); expected first-job salary (q16) keeps its 12 bands; hours learning in the World Bank hour bands; months programming and months spent looking for the last job in duration bands; age banded.
- Explicit 'not applicable' answers (e.g. 'I am not currently working', 'I am already a developer', 'Not Applicable', 'I am not living in the US') become NA_GATED. The gate parent is chosen from a short candidate list (questionnaire logic) by substantive answer rates: parent levels answering at >= 25 % of the best level's rate form observed_if; the gate is kept when the other levels answer at most 20 %. Blank cells of eligible respondents are 'Not answered'. Where no gate is accepted the 'not applicable' answer stays an ordinary level.
- Select-all questions (learning methods, resources, events, podcasts, YouTube, reasons) reduced to a few tick items: 'Yes' / 'No' if the question was answered, otherwise 'Not answered'. Debt grid (q39_k): a blank row is the level 'None / left blank'.
- Employment status capped at 9 levels + Other (free-text 'other' answers); other nominal items capped similarly.
- Every cell is a string; no NaN. A gated item's cell is `NA_GATED` when the gate rule says the question was not put to the respondent and the cell is blank; a blank cell of an eligible respondent is `Not answered` (drop-out / item non-response). Answers given despite the rule are kept, which is why agreement can be below 1.
- Roles drawn at random with a fixed seed (75 / 7.5 / 17.5 %), rows permuted before delivery.
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Resemblance to the World Bank file

Closest of the sets to the World Bank file: a global (incl. Sub-Saharan African) young job-seeker population, earnings in fixed bands as GIVEN, expected-salary bands, job-search plans and months spent searching, employment-status-routed job blocks with ordered 1-10 and 4-point satisfaction scales, gates mostly on GIVEN columns. Different: no psychometric or cognitive-task scores, no randomised arm or follow-up wave, 'not asked' is partly self-declared (explicit not-applicable answers) rather than enforced routing, so gate agreement is below 1.

## Gates

| item | parent | parent is GIVEN | observed_if | agreement |
|---|---|---|---|---|
| q44 | q20 | yes | A stay-at-home parent or homemaker, Full-time employed for wages, Not working but looking for work, Other, Part-time employed for wages, Self-employed busine... | 0.7645 |
| q33 | q32 | yes | Associate’s degree, Bachelor’s degree, High school diploma or equivalent (GED), Master's degree (non-professional), Ph.D., Professional degree (MBA, MD, JD, ... | 0.8131 |
| q45_2 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.8900 |
| q45_7 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.8912 |
| q21 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.8916 |
| q46 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.8933 |
| q45_6 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.9008 |
| q45_5 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.9010 |
| q45_3 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.9047 |
| q45_8 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.9070 |
| q45_1 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.9082 |
| q45_4 | q20 | yes | Full-time employed for wages, Other, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.9091 |
| q40 | q20 | yes | Full-time employed for wages, Part-time employed for wages, Self-employed business owner, Self-employed freelancer | 0.9366 |
| q11 | q10 | yes | Yes | 0.9524 |
| q12 | q10 | yes | No, Not answered | 0.9642 |
| q27 | q26 | yes | North America | 0.9642 |
| q43 | q20 | yes | A stay-at-home parent or homemaker, Full-time employed for wages, Not working but looking for work, Other, Part-time employed for wages, Self-employed busine... | 0.9718 |
