"""Shared machinery for the fabricated UNICEF / World Bank test datasets.

A dataset is defined by two functions:

  make_given(n, roles, rng) -> DataFrame of the GIVEN columns (schema values)
  simulate(given, rng)      -> (values, probs)
        values[item]: (n,) object array, the drawn answer (schema value or NA_GATED)
        probs[item]:  (n, width) the analytic distribution of the item given the
                      GIVEN block, the row's latent draws and its already drawn
                      ancestors (gate slot last when the item is gated)

Because `simulate` returns the analytic conditional of every item given the
row's latent state, the true conditional P(item | GIVEN) of a held-out row is
the average of `probs` over many independent replicates of that row
(Rao-Blackwellised Monte Carlo). That average is the "ceiling": the best any
submission can do in expectation. Items that are deterministic functions of
other sampled quantities (score bands) get a one-hot `probs`, so their ceiling
is estimated by frequency over the replicates (slightly pessimistic).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "starter-kit"))
SENT = "NA_GATED"
ROLES = ("TRAIN", "DEV", "TEST")


# ------------------------------------------------------------ schema ---------

def load_real_schema(name):
    with open(os.path.join(ROOT, "starter-kit", "data", name + ".json"), encoding="utf-8") as fh:
        schema = json.load(fh)
    schema["gated_value"] = SENT
    return schema


def options(schema, item):
    rec = schema["items"][item]
    return list(rec["values"]) + ([SENT] if rec.get("gate") else [])


# ------------------------------------------------------------ sampling -------

def softmax(L):
    L = L - L.max(axis=1, keepdims=True)
    E = np.exp(L)
    return E / E.sum(axis=1, keepdims=True)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def ordinal(eta, cuts):
    """Ordered logit: eta (n,), cuts (K-1,) increasing -> (n, K)."""
    cdf = sigmoid(np.asarray(cuts)[None, :] - np.asarray(eta)[:, None])
    cdf = np.concatenate([np.zeros((len(eta), 1)), cdf, np.ones((len(eta), 1))], axis=1)
    return np.clip(np.diff(cdf, axis=1), 0.0, None)


def draw(P, rng):
    P = P / P.sum(axis=1, keepdims=True)
    return (P.cumsum(axis=1) > rng.random((P.shape[0], 1))).argmax(axis=1)


def onehot(idx, width):
    out = np.zeros((len(idx), width))
    out[np.arange(len(idx)), idx] = 1.0
    return out


def given_col(rng, levels, P, n=None):
    """Draw a GIVEN column; P is (n, K), or (K,) together with n."""
    P = np.asarray(P, dtype=float)
    if P.ndim == 1:
        P = np.tile(P, (n, 1))
    return np.asarray(levels, dtype=object)[draw(P, rng)]


class Sim:
    """Accumulates drawn values and analytic conditionals in generation order."""

    def __init__(self, schema, given, rng):
        self.schema, self.rng = schema, rng
        self.n = len(given)
        self.values = {c: given[c].to_numpy(dtype=object) for c in given.columns}
        self.probs = {}

    def opts(self, item):
        return self.schema["items"][item]["values"]

    def idx(self, item, value):
        return self.opts(item).index(value)

    def is_(self, item, *vals):
        return np.isin(self.values[item], np.asarray(vals, dtype=object))

    def put(self, item, P, obey=1.0, leak=0.0, values=None):
        """P (n, W) over the schema values. Gate: P(asked) = obey if the parent
        is in observed_if, leak otherwise (exact gate: obey=1, leak=0).
        `values` (n,) optionally gives the answers already drawn (consistent with
        P); the gate is then applied on top of them."""
        P = np.asarray(P, dtype=float)
        W = len(self.opts(item))
        assert P.shape == (self.n, W), (item, P.shape, W)
        P = P / P.sum(axis=1, keepdims=True)
        gate = self.schema["items"][item].get("gate")
        if gate:
            open_ = np.isin(self.values[gate["parent"]], np.asarray(gate["observed_if"], dtype=object))
            asked = np.where(open_, obey, leak)
            P = np.concatenate([P * asked[:, None], (1.0 - asked)[:, None]], axis=1)
        if values is None:
            k = draw(P, self.rng)
            self.values[item] = np.asarray(options(self.schema, item), dtype=object)[k]
        else:
            values = np.asarray(values, dtype=object)
            if gate:
                values = np.where(self.rng.random(self.n) < asked, values, SENT)
            self.values[item] = values
        self.probs[item] = P
        return self.values[item]

    def put_value(self, item, values, **gate):
        """A deterministic item: values (n,) of schema values."""
        W = len(self.opts(item))
        idx = np.array([self.opts(item).index(v) for v in values])
        return self.put(item, onehot(idx, W), **gate)


# ------------------------------------------------------------ building -------

def assign_roles(schema, rng):
    split = schema["split"]
    roles = np.repeat(np.asarray(ROLES, dtype=object), [split["n_train"], split["n_dev"], split["n_test"]])
    return roles[rng.permutation(len(roles))]


def ceiling_probs(schema, simulate, given, rng, reps=300, chunk=50):
    """Mean over `reps` replicates of simulate(...).probs for the rows of `given`."""
    targets = [k for k, r in schema["items"].items() if r["class"] == "PREDICT"]
    acc = {t: 0.0 for t in targets}
    done = 0
    while done < reps:
        m = min(chunk, reps - done)
        rep = pd.concat([given] * m, ignore_index=True)
        _, probs = simulate(rep, rng)
        for t in targets:
            acc[t] = acc[t] + probs[t].reshape(m, len(given), -1).sum(axis=0)
        done += m
    return {t: acc[t] / reps for t in targets}


def score_vectors(schema_path, data_dir, phase, vec_fn):
    """Score vectors with the organisers' functions. vec_fn(frame, cells) -> list of vectors.
    Returns dict(skill, reference, by_item skill)."""
    import score as S
    from make_sandbox import load_config
    config = load_config(os.path.join(ROOT, "starter-kit", "config.yml"))
    floor = config["scoring"]["floor"]
    schema = json.load(open(schema_path))
    schema.setdefault("gated_value", SENT)
    frame, cells, truth = S.sample_rows(schema, S.load_frames(data_dir, schema), phase)
    ref = S.marginal_reference(schema, frame, cells, truth, floor)
    vec = vec_fn(frame, cells)
    S.check(schema, vec, cells)
    res = S.score(schema, config, S.floored(vec, schema, cells, floor), truth, cells, ref)
    by_item = (1.0 + res["by_item"]["mean"] / ref).round(4).to_dict()
    return {"skill": round(res["skill"], 4), "reference": round(ref, 4), "by_item_skill_share": by_item}


def build(name, schema_name, make_given, simulate, seed, post_edit=None, reps=300,
          planted="", ceiling_phases=(1, 2)):
    """Generate, validate with the organisers' loader, write files, compute ceilings."""
    import score as S
    schema = load_real_schema(schema_name)
    n = schema["dataset"]["n_rows"]
    rng = np.random.default_rng(seed)
    roles = assign_roles(schema, rng)
    given = make_given(n, roles, rng)
    gcols = [k for k, r in schema["items"].items() if r["class"] == "GIVEN"]
    assert list(given.columns) == gcols, (list(given.columns), gcols)
    values, _ = simulate(given.reset_index(drop=True), rng)
    items = [k for k, r in schema["items"].items() if r["class"] in ("GIVEN", "PREDICT")]
    frame = pd.DataFrame({c: values[c] for c in items})
    frame.insert(0, "respondent_id", ["R%06d" % i for i in range(1, n + 1)])
    frame.insert(1, "role", roles)
    if post_edit is not None:
        frame = post_edit(frame, rng)
    frame = frame.astype(object)
    assert not frame.isna().any().any()

    out = os.path.join(ROOT, "experiments", "datasets", name)
    os.makedirs(out, exist_ok=True)
    frame.to_parquet(os.path.join(out, "respondents.parquet"), index=False)
    with open(os.path.join(out, "schema.json"), "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    # the organisers' own checks
    from make_sandbox import load_config, load_schema
    config = load_config(os.path.join(ROOT, "starter-kit", "config.yml"))
    load_schema(os.path.join(out, "schema.json"), config)
    S.load_frames(out, schema)

    # ceiling: true conditional given GIVEN, for the rows scored in each phase
    ceiling = {}
    hidden_role = {1: "DEV", 2: "TEST"}
    for phase in ceiling_phases:
        rows = np.flatnonzero(roles == hidden_role[phase])
        g = given.iloc[rows].reset_index(drop=True)
        P = ceiling_probs(schema, simulate, g, np.random.default_rng(seed + 1000 + phase), reps=reps)
        id2row = {rid: i for i, rid in enumerate(frame["respondent_id"].to_numpy()[rows])}
        targets = [k for k, r in schema["items"].items() if r["class"] == "PREDICT"]

        def vec_fn(fr, cells, P=P, id2row=id2row):
            return [P[item][id2row[rid]] for _, rid, item in cells]
        if os.environ.get("CEIL_DIR"):
            import pickle
            with open(os.path.join(os.environ["CEIL_DIR"], "%s_p%d.pkl" % (name, phase)), "wb") as fh:
                pickle.dump({"ids": list(id2row), "P": P}, fh)
        ceiling[phase] = score_vectors(os.path.join(out, "schema.json"), out, phase, vec_fn)
        print("%s phase %d ceiling skill %.4f (reference %.4f nats)"
              % (name, phase, ceiling[phase]["skill"], ceiling[phase]["reference"]))
    with open(os.path.join(out, "ceiling.json"), "w") as fh:
        json.dump({"seed": seed, "replicates": reps, "phases": ceiling}, fh, indent=1)
    return frame, ceiling
