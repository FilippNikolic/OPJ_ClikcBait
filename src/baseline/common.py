#!/usr/bin/env python3
"""Faza 3 — zajednički alat za sve modele (učitavanje skupa, metrike, izlaz).

Koriste ga baseline, transformeri i dekoderski eval da bi metrike i format
rezultata bili IDENTIČNI (uslov: pregledne uporedne tabele).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASET_TSV = ROOT / "data" / "annotated" / "dataset.tsv"
SAMPLE_TSV = ROOT / "data" / "annotated" / "dataset.sample.tsv"
RESULTS = ROOT / "results"

SEED = 42
N_FOLDS = 10            # 10-slojna stratifikovana CV (zahtev postavke)
POS_LABEL = 1           # klikbejt je pozitivna klasa (fokus metrika)


def load_dataset(path: Path | str | None = None):
    """Učita 'naslov\\tlabela' TSV. Vrati (texts, labels). Padne nazad na
    sample skup ako pravi dataset.tsv još ne postoji (anotacija u toku)."""
    if path is None:
        path = DATASET_TSV if DATASET_TSV.exists() else SAMPLE_TSV
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Nema skupa: {path}. Završi Fazu 2 (build_dataset.py) ili koristi "
            f"--dataset {SAMPLE_TSV.name} za smoke-test."
        )
    texts, labels = [], []
    with open(path, encoding="utf-8") as f:
        header = f.readline()  # 'naslov\tlabela'
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            naslov, _, lab = line.rpartition("\t")
            texts.append(naslov)
            labels.append(int(lab))
    if path.name == SAMPLE_TSV.name:
        print(f"⚠️  Koristim SMOKE-TEST sample ({len(texts)} naslova) — "
              f"pravi dataset.tsv još ne postoji.")
    return texts, labels


def compute_metrics(y_true, y_pred, y_score=None):
    """Vrati dict metrika; fokus na klikbejt (POS_LABEL=1)."""
    from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                                 recall_score, roc_auc_score)
    m = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_kb": precision_score(y_true, y_pred, pos_label=POS_LABEL,
                                        zero_division=0),
        "recall_kb": recall_score(y_true, y_pred, pos_label=POS_LABEL,
                                  zero_division=0),
        "f1_kb": f1_score(y_true, y_pred, pos_label=POS_LABEL, zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }
    if y_score is not None:
        try:
            m["roc_auc"] = roc_auc_score(y_true, y_score)
        except ValueError:
            m["roc_auc"] = float("nan")
    return m


def write_results_csv(rows, path):
    """rows: lista dict-ova. Upisuje uniju ključeva kao kolone."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"📄 Rezultati: {path}")


def append_jsonl(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def fmt_mean_std(values):
    import statistics
    if not values:
        return "—"
    if len(values) == 1:
        return f"{values[0]:.3f}"
    return f"{statistics.mean(values):.3f}±{statistics.pstdev(values):.3f}"
