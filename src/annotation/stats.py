#!/usr/bin/env python3
"""Faza 2 — deskriptivna statistika anotiranog skupa (za dokumentaciju).

Ulaz:  data/annotated/dataset_full.csv (svi labelirani; napravi build_dataset.py)
       data/interim/headlines.csv      (za rubriku po id-u)

Izlaz: ispis na ekran + results/faza2_statistika.txt
  - raspodela klasa (broj + %)
  - dužina naslova po klasi (reči + karakteri, prosek)
  - učestalost pod-tipova (KJ/PV/EN/SF) među klikbejtom
  - top rubrike po klasi

Pokretanje:
  .venv/bin/python src/annotation/stats.py
"""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / "data" / "annotated" / "dataset_full.csv"
HEAD = ROOT / "data" / "interim" / "headlines.csv"
OUT = ROOT / "results" / "faza2_statistika.txt"


def read_rows(path, enc="utf-8-sig"):
    with open(path, encoding=enc, newline="") as f:
        return list(csv.DictReader(f))


def main():
    if not FULL.exists():
        print(f"Nema {FULL.relative_to(ROOT)} — prvo pokreni build_dataset.py")
        return
    rows = read_rows(FULL)
    rubrika = {r["id"]: r.get("rubrika", "") for r in read_rows(HEAD, "utf-8")}

    lines = []
    def out(s=""):
        print(s)
        lines.append(s)

    kb = [r for r in rows if r["labela"].strip() == "1"]
    ne = [r for r in rows if r["labela"].strip() == "0"]
    n = len(rows)
    out("=== FAZA 2 — DESKRIPTIVNA STATISTIKA ===\n")
    out(f"Ukupno labelirano: {n}")
    if n:
        out(f"  klikbejt (1): {len(kb)}  ({100*len(kb)/n:.1f}%)")
        out(f"  nije     (0): {len(ne)}  ({100*len(ne)/n:.1f}%)")

    def duzine(group, naziv):
        if not group:
            return
        w = [len(r["naslov"].split()) for r in group]
        c = [len(r["naslov"]) for r in group]
        out(f"\nDužina naslova — {naziv}:")
        out(f"  reči:      min {min(w)}  max {max(w)}  prosek {sum(w)/len(w):.1f}")
        out(f"  karakteri: min {min(c)}  max {max(c)}  prosek {sum(c)/len(c):.1f}")

    out("\n--- Dužina naslova po klasi ---")
    duzine(kb, "klikbejt")
    duzine(ne, "nije")

    out("\n--- Pod-tipovi među klikbejtom (KJ/PV/EN/SF) ---")
    pod = Counter()
    for r in kb:
        for t in (r.get("podtip") or "").replace(" ", "").split(","):
            if t:
                pod[t.upper()] += 1
    if pod:
        for k, v in pod.most_common():
            out(f"  {k}: {v}")
    else:
        out("  (pod-tipovi nisu unošeni — opciono)")

    out("\n--- Top rubrike po klasi ---")
    for group, naziv in ((kb, "klikbejt"), (ne, "nije")):
        if not group:
            continue
        c = Counter(rubrika.get(r["id"], "?") for r in group)
        out(f"  {naziv}:")
        for k, v in c.most_common(10):
            out(f"    {v:5}  {k}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSačuvano: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
