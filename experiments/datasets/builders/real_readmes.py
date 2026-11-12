"""Write README.md for every experiments/datasets/real_* dataset from its
build_info.json, the per-dataset source notes below, and the scores recorded in
experiments/eval/results.csv (latest PASS per submission, phase 2, tag real_data)."""
import csv, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K

META = {
    "cps_panel": dict(
        title="US Current Population Survey, Jan + Feb 2024, rotating household panel",
        builder="real_cps_panel.py",
        url="https://www2.census.gov/programs-surveys/cps/datasets/2024/basic/ (jan24pub.csv, feb24pub.csv, "
            "2024_Basic_CPS_Public_Use_Record_Layout_plus_IO_Code_list.txt)",
        licence="US federal government work, public domain (17 U.S.C. 105). No registration.",
        citation="U.S. Census Bureau and Bureau of Labor Statistics, Current Population Survey, Basic Monthly "
                 "Public Use Microdata, January and February 2024.",
        notes=["One row per responding household per month: the household reference person (PERRP 40/41, "
               "complete interview, adult civilian).",
               "Panel: households are linked across months by HRHHID+HRHHID2+PULINENO (used only to sample; "
               "not shipped). 3,600 households appear in both waves, 2,716 only in wave 1, 433 only in wave 2, "
               "so wave 1 = 6,316 rows and wave 2 = 4,033 rows, the UNHCR file's round sizes.",
               "Roles are drawn at random within wave (75/7.5/17.5%), independently of household, so a "
               "held-out row's other-wave row is usually visible (see repeat share).",
               "Skip logic: CPS code -1 = not in universe (never asked) -> NA_GATED when a gate was inferred. "
               "Codes -2/-3/-9 are ordinary levels. Hours/durations banded into <=8 quantile bands.",
               "Admin, weight, allocation-flag, earnings (outgoing-rotation only), detailed industry/occupation "
               "and edit-check items are dropped."]),
    "cps_nopanel": dict(
        title="CONTROL: same CPS months and row counts, no household repeated",
        builder="real_cps_panel.py --nopanel",
        url="as real_cps_panel", licence="public domain (US federal government work)",
        citation="as real_cps_panel",
        notes=["Identical construction to real_cps_panel except that every row is a different household "
               "(6,316 wave-1 and 4,033 wave-2 households, none in both). Use it to separate the gain a model "
               "gets from repeat households from the gain it gets on the instrument itself."]),
    "yougov_vaccine": dict(
        title="Imperial College London / YouGov COVID-19 Behaviour Tracker, 10 countries, Mar-Apr 2021",
        builder="real_yougov_vaccine.py",
        url="https://github.com/YouGov-Data/covid-19-tracker (data/<country>.zip for australia, canada, denmark, "
            "france, germany, israel, italy, japan, spain, united-kingdom; codebook.xlsx)",
        licence="Repository README: 'copyright 2020 YouGov Plc, all rights reserved, is provided to the public "
                "strictly for educational and academic research purposes.' No registration. Not an open licence: "
                "keep for internal research/evaluation only, do not redistribute.",
        citation="Jones, Sarah P., Imperial College London Big Data Analytical Unit and YouGov Plc. 2020, Imperial "
                 "College London YouGov Covid Data Hub, v1.0, YouGov Plc, April 2020.",
        notes=["Online panel survey, one row per respondent, random 20,000 of the ~36,000 interviews dated "
               "1 March - 30 April 2021 in the 10 countries.",
               "Blank cells = questions the online routing never showed -> NA_GATED when a gate was inferred. "
               "Multi-select options are separate Yes/No items. Free-text (_open/_other) dropped.",
               "GIVEN region is 'Country: region', capped at 49 levels + Other."]),
    "afrobarometer_r8": dict(
        title="Afrobarometer Round 8 merged file, part-2 countries (2021-2022, with COVID-19 module)",
        builder="real_afrobarometer_r8.py",
        url="https://www.afrobarometer.org/wp-content/uploads/2023/03/afrobarometer_release-dataset_merge-34ctry_r8_en_2023-03-01.sav "
            "(codebook https://www.afrobarometer.org/wp-content/uploads/2025/07/R8_Merge-Codebook_28May24.final_.pdf)",
        licence="Afrobarometer data are free to use with citation (afrobarometer.org/data); direct download, no "
                "registration. (The same rounds are mirrored on Hugging Face as electricsheepafrica/"
                "africa-afrobarometer-<country>, CC-BY-4.0, but that mirror unions columns across rounds, so the "
                "official merged file was used.)",
        citation="Afrobarometer Data, Round 8 merged data set (34 countries), 2019-2022, release 2023-03-01, "
                 "available at www.afrobarometer.org.",
        notes=["Face-to-face, one adult per household; restricted to R8 part-2 countries (the ones carrying the "
               "COVID-19 module), random 20,000 respondents; roles stratified by country.",
               "Codes labelled 'Not applicable ...' (routed past) or 'Not asked in this country' -> NA_GATED when "
               "a gate was inferred; 'Missing', 'Refused', 'Don't know' are ordinary levels.",
               "Dropped: interviewer/admin fields, verbatims, weights, party/ethnic-group lists, the election-"
               "specific block, Q10-Q19 (dropped by a prefix rule), tax, media-regulation, China/external-"
               "influence blocks (to keep PREDICT near 200).",
               "Many gates are country-level (an item not fielded in some countries), like UNICEF's Q01 on Country."]),
    "dass_tipi": dict(
        title="Open-Source Psychometrics Project: DASS-42 + TIPI + vocabulary check list, 2017-2019",
        builder="real_dass_tipi.py",
        url="https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip",
        licence="No licence named; the raw-data page releases the data 'for general public edification', "
                "anonymous, collected with research consent. No registration.",
        citation="Open-Source Psychometrics Project, DASS (Depression Anxiety Stress Scales) online data, "
                 "collected 2017-2019, https://openpsychometrics.org/_rawdata/.",
        notes=["One row per respondent, random 20,000 of 39,775.",
               "Derived PREDICT items mimic the World Bank file's score bands: DASS-42 severity bands "
               "(standard cut-offs), TIPI trait quintiles, vocabulary-score band, test-duration quintile.",
               "No routed items in this instrument, so no gates (the World Bank file has 40)."]),
    "big5_ipip": dict(
        title="Open-Source Psychometrics Project BIG5: 50-item IPIP Big-Five markers, c. 2012",
        builder="real_big5_ipip.py",
        url="http://openpsychometrics.org/_rawdata/BIG5.zip",
        licence="No licence named; released 'for general public edification', anonymous, research consent at "
                "collection; IPIP items are public domain. No registration.",
        citation="Open-Source Psychometrics Project, BIG5 data (IPIP Big-Five Factor Markers), c. 2012, "
                 "https://openpsychometrics.org/_rawdata/.",
        notes=["One row per respondent, all 19,719.",
               "Derived PREDICT items: quintile bands of the five trait scores (mean of 10 items, reverse-keyed).",
               "No routed items, so no gates."]),
}


def scores(name):
    path = os.path.join(K.ROOT, "experiments", "eval", "results.csv")
    out = {}
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path)):
        if r["dataset"] == "real_" + name and r["phase"] == "2" and r["tag"].startswith("real_data"):
            out[r["submission"]] = r
    return out


def main():
    for name, m in META.items():
        d = os.path.join(K.DATASETS, "real_" + name)
        if not os.path.exists(os.path.join(d, "build_info.json")):
            continue
        info = json.load(open(os.path.join(d, "build_info.json")))
        s = info["summary"]
        L = ["# real_%s — %s" % (name, m["title"]), "",
             "Built by `experiments/datasets/builders/%s` (raw files in `experiments/datasets/raw/`)." % m["builder"], "",
             "- **Source:** %s" % m["url"], "- **Licence / terms:** %s" % m["licence"],
             "- **Citation:** %s" % m["citation"], "",
             "## Shape", "",
             "| rows | GIVEN | PREDICT | gated | gated cells (mean share over PREDICT) | split train/dev/test |",
             "|---|---|---|---|---|---|",
             "| %d | %d | %d | %d | %.3f | %d / %d / %d |" % (s["rows"], s["given"], s["predict"], s["gated"],
                                                         s["gated_cell_share"], s["split"]["n_train"],
                                                         s["split"]["n_dev"], s["split"]["n_test"]), ""]
        if "repeat_share" in info:
            rs = info["repeat_share"]
            L += ["## Repeat households", "",
                  "Share of rows whose household also has a row in the other wave: %.3f." % info["linked_row_share"],
                  "Share of held-out rows whose other-wave row is visible: phase 1 (DEV held out, TRAIN visible) "
                  "%.3f; phase 2 (TEST held out, TRAIN+DEV visible) %.3f." % (rs["phase1"], rs["phase2"]), ""]
        L += ["## What was done", ""] + ["- " + n for n in m["notes"]] + [
              "- Every cell is a string; no NaN. Item non-response has its own level. Levels under 1% of answers "
              "are folded into 'Other'. Roles assigned at random with a fixed seed (75/7.5/17.5%).",
              "- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).", ""]
        g = info.get("gates", {})
        if g:
            ag = np.array([v["agreement"] for v in g.values()])
            L += ["## Gates", "",
                  "Inferred from the data: for each item with not-asked cells, the single other item and value "
                  "set S (values at which most rows hold an answer) that best predicts who was asked; a sibling "
                  "with exactly the same not-asked rows is not allowed as parent, and the gate graph is acyclic. "
                  "Accepted if agreement >= 0.6; otherwise the not-asked cells become the ordinary level "
                  "'Not asked'. Gates are not a constraint the rows satisfy exactly.", "",
                  "Agreement (share of rows where `answered == parent in observed_if`): median %.4f, min %.4f, "
                  "max %.4f, %d gates; %d below 0.95." % (np.median(ag), ag.min(), ag.max(), len(ag), (ag < 0.95).sum()),
                  "", "| item | parent | #observed_if | agreement |", "|---|---|---|---|"]
            for k, v in g.items():
                L.append("| %s | %s | %d | %.4f |" % (k, v["parent"], len(v["observed_if"]), v["agreement"]))
            rej = info.get("rejected_gates_best_agreement", {})
            if rej:
                L += ["", "Items with not-asked cells but no accepted gate (not-asked kept as ordinary level "
                      "'Not asked'; None = fewer than 1%% of cells): %s" % ", ".join("%s (%s)" % kv for kv in rej.items())]
            L.append("")
        else:
            L += ["## Gates", "", "None.", ""]
        sc = scores(name)
        if sc:
            L += ["## Scores (phase 2: TRAIN+DEV visible, TEST scored; `experiments/eval/run.py`)", "",
                  "| submission | skill | s.e. | seconds |", "|---|---|---|---|"]
            for sub in ("external_model", "external_model_clipped", "v1_learned_gates", "v2_joint"):
                if sub in sc:
                    r = sc[sub]
                    L.append("| %s | %s | %s | %s |" % (sub, r["skill"] or r["status"], r["std_error"], r["seconds"]))
            L += ["", "`external_model` is the organisers' baseline as shipped; on datasets with chained gates it "
                  "returns -2.2e-16 in the NA_GATED slot and the scorer rejects it (FAIL). "
                  "`external_model_clipped` is the same code with outputs clipped at 0 (scratchpad wrapper). "
                  "v1/v2 have run-time guards, so on a busy machine they may fit fewer questions; see the "
                  "dataset notes in the hand-off report.", ""]
        if name == "cps_panel" and os.path.exists(os.path.join(d, "repeat_analysis.json")):
            L += ["## Value of the repeat households (`builders/analyse_cps_repeats.py`)", "", "```",
                  open(os.path.join(d, "repeat_analysis.json")).read().strip(), "```",
                  "oracle_link uses the hidden household key (lam * other-wave answer + (1-lam) * marginal); "
                  "given_match finds the partner as the unique other-wave visible row with identical GIVEN "
                  "columns, without the key.", ""]
        open(os.path.join(d, "README.md"), "w").write("\n".join(L))
        print("wrote", name)


if __name__ == "__main__":
    main()
