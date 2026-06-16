#!/usr/bin/env python3
"""Faza 3a — Baseline modeli: Logistička regresija + Naivni Bajes.

Protokol (zahtev postavke):
  • 10-slojna stratifikovana unakrsna validacija (spoljna petlja)
  • UGNEŽĐENA (nested) CV za hiperparametre (unutrašnja petlja, GridSearchCV)
        - LR  : C (jačina regularizacije)
        - MNB : alpha (Laplace smoothing)
  • EFEKAT pretprocesiranja: poredimo varijante normalize × scheme × ngram

Reprezentacije odlika (TF/IDF/TF-IDF — naglašeno od profesora):
  • bow   : CountVectorizer (frekvencije reči)
  • tf     : normalizovana term-frekvencija (TfidfVectorizer, use_idf=False, l2)
  • idf    : prisustvo × IDF (TfidfVectorizer, binary=True, use_idf=True)
  • tfidf  : pun TF-IDF (TfidfVectorizer)

Metrike: accuracy, precision/recall/F1 za klikbejt klasu, macro-F1, ROC-AUC.

Pokretanje:
  pip install -r requirements-baseline.txt
  python src/baseline/run_baseline.py                # podrazumevani grid
  python src/baseline/run_baseline.py --normalize none stem lemma
  python src/baseline/run_baseline.py --full         # ceo grid (sporije)
  python src/baseline/run_baseline.py --quick        # brz smoke-test
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from baseline import common  # noqa: E402
from preprocessing import serbian  # noqa: E402


# --- definicije eksperimenata ------------------------------------------------
def make_vectorizer(scheme: str, ngram: tuple[int, int]):
    """Vrati neobučen sklearn vektorizator za datu šemu ponderisanja.
    lowercase=False jer normalizaciju (uklj. lowercase) radi preprocesor."""
    from sklearn.feature_extraction.text import (CountVectorizer,
                                                  TfidfVectorizer)
    common_kw = dict(lowercase=False, token_pattern=r"(?u)\S+",
                     ngram_range=ngram, min_df=2)
    if scheme == "bow":
        return CountVectorizer(**common_kw)
    if scheme == "tf":
        return TfidfVectorizer(use_idf=False, norm="l2", **common_kw)
    if scheme == "idf":
        return TfidfVectorizer(binary=True, use_idf=True, norm=None, **common_kw)
    if scheme == "tfidf":
        return TfidfVectorizer(use_idf=True, norm="l2", sublinear_tf=True,
                               **common_kw)
    raise ValueError(f"nepoznata scheme: {scheme}")


def make_model_and_grid(name: str):
    """Vrati (estimator, param_grid) za GridSearchCV (nad 'clf__' korakom)."""
    if name == "logreg":
        from sklearn.linear_model import LogisticRegression
        est = LogisticRegression(max_iter=2000, solver="liblinear")
        grid = {"clf__C": [0.01, 0.1, 1.0, 10.0, 100.0]}
        return est, grid
    if name == "mnb":
        from sklearn.naive_bayes import MultinomialNB
        est = MultinomialNB()
        grid = {"clf__alpha": [0.01, 0.1, 0.5, 1.0, 2.0]}
        return est, grid
    if name == "bnb":
        from sklearn.naive_bayes import BernoulliNB
        est = BernoulliNB()
        grid = {"clf__alpha": [0.01, 0.1, 0.5, 1.0, 2.0]}
        return est, grid
    raise ValueError(f"nepoznat model: {name}")


def nested_cv(X_text, y, scheme, ngram, model_name, n_folds, inner_folds, seed,
              n_jobs):
    """Spoljna stratifikovana CV + unutrašnji GridSearchCV. Vrati listu
    per-fold metrika + listu izabranih hiperparametara."""
    import numpy as np
    from sklearn.model_selection import GridSearchCV, StratifiedKFold
    from sklearn.pipeline import Pipeline

    y = np.asarray(y)
    X_text = np.asarray(X_text, dtype=object)
    outer = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    inner = StratifiedKFold(n_splits=inner_folds, shuffle=True,
                            random_state=seed)
    est, grid = make_model_and_grid(model_name)

    fold_metrics, best_params = [], []
    for tr, te in outer.split(X_text, y):
        pipe = Pipeline([
            ("vec", make_vectorizer(scheme, ngram)),
            ("clf", est),
        ])
        gs = GridSearchCV(pipe, grid, scoring="f1", cv=inner, n_jobs=n_jobs,
                          refit=True)
        gs.fit(X_text[tr], y[tr])
        best = gs.best_estimator_
        y_pred = best.predict(X_text[te])
        try:
            y_score = best.predict_proba(X_text[te])[:, 1]
        except (AttributeError, NotImplementedError):
            y_score = None
        fold_metrics.append(common.compute_metrics(y[te], y_pred, y_score))
        best_params.append(gs.best_params_)
    return fold_metrics, best_params


def aggregate(fold_metrics):
    """Vrati dict 'metric' -> 'mean±std' string + sirovi mean za sortiranje."""
    keys = fold_metrics[0].keys()
    agg = {}
    for k in keys:
        vals = [m[k] for m in fold_metrics]
        agg[k] = common.fmt_mean_std(vals)
        agg[f"_{k}_mean"] = sum(vals) / len(vals)
    return agg


def main():
    ap = argparse.ArgumentParser(description="Faza 3a baseline (LR + NB).")
    ap.add_argument("--dataset", default=None, help="putanja do *.tsv")
    ap.add_argument("--normalize", nargs="+", default=["none", "stem"],
                    choices=["none", "stem", "lemma"])
    ap.add_argument("--scheme", nargs="+", default=["bow", "tf", "tfidf"],
                    choices=["bow", "tf", "idf", "tfidf"])
    ap.add_argument("--ngram", nargs="+", default=["1-1", "1-2"],
                    help="npr. 1-1 1-2")
    ap.add_argument("--models", nargs="+", default=["logreg", "mnb"],
                    choices=["logreg", "mnb", "bnb"])
    ap.add_argument("--no-lowercase", action="store_true")
    ap.add_argument("--keep-punct", action="store_true")
    ap.add_argument("--folds", type=int, default=common.N_FOLDS)
    ap.add_argument("--inner-folds", type=int, default=5)
    ap.add_argument("--n-jobs", type=int, default=-1)
    ap.add_argument("--out", default=str(common.RESULTS / "baseline_results.csv"))
    ap.add_argument("--full", action="store_true",
                    help="ceo grid: sve scheme, oba ngram, sva tri modela")
    ap.add_argument("--quick", action="store_true",
                    help="brz smoke-test: 3 fold-a, mali grid")
    args = ap.parse_args()

    if args.full:
        args.scheme = ["bow", "tf", "idf", "tfidf"]
        args.ngram = ["1-1", "1-2"]
        args.models = ["logreg", "mnb", "bnb"]
    if args.quick:
        args.folds, args.inner_folds = 3, 3
        args.normalize, args.scheme, args.ngram = ["none"], ["tfidf"], ["1-1"]
        args.models = ["logreg", "mnb"]

    ngrams = [tuple(int(x) for x in g.split("-")) for g in args.ngram]

    texts, y = common.load_dataset(args.dataset)
    print(f"Učitano: {len(texts)} naslova  "
          f"(klikbejt={sum(y)}, nije={len(y)-sum(y)})")

    # pretprocesiranje radimo JEDNOM po normalize varijanti (nema curenja)
    rows = []
    t0 = time.time()
    for nm in args.normalize:
        print(f"\n=== Pretprocesiranje: normalize={nm} ===")
        Xn = serbian.preprocess_corpus(
            texts, normalize=nm, lowercase=not args.no_lowercase,
            strip_punct=not args.keep_punct)
        for scheme in args.scheme:
            for ngram in ngrams:
                for model in args.models:
                    tag = f"{model}|{nm}|{scheme}|{ngram[0]}-{ngram[1]}"
                    sys.stdout.write(f"  • {tag} ... ")
                    sys.stdout.flush()
                    tic = time.time()
                    fm, bp = nested_cv(
                        Xn, y, scheme, ngram, model, args.folds,
                        args.inner_folds, common.SEED, args.n_jobs)
                    agg = aggregate(fm)
                    row = {
                        "model": model, "normalize": nm, "scheme": scheme,
                        "ngram": f"{ngram[0]}-{ngram[1]}",
                        "lowercase": not args.no_lowercase,
                        "strip_punct": not args.keep_punct,
                        "accuracy": agg["accuracy"],
                        "precision_kb": agg["precision_kb"],
                        "recall_kb": agg["recall_kb"],
                        "f1_kb": agg["f1_kb"],
                        "f1_macro": agg["f1_macro"],
                        "roc_auc": agg.get("roc_auc", "—"),
                        "_f1_kb_mean": agg["_f1_kb_mean"],
                    }
                    rows.append(row)
                    print(f"F1_kb={row['f1_kb']}  ({time.time()-tic:.1f}s)")

    rows.sort(key=lambda r: r["_f1_kb_mean"], reverse=True)
    for r in rows:
        r.pop("_f1_kb_mean", None)
    common.write_results_csv(rows, args.out)

    print(f"\n✅ Gotovo za {time.time()-t0:.1f}s. Najbolje (po F1_kb):")
    for r in rows[:5]:
        print(f"   {r['model']:6} {r['normalize']:5} {r['scheme']:5} "
              f"{r['ngram']:3}  F1_kb={r['f1_kb']}  AUC={r['roc_auc']}")


if __name__ == "__main__":
    main()
