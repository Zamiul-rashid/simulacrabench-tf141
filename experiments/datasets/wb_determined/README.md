# wb_determined

`wb_realistic` (same respondents, same roles, same schema) with module availability made **exactly** determined by GIVEN cells. Builder: `builders/wb_determined.py` (deterministic post-edit of wb_realistic, no randomness).

- arm `yes4` (no feedback, scores only): post-feedback items ['user.jobStrengthsAndWeaknesses', 'user.helpJobSearch', 'user.helpGettingJob', 'user.planToIncreaseJobSearch'] all 'Not answered'.
- arms `yes3`, `yes4` (no skills feedback): ['user.plansToAttachSkillsReport', 'user.willSkillsAttachHelpGetInterview', 'user.accessedLearningLinks', 'user.plannedCourses', 'user.helpGetInterview', 'user.helpGetJobInDesiredSector'] all 'Not answered'; `user.howManyHoursToUpskillPerWeek` NA_GATED.
- arms `yes2`, `yes4` (no job matches): `user.targetSector` 'Not answered'.
- `user.country` recorded (old platform version): ['user.plannedCourses', 'user.helpGetInterview', 'user.helpGetJobInDesiredSector', 'sc_nstd_mtpt_quit_1', 'sc_nstd_mtpt_err_per_s', 'sc_nstd_bret_prop'] all 'Not answered' (courses module absent; mirror tracing and BRET games absent).

Purpose: test whether predictions are sharp enough in cells the visible rows show to be 100% determined (e.g. a generic pure-cell rule, see experiments/wb_ideas/). No ceiling.json (not recomputed).

Cells changed per column vs wb_realistic:

sc_nstd_mtpt_quit_1                      1960
sc_nstd_mtpt_err_per_s                   1960
sc_nstd_bret_prop                        1904
user.jobStrengthsAndWeaknesses              7
user.helpJobSearch                          8
user.helpGettingJob                         7
user.planToIncreaseJobSearch                8
user.targetSector                         370
user.plansToAttachSkillsReport             12
user.willSkillsAttachHelpGetInterview       8
user.accessedLearningLinks                392
user.howManyHoursToUpskillPerWeek         295
user.plannedCourses                        85
user.helpGetInterview                      84
user.helpGetJobInDesiredSector             78
