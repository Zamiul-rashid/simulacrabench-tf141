# Local datasets

No survey data is committed. Each dataset is rebuilt locally by a script in `builders/`
(or `../proxy_survey/` for the two OpenML proxies) and written to
`experiments/datasets/<name>/` as `respondents.parquet` + `schema.json`, in the
competition's exact format (validated with the organisers' `load_schema`, `load_frames`,
`sample_rows`). Each folder here keeps the dataset's README: what was built, from what,
and under which licence.

None of these datasets is used by the submission. They were used only offline, to choose
between model designs, because the hosted grader is silent and its dev scores are coarse.

## Fabricated datasets (our own generators, no external data)

| Dataset | Builder | Shape of | What it plants |
|---|---|---|---|
| `unhcr_full`, `unhcr_repeats`, `unhcr_panel`, `unhcr_additive`, `unhcr_edge`, `unhcr_noisygates`, `unhcr_small_branches` | `unhcr_gen.py` + one config file each | UNHCR schema | Household survey with long skip chains, imperfect gates, repeat interviews of the same household across two rounds (varying share), additive vs interaction effects. True probabilities are recoverable, so `eval/gap_unhcr.py` measures the distance to the best possible score. |
| `wb_realistic`, `wb_edges`, `wb_determined` | `wb_build.py`, `wb_determined.py` | World Bank schema | Platform versions, randomised feedback arms with exact gates, monotone drop-out, derived score bands, near-duplicate before/after items. `ceiling.json` gives the skill of the true conditional. |
| `unicef_realistic`, `unicef_edges` | `unicef_build.py` | UNICEF schema | Country-stratified items, gated items, rare levels. |

## Real public surveys reshaped into the competition format

| Dataset | Builder | Source | Licence |
|---|---|---|---|
| `real_wb_fcc2016_s1/s2` | `real_wb_fcc2016.py` | freeCodeCamp 2016 New Coder Survey (Kaggle) | ODbL-1.0 |
| `real_wb_fcc2021_s1/s2` | `real_wb_fcc2021.py` | freeCodeCamp 2021 New Coder Survey (Kaggle) | CC-BY-SA-4.0 |
| `real_wb_kaggle2017_s1/s2` | `real_wb_kaggle2017.py` | Kaggle ML & Data Science Survey 2017 | ODbL-1.0 |
| `real_wb_so2018_s1/s2/s3` | `real_wb_so2018.py` | Stack Overflow Developer Survey 2018 | ODbL-1.0 (DbCL on Kaggle) |
| `real_cps_panel`, `real_cps_nopanel` | `real_cps_panel.py` | US Current Population Survey, basic monthly public-use files, Jan + Feb 2024 | Public domain |
| `real_afrobarometer_r8` | `real_afrobarometer_r8.py` | Afrobarometer Round 8 merged release (2023-03-01) | Free with citation |
| `real_big5_ipip` | `real_big5_ipip.py` | Open-Source Psychometrics Project, BIG5 (IPIP) | No licence named; released for public use |
| `real_dass_tipi` | `real_dass_tipi.py` | Open-Source Psychometrics Project, DASS 2017-2019 | No licence named; released for public use |
| `proxy`, `proxy_repeat` | `../proxy_survey/build_proxy.py`, `build_repeat_proxy.py` | OpenML `kdd_internet_usage` (1997 GVU survey) | OpenML public dataset |

Raw downloads go in `experiments/datasets/raw/<source>/` (paths at the top of each builder;
the Kaggle sets were fetched with the Kaggle CLI). The `_wb*` sets are mapped onto the
World Bank survey's shape (9 GIVEN columns, ~75 PREDICT, the same split sizes).

We also evaluated on one research-only dataset (the Imperial College London / YouGov
COVID-19 Behaviour Tracker). Its terms do not allow redistribution, so its builder and
data are not in this repository; `builders/real_readmes.py` keeps its citation.
