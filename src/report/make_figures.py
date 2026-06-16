#!/usr/bin/env python3
"""Faza 4 — generisanje PNG grafikona za izveštaj u report/figures/.

Grafici:
  raspodela_klasa.png    — broj naslova po klasi (klikbejt/regularan)
  duzina_naslova.png     — histogram dužine naslova (reči) po klasi
  poredjenje_modela.png  — F1 (klikbejt) najboljih varijanti po tipu modela

Ulazi (otporno na nedostajuće):
  data/annotated/dataset_full.csv  ili dataset.tsv  ili dataset.sample.tsv
  results/*.csv (za poređenje modela)

Pokretanje:
  .venv/bin/pip install -r requirements-report.txt
  .venv/bin/python src/report/make_figures.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

FIG = ROOT / "report" / "figures"
RESULTS = ROOT / "results"

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from baseline import common  # noqa: E402


def _save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    path = FIG / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"🖼️  {path.relative_to(ROOT)}")


def fig_raspodela_i_duzina():
    texts, labels = common.load_dataset()
    n_kb = sum(labels)
    n_ne = len(labels) - n_kb

    fig, ax = plt.subplots(figsize=(4, 3.2))
    ax.bar(["regularan (0)", "klikbejt (1)"], [n_ne, n_kb],
           color=["#4C72B0", "#C44E52"])
    ax.set_ylabel("broj naslova")
    ax.set_title("Raspodela klasa")
    for i, v in enumerate([n_ne, n_kb]):
        ax.text(i, v, str(v), ha="center", va="bottom")
    _save(fig, "raspodela_klasa.png")

    len_ne = [len(t.split()) for t, y in zip(texts, labels) if y == 0]
    len_kb = [len(t.split()) for t, y in zip(texts, labels) if y == 1]
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    bins = range(0, max(max(len_ne or [1]), max(len_kb or [1])) + 2)
    ax.hist([len_ne, len_kb], bins=bins, label=["regularan", "klikbejt"],
            color=["#4C72B0", "#C44E52"])
    ax.set_xlabel("dužina naslova (reči)")
    ax.set_ylabel("broj naslova")
    ax.set_title("Dužina naslova po klasi")
    ax.legend()
    _save(fig, "duzina_naslova.png")


def _read_csv(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _best_f1(rows):
    def num(r):
        try:
            return float(str(r.get("f1_kb", "0")).split("±")[0])
        except ValueError:
            return -1.0
    return max((num(r) for r in rows), default=0.0)


def fig_poredjenje():
    names, vals = [], []
    b = _read_csv(RESULTS / "baseline_results.csv")
    if b:
        names.append("Baseline")
        vals.append(_best_f1(b))
    for key, lbl in (("bertic", "BERTić"), ("mbert", "mBERT")):
        r = _read_csv(RESULTS / f"encoder_{key}_results.csv")
        if r:
            names.append(lbl)
            vals.append(_best_f1(r))
    d = _read_csv(RESULTS / "decoder_results.csv")
    if d:
        names.append("ChatGPT")
        vals.append(_best_f1(d))

    if not names:
        print("ℹ️  Nema results/*.csv — preskačem poredjenje_modela.png "
              "(generiše se posle Faze 3).")
        return
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.bar(names, vals, color="#55A868")
    ax.set_ylabel("F1 (klikbejt klasa)")
    ax.set_ylim(0, 1)
    ax.set_title("Poređenje modela (najbolja varijanta)")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.3f}", ha="center", va="bottom")
    _save(fig, "poredjenje_modela.png")


def main():
    fig_raspodela_i_duzina()
    fig_poredjenje()
    print("\n✅ Grafici u report/figures/. Prekompajliraj izvestaj.tex.")


if __name__ == "__main__":
    main()
