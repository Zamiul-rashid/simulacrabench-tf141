"""v10: four standard models of P(answer | GIVEN columns), blended per question.

For every PREDICT question the gate sentinel ("not asked") is one more answer
option; the schema's gate rules are never applied as exact (the UNHCR schema
says they agree with the data only 29-98% of the time).

Members, all fitted on the visible rows at run time:
  1. crowd marginal                         (always available; the fallback)
  2. one shared neural network with an output head per question
  3. similarity model: every visible person votes on a held-out person's
     answers, weighted by agreement on the GIVEN columns (column weights learned
     by leave-one-out loss). Where nobody is similar it falls back to the
     network's prediction, so it only departs from it when it has evidence.
  4. per-question regularised logistic regression
  5. TabICL v2, a pretrained tabular model used purely for inference (the
     checkpoint ships in the archive; no fine-tuning). Dropped with a log line
     if the package or the checkpoint is unavailable.
Blend: per-question linear pool, weights fitted by EM on predictions for rows
the member did not train on, shrunk toward the survey-wide weights; averaged with
a geometric (log) pool of the same members, which can sharpen where the linear
pool is under-confident. Last step: a correction for the grader's floor, applied
only as far as the held-back rows support it.

Everything is time-guarded; a question that fails or is not reached keeps
whatever members it has, down to the marginal.
"""
import os
import time
import types
import warnings

import numpy as np
import pandas as pd

# The hosted run imports this file once and calls predict() for each survey in turn,
# under one clock (900 s in development, 3600 s in the final). So the clock starts
# here, and each call takes its share of what is actually left: time one survey does
# not use goes to the surveys after it.
CLOCK_SECONDS = {1: 800.0, 2: 2900.0}
_CLOCK = {"start": time.time(), "targets_done": 0.0}
TOTAL_TARGETS = 301.0
MIN_SECONDS = 80.0
FULL_PASSES = int(os.environ.get("SB_FULL_PASSES", "4"))   # two TabICL members per pass
FLOOR = 1e-3
N_FOLDS = 5
KNN_BETAS = (0.5, 1.0, 2.0, 4.0)       # weight = exp(-beta * columns that differ)
KNN_ALPHAS = (0.05, 0.5, 5.0)                # pseudo-count toward the marginal
LR_CS = (0.03, 0.3, 3.0, 30.0)
PRIOR_ROWS = 40.0                      # shrinkage of blend weights toward survey-wide


def _floored(p, width):
    return FLOOR + (1.0 - width * FLOOR) * p


# ------------------------------------------------------------------ members --

def knn_member(torch, dev, Xv, Xh, Yv, slices, marg, y_codes, blend_rows, col_owner,
               train_deadline, deadline, base_v=None, base_h=None):
    """Similarity search with learned column weights. Similarity of two people is
    the weighted count of GIVEN columns on which they agree; the weights are
    learned by leave-one-out log loss on the visible rows. Returns
    ({q: blend-row preds}, {q: hidden preds}) with (scale, alpha) chosen per
    question by leave-one-out log loss."""
    n = Xv.shape[0]
    configs = [(b, a) for b in KNN_BETAS for a in KNN_ALPHAS]
    m = torch.tensor(np.concatenate([marg[q] for q in slices]), device=dev, dtype=torch.float32)
    is_blend = torch.zeros(n, dtype=torch.bool, device=dev); is_blend[blend_rows] = True
    loss = {c: torch.zeros(len(slices), device=dev) for c in configs}
    keep_blend = {c: [] for c in configs}
    keep_hidden = {c: [] for c in configs}
    starts = torch.tensor([s for s, _ in slices.values()], device=dev)
    widths = torch.tensor([w for _, w in slices.values()], device=dev)
    owner = torch.repeat_interleave(torch.arange(len(slices), device=dev), widths)
    ycol = torch.tensor(np.column_stack([y_codes[q] for q in slices]), device=dev) + starts[None, :]
    col_owner = torch.tensor(col_owner, device=dev)

    if base_v is None:
        base_v, base_h = m[None, :].expand(n, -1), m[None, :].expand(Xh.shape[0], -1)

    def normalise(S, alpha, prior):
        num = S + alpha * prior
        den = torch.zeros(S.shape[0], len(slices), device=dev).index_add_(1, owner, num)
        return num / den[:, owner]

    # ---- learn one weight per GIVEN column (start: every column counts 1) ----
    log_theta = torch.zeros(int(col_owner.max()) + 1, device=dev, requires_grad=True)
    log_alpha = torch.tensor(float(np.log(0.3)), device=dev, requires_grad=True)
    opt = torch.optim.Adam([log_theta, log_alpha], lr=0.08)
    gen = torch.Generator(device="cpu").manual_seed(0)
    best_state, best_val, bad = log_theta.detach().clone(), float("inf"), 0
    probe = torch.randperm(n, generator=gen)[:min(n, 1024)].to(dev)

    def loo_loss(rows, lt, la):
        theta = lt.exp()
        sim = (Xv[rows] * theta[col_owner][None, :]) @ Xv.T - theta.sum()
        W = torch.exp(sim)
        W = W.masked_fill(torch.arange(n, device=dev)[None, :] == rows[:, None], 0.0)
        P = normalise(W @ Yv, la.exp(), base_v[rows])
        return -torch.log(P.gather(1, ycol[rows]).clamp_min(1e-6)).mean()

    with torch.enable_grad():
        for it in range(300):
            if time.time() > train_deadline:
                break
            rows = torch.randperm(n, generator=gen)[:512].to(dev)
            l = loo_loss(rows, log_theta, log_alpha)
            opt.zero_grad(); l.backward(); opt.step()
            with torch.no_grad():
                log_theta.clamp_(-6.0, 3.0)
            if it % 10 == 9:
                with torch.no_grad():
                    v = float(loo_loss(probe, log_theta, log_alpha))
                if v < best_val - 1e-4:
                    best_val, bad, best_state = v, 0, log_theta.detach().clone()
                else:
                    bad += 1
                    if bad >= 4:
                        break
    theta = best_state.exp()
    Xw_v, Xw_h, p = Xv * theta[col_owner][None, :], Xh * theta[col_owner][None, :], float(theta.sum())

    step = 1024
    for beta in KNN_BETAS:
        if time.time() > deadline:
            return None
        for lo in range(0, n, step):
            if time.time() > deadline:
                return None
            hi = min(lo + step, n)
            W = torch.exp(beta * (Xw_v[lo:hi] @ Xv.T - p))
            W[torch.arange(hi - lo, device=dev), torch.arange(lo, hi, device=dev)] = 0.0   # leave one out
            S = W @ Yv
            for alpha in KNN_ALPHAS:
                P = normalise(S, alpha, base_v[lo:hi])
                wq = widths[None, :].float()
                picked = FLOOR + (1.0 - wq * FLOOR) * P.gather(1, ycol[lo:hi])
                loss[(beta, alpha)] -= torch.log(picked).sum(0)
                sel = is_blend[lo:hi]
                if sel.any():
                    keep_blend[(beta, alpha)].append(P[sel].cpu())
        for lo in range(0, Xh.shape[0], step):
            if time.time() > deadline:
                return None
            S = torch.exp(beta * (Xw_h[lo:lo + step] @ Xv.T - p)) @ Yv
            for alpha in KNN_ALPHAS:
                keep_hidden[(beta, alpha)].append(normalise(S, alpha, base_h[lo:lo + step]).cpu())
    L = torch.stack([loss[c] for c in configs]).cpu().numpy()            # configs x questions
    best = L.argmin(0)
    B = {c: torch.cat(keep_blend[c]).numpy() for c in configs}
    Hd = {c: torch.cat(keep_hidden[c]).numpy() for c in configs}
    blend, hidden = {}, {}
    for j, (q, (s, w)) in enumerate(slices.items()):
        c = configs[best[j]]
        blend[q], hidden[q] = B[c][:, s:s + w], Hd[c][:, s:s + w]
    return blend, hidden, [round(float(x), 2) for x in theta.cpu()]


def mlp_member(torch, dev, Xv, Xh, slices, marg, y_codes, fold, blend_rows, deadline,
               hidden=(128,), dropout=0.5):
    """Shared one-hidden-layer network, one softmax head per question. Net f trains
    on three folds, early-stops on fold f+1 and predicts fold f (so those
    predictions are honest); hidden rows get the mean of the nets."""
    nn = torch.nn
    n, D = Xv.shape
    T = sum(w for _, w in slices.values())
    names = list(slices)
    starts = torch.tensor([slices[q][0] for q in names], device=dev)
    widths = [slices[q][1] for q in names]
    owner = torch.repeat_interleave(torch.arange(len(names), device=dev),
                                    torch.tensor(widths, device=dev))
    Y = torch.tensor(np.column_stack([y_codes[q] for q in names]), device=dev) + starts[None, :]
    bias0 = torch.tensor(np.log(np.concatenate([marg[q] for q in names])),
                         device=dev, dtype=torch.float32)
    fold_t = torch.tensor(fold, device=dev)

    def log_probs(logits):
        mx = torch.full((logits.shape[0], len(names)), -1e30, device=dev)
        mx = mx.scatter_reduce(1, owner[None, :].expand(logits.shape[0], -1), logits, "amax")
        z = logits - mx[:, owner]
        den = torch.zeros(logits.shape[0], len(names), device=dev).index_add_(1, owner, z.exp())
        return z - den.log()[:, owner]

    oof = torch.zeros(n, T, device=dev)
    hid = torch.zeros(Xh.shape[0], T, device=dev)
    done = 0
    for f in range(N_FOLDS):
        if time.time() > deadline:
            break
        stop_f = (f + 1) % N_FOLDS
        tr = torch.nonzero((fold_t != f) & (fold_t != stop_f)).squeeze(1)
        va = torch.nonzero(fold_t == stop_f).squeeze(1)
        te = torch.nonzero(fold_t == f).squeeze(1)
        torch.manual_seed(f)
        layers, size = [], D
        for h in hidden:
            layers += [nn.Linear(size, h), nn.ReLU(), nn.Dropout(dropout)]
            size = h
        net = nn.Sequential(*layers, nn.Linear(size, T)).to(dev)
        with torch.no_grad():
            net[-1].bias.copy_(bias0)
        decay = [p for name, p in net.named_parameters() if p is not net[-1].bias]
        opt = torch.optim.AdamW([{"params": decay, "weight_decay": 1e-2},
                                 {"params": [net[-1].bias], "weight_decay": 0.0}], lr=3e-3)
        best_q = torch.full((len(names),), float("inf"), device=dev)
        best_all, bad = float("inf"), 0
        keep_te = torch.zeros(len(te), T, device=dev)
        keep_h = torch.zeros(Xh.shape[0], T, device=dev)
        for epoch in range(80):
            net.train()
            perm = tr[torch.randperm(len(tr), device=dev)]
            for lo in range(0, len(perm), 512):
                if time.time() > deadline:
                    return None
                idx = perm[lo:lo + 512]
                lp = log_probs(net(Xv[idx]))
                loss = -lp.gather(1, Y[idx]).mean()
                opt.zero_grad(); loss.backward(); opt.step()
            net.eval()
            with torch.no_grad():
                vq = -log_probs(net(Xv[va])).gather(1, Y[va]).mean(0)          # per question
                better = vq < best_q
                if better.any():
                    cols = better[owner]
                    keep_te[:, cols] = log_probs(net(Xv[te])).exp()[:, cols]
                    keep_h[:, cols] = log_probs(net(Xh)).exp()[:, cols]
                    best_q = torch.where(better, vq, best_q)
                total = float(vq.mean())
            if total < best_all - 1e-5:
                best_all, bad = total, 0
            else:
                bad += 1
                if bad >= 10:
                    break
            if time.time() > deadline:
                break
        oof[te] = keep_te
        hid += keep_h
        done += 1
    if done < N_FOLDS:
        return None                                  # incomplete OOF: do not blend it
    oof, hid = oof.cpu().numpy(), (hid / done).cpu().numpy()
    oof_blend = oof[blend_rows]          # one copy; indexing inside the loop made one per question
    blend = {q: oof_blend[:, s:s + w] for q, (s, w) in slices.items()}
    hidden = {q: hid[:, s:s + w] for q, (s, w) in slices.items()}
    return blend, hidden, oof, hid


def lr_member(Xv, Xh, y, width, fit_idx, val_idx, deadline):
    """Per-question logistic regression. Penalty chosen on the held-back fold.
    Returns (held-back-fold preds, hidden preds) or None."""
    from sklearn.linear_model import LogisticRegression

    def proba(model, X):
        out = np.zeros((X.shape[0], width)); out[:, model.classes_] = model.predict_proba(X)
        return out

    yf, yv = y[fit_idx], y[val_idx]
    if len(np.unique(yf)) < 2:
        return None
    best = (np.inf, None, None)
    for c in LR_CS:
        if time.time() > deadline:
            break
        model = LogisticRegression(C=c, max_iter=200).fit(Xv[fit_idx], yf)
        pv = proba(model, Xv[val_idx])
        loss = -np.log(_floored(pv, width)[np.arange(len(yv)), yv]).mean()
        if loss < best[0]:
            best = (loss, c, pv)
    if best[1] is None or time.time() > deadline:
        return None
    model = LogisticRegression(C=best[1], max_iter=300).fit(Xv, y)
    return best[2], proba(model, Xh)


TABICL_CKPT = "tabicl-classifier-v2-20260212.ckpt"
_TABICL = {}


def tabicl_member(codes_v, codes_h, cards, y_codes, order, width, fit_rows, blend_rows, deadline,
                  passes=(0, 1), blend=None, hidden=None, n_full=None):
    """TabICL per question, most uncertain questions first, until the deadline.
    GIVEN columns are fed twice: as the frequency rank of each level among the
    context rows and as the schema's own level order; two ensemble members. Two passes per question: fit rows -> blend rows (for the blend
    weights), then all visible rows -> hidden rows."""
    import torch
    from tabicl import TabICLClassifier
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), TABICL_CKPT)
    if not os.path.exists(path):
        raise FileNotFoundError(TABICL_CKPT)

    def cached_load(self):                         # load the weights once, not per question
        if "m" not in _TABICL:
            ck = torch.load(path, map_location="cpu", weights_only=True)
            from tabicl._model.tabicl import TabICL
            model = TabICL(**ck["config"]); model.load_state_dict(ck["state_dict"]); model.eval()
            _TABICL["m"], _TABICL["cfg"] = model, ck["config"]
        self.model_path_, self.model_, self.model_config_ = path, _TABICL["m"], _TABICL["cfg"]

    def encode(context, *others):
        p = context.shape[1]
        outs = [np.empty((a.shape[0], 2 * p), np.float32) for a in (context,) + others]
        for j in range(p):
            count = np.bincount(context[:, j], minlength=cards[j])
            rank = np.empty(cards[j], np.float32)
            rank[np.argsort(-count, kind="stable")] = np.arange(cards[j])
            for o, a in zip(outs, (context,) + others):
                o[:, j] = rank[a[:, j]]
                o[:, p + j] = a[:, j]
        return outs

    def run(Xc, y, Xq, k, full):
        if full:                                   # both encodings, two ensemble members
            clf = TabICLClassifier(n_estimators=2, norm_methods=["none"], model_path=path,
                                   allow_auto_download=False, softmax_temperature=1.0,
                                   random_state=full - 1)
        else:                                      # frequency ranks only, one member: about 2.4x faster
            Xc, Xq = Xc[:, :n_given], Xq[:, :n_given]
            clf = TabICLClassifier(n_estimators=1, model_path=path, allow_auto_download=False,
                                   softmax_temperature=1.0, random_state=0)
        clf._load_model = types.MethodType(cached_load, clf)
        clf.fit(Xc, y)
        out = np.zeros((Xq.shape[0], k))
        out[:, np.asarray(clf.classes_, dtype=int)] = clf.predict_proba(Xq)
        return out

    n_given = codes_v.shape[1]
    Xf, Xb = encode(codes_v[fit_rows], codes_v[blend_rows])
    Xa, Xh = encode(codes_v, codes_h)
    blend = {} if blend is None else blend
    hidden = {} if hidden is None else hidden
    errors, upgraded = 0, {}
    n_full = {} if n_full is None else n_full      # question -> full passes averaged so far
    # Pass 0: the fast setting for every question, so coverage never depends on a time
    # estimate. Pass 1: redo questions with the full setting, most uncertain first.
    # Passes 2, 3, ...: two more ensemble members each (a new seed), averaged into what
    # is there. Every pass stops at the deadline, so a faster machine simply gets
    # further; nothing here needs to know the machine's speed in advance.
    for full in passes:
        for t in order:
            if time.time() > deadline:
                break
            y = y_codes[t]
            if len(np.unique(y[fit_rows])) < 2:
                continue
            try:
                pb = run(Xf, y[fit_rows], Xb, width[t], full)
                ph = run(Xa, y, Xh, width[t], full)
                if np.isfinite(pb).all() and np.isfinite(ph).all():
                    m = n_full.get(t, 0)
                    if full and m and blend.get(t) is not None and blend[t].shape == pb.shape:
                        blend[t] = (blend[t] * m + pb) / (m + 1)
                        hidden[t] = (hidden[t] * m + ph) / (m + 1)
                    else:
                        blend[t], hidden[t] = pb, ph
                    if full:
                        n_full[t] = m + 1
                        upgraded[full] = upgraded.get(full, 0) + 1
            except Exception:
                errors += 1
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                if errors >= 3 and not blend:
                    raise
    return blend, hidden, "%d questions covered; questions done per full pass %s" % (
        len(blend), upgraded or "none")


def floor_correct(q, eps=FLOOR):
    """q: (n, K) beliefs. Returns p (n, K) to submit. Water-filling solution of
    max_p sum_k q_k log(eps + (1 - K eps) p_k): scored vector p'_k = max(c q_k, eps).
    Apply as the very last step, after any exact skip rules, to every question."""
    q = np.clip(np.asarray(q, float), 0, None)
    q = q / q.sum(1, keepdims=True)
    n, K = q.shape
    if K * eps >= 1:
        return q
    srt = -np.sort(-q, axis=1)
    c = (1 - (K - np.arange(1, K + 1)[None, :]) * eps) / np.maximum(np.cumsum(srt, axis=1), 1e-300)
    m = np.maximum((c * srt > eps).sum(1), 1)
    pp = np.maximum(c[np.arange(n), m - 1][:, None] * q, eps)
    pp /= pp.sum(1, keepdims=True)
    return np.clip((pp - eps) / (1 - K * eps), 0, None)


def _logpool(tabs, w):
    L = sum(wj * np.log(np.clip(p / p.sum(1, keepdims=True), 1e-6, None)) for wj, p in zip(w, tabs))
    L = L - L.max(1, keepdims=True)
    e = np.exp(L)
    return e / e.sum(1, keepdims=True)


def _nll(p, y, eps=FLOOR):
    K = p.shape[1]
    return -np.log(eps + (1 - K * eps) * p[np.arange(len(y)), y]).mean()


def fit_log_pool(blend_tabs, y_blend, members, shrink=1.0, wmax=3.0):
    from scipy.optimize import minimize
    """blend_tabs: {member: {t: (n_blend, K_t)}}; y_blend: {t: int codes}; members: list of
    member names (exclude the marginal: a geometric pool does not need it, the weights need not
    sum to 1, which lets the pool sharpen or flatten). Returns {t: (names, weights)}.
    Questions where a member is missing get a pool over the members they have."""
    qs = list(y_blend)
    have = {t: [m for m in members if t in blend_tabs.get(m, {})] for t in qs}
    full = [t for t in qs if len(have[t]) == len(members)]

    def total(w):
        return sum(_nll(_logpool([blend_tabs[m][t] for m in members], w), y_blend[t]) for t in full) / max(len(full), 1)
    M = len(members)
    g = minimize(total, np.ones(M) / M, bounds=[(0, wmax)] * M, method="L-BFGS-B").x if full else np.ones(M) / M
    gmap = dict(zip(members, g))
    out = {}
    for t in qs:
        names = have[t]
        if not names:
            continue
        g0 = np.array([gmap[m] for m in names])
        tabs = [blend_tabs[m][t] for m in names]
        f = lambda w: _nll(_logpool(tabs, w), y_blend[t]) + shrink * ((w - g0) ** 2).sum()
        out[t] = (names, minimize(f, g0, bounds=[(0, wmax)] * len(names), method="L-BFGS-B").x)
    return out


def apply_log_pool(hidden_tabs, pool, t):
    names, w = pool[t]
    return _logpool([hidden_tabs[m][t] for m in names], w)




TOP_BETAS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
TOP_ALPHAS = (0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0)
TOP_MARGIN = float(os.environ.get("SB_TOP_MARGIN", "0.0003"))   # nats per row a setting must gain
TOP_Z = float(os.environ.get("SB_TOP_Z", "2.0"))     # survey-level honest gain must exceed this many standard errors


def similarity_top(Xv, Xh, theta_cols, col_owner, y_codes, slices, blend_rows, prior_b, prior_h,
                   width, deadline):
    """The similarity model once more, as the last layer: for each row, the answers of
    the visible rows that look like it (same learned column weights as the blend
    member) are added to the blended prediction, which acts as the prior. A row with
    no close match keeps the blend; a row with a near-identical visible row moves
    toward that row's answers. How sharply 'close' is defined is one setting for the
    survey, and how much the prior counts is chosen per question, both on the
    held-back rows with each row's own answers left out. A question is left untouched
    unless the layer improves it there."""
    n, T = Xv.shape[0], sum(w for _, w in slices.values())
    th = np.asarray(theta_cols, np.float32)[np.asarray(col_owner)]
    tot = float(np.asarray(theta_cols, np.float64).sum())
    Yv = np.zeros((n, T), np.float32)
    for t, (s0, w) in slices.items():
        Yv[np.arange(n), y_codes[t] + s0] = 1.0
    XvT = np.ascontiguousarray(Xv.T)

    def votes(Xq, beta, self_idx=None):
        out = np.empty((Xq.shape[0], T), np.float32)
        Xq = Xq * th[None, :]
        for lo in range(0, Xq.shape[0], 1024):
            hi = min(lo + 1024, Xq.shape[0])
            W = np.exp(beta * (Xq[lo:hi] @ XvT - tot))
            if self_idx is not None:
                W[np.arange(hi - lo), self_idx[lo:hi]] = 0.0          # leave the row itself out
            out[lo:hi] = W @ Yv
        return out

    qs = [t for t in slices if t in prior_b and t in prior_h]
    rows = np.arange(len(blend_rows))
    off_r = {t: -np.log(_floored(prior_b[t], width[t])[rows, y_codes[t][blend_rows]]) for t in qs}
    off = {t: float(off_r[t].mean()) for t in qs}
    table = {}                                             # beta -> {t: (loss, alpha)}
    for beta in TOP_BETAS:
        if time.time() > deadline:
            break
        Sb = votes(Xv[blend_rows], beta, np.asarray(blend_rows))
        best = {}
        for t in qs:
            s0, w = slices[t]
            yb = y_codes[t][blend_rows]
            for alpha in TOP_ALPHAS:
                P = Sb[:, s0:s0 + w] + alpha * prior_b[t]
                P = P / P.sum(1, keepdims=True)
                loss = float(-np.log(_floored(P, w)[rows, yb]).mean())
                if t not in best or loss < best[t][0]:
                    best[t] = (loss, alpha)
        table[beta] = best
    if not table:
        return {}, "out of time"
    total = {b: sum(min(v[t][0], off[t]) for t in qs) for b, v in table.items()}
    beta = min(total, key=total.get)
    use = {t: table[beta][t][1] for t in qs if table[beta][t][0] < off[t] - TOP_MARGIN}
    if not use:
        return {}, "no question improved"
    # Honest check for the survey as a whole. Choosing among settings and questions on
    # the same rows flatters the result, so: split the held-back rows in two, make the
    # choices on one half, measure them on the other, and swap. Apply the layer only if
    # that honest gain, summed over questions per row, is clearly above zero.
    Sb = votes(Xv[blend_rows], beta, np.asarray(blend_rows))
    half = np.random.default_rng(7).random(len(rows)) < 0.5
    d_row = np.zeros(len(rows))
    for t in qs:
        s0, w = slices[t]
        yb = y_codes[t][blend_rows]
        L = np.stack([-np.log(_floored((lambda P: P / P.sum(1, keepdims=True))(
            Sb[:, s0:s0 + w] + alpha * prior_b[t]), w)[rows, yb]) for alpha in TOP_ALPHAS])
        for pick, score in ((half, ~half), (~half, half)):
            k = int(L[:, pick].mean(1).argmin())
            if L[k, pick].mean() < off_r[t][pick].mean() - TOP_MARGIN:
                d_row[score] += off_r[t][score] - L[k, score]
    honest = float(d_row.mean())
    se = float(d_row.std(ddof=1) / np.sqrt(len(d_row)))
    if not honest > TOP_Z * se:
        return {}, "not applied: honest gain %.4f per row summed over questions, below %.1f x its standard error %.4f" % (
            honest, TOP_Z, se)
    Sh = votes(Xh, beta)
    out = {}
    for t, alpha in use.items():
        s0, w = slices[t]
        pb, ph = Sb[:, s0:s0 + w] + alpha * prior_b[t], Sh[:, s0:s0 + w] + alpha * prior_h[t]
        out[t] = (pb / pb.sum(1, keepdims=True), ph / ph.sum(1, keepdims=True))
    gain = float(np.mean([off[t] - table[beta][t][0] if t in use else 0.0 for t in qs]))
    return out, ("sharpness %s; %d of %d questions adjusted; held-back loss down %.4f per question on average; "
                 "honest gain %.4f per row (standard error %.4f)") % (beta, len(use), len(qs), gain, honest, se)


def em_weights(P, prior, iters=400):
    """P: (rows, members) probability each member gave the true answer."""
    w = prior.copy()
    for _ in range(iters):
        r = w[None, :] * P
        r /= r.sum(1, keepdims=True)
        w = (r.sum(0) + PRIOR_ROWS * prior) / (len(P) + PRIOR_ROWS)
    return w


# ------------------------------------------------------------------ predict --

def predict(frame, schema):
    started = time.time()
    warnings.filterwarnings("ignore")
    records, sentinel = schema["items"], schema["gated_value"]
    items = [n for n, r in records.items() if r["class"] in ("GIVEN", "PREDICT")]
    given = [n for n in items if records[n]["class"] == "GIVEN"]
    targets = [n for n in items if records[n]["class"] == "PREDICT"]
    options = {n: list(records[n]["values"]) + ([sentinel] if records[n].get("gate") else [])
               for n in items}
    width = {t: len(options[t]) for t in targets}
    hidden = frame[targets].isna().any(axis=1).to_numpy()
    vis_idx, hid_idx = np.flatnonzero(~hidden), np.flatnonzero(hidden)
    n_hidden = len(hid_idx)
    # The final phase scores the TEST respondents and allows four times the run time.
    split = schema.get("split") or {}
    phase = 2 if (n_hidden == split.get("n_test") and n_hidden != split.get("n_dev")) else 1
    clock = float(os.environ.get("SB_CLOCK_SECONDS") or CLOCK_SECONDS[phase])
    left = clock - (started - _CLOCK["start"])
    n_t = float(len(targets))
    targets_left = max(TOTAL_TARGETS - _CLOCK["targets_done"], n_t)
    rest = targets_left - n_t                       # questions in the surveys still to come
    floor_s = min(MIN_SECONDS, 0.25 * left)
    if rest > 0:                                    # set one small survey's minimum aside
        budget = max((left - floor_s) * n_t / targets_left, floor_s)
        budget = min(budget, left - floor_s)
    else:                                           # last survey: everything that is left
        budget = left
    budget = max(min(budget, left - 5.0), 20.0)
    _CLOCK["targets_done"] += n_t
    dropped = []

    # ---- crowd marginal: every question starts and can end here --------------
    marg, y_codes, usable = {}, {}, []
    for t in targets:
        lookup = {v: i for i, v in enumerate(options[t])}
        y = frame[t].iloc[vis_idx].map(lookup)
        seen = y.dropna().to_numpy().astype(np.int64)
        w = np.bincount(seen, minlength=width[t]) + 0.5
        marg[t] = w / w.sum()
        if not y.isna().any():
            y_codes[t] = y.to_numpy().astype(np.int64); usable.append(t)
    final = {t: np.tile(marg[t], (n_hidden, 1)) for t in targets}

    try:
        # ---- shared inputs ----------------------------------------------------
        cols, off, col_owner, raw_codes, cards = [], 0, [], [], []
        for gi, g in enumerate(given):
            lookup = {v: i for i, v in enumerate(options[g])}
            c = frame[g].map(lookup).fillna(len(lookup)).to_numpy().astype(np.int64)
            raw_codes.append(c); cards.append(len(lookup) + 1)
            cols.append(c + off); off += len(lookup) + 1; col_owner += [gi] * (len(lookup) + 1)
        X = np.zeros((len(frame), off), dtype=np.float32)
        for c in cols:
            X[np.arange(len(frame)), c] = 1.0
        Xv_np, Xh_np = X[vis_idx], X[hid_idx]
        rng = np.random.default_rng(0)
        fold = rng.permutation(len(vis_idx)) % N_FOLDS
        blend_rows = np.flatnonzero(fold == 0)
        fit_rows = np.flatnonzero(fold != 0)
        slices, s = {}, 0
        for t in usable:
            slices[t] = (s, width[t]); s += width[t]

        members = {}                                   # name -> ({q: blend}, {q: hidden})
        knn_theta = None
        try:
            import torch
            torch.set_flush_denormal(True)
            dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            if dev.type == "cpu":
                torch.set_num_threads(8)
            Xv, Xh = torch.tensor(Xv_np, device=dev), torch.tensor(Xh_np, device=dev)
            Yv = torch.zeros(len(vis_idx), s, device=dev)
            for t in usable:
                Yv[torch.arange(len(vis_idx), device=dev),
                   torch.tensor(y_codes[t] + slices[t][0], device=dev)] = 1.0
            base_v = base_h = None
            try:
                out = mlp_member(torch, dev, Xv, Xh, slices, marg, y_codes, fold, blend_rows,
                                 started + 0.15 * budget)
                if not out:
                    dropped.append("network (out of time)")
                if out:
                    members["mlp"] = out[:2]
                    clean = lambda a: torch.tensor(np.clip(np.nan_to_num(a), 1e-6, None),
                                                   device=dev, dtype=torch.float32)
                    base_v, base_h = clean(out[2]), clean(out[3])
            except Exception as exc:
                dropped.append("network (%s)" % type(exc).__name__)
            # A second, larger and less regularised network: surveys where the GIVEN
            # columns determine a lot (through combinations) need the capacity.
            try:
                out = mlp_member(torch, dev, Xv, Xh, slices, marg, y_codes, fold, blend_rows,
                                 started + 0.30 * budget, hidden=(384, 384), dropout=0.15)
                if not out:
                    dropped.append("wide network (out of time)")
                if out:
                    members["mlp2"] = out[:2]
            except Exception as exc:
                dropped.append("wide network (%s)" % type(exc).__name__)
            try:
                with torch.no_grad():
                    out = knn_member(torch, dev, Xv, Xh, Yv, slices, marg, y_codes, blend_rows,
                                     np.array(col_owner), started + 0.37 * budget,
                                     started + 0.48 * budget, base_v, base_h)
                if not out:
                    dropped.append("similarity (out of time)")
                if out:
                    members["knn"] = out[:2]
                    knn_theta = out[2]
                    print("[v13] learned column weights %s" % dict(zip(range(len(given)), out[2])))
            except Exception as exc:
                dropped.append("similarity (%s)" % type(exc).__name__)
            del Xv, Xh, Yv
        except Exception as exc:
            dropped.append("torch members (%s)" % type(exc).__name__)

        entropy = {t: -float((marg[t] * np.log(marg[t])).sum()) for t in usable}
        by_entropy = sorted(usable, key=entropy.get, reverse=True)

        # ---- TabICL ----------------------------------------------------------------
        try:
            codes = np.column_stack(raw_codes)
            out = tabicl_member(codes[vis_idx], codes[hid_idx], cards, y_codes, by_entropy, width,
                                fit_rows, blend_rows, started + 0.70 * budget, passes=(0,))
            print("[v13] TabICL: %s" % out[2])
            if out[0]:
                members["tabicl"] = out[:2]
            if len(out[0]) < len(usable):
                dropped.append("TabICL on %d of %d questions" % (len(usable) - len(out[0]), len(usable)))
        except Exception as exc:
            dropped.append("TabICL (%s)" % type(exc).__name__)

        # ---- per-question logistic regression, most uncertain questions first --
        lr_blend, lr_hidden = {}, {}
        try:
            from scipy import sparse
            Xs_v, Xs_h = sparse.csr_matrix(Xv_np), sparse.csr_matrix(Xh_np)
            lr_deadline = started + 0.84 * budget
            for t in by_entropy:
                if time.time() > lr_deadline:
                    break
                try:
                    out = lr_member(Xs_v, Xs_h, y_codes[t], width[t], fit_rows, blend_rows, lr_deadline)
                    if out:
                        lr_blend[t], lr_hidden[t] = out
                except Exception:
                    pass
        except Exception:
            pass
        if lr_blend:
            members["lr"] = (lr_blend, lr_hidden)
        if len(lr_blend) < len(usable):
            dropped.append("logistic regression on %d of %d questions" % (len(usable) - len(lr_blend), len(usable)))

        # ---- TabICL, second pass: the full setting with whatever time is left -----
        if "tabicl" in members:
            try:
                out = tabicl_member(codes[vis_idx], codes[hid_idx], cards, y_codes, by_entropy, width,
                                    fit_rows, blend_rows, started + 0.94 * budget,
                                    passes=tuple(range(1, FULL_PASSES + 1)),
                                    blend=members["tabicl"][0], hidden=members["tabicl"][1])
                print("[v13] TabICL second pass: %s" % out[2])
            except Exception as exc:
                dropped.append("TabICL second pass (%s)" % type(exc).__name__)

        # ---- blend ----------------------------------------------------------------
        order = ["marginal"] + [m for m in ("knn", "mlp", "mlp2", "tabicl", "lr") if m in members]
        stats = {}
        clean_b = {m: {} for m in order if m != "marginal"}
        clean_h = {m: {} for m in order if m != "marginal"}
        for t in usable:
            yb = y_codes[t][blend_rows]
            have, cols_b, cols_h, full_b = [], [], [], []
            for m in order:
                if m == "marginal":
                    pb, ph = np.tile(marg[t], (len(yb), 1)), final[t]
                elif t in members[m][0]:
                    pb, ph = members[m][0][t], members[m][1][t]
                else:
                    continue
                pb = np.clip(np.nan_to_num(pb), 0, None); ph = np.clip(np.nan_to_num(ph), 0, None)
                pb = pb / np.maximum(pb.sum(1, keepdims=True), 1e-12)
                ph = ph / np.maximum(ph.sum(1, keepdims=True), 1e-12)
                have.append(m); cols_b.append(_floored(pb, width[t])[np.arange(len(yb)), yb]); cols_h.append(ph)
                full_b.append(pb)
                if m != "marginal":
                    clean_b[m][t], clean_h[m][t] = pb, ph
            stats[t] = (have, np.column_stack(cols_b), cols_h, full_b)
        # survey-wide weights first, then per-question weights shrunk toward them
        glob = {m: 1.0 for m in order}
        for _ in range(300):
            acc = {m: 0.0 for m in order}; rows = 0
            for t, (have, P, _, _) in stats.items():
                w = np.array([glob[m] for m in have]); w /= w.sum()
                r = w[None, :] * P; r /= r.sum(1, keepdims=True)
                for j, m in enumerate(have):
                    acc[m] += r[:, j].sum()
                rows += len(P)
            glob = {m: max(acc[m] / rows, 1e-4) for m in order}
        blend_final = {}                                   # blend-row version of the final prediction
        for t, (have, P, cols_h, full_b) in stats.items():
            prior = np.array([glob[m] for m in have]); prior /= prior.sum()
            w = em_weights(P, prior)
            p = sum(wj * ph for wj, ph in zip(w, cols_h))
            if p.shape == final[t].shape and np.isfinite(p).all() and (p >= 0).all() and (p.sum(1) > 0).all():
                final[t] = p / p.sum(1, keepdims=True)
                pb = sum(wj * fb for wj, fb in zip(w, full_b))
                blend_final[t] = pb / pb.sum(1, keepdims=True)

        # ---- geometric pool of the same members, averaged with the linear pool ----
        n_log = 0
        try:
            names = [m for m in order if m != "marginal" and m != "asked_crowd"]
            y_blend = {t: y_codes[t][blend_rows] for t in blend_final}
            shrink = float(np.clip(2000.0 / max(len(blend_rows), 1), 1.0, 4.0))
            pool = fit_log_pool(clean_b, y_blend, names, shrink=shrink)
            for t in blend_final:
                if t not in pool:
                    continue
                lh = apply_log_pool(clean_h, pool, t)
                lb = apply_log_pool(clean_b, pool, t)
                if lh.shape == final[t].shape and np.isfinite(lh).all() and np.isfinite(lb).all():
                    final[t] = 0.5 * lh + 0.5 * final[t]
                    blend_final[t] = 0.5 * lb + 0.5 * blend_final[t]
                    n_log += 1
        except Exception as exc:
            dropped.append("log pool (%s)" % type(exc).__name__)

        # ---- similarity as the last layer, with the blend as its prior -------------
        if knn_theta is not None and os.environ.get("SB_TOP", "1") != "0":
            try:
                t_top = time.time()
                top, msg = similarity_top(np.asarray(Xv_np, np.float32), np.asarray(Xh_np, np.float32),
                                          knn_theta, col_owner, y_codes, slices, blend_rows,
                                          blend_final, final, width, started + budget + 15.0)
                for t, (pb, ph) in top.items():
                    if ph.shape == final[t].shape and np.isfinite(ph).all() and np.isfinite(pb).all():
                        final[t], blend_final[t] = ph, pb
                print("[v13] similarity layer: %s (%.0fs, at %.0fs of %.0fs)" % (
                    msg, time.time() - t_top, time.time() - started, budget))
            except Exception as exc:
                dropped.append("similarity layer (%s)" % type(exc).__name__)

        # ---- how much floor correction the held-back rows support, by number of options ----
        floor_g = {}
        try:
            groups = {}
            for t in blend_final:
                key = 0 if width[t] <= 3 else 1 if width[t] <= 6 else 2 if width[t] <= 10 else 3
                groups.setdefault(key, []).append(t)
            for key, ts in groups.items():
                best = (None, 0.0)
                for g in (0.0, 0.5, 1.0, 1.5):
                    loss = float(np.mean([
                        -np.log(_floored(floor_correct(blend_final[t], g * FLOOR) if g else blend_final[t],
                                         width[t])[np.arange(len(blend_rows)), y_codes[t][blend_rows]]).mean()
                        for t in ts]))
                    if best[0] is None or loss < best[0] - 1e-6:
                        best = (loss, g)
                floor_g[key] = best[1]
        except Exception as exc:
            floor_g = {}
            dropped.append("floor correction (%s)" % type(exc).__name__)
        member_loss = {m: round(float(np.mean([-np.log(P[:, have.index(m)]).mean()
                                               for have, P, _, _ in stats.values() if m in have])), 4)
                       for m in order}
        print("[v13] blend-row loss per member %s" % member_loss)

        # ---- exact skip rules, only where the visible rows obey them without exception ----
        n_rules = 0
        for t in usable:
            g = records[t].get("gate")
            if not g or g.get("parent") not in given:
                continue
            allowed = set(g.get("observed_if") or [])
            rule_v = frame[g["parent"]].iloc[vis_idx].isin(allowed).to_numpy()
            sent = width[t] - 1
            if not np.array_equal(y_codes[t] == sent, ~rule_v):
                continue
            n_ask, n_not = int(rule_v.sum()), int((~rule_v).sum())
            if n_ask < 20 or n_not < 20:
                continue
            rule_h = frame[g["parent"]].iloc[hid_idx].isin(allowed).to_numpy()
            p = final[t].copy()
            rest = p[:, :sent] + 1e-9
            rest = rest / rest.sum(1, keepdims=True)
            e_ask, e_not = 1.0 / (n_ask + 2), 1.0 / (n_not + 2)      # rule of succession
            p[rule_h, :sent], p[rule_h, sent] = rest[rule_h] * (1 - e_ask), e_ask
            p[~rule_h, :sent], p[~rule_h, sent] = rest[~rule_h] * e_not, 1 - e_not
            final[t] = p
            n_rules += 1
        print("[v13] phase %d; members %s; weights %s; exact skip rules on %d questions; %.0fs of %.0fs"
              % (phase, order, {m: round(float(glob[m]), 3) for m in order}, n_rules,
                 time.time() - started, budget))
        print("[v13] log pool on %d questions; floor correction strength by option count (2-3, 4-6, 7-10, 11+): %s"
              % (n_log, [floor_g.get(k) for k in range(4)]))
        # the floor correction is the very last transformation
        for t in list(final):
            g = floor_g.get(0 if width[t] <= 3 else 1 if width[t] <= 6 else 2 if width[t] <= 10 else 3, 0.0)
            if g:
                try:
                    q = floor_correct(final[t], g * FLOOR)
                    if q.shape == final[t].shape and np.isfinite(q).all() and (q >= 0).all() and (q.sum(1) > 0).all():
                        final[t] = q
                except Exception:
                    pass
        print("[v13] dropped: %s" % (dropped or "nothing"))
    except Exception as exc:
        print("[v13] fell back to simpler output: %s" % type(exc).__name__)

    # ---- one vector per blank cell, canonical order ------------------------------
    grid = frame[items].to_numpy(dtype=object)
    position = np.cumsum(hidden) - 1
    out = []
    for row in np.flatnonzero(pd.isna(grid).any(axis=1)):
        for column, item in enumerate(items):
            if pd.isna(grid[row, column]):
                out.append(np.clip(final[item][position[row]], 0.0, None) if item in final
                           else np.full(len(options[item]), 1.0 / len(options[item])))
    return out
