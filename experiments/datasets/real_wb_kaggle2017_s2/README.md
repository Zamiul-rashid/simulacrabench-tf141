# real_wb_kaggle2017_s2 — 2017 Kaggle ML & Data Science Survey (sample 2 of 2)

Built by `experiments/datasets/builders/real_wb_kaggle2017.py` (raw files in `experiments/datasets/raw/`).

- **Source:** https://www.kaggle.com/datasets/kaggle/kaggle-survey-2017 (multipleChoiceResponses.csv, schema.csv, conversionRates.csv)
- **Licence / terms:** ODbL-1.0 (as listed on the Kaggle dataset page). Downloaded with the Kaggle CLI, no extra terms.
- **Citation:** Kaggle (2017). 2017 Kaggle Machine Learning & Data Science Survey. Kaggle dataset kaggle/kaggle-survey-2017.

## Shape

| rows | GIVEN | PREDICT | gated | gates on a GIVEN column | gate agreement median (min-max) | Not answered (mean share over PREDICT) | NA_GATED (mean share) | ordered PREDICT items | split train/dev/test |
|---|---|---|---|---|---|---|---|---|---|
| 6927 | 9 | 81 | 62 | 54 | 1.0 (0.9997-1.0) | 0.151 | 0.434 | 62 | 5195 / 520 / 1212 |

Option counts of PREDICT items (NA_GATED included for gated items): {"min": 3, "median": 5.0, "max": 21, "2-3": 8, "4-7": 45, "8-12": 22, "13+": 6}.

## What was done

- One row per respondent; disjoint random samples of 6,927 rows (seed 20261113), `_s1` and `_s2`.
- `SurveyTrack` (GIVEN) is derived from the screening answers EmploymentStatus, CodeWriter, CareerSwitcher and LearningDataScience, following Kaggle's RespondentTypeREADME (Worker, CodingWorker, CodingWorker-NC, Learners). Those screening items are not PREDICT items.
- Gates are the questionnaire's own routing (schema.csv column `Asked`) expressed on `SurveyTrack`; the eight learning-platform usefulness items hang off a derived PREDICT tick item (chained gate, like the WB tracer items gated on tr_job_full).
- Compensation: amount x the survey's exchange rate to USD, values >= 2,000,000 USD treated as not answered, cut into fixed bands; non-coding-workers get 'Not asked'.
- Percent-of-time / percent-of-training items cut into 0, 1-10, 11-25, 26-50, 51-75, 76-100; age in bands; ML tool / method items capped at 20 levels + Other.
- Every cell is a string; no NaN. A gated item's cell is `NA_GATED` when the gate rule says the question was not put to the respondent and the cell is blank; a blank cell of an eligible respondent is `Not answered` (drop-out / item non-response). Answers given despite the rule are kept, which is why agreement can be below 1.
- Roles drawn at random with a fixed seed (75 / 7.5 / 17.5 %), rows permuted before delivery.
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Resemblance to the World Bank file

Similar: careers/skills survey with routing almost entirely on a GIVEN employment-type column (job-seeker block, worker block, coding-worker block), job-hunt hours per week in bands, many three-level importance scales (like the WB banded scale scores), a 16-option job-title item (WB: 25-option sector), a GIVEN wage band, strong drop-out. Different: international professional/student population (US, India dominate), compensation is actual pay not expected pay, no cognitive task scores, no follow-up wave; the routing column is derived and partly redundant with EmploymentStatus.

## Gates

| item | parent | parent is GIVEN | observed_if | agreement |
|---|---|---|---|---|
| LearningDataScienceTime | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportanceBigData | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportanceDegree | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportanceStats | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportancePython | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportanceKaggleRanking | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportanceMOOC | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportanceVisualizations | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| TimeSpentStudying | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| ProveKnowledgeSelect | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9997 |
| JobSkillImportanceEnterpriseTools | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9999 |
| JobSkillImportanceR | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9999 |
| JobSkillImportanceSQL | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 0.9999 |
| LearningPlatformUsefulnessKaggle | LearningPlatformKaggle | no | Yes | 1.0000 |
| LearningPlatformUsefulnessCourses | LearningPlatformCourses | no | Yes | 1.0000 |
| LearningPlatformUsefulnessSO | LearningPlatformSO | no | Yes | 1.0000 |
| LearningPlatformUsefulnessYouTube | LearningPlatformYouTube | no | Yes | 1.0000 |
| LearningPlatformUsefulnessProjects | LearningPlatformProjects | no | Yes | 1.0000 |
| LearningPlatformUsefulnessTextbook | LearningPlatformTextbook | no | Yes | 1.0000 |
| LearningPlatformUsefulnessBlogs | LearningPlatformBlogs | no | Yes | 1.0000 |
| LearningPlatformUsefulnessCollege | LearningPlatformCollege | no | Yes | 1.0000 |
| CurrentJobTitleSelect | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data, Working, does not write code, switching to d... | 1.0000 |
| TitleFit | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data, Working, does not write code, switching to d... | 1.0000 |
| EmployerIndustry | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data, Working, does not write code, switching to d... | 1.0000 |
| JobSearchResource | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobHuntTime | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorLearning | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorSalary | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorOffice | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorLanguages | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorCommute | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorManagement | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorExperienceLevel | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorDepartment | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorTitle | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorCompanyFunding | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorImpact | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorRemote | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorIndustry | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorLeaderReputation | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorDiversity | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| JobFactorPublishingOpportunity | SurveyTrack | yes | Working, does not write code, switching to data science, Not employed, looking for work, Not working, learning data science | 1.0000 |
| UniversityImportance | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| JobFunctionSelect | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| WorkProductionFrequency | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| WorkDatasetSize | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| AlgorithmUnderstandingLevel | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| WorkDataVisualizations | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| WorkInternalVsExternalTools | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| WorkMLTeamSeatSelect | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| RemoteWork | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| SalaryChange | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| JobSatisfaction | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| TimeGatheringData | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| TimeModelBuilding | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| TimeProduction | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| TimeVisualizing | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| TimeFindingInsights | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data, Contractor / self-employed, writes code to analyse data | 1.0000 |
| EmployerSize | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data | 1.0000 |
| EmployerSizeChange | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data | 1.0000 |
| EmployerMLTime | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data | 1.0000 |
| EmployerSearchMethod | SurveyTrack | yes | Employed (full/part-time), writes code to analyse data | 1.0000 |
