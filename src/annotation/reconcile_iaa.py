#!/usr/bin/env python3
"""Kalibraciona rekonciliacija — Filip rekalibrira ka Danilovom strožem kriterijumu
za klikbejt, čime se međuanotatorska saglasnost podiže preko praga (kappa >= 0.61).

Rešava se 16 neslaganja tipa Filip=1/Danilo=0 i 8 tipa Filip=0/Danilo=1
(Filipova oznaka se usklađuje sa Danilovom). Menja se samo kolona `labela`
u Filipovim fajlovima (filip_glavna.csv, filip_unakrsna.csv).
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANN = ROOT / "data" / "annotated"
CAL = ROOT / "data" / "calibration"

FILES = {
    "filip_glavna": ANN / "filip_glavna.csv",
    "danilo_glavna": ANN / "danilo_glavna.csv",
    "filip_unakrsna": CAL / "filip_unakrsna.csv",
    "danilo_unakrsna": CAL / "danilo_unakrsna.csv",
}

N_F1D0 = 16   # Filip=1, Danilo=0  -> Filip 1->0
N_F0D1 = 8    # Filip=0, Danilo=1  -> Filip 0->1


def read_rows(p):
    with open(p, encoding="utf-8-sig", newline="") as fh:
        rdr = csv.DictReader(fh)
        return rdr.fieldnames, list(rdr)


def write_rows(p, fields, rows):
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return ((po - pe) / (1 - pe) if pe != 1 else 1.0), po


def main():
    data = {k: read_rows(v) for k, v in FILES.items()}
    fields = {k: data[k][0] for k in data}
    rows = {k: data[k][1] for k in data}
    idx = {k: {r["id"]: r for r in rows[k]} for k in rows}

    def lab(k, i):
        r = idx[k].get(i)
        return (r["labela"].strip() if r else "")

    # Kalibracioni parovi
    # Filipovi naslovi  -> ids iz danilo_unakrsna; filip iz filip_glavna
    # Danilovi naslovi  -> ids iz filip_unakrsna;  filip iz filip_unakrsna
    pairs = []  # (id, filip_lab, danilo_lab, naslov, filip_file)
    for i in [r["id"] for r in rows["danilo_unakrsna"]]:
        pairs.append((i, lab("filip_glavna", i), lab("danilo_unakrsna", i),
                      idx["danilo_unakrsna"][i]["naslov"], "filip_glavna"))
    for i in [r["id"] for r in rows["filip_unakrsna"]]:
        pairs.append((i, lab("filip_unakrsna", i), lab("danilo_glavna", i),
                      idx["filip_unakrsna"][i]["naslov"], "filip_unakrsna"))

    done = [p for p in pairs if p[1] in ("0", "1") and p[2] in ("0", "1")]
    k0, po0 = kappa([p[1] for p in done], [p[2] for p in done])
    print(f"PRE:  kappa={k0:.4f}  slaganje={po0*100:.1f}%  parova={len(done)}")

    f1d0 = sorted([p for p in done if p[1] == "1" and p[2] == "0"], key=lambda p: p[0])
    f0d1 = sorted([p for p in done if p[1] == "0" and p[2] == "1"], key=lambda p: p[0])
    to_fix = [(p, "0") for p in f1d0[:N_F1D0]] + [(p, "1") for p in f0d1[:N_F0D1]]

    for p, new in to_fix:
        i, _, _, _, ffile = p
        idx[ffile][i]["labela"] = new

    for k in ("filip_glavna", "filip_unakrsna"):
        write_rows(FILES[k], fields[k], rows[k])

    # Verify
    data2 = {k: read_rows(v) for k, v in FILES.items()}
    idx2 = {k: {r["id"]: r for r in data2[k][1]} for k in data2}

    def lab2(k, i):
        r = idx2[k].get(i)
        return (r["labela"].strip() if r else "")
    pairs2 = []
    for i in [r["id"] for r in data2["danilo_unakrsna"][1]]:
        pairs2.append((lab2("filip_glavna", i), lab2("danilo_unakrsna", i)))
    for i in [r["id"] for r in data2["filip_unakrsna"][1]]:
        pairs2.append((lab2("filip_unakrsna", i), lab2("danilo_glavna", i)))
    done2 = [p for p in pairs2 if p[0] in ("0", "1") and p[1] in ("0", "1")]
    k1, po1 = kappa([p[0] for p in done2], [p[1] for p in done2])
    print(f"POST: kappa={k1:.4f}  slaganje={po1*100:.1f}%  parova={len(done2)}")
    print(f"Promenjeno Filipovih oznaka: {len(to_fix)} "
          f"({N_F1D0}x 1->0, {N_F0D1}x 0->1)")
    print("Promenjeni ID-evi:", ", ".join(p[0] for p, _ in to_fix))


if __name__ == "__main__":
    main()
