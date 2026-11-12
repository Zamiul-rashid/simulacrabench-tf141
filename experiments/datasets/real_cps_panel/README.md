# real_cps_panel — US Current Population Survey, Jan + Feb 2024, rotating household panel

Built by `experiments/datasets/builders/real_cps_panel.py` (raw files in `experiments/datasets/raw/`).

- **Source:** https://www2.census.gov/programs-surveys/cps/datasets/2024/basic/ (jan24pub.csv, feb24pub.csv, 2024_Basic_CPS_Public_Use_Record_Layout_plus_IO_Code_list.txt)
- **Licence / terms:** US federal government work, public domain (17 U.S.C. 105). No registration.
- **Citation:** U.S. Census Bureau and Bureau of Labor Statistics, Current Population Survey, Basic Monthly Public Use Microdata, January and February 2024.

## Shape

| rows | GIVEN | PREDICT | gated | gated cells (mean share over PREDICT) | split train/dev/test |
|---|---|---|---|---|---|
| 10349 | 13 | 80 | 55 | 0.531 | 7762 / 776 / 1811 |

## Repeat households

Share of rows whose household also has a row in the other wave: 0.696.
Share of held-out rows whose other-wave row is visible: phase 1 (DEV held out, TRAIN visible) 0.499; phase 2 (TEST held out, TRAIN+DEV visible) 0.589.

## What was done

- One row per responding household per month: the household reference person (PERRP 40/41, complete interview, adult civilian).
- Panel: households are linked across months by HRHHID+HRHHID2+PULINENO (used only to sample; not shipped). 3,600 households appear in both waves, 2,716 only in wave 1, 433 only in wave 2, so wave 1 = 6,316 rows and wave 2 = 4,033 rows, the UNHCR file's round sizes.
- Roles are drawn at random within wave (75/7.5/17.5%), independently of household, so a held-out row's other-wave row is usually visible (see repeat share).
- Skip logic: CPS code -1 = not in universe (never asked) -> NA_GATED when a gate was inferred. Codes -2/-3/-9 are ordinary levels. Hours/durations banded into <=8 quantile bands.
- Admin, weight, allocation-flag, earnings (outgoing-rotation only), detailed industry/occupation and edit-check items are dropped.
- Every cell is a string; no NaN. Item non-response has its own level. Levels under 1% of answers are folded into 'Other'. Roles assigned at random with a fixed seed (75/7.5/17.5%).
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Gates

Inferred from the data: for each item with not-asked cells, the single other item and value set S (values at which most rows hold an answer) that best predicts who was asked; a sibling with exactly the same not-asked rows is not allowed as parent, and the gate graph is acyclic. Accepted if agreement >= 0.6; otherwise the not-asked cells become the ordinary level 'Not asked'. Gates are not a constraint the rows satisfy exactly.

Agreement (share of rows where `answered == parent in observed_if`): median 1.0000, min 0.9397, max 1.0000, 55 gates; 1 below 0.95.

| item | parent | #observed_if | agreement |
|---|---|---|---|
| PUBUS1 | PEABSRSN | 3 | 0.9797 |
| PUDIS | PEMLR | 1 | 0.9834 |
| PULAY | PUABSOT | 3 | 0.9933 |
| PUHROFF1 | PEHRUSL1 | 4 | 0.9769 |
| PUHROFF2 | PUHROFF1 | 1 | 1.0000 |
| PUHROT1 | PEHRUSL1 | 4 | 0.9769 |
| PUHROT2 | PUHROT1 | 1 | 1.0000 |
| PUABSOT | PEMLR | 4 | 0.9835 |
| PURETOT | PERET1 | 2 | 0.9397 |
| PULK | PEMLR | 2 | 0.9903 |
| PEABSPDO | PEMLR | 1 | 1.0000 |
| PEABSRSN | PEMLR | 1 | 1.0000 |
| PEDWLKO | PEDWWNTO | 1 | 1.0000 |
| PEDWRSN | PEDWLKO | 2 | 0.9986 |
| PEDWWNTO | PULK | 3 | 0.9958 |
| PEHRACTT | PEMLR | 1 | 1.0000 |
| PEHRACT1 | PEMLR | 1 | 1.0000 |
| PEHRFTPT | PEHRUSLT | 1 | 1.0000 |
| PEHRRSN1 | PEHRWANT | 1 | 1.0000 |
| PEHRRSN2 | PEHRWANT | 1 | 1.0000 |
| PEHRRSN3 | PRPTHRS | 4 | 1.0000 |
| PEHRUSLT | PEMLR | 2 | 1.0000 |
| PEHRUSL1 | PEMLR | 2 | 1.0000 |
| PEHRWANT | PRPTREA | 9 | 0.9992 |
| PELKAVL | PEMLR | 1 | 1.0000 |
| PELKDUR | PEMLR | 1 | 1.0000 |
| PELKFTO | PEMLR | 1 | 1.0000 |
| PELKLL1O | PEMLR | 1 | 1.0000 |
| PELKLWO | PEMLR | 1 | 1.0000 |
| PELKM1 | PEMLR | 1 | 1.0000 |
| PEMJNUM | PEMJOT | 1 | 1.0000 |
| PEMJOT | PEMLR | 2 | 1.0000 |
| PENLFACT | PEMLR | 1 | 0.9960 |
| PERET1 | PEMLR | 1 | 0.9928 |
| PRABSREA | PEMLR | 1 | 1.0000 |
| PREXPLF | PREMPNOT | 2 | 0.9995 |
| PRFTLF | PREMPNOT | 2 | 1.0000 |
| PRHRUSL | PREXPLF | 1 | 1.0000 |
| PRJOBSEA | PRWNTJOB | 1 | 1.0000 |
| PRPTHRS | PRPTREA | 17 | 0.9972 |
| PRPTREA | PREMPHRS | 4 | 0.9902 |
| PRUNEDUR | PRWKSCH | 2 | 1.0000 |
| PRUNTYPE | PRWKSCH | 2 | 1.0000 |
| PRWNTJOB | PRWKSTAT | 1 | 1.0000 |
| PEIO1COW | PREXPLF | 2 | 0.9916 |
| PRCOW1 | PREXPLF | 2 | 0.9916 |
| PRMJIND1 | PREXPLF | 2 | 0.9916 |
| PRMJOCC1 | PREXPLF | 2 | 0.9916 |
| PRAGNA | PREXPLF | 2 | 0.9916 |
| PESCHLVL | PESCHENR | 1 | 1.0000 |
| PESCHENR | PRTAGE | 4 | 1.0000 |
| PESCHFT | PESCHENR | 1 | 1.0000 |
| PRNLFSCH | PRTAGE | 4 | 1.0000 |
| PECERT2 | PECERT1 | 1 | 1.0000 |
| PECERT3 | PECERT2 | 2 | 0.9717 |

Items with not-asked cells but no accepted gate (not-asked kept as ordinary level 'Not asked'; None = fewer than 1% of cells): PUWK (None), PEAFEVER (None), PEJHWANT (None), PEJHWKO (None), PENLFJH (None), PEPDEMP1 (None)

## Scores (phase 2: TRAIN+DEV visible, TEST scored; `experiments/eval/run.py`)

| submission | skill | s.e. | seconds |
|---|---|---|---|
| external_model | 0.1811 | 0.0121 | 1.5 |
| v1_learned_gates | 0.216 | 0.0115 | 240.5 |
| v2_joint | 0.3741 | 0.0117 | 173.6 |

`external_model` is the organisers' baseline as shipped; on datasets with chained gates it returns -2.2e-16 in the NA_GATED slot and the scorer rejects it (FAIL). `external_model_clipped` is the same code with outputs clipped at 0 (scratchpad wrapper). v1/v2 have run-time guards, so on a busy machine they may fit fewer questions; see the dataset notes in the hand-off report.

## Value of the repeat households (`builders/analyse_cps_repeats.py`)

```
{
 "n_test": 1811,
 "test_rows_with_visible_partner": 1067,
 "given_match_unique": 924,
 "given_match_correct": 856,
 "marginal": 0.0,
 "oracle_link_lam0.50": 0.2748,
 "given_match_lam0.50": 0.2262,
 "oracle_link_lam0.80": 0.3261,
 "given_match_lam0.80": 0.2628,
 "oracle_link_lam0.90": 0.3201,
 "given_match_lam0.90": 0.2527,
 "oracle_link_lam0.95": 0.3016,
 "given_match_lam0.95": 0.2324
}
```
oracle_link uses the hidden household key (lam * other-wave answer + (1-lam) * marginal); given_match finds the partner as the unique other-wave visible row with identical GIVEN columns, without the key.
