# real_cps_nopanel — CONTROL: same CPS months and row counts, no household repeated

Built by `experiments/datasets/builders/real_cps_panel.py --nopanel` (raw files in `experiments/datasets/raw/`).

- **Source:** as real_cps_panel
- **Licence / terms:** public domain (US federal government work)
- **Citation:** as real_cps_panel

## Shape

| rows | GIVEN | PREDICT | gated | gated cells (mean share over PREDICT) | split train/dev/test |
|---|---|---|---|---|---|
| 10349 | 13 | 80 | 55 | 0.532 | 7762 / 776 / 1811 |

## Repeat households

Share of rows whose household also has a row in the other wave: 0.000.
Share of held-out rows whose other-wave row is visible: phase 1 (DEV held out, TRAIN visible) 0.000; phase 2 (TEST held out, TRAIN+DEV visible) 0.000.

## What was done

- Identical construction to real_cps_panel except that every row is a different household (6,316 wave-1 and 4,033 wave-2 households, none in both). Use it to separate the gain a model gets from repeat households from the gain it gets on the instrument itself.
- Every cell is a string; no NaN. Item non-response has its own level. Levels under 1% of answers are folded into 'Other'. Roles assigned at random with a fixed seed (75/7.5/17.5%).
- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).

## Gates

Inferred from the data: for each item with not-asked cells, the single other item and value set S (values at which most rows hold an answer) that best predicts who was asked; a sibling with exactly the same not-asked rows is not allowed as parent, and the gate graph is acyclic. Accepted if agreement >= 0.6; otherwise the not-asked cells become the ordinary level 'Not asked'. Gates are not a constraint the rows satisfy exactly.

Agreement (share of rows where `answered == parent in observed_if`): median 1.0000, min 0.9111, max 1.0000, 55 gates; 1 below 0.95.

| item | parent | #observed_if | agreement |
|---|---|---|---|
| PUBUS1 | PEABSRSN | 2 | 0.9765 |
| PUDIS | PEMLR | 1 | 0.9793 |
| PULAY | PUABSOT | 3 | 0.9944 |
| PUHROFF1 | PEHRUSL1 | 4 | 0.9754 |
| PUHROFF2 | PUHROFF1 | 1 | 1.0000 |
| PUHROT1 | PEHRUSL1 | 4 | 0.9754 |
| PUHROT2 | PUHROT1 | 1 | 1.0000 |
| PUABSOT | PEMLR | 4 | 0.9776 |
| PURETOT | PERET1 | 1 | 0.9111 |
| PULK | PEMLR | 2 | 0.9881 |
| PUDIS1 | PUABSOT | 1 | 0.9831 |
| PEABSPDO | PEMLR | 1 | 1.0000 |
| PEABSRSN | PEMLR | 1 | 1.0000 |
| PEDWLKO | PEDWWNTO | 1 | 1.0000 |
| PEDWRSN | PEDWLKO | 2 | 0.9997 |
| PEDWWNTO | PULK | 3 | 0.9977 |
| PEHRACTT | PEMLR | 1 | 1.0000 |
| PEHRACT1 | PEMLR | 1 | 1.0000 |
| PEHRFTPT | PEHRUSLT | 1 | 0.9997 |
| PEHRRSN2 | PEHRWANT | 1 | 1.0000 |
| PEHRRSN3 | PRPTREA | 8 | 0.9997 |
| PEHRUSLT | PEMLR | 2 | 1.0000 |
| PEHRUSL1 | PEMLR | 2 | 1.0000 |
| PEHRWANT | PRPTREA | 9 | 0.9986 |
| PELKAVL | PEMLR | 1 | 1.0000 |
| PELKDUR | PEMLR | 1 | 1.0000 |
| PELKFTO | PEMLR | 1 | 1.0000 |
| PELKLL1O | PEMLR | 1 | 1.0000 |
| PELKLWO | PEMLR | 1 | 1.0000 |
| PELKM1 | PEMLR | 1 | 1.0000 |
| PEMJNUM | PEMJOT | 1 | 1.0000 |
| PEMJOT | PEMLR | 2 | 1.0000 |
| PENLFACT | PEMLR | 1 | 0.9934 |
| PERET1 | PEMLR | 1 | 0.9883 |
| PRABSREA | PEMLR | 1 | 1.0000 |
| PREXPLF | PREMPNOT | 2 | 0.9994 |
| PRFTLF | PREMPNOT | 2 | 1.0000 |
| PRHRUSL | PREXPLF | 1 | 1.0000 |
| PRJOBSEA | PRWNTJOB | 1 | 1.0000 |
| PRPTHRS | PRPTREA | 17 | 0.9985 |
| PRPTREA | PREMPHRS | 4 | 0.9903 |
| PRUNEDUR | PRWKSCH | 2 | 1.0000 |
| PRUNTYPE | PRWKSCH | 2 | 1.0000 |
| PRWNTJOB | PRWKSTAT | 1 | 1.0000 |
| PEIO1COW | PREXPLF | 2 | 0.9945 |
| PRCOW1 | PREXPLF | 2 | 0.9945 |
| PRMJIND1 | PREXPLF | 2 | 0.9945 |
| PRMJOCC1 | PREXPLF | 2 | 0.9945 |
| PRAGNA | PREXPLF | 2 | 0.9945 |
| PESCHLVL | PESCHENR | 1 | 1.0000 |
| PESCHENR | PRTAGE | 4 | 0.9997 |
| PESCHFT | PESCHENR | 1 | 1.0000 |
| PRNLFSCH | PRTAGE | 4 | 0.9997 |
| PECERT2 | PECERT1 | 1 | 1.0000 |
| PECERT3 | PECERT2 | 2 | 0.9716 |

Items with not-asked cells but no accepted gate (not-asked kept as ordinary level 'Not asked'; None = fewer than 1% of cells): PUWK (None), PEAFEVER (None), PEJHWANT (None), PEJHWKO (None), PENLFJH (None), PEPDEMP1 (None)

## Scores (phase 2: TRAIN+DEV visible, TEST scored; `experiments/eval/run.py`)

| submission | skill | s.e. | seconds |
|---|---|---|---|
| external_model | 0.1599 | 0.0127 | 1.2 |
| v1_learned_gates | 0.2079 | 0.0117 | 195.2 |
| v2_joint | 0.2137 | 0.0116 | 160.4 |

`external_model` is the organisers' baseline as shipped; on datasets with chained gates it returns -2.2e-16 in the NA_GATED slot and the scorer rejects it (FAIL). `external_model_clipped` is the same code with outputs clipped at 0 (scratchpad wrapper). v1/v2 have run-time guards, so on a busy machine they may fit fewer questions; see the dataset notes in the hand-off report.
