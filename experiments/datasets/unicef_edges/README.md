# unicef_edges

Fabricated respondents on the **real UNICEF schema** (unchanged; `gated_value` added), same size and
random role assignment as the real file. Builder: `builders/unicef_build.py edges` (seed 202).
Same generator as `unicef_realistic` with these edge cases planted:

GATES
- Q14-Q18 gated on the GIVEN Q13, exact; **Q13 = Yes for only 4%** -> ~600 asked rows in TRAIN.
- Q09/Q10 gated on Q08 = No but **obeyed only ~96%**: 4% of Q08 = No respondents are NA_GATED and 3%
  of Q08 = Yes respondents answered anyway (TRAIN agreement 96.6% / 96.4%).
- Q01 (GIVEN) NA_GATED exactly for Egypt; Q01's gate has 9 observed_if values.

OPTIONS
- Q10 'Goes against my religious belief' is **never seen in TRAIN** (replaced by 'Other' there) but occurs in DEV/TEST.
- **Q07 is constant ('Yes') in TRAIN**; in DEV/TEST 1% answer 'Not sure'.
- Very rare options: Q06 'No response' (~0.1-0.3%), Q17 'No response'.

GIVEN
- **Unseen held-out GIVEN levels**: Q05 = 'Jewish' only in DEV and TEST (2.5% of them) -> unseen in phase-1
  visible rows; Q05 = 'Sikh' only in TEST (2%) -> unseen in both phases.
- **Q03 (Rural/Urban) is pure noise** (50/50, affects nothing).
- **Q12 is a deterministic function of the GIVEN Q05** (religion -> one of the 8 options).
- **XOR**: Q08 (vaccinated) has logit +2.2 if (Q02 = Female) XOR (Q04 = Member of religious community),
  -2.2 otherwise; Q02 and Q04 are balanced so neither shows a main effect. Q09/Q10's gate inherits it.

`ceiling.json`: skill of the true generating conditional given GIVEN (the generator for held-out rows;
TRAIN-only edits above are not part of it).

## Results (phase 1)
baseline 0.3135 | v1 0.3149 | v2 0.4229 | v2 + hard gates 0.4233 | ceiling 0.4515.
- XOR on Q08: v1 item skill 0.001 against a ceiling of 0.486 (a main-effects LR cannot see it, and the Q09/Q10 gates
  inherit the miss): costs v1 0.114 overall skill. v2 reaches 0.484.
- Unseen Q05='Jewish' rows: v2 0.94 nats/cell, marginal 1.17, ceiling 0.35. No crash; the rest of the gap
  needs the planted Q12 mapping, which no model can know.
- Unseen option / constant item: every model hits the 0.001 floor (6.9 nats) on those cells; not fixable.
- Q09/Q10 obey their gate 96.6% in TRAIN, so the conditional hard rule correctly skips them.
