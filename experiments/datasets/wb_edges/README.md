# wb_edges

Fabricated respondents on the **real World Bank schema** (unchanged; `gated_value` added), same size and
random role assignment. Builder: `builders/wb_build.py edges` (seed 404). Same generator as
`wb_realistic` with these edge cases planted:

GATES
- The 6 pre-survey items gated on the **GIVEN** `user.employmentStatus` obey the gate only ~94%: 4% of
  non-searchers answered anyway, 6% of the asked group are NA_GATED (TRAIN agreement ~94%).
  A hard gate rule would be wrong here; the `user.age` and `group` gates stay exact.
- `tr_feel_work` / `tr_job_number` (gated on `tr_job_full` = Yes): employment at follow-up made rare ->
  **54 asked rows in TRAIN**.

OPTIONS
- `user.preferredSector` = 'Legal' **never appears in TRAIN** (36 held-out rows have it).
- `user.helpGetJobInDesiredSector` is **constant ('Not answered') in TRAIN**; 2.4% of DEV/TEST answer '4'.
- 25-option sector items with more skewed popularity (rare sectors with a handful of rows).

GIVEN
- **Unseen held-out GIVEN levels**: education 'Professional degree (Law, Medicine, PhD)' only in DEV/TEST
  (3% of them); gender 'Other' only in TEST (2%).
- **`user.hadJob` is pure noise** (50/50, affects nothing).
- **`user.plansToAttachSkillsReport` is a deterministic function of the GIVEN education** ('yes' iff a
  university degree), never 'Not answered'.
- **XOR**: `sc_nstd_mtpt_quit_1` (when reached) is '1' with p .85 if (country not answered) XOR
  (gender Female), else .08.

`ceiling.json`: skill of the true conditional given GIVEN for the held-out generator (TRAIN-only edits
above are not part of it).

## Results (phase 1)
baseline 0.1262 | v1 0.1503 | v2 0.1558 | v2 + conditional hard gates 0.1566 | ceiling 0.1677.
Applying the employment-status gates as hard rules even though TRAIN obeys them only 94-95% costs
-0.0071 (v2 0.1487), so a hard rule must be conditioned on 100% agreement in the visible rows.
XOR item `sc_nstd_mtpt_quit_1`: v1 0.055, v2 0.107, ceiling 0.244 (item skill).
