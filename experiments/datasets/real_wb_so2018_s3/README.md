# real_wb_so2018_s3 — Stack Overflow Developer Survey 2018 (sample 3 of 3)

Built by `experiments/datasets/builders/real_wb_so2018.py` (raw files in `experiments/datasets/raw/`).

- **Source:** https://www.kaggle.com/datasets/stackoverflow/stack-overflow-2018-developer-survey (survey_results_public.csv, survey_results_schema.csv); publisher page https://survey.stackoverflow.co/
- **Licence / terms:** Kaggle lists DbCL-1.0 (Database Contents License); Stack Overflow releases the survey data under the Open Database License (ODbL). Downloaded with the Kaggle CLI, no extra terms.
- **Citation:** Stack Overflow (2018). Stack Overflow Developer Survey 2018. Kaggle dataset stackoverflow/stack-overflow-2018-developer-survey.

## Shape

| rows | GIVEN | PREDICT | gated | gates on a GIVEN column | gate agreement median (min-max) | Not answered (mean share over PREDICT) | NA_GATED (mean share) | ordered PREDICT items | split train/dev/test |
|---|---|---|---|---|---|---|---|---|---|
| 6927 | 9 | 79 | 9 | 4 | 1.0 (1.0-1.0) | 0.283 | 0.043 | 59 | 5195 / 520 / 1212 |

Option counts of PREDICT items (NA_GATED included for gated items): {"min": 2, "median": 6.0, "max": 13, "2-3": 3, "4-7": 41, "8-12": 33, "13+": 2}.

## What was done

- One row per respondent; 3 disjoint random samples of 6,927 rows (seed 20261114).
- Salary: ConvertedSalary (annual USD, Stack Overflow's conversion) cut into fixed bands, GIVEN, with 'Not asked' for respondents outside the employed statuses.
- Rank items (AssessJob, AssessBenefits, JobContactPriorities) kept as their rank 1..k, in numeric order; DevType and LanguageWorkedWith reduced to banded counts of ticks; a derived tick item `EducationBootcamp` is the parent of TimeAfterBootcamp.
- Gates: for each PREDICT item the item-specific parent (if any) and then Employment, Student, FormalEducation are tried in order; the parent levels whose answer rate is >= 25 % of the best level's form `observed_if`, and the gate is kept when the other (substantive) levels hold >= 0.3 % of rows and answer at most 10 % of the time.
- Gender: Male, Female, or 'Other / several' (multi-select); country capped at 20 + Other; undergrad major capped at 10 + Other.
- Every cell is a string; no NaN. A gated item's cell is `NA_GATED` when the gate rule says the question was not put to the respondent and the cell is blank; a blank cell of an eligible respondent is `Not answered` (drop-out / item non-response). Answers given despite the rule are kept, which is why agreement can be below 1.
- Roles drawn at random with a fixed seed (75 / 7.5 / 17.5 %), rows permuted before delivery.
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Resemblance to the World Bank file

Similar: employment status and salary band GIVEN, job-seeking status and job-assessment priorities PREDICT, many ordered scales (7-point satisfaction, 5-point agreement and interest, 0-10 recommendation, frequency bands), routing on GIVEN employment / education, strong drop-out. Different: professional developers rather than young job seekers, ranks (each person's ranks form a permutation) rather than banded scale scores, no cognitive tasks, no follow-up wave, salary is actual pay not expected pay, many gates hang off PREDICT items (ad blocker, Stack Overflow account) rather than GIVEN ones.

## Gates

| item | parent | parent is GIVEN | observed_if | agreement |
|---|---|---|---|---|
| UndergradMajor | FormalEducation | yes | Associate degree, Bachelor’s degree (BA, BS, B.Eng., etc.), Master’s degree (MA, MS, M.Eng., MBA, etc.), Other doctoral degree (Ph.D, Ed.D., etc.), Professio... | 1.0000 |
| CompanySize | Employment | yes | Employed full-time, Employed part-time | 1.0000 |
| JobSatisfaction | Employment | yes | Employed full-time, Employed part-time, Independent contractor, freelancer, or self-employed | 1.0000 |
| TimeFullyProductive | Employment | yes | Employed full-time, Employed part-time | 1.0000 |
| TimeAfterBootcamp | EducationBootcamp | no | Yes | 1.0000 |
| AdBlockerDisable | AdBlocker | no | Yes | 1.0000 |
| StackOverflowParticipate | StackOverflowHasAccount | no | Yes | 1.0000 |
| StackOverflowDevStory | StackOverflowHasAccount | no | Yes | 1.0000 |
| StackOverflowJobsRecommend | StackOverflowJobs | no | Yes | 1.0000 |
