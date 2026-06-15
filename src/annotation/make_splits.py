#!/usr/bin/env python3
"""Faza 2 — priprema datoteka za ručnu anotaciju (50/50 podela).

Dataset (2994) deli se TAČNO na pola:
  - Filip:  1497 naslova  (data/annotated/filip_glavna.csv)
  - Danilo: 1497 naslova  (data/annotated/danilo_glavna.csv)

Kalibracija za Cohen's kappa = 220 naslova (110 iz Filipove + 110 iz Danilove
polovine). Te naslove anotiraju OBA člana (unakrsno), pa se mogu uporediti:
  - Prvih 110 redova u svakom *_glavna.csv su kalibracioni (anotiraj ih PRVO).
  - data/calibration/filip_unakrsna.csv  = 110 Danilovih kalib. naslova (anotira Filip)
  - data/calibration/danilo_unakrsna.csv = 110 Filipovih kalib. naslova (anotira Danilo)

Tako svaki član poseduje pola skupa (1497), a 220 naslova ima po dve nezavisne
anotacije → Cohen's kappa.

Determinističko (seed 42). Pokretanje:
  .venv/bin/python src/annotation/make_splits.py
  .venv/bin/python src/annotation/make_splits.py --kalibracija 110
"""
import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "interim" / "headlines.csv"
CAL_DIR = ROOT / "data" / "calibration"
ANN_DIR = ROOT / "data" / "annotated"
SEED = 42
COLS = ["id", "naslov", "labela", "podtip", "napomena"]


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig (BOM) -> ispravno otvaranje u Excel/Numbers/Google Sheets
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(COLS)
        for r in rows:
            w.writerow([r["id"], r["naslov"], "", "", ""])
    print(f"  {path.relative_to(ROOT)}  ->  {len(rows)} naslova")


def has_labels(path):
    if not path.exists():
        return False
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        if (r.get("labela") or "").strip():
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kalibracija", type=int, default=110,
                    help="kalib. naslova po članu (ukupno 2x ovoliko se poredi za kappa)")
    ap.add_argument("--force", action="store_true",
                    help="prepiši datoteke i ako već sadrže anotacije (BRIŠE napredak!)")
    args = ap.parse_args()

    # ZAŠTITA: ne brisati postojeći anotatorski rad
    targets = [ANN_DIR / "filip_glavna.csv", ANN_DIR / "danilo_glavna.csv",
               CAL_DIR / "filip_unakrsna.csv", CAL_DIR / "danilo_unakrsna.csv"]
    if not args.force and any(has_labels(p) for p in targets):
        print("⛔ Postoje već unete anotacije — NEĆU prepisati (zaštita napretka).")
        print("   Anotator (annotator/app.py) sam nastavlja od prvog neoznačenog.")
        print("   Ako baš želiš ponovo da generišeš PRAZNE datoteke: --force")
        return

    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    print(f"Učitano {len(rows)} naslova iz {SRC.relative_to(ROOT)}")

    rnd = random.Random(SEED)
    rnd.shuffle(rows)

    half = len(rows) // 2
    A = rows[:half]          # Filipova polovina
    B = rows[half:]          # Danilova polovina
    k = args.kalibracija
    cal_A, cal_B = A[:k], B[:k]   # kalibracioni naslovi svake polovine

    print("\nGlavne polovine (kalibracioni naslovi su PRVIH {} redova):".format(k))
    # kalibracioni prvi -> lako ih je anotirati prvo
    write_csv(ANN_DIR / "filip_glavna.csv", cal_A + A[k:])
    write_csv(ANN_DIR / "danilo_glavna.csv", cal_B + B[k:])

    print("\nUnakrsna kalibracija (anotira drugi član, za Cohen's kappa):")
    write_csv(CAL_DIR / "filip_unakrsna.csv", cal_B)   # Filip anotira Danilove
    write_csv(CAL_DIR / "danilo_unakrsna.csv", cal_A)  # Danilo anotira Filipove

    print(f"\nPodela: Filip {len(A)} + Danilo {len(B)} = {len(rows)} (po pola).")
    print(f"Kalibracija (kappa) na {2*k} naslova ({k} iz svake polovine).")
    print("Svaki član anotira: 1497 svojih + {} unakrsnih = {} ukupno.".format(k, len(A)+k))


if __name__ == "__main__":
    main()
