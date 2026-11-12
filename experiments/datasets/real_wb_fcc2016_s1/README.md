# real_wb_fcc2016_s1 — freeCodeCamp 2016 New Coder Survey (sample 1 of 2)

Built by `experiments/datasets/builders/real_wb_fcc2016.py` (raw files in `experiments/datasets/raw/`).

- **Source:** https://www.kaggle.com/datasets/freecodecamp/2016-new-coder-survey- (file 2016-FCC-New-Coders-Survey-Data.csv); original repository https://github.com/freeCodeCamp/2016-new-coder-survey
- **Licence / terms:** ODbL-1.0 (as listed on the Kaggle dataset page). Downloaded with the Kaggle CLI, no extra terms.
- **Citation:** freeCodeCamp and CodeNewbie (2016). 2016 New Coder Survey. Kaggle dataset freecodecamp/2016-new-coder-survey-.

## Shape

| rows | GIVEN | PREDICT | gated | gates on a GIVEN column | gate agreement median (min-max) | Not answered (mean share over PREDICT) | NA_GATED (mean share) | ordered PREDICT items | split train/dev/test |
|---|---|---|---|---|---|---|---|---|---|
| 6927 | 9 | 62 | 24 | 14 | 1.0 (1.0-1.0) | 0.074 | 0.245 | 11 | 5195 / 520 / 1212 |

Option counts of PREDICT items (NA_GATED included for gated items): {"min": 3, "median": 3.0, "max": 23, "2-3": 32, "4-7": 16, "8-12": 8, "13+": 6}.

## What was done

- One row per respondent; disjoint random samples of 6,927 rows (seed 20261112), `_s1` and `_s2`.
- Money (income, expected salary, bootcamp salary, debts) cut into fixed USD bands; hours learning in the World Bank hour bands; months programming / months since bootcamp in WB-like duration bands.
- Gates: for every routed item a short list of candidate parents (questionnaire logic) is tried in order and the parent levels with an answer rate >= 25 % of the best level form `observed_if`; the gate is kept when the other levels answer at most 10 % of the time.
- Select-all ticks (resources, events, podcasts): 'Yes' if ticked, 'No' if anything else in the block was ticked, otherwise 'Not answered'.
- Income is GIVEN with an extra level 'Not asked' for respondents outside the employed statuses.
- Every cell is a string; no NaN. A gated item's cell is `NA_GATED` when the gate rule says the question was not put to the respondent and the cell is blank; a blank cell of an eligible respondent is `Not answered` (drop-out / item non-response). Answers given despite the rule are kept, which is why agreement can be below 1.
- Roles drawn at random with a fixed seed (75 / 7.5 / 17.5 %), rows permuted before delivery.
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Resemblance to the World Bank file

Similar: job-seeker population (72 % are not yet developers), employment status and an income band GIVEN, expected-salary band and job-search plans PREDICT with gates on GIVEN columns, a ~6 % follow-up-like bootcamp block gated on a GIVEN column with a chained sub-gate, many banded/ordered items, real drop-out. Different: US-centred (about 50 % in the USA), USD amounts, no psychometric or cognitive-task scores, many binary select-all items instead of Likert scales, no randomised arm.

## Gates

| item | parent | parent is GIVEN | observed_if | agreement |
|---|---|---|---|---|
| JobApplyWhen | IsSoftwareDev | yes | No, Not answered | 1.0000 |
| JobRoleInterest | IsSoftwareDev | yes | No, Not answered | 1.0000 |
| JobPref | IsSoftwareDev | yes | No, Not answered | 1.0000 |
| JobWherePref | IsSoftwareDev | yes | No, Not answered | 1.0000 |
| JobRelocateYesNo | IsSoftwareDev | yes | No, Not answered | 1.0000 |
| ExpectedEarning | IsSoftwareDev | yes | No, Not answered | 1.0000 |
| EmploymentField | EmploymentStatus | yes | Employed for wages, Self-employed business owner, Self-employed freelancer | 1.0000 |
| IsUnderEmployed | EmploymentStatus | yes | Employed for wages, Self-employed business owner, Self-employed freelancer | 1.0000 |
| CommuteTime | EmploymentStatus | yes | Employed for wages, Self-employed business owner, Self-employed freelancer | 1.0000 |
| BootcampFinish | AttendedBootcamp | yes | Yes | 1.0000 |
| BootcampLoanYesNo | AttendedBootcamp | yes | Yes | 1.0000 |
| BootcampRecommend | AttendedBootcamp | yes | Yes | 1.0000 |
| BootcampName | AttendedBootcamp | yes | Yes | 1.0000 |
| BootcampFullJobAfter | BootcampFinish | no | Yes | 1.0000 |
| BootcampMonthsAgo | BootcampFinish | no | Yes | 1.0000 |
| BootcampPostSalary | BootcampFullJobAfter | no | Yes | 1.0000 |
| HasChildren | HasFinancialDependents | no | Yes | 1.0000 |
| ChildrenNumber | HasChildren | no | Yes | 1.0000 |
| FinanciallySupporting | HasFinancialDependents | no | Yes | 1.0000 |
| HasStudentDebt | HasDebt | no | Yes | 1.0000 |
| StudentDebtOwe | HasStudentDebt | no | Yes | 1.0000 |
| HasHomeMortgage | HasDebt | no | Yes | 1.0000 |
| HomeMortgageOwe | HasHomeMortgage | no | Yes | 1.0000 |
| SchoolMajor | SchoolDegree | yes | Ph.D., associate's degree, bachelor's degree, master's degree (non-professional), professional degree (MBA, MD, JD, etc.) | 1.0000 |
