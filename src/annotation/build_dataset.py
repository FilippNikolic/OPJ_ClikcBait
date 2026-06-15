#!/usr/bin/env python3
"""Faza 2 — spajanje anotiranih polovina + balansiranje + izvoz finalnog skupa.

Ulaz:
  data/annotated/filip_glavna.csv   (kanonske labele Filipove polovine)
  data/annotated/danilo_glavna.csv  (kanonske labele Danilove polovine)

Izlaz:
  data/annotated/dataset_full.csv   (sve labelirano, NEbalansirano, sa id/podtip)
  data/annotated/dataset.tsv        (BALANSIRANO, 'naslov \\t labela' — ulaz za Fazu 3)

Napomena: za 220 kalibracionih naslova kanonska je labela iz *_glavna.csv
(vlasnika). Ako posle IAA usaglasite neku spornu labelu, ispravi je u glavnoj
datoteci pa ponovo pokreni ovu skriptu.

Balansiranje: uzima do --po-klasi (podrazumevano 1100) naslova svake klase
(deterministički, seed 42). Ako klasa ima manje — uzme sve i upozori
(ručno doskupljanje je naša odluka, skripta ne staje).

Pokretanje:
  .venv/bin/python src/annotation/build_dataset.py
  .venv/bin/python src/annotation/build_dataset.py --po-klasi 1100
"""
import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANN = ROOT / "data" / "annotated"
GLAVNA = [ANN / "filip_glavna.csv", ANN / "danilo_glavna.csv"]
SEED = 42


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--po-klasi", type=int, default=1100,
                    help="ciljani broj naslova po klasi u balansiranom skupu")
    args = ap.parse_args()

    rows = []
    for p in GLAVNA:
        rows += read_rows(p)

    labeled = [r for r in rows if (r.get("labela") or "").strip() in ("0", "1")]
    unlabeled = len(rows) - len(labeled)
    kb = [r for r in labeled if r["labela"].strip() == "1"]
    ne = [r for r in labeled if r["labela"].strip() == "0"]

    print(f"Učitano:        {len(rows)} naslova")
    print(f"Labelirano:     {len(labeled)}  (neoznačeno: {unlabeled})")
    print(f"  klikbejt (1): {len(kb)}")
    print(f"  nije     (0): {len(ne)}")

    if unlabeled:
        print(f"\n⚠️  {unlabeled} naslova još nema labelu — dovrši anotaciju pre finalnog skupa.")

    # --- dataset_full.csv (sve labelirano, nebalansirano) ---
    full_path = ANN / "dataset_full.csv"
    with open(full_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "naslov", "labela", "podtip"],
                           quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in labeled:
            w.writerow({k: r.get(k, "") for k in ("id", "naslov", "labela", "podtip")})
    print(f"\nUpisano: {full_path.relative_to(ROOT)}  ({len(labeled)} redova)")

    # --- balansiranje ---
    n = args.po_klasi
    rnd = random.Random(SEED)
    sel_kb, sel_ne = kb[:], ne[:]
    rnd.shuffle(sel_kb)
    rnd.shuffle(sel_ne)
    for naziv, sel in (("klikbejt", sel_kb), ("nije", sel_ne)):
        if len(sel) < n:
            print(f"⚠️  klasa '{naziv}' ima {len(sel)} < {n} — uzimam sve "
                  f"(fali {n-len(sel)}, doskupiti ručno po potrebi).")
    bal = sel_kb[:n] + sel_ne[:n]
    rnd.shuffle(bal)

    tsv_path = ANN / "dataset.tsv"
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        f.write("naslov\tlabela\n")
        for r in bal:
            naslov = r["naslov"].replace("\t", " ").strip()
            f.write(f"{naslov}\t{r['labela'].strip()}\n")
    print(f"Upisano: {tsv_path.relative_to(ROOT)}  "
          f"({min(len(sel_kb),n)} klikbejt + {min(len(sel_ne),n)} nije = {len(bal)})")
    print("\nFinalni balansiran skup spreman za Fazu 3.")


if __name__ == "__main__":
    main()
