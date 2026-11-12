"""Real panel household survey with CATI skip logic: US Current Population Survey
(CPS) basic monthly public-use files, January and February 2024.

The CPS is a rotating panel: a household answers in consecutive months, so ~75%
of January households are re-interviewed in February. One row per household per
month = the household reference person's record (labour-force questionnaire,
which is heavily routed: -1 = "not in universe" = never asked). Both waves are
kept as separate rows with a `wave` GIVEN column and no household identifier,
mirroring the UNHCR file (6,316 wave-1 rows, 4,033 wave-2 rows).

Source: https://www2.census.gov/programs-surveys/cps/datasets/2024/basic/
Licence: US federal government work, public domain (17 U.S.C. 105).
"""
import json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K

# `--nopanel` builds the control real_cps_nopanel: same months, same row counts, but
# every row is a different household (no household appears in both waves).
NOPANEL = "--nopanel" in sys.argv
NAME = "cps_nopanel" if NOPANEL else "cps_panel"
SEED = 20261111
RAW = os.path.join(K.RAW, "cps")
N_PAIRS, N_W1_ONLY, N_W2_ONLY = 3600, 2716, 433       # wave 1: 6316 rows, wave 2: 4033


def parse_layout(path):
    """{VAR: (question, {code: label})} from the Census record layout text.
    Codes are normalised to int strings ("01" -> "1"); multi-column value tables
    ("01 AL   30 MT") are read as pairs."""
    txt = open(path, encoding="latin1").read().replace("\x85", "...").replace("\x92", "'").splitlines()
    head = re.compile(r"^([A-Z][A-Z0-9_]+)\s+(\d+)\s+(.*?)\s+\(?(\d+)\s*-\s*(\d+)\)?\s*$")
    out, cur, q, lab, in_q, in_vals = {}, None, [], {}, False, False
    def flush():
        if cur and cur not in out:
            out[cur] = (" ".join(" ".join(q).split()), dict(lab))
    for line in txt:
        m = head.match(line)
        if m:
            flush(); cur = m.group(1); q = [m.group(3).strip()]; lab = {}; in_q = True; in_vals = False
            continue
        if cur is None:
            continue
        s = line.strip()
        if not s:
            in_q = False; continue
        if s.startswith("VALID ENTRIES"):
            in_q = False; in_vals = True; continue
        if s.startswith(("EDITED UNIVERSE", "UNIVERSE", "EDIT")):
            in_q = False; continue
        if in_q and line[:1] in "\t ":
            q.append(s); continue
        if in_vals:
            tok = [t for t in re.split(r"\t+|\s{2,}", s) if t]
            i = 0
            while i < len(tok) - 1:
                if re.fullmatch(r"-?\d+", tok[i]) and not re.fullmatch(r"-?\d+", tok[i + 1]):
                    lab.setdefault(str(int(tok[i])), tok[i + 1].strip()); i += 2
                else:
                    i += 1
    flush()
    return out


LAYOUT = parse_layout(os.path.join(RAW, "2024_Basic_CPS_Public_Use_Record_Layout_plus_IO_Code_list.txt"))
NEG = {"-2": "Don't know", "-3": "Refused", "-9": "No response", "-4": "Hours vary"}

GIVEN_SRC = ["GESTFIPS", "GTMETSTA", "HRNUMHOU", "HRHTYPE", "PRTAGE", "PESEX", "PTDTRACE",
             "PEHSPNON", "PEMARITL", "PEEDUCA", "PRCITSHP", "PENATVTY"]
DROP_PREFIX = ("PX", "PW", "HX", "GT", "GE", "QSTNUM", "OCCURNUM", "HRHHID", "HRMIS", "HRMONTH",
               "HRYEAR4", "HUFINAL", "HURESPLI", "HRLONGLK", "HWHH", "PULINENO", "HUINTTYP",
               "HUPRSCNT", "HRINTSTA", "PRPERTYP", "PERRP", "PEERN", "PTERN", "PRERN", "PRHERN",
               "PRWERN", "PRERELG", "PEIO1ICD", "PEIO2ICD", "PEIO1OCD", "PEIO2OCD", "PTIO1OCD",
               "PTIO2OCD", "PRDTIND", "PRDTOCC", "PRIMIND", "PRDTCOW", "PRCHLD", "PUHRCK",
               "PUBUSCK", "PULAYCK", "PUDWCK", "PUJHCK", "PUIOCK", "PUNLFCK", "PUJHDP",
               "PUIODP", "PUIO1MFG", "PUIO2MFG", "PULKM", "PULKDK", "PULKPS", "PULKAVR",
               "PULAYAVR", "PULAYDT", "PULAY6M", "PUSLFPRX", "PECOHAB", "PULKAVR", "PEPAR",
               "PRFAMNUM", "PRFAMREL", "PEFNTVTY", "PEMNTVTY", "PESPOUSE", "PRTFAGE", "HUTYPB",
               "HUTYPC", "HUTYPEA", "HUBUSL", "PTHR", "PTWK", "PTOT", "PTNMEMP", "PRNAG",
               "PRDASIAN", "PRDTHSP", "PRMARSTA", "PEDIPGED", "PEHGCOMP", "PECYC", "PRINUYER",
               "PEAFWHN", "PRDISC", "PRIOELG", "PRCOWPG", "PRSJMJ", "PRMJOCGR", "PEIO2COW",
               "PRCOW2", "PRMJIND2", "PRMJOCC2", "PEPDEMP2", "PENLFRET", "PEHRUSL2", "PEHRACT2",
               "PRNMCHLD", "HETELAVL", "HEPHONEO", "PRCITFLG", "PUCHINHH")


def label(var, code):
    lab = LAYOUT.get(var, ("", {}))[1]
    try:
        code = str(int(code))
    except ValueError:
        pass
    if code in lab:
        return "%s. %s" % (code, lab[code].title())
    if code in NEG:
        return NEG[code]
    return code


def load():
    frames = []
    for w, f in ((1, "jan24pub.csv"), (2, "feb24pub.csv")):
        d = pd.read_csv(os.path.join(RAW, f), dtype=str)
        d.columns = d.columns.str.upper()
        d = d[(d.HRINTSTA == "1") & d.PERRP.isin(["40", "41"]) & (d.PRPERTYP == "2")].copy()
        d["wave"] = w
        frames.append(d)
    a, b = frames
    key = ["HRHHID", "HRHHID2", "PULINENO"]
    a["hh"] = a[key].agg("-".join, axis=1); b["hh"] = b[key].agg("-".join, axis=1)
    both = sorted(set(a.hh) & set(b.hh))
    rng = np.random.default_rng(SEED)
    if NOPANEL:
        pairs = np.array([], dtype=object)
        a_only = rng.choice(sorted(set(a.hh)), N_PAIRS + N_W1_ONLY, replace=False)
        b_only = rng.choice(sorted(set(b.hh) - set(a_only)), N_PAIRS + N_W2_ONLY, replace=False)
    else:
        pairs = rng.choice(both, N_PAIRS, replace=False)
        a_only = rng.choice(sorted(set(a.hh) - set(both)), N_W1_ONLY, replace=False)
        b_only = rng.choice(sorted(set(b.hh) - set(both)), N_W2_ONLY, replace=False)
    d = pd.concat([a[a.hh.isin(np.concatenate([pairs, a_only]))],
                   b[b.hh.isin(np.concatenate([pairs, b_only]))]], ignore_index=True)
    return d


def main():
    d = load()
    unit = d.pop("hh").to_numpy()
    cols = [c for c in d.columns if c != "wave" and not c.startswith(DROP_PREFIX)]
    out = pd.DataFrame(index=d.index)
    q = {}
    out["wave"] = d.wave.map({1: "Wave 1 (January 2024)", 2: "Wave 2 (February 2024)"})
    q["wave"] = "Survey round (interview month)."
    # GIVEN block
    st = d.GESTFIPS.map(lambda c: label("GESTFIPS", c))
    out["GESTFIPS"] = K.cap_levels(st, 45)
    out["GTMETSTA"] = d.GTMETSTA.map(lambda c: label("GTMETSTA", c))
    out["HRNUMHOU"] = K.band(d.HRNUMHOU, [0, 1, 2, 3, 4, 5, 99], ["1", "2", "3", "4", "5", "6+"])
    out["HRHTYPE"] = d.HRHTYPE.map(lambda c: label("HRHTYPE", c))
    out["PRTAGE"] = K.band(d.PRTAGE, [14, 24, 34, 44, 54, 64, 74, 120],
                           ["15-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"])
    for c in ["PESEX", "PEHSPNON", "PEMARITL", "PEEDUCA", "PRCITSHP"]:
        out[c] = d[c].map(lambda v, c=c: label(c, v))
    out["PTDTRACE"] = K.cap_levels(d.PTDTRACE.map(lambda v: label("PTDTRACE", v)), 6)
    out["PENATVTY"] = K.cap_levels(d.PENATVTY.map(lambda v: label("PENATVTY", v)), 12)
    given = ["wave"] + GIVEN_SRC
    for c in GIVEN_SRC:
        q[c] = LAYOUT.get(c, (c, {}))[0] or c
        out[c] = out[c].fillna("Not in universe").replace("-1", "Not in universe").astype(str)
    # PREDICT block
    predict = []
    for c in cols:
        if c in GIVEN_SRC:
            continue
        v = d[c].fillna("-1").astype(str).str.strip()
        v = v.where(v != "", "-1")
        skip = v == "-1"
        if skip.mean() > 0.985:
            continue
        lab = LAYOUT.get(c, ("", {}))[1]
        num = pd.to_numeric(v, errors="coerce")
        pos = num[(num >= 0) & ~skip]
        if (pos.nunique() > 25 and len(lab) < 10) or (len(lab) <= 3 and pos.nunique() > 12):
            # numeric: band observed non-negative values into <= 8 ordered bands
            qs = np.unique(np.quantile(pos, np.linspace(0, 1, 9)))
            edges = [-0.5] + list(qs[1:-1]) + [np.inf]
            edges = sorted(set(edges))
            labs = []
            for lo, hi in zip(edges[:-1], edges[1:]):
                lo_i = int(np.floor(lo)) + 1 if lo > -0.5 else 0
                labs.append("%d+" % lo_i if np.isinf(hi) else ("%d-%d" % (lo_i, int(np.floor(hi)))))
            b = pd.cut(num, edges, labels=labs).astype(object)
            s = pd.Series(np.where(skip, K.SKIP, np.where(num >= 0, b, v.map(lambda x: NEG.get(x, x)))),
                          index=v.index).astype(str)
        else:
            s = v.map(lambda x, c=c: K.SKIP if x == "-1" else label(c, x))
            if s[s != K.SKIP].nunique() > 25:
                s = K.cap_levels(s, 20, keep=(K.SKIP,))
            s = K.cap_rare(s)
        if s[s != K.SKIP].nunique() < 2:
            continue
        out[c] = s
        predict.append(c)
        q[c] = LAYOUT.get(c, (c, {}))[0] or c
    order = given + predict
    acc, rej = K.infer_gates(out, order)
    gates = {k: (p, S) for k, (p, S, a) in acc.items()}
    desc = ("US Current Population Survey (CPS) basic monthly labour-force survey, January and February "
            "2024, public-use file. One row per responding household per month: the household reference "
            "person's record. The CPS is a rotating panel, so many households answer in both months; the "
            "two months are kept as separate rows (GIVEN `wave`) with no household identifier, so linked "
            "rows are not marked. Wave 1 contributes %d rows and wave 2 %d. CATI routing: a cell coded "
            "-1 (not in universe) is a question never put to the respondent; gates are inferred from the "
            "data (best single earlier item and value set) and are not a constraint the rows satisfy "
            "exactly. Numeric items (hours, durations, counts) are cut into <=8 quantile bands; negative "
            "codes -2/-3/-9 are ordinary levels. Source: US Census Bureau, public domain."
            % ((out.wave.str.startswith("Wave 1")).sum(), (out.wave.str.startswith("Wave 2")).sum()))
    frame, schema, unit_p = K.write_dataset(NAME, out, given, predict, q, gates, desc, SEED,
                                            strata=out.wave.to_numpy(), extra_cols=pd.Series(unit))
    K.validate(NAME)
    s, ag = K.summary(frame, schema)
    rs = K.repeat_share(frame, unit_p.to_numpy())
    # private household key for analysis only (never shipped in the dataset dir)
    pd.DataFrame({"respondent_id": frame.respondent_id, "household": unit_p.to_numpy()}).to_parquet(
        os.path.join(RAW, "household_key_%s.parquet" % NAME), index=False)
    linked = pd.Series(unit_p).duplicated(keep=False).mean()
    info = {"summary": s, "repeat_share": rs, "linked_row_share": round(float(linked), 4),
            "gates": {k: {"parent": acc[k][0], "observed_if": acc[k][1], "agreement": ag[k]} for k in acc},
            "rejected_gates_best_agreement": rej}
    json.dump(info, open(os.path.join(K.DATASETS, "real_" + NAME, "build_info.json"), "w"), indent=1)
    print(json.dumps({"summary": s, "repeat_share": rs, "linked_row_share": info["linked_row_share"],
                      "n_rejected": len(rej)}, indent=1))


if __name__ == "__main__":
    main()
