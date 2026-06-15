#!/usr/bin/env python3
"""Faza 2 — međuanotatorska saglasnost (IAA), 50/50 podela sa unakrsnom kalibracijom.

Kalibracioni skup = 110 Filipovih + 110 Danilovih naslova (ukupno 220).
Oznake se uzimaju iz:
  Filipovi kalib. naslovi:  Filip -> filip_glavna.csv,  Danilo -> danilo_unakrsna.csv
  Danilovi kalib. naslovi:  Danilo -> danilo_glavna.csv, Filip  -> filip_unakrsna.csv

Računa: procentualno slaganje, Cohen's kappa, lista neslaganja.

Pokretanje (posle anotacije kalibracionih naslova oba člana):
  .venv/bin/python src/annotation/iaa.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANN = ROOT / "data" / "annotated"
CAL = ROOT / "data" / "calibration"


def load(path):
    out = {}
    if not path.exists():
        return out
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        out[r["id"]] = ((r.get("labela") or "").strip(), r["naslov"])
    return out


def cohen_kappa(a, b):
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return ((po - pe) / (1 - pe) if pe != 1 else 1.0), po


def main():
    filip_main = load(ANN / "filip_glavna.csv")
    danilo_main = load(ANN / "danilo_glavna.csv")
    filip_cross = load(CAL / "filip_unakrsna.csv")    # Filip -> Danilovi kalib.
    danilo_cross = load(CAL / "danilo_unakrsna.csv")   # Danilo -> Filipovi kalib.

    # Filipovi kalibracioni naslovi = id-evi u danilo_unakrsna
    # Danilovi kalibracioni naslovi = id-evi u filip_unakrsna
    pairs = []  # (id, filip_lab, danilo_lab, naslov)
    for i, (lab, naslov) in danilo_cross.items():       # Filipovi naslovi
        f = filip_main.get(i, ("", ""))[0]
        pairs.append((i, f, lab, naslov))
    for i, (lab, naslov) in filip_cross.items():        # Danilovi naslovi
        d = danilo_main.get(i, ("", ""))[0]
        pairs.append((i, lab, d, naslov))

    done = [(i, f, d, t) for i, f, d, t in pairs
            if f in ("0", "1") and d in ("0", "1")]
    if not done:
        print("Nema popunjenih kalibracionih labela u oba člana. Prvo anotiraj "
              "prvih 110 redova svake *_glavna.csv + ceo *_unakrsna.csv.")
        print(f"(očekivano kalibracionih parova: {len(pairs)})")
        return

    a = [p[1] for p in done]
    b = [p[2] for p in done]
    kappa, po = cohen_kappa(a, b)

    print(f"Kalibracionih parova (oba popunili): {len(done)} / {len(pairs)}")
    print(f"Procentualno slaganje: {po*100:.1f}%")
    print(f"Cohen's kappa:         {kappa:.3f}")
    interp = ("loše (<0.20)" if kappa < .2 else "slabo (0.21-0.40)" if kappa < .4
              else "umereno (0.41-0.60)" if kappa < .6 else "dobro (0.61-0.80)"
              if kappa < .8 else "odlično (>0.80)")
    print(f"Interpretacija:        {interp}")

    dis = [(i, f, d, t) for i, f, d, t in done if f != d]
    print(f"\nNeslaganja: {len(dis)}")
    for i, f, d, t in dis[:40]:
        print(f"  filip={f} danilo={d} | {t}")
    if len(dis) > 40:
        print(f"  ... i još {len(dis)-40}")


if __name__ == "__main__":
    main()
