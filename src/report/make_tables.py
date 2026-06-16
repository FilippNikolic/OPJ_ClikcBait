#!/usr/bin/env python3
"""Faza 4 — generisanje LaTeX tabela iz results/*.csv u report/tables/.

Čita rezultate Faze 3 i piše `booktabs` tabele spremne za \\input u izvestaj.tex:
  results/baseline_results.csv          -> report/tables/baseline.tex
  results/encoder_*_results.csv         -> report/tables/encoder.tex
  results/decoder_results.csv           -> report/tables/decoder.tex
  (najbolji po tipu modela)             -> report/tables/poredjenje.tex

Otporno na nedostajuće ulaze: ako CSV ne postoji, piše placeholder tabelu sa
napomenom (skelet izveštaja se svejedno kompajlira).

Pokretanje:
  .venv/bin/python src/report/make_tables.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
TABLES = ROOT / "report" / "tables"


def read_csv(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def esc(s: str) -> str:
    """Escape za LaTeX (osnovno)."""
    return (str(s).replace("\\", r"\textbackslash{}").replace("_", r"\_")
            .replace("%", r"\%").replace("&", r"\&").replace("#", r"\#")
            .replace("±", r"$\pm$"))


def latex_table(caption, label, headers, rows, colspec=None, note=None):
    colspec = colspec or ("l" * (len(headers) - 1) + "r" * 1 if headers else "l")
    # zaglavlja su namerni LaTeX (npr. F1$_{kb}$) -> NE escape-ovati;
    # ćelije sa podacima dolaze iz CSV-a -> escape (npr. sr_zero_def, ±).
    out = ["\\begin{table}[H]\\centering",
           f"\\caption{{{caption}}}\\label{{{label}}}",
           f"\\begin{{tabular}}{{{colspec}}}", "\\toprule",
           " & ".join(headers) + " \\\\", "\\midrule"]
    for r in rows:
        out.append(" & ".join(esc(c) for c in r) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    if note:
        out.append(f"\\\\[2pt]\\footnotesize {esc(note)}")
    out.append("\\end{table}")
    return "\n".join(out) + "\n"


def placeholder(caption, label, msg):
    return latex_table(caption, label, ["Status"], [[msg]], colspec="l")


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"📄 {path.relative_to(ROOT)}")


# --- baseline ----------------------------------------------------------------
def gen_baseline():
    rows = read_csv(RESULTS / "baseline_results.csv")
    out = TABLES / "baseline.tex"
    if not rows:
        write(out, placeholder("Osnovni modeli --- rezultati.", "tab:baseline",
                               "Pokreni Fazu 3a (run_baseline.py)."))
        return
    cols = ["model", "normalize", "scheme", "ngram", "f1_kb", "accuracy",
            "roc_auc"]
    head = ["Model", "Norm.", "Šema", "n-gram", "F1$_{kb}$", "Acc.", "AUC"]
    body = [[r.get(c, "—") for c in cols] for r in rows[:20]]
    note = f"Prikazano top {len(body)} (po F1 klikbejt klase), nested 10-fold CV."
    write(out, latex_table("Osnovni modeli --- efekat preprocessinga i odlika.",
                           "tab:baseline", head, body,
                           colspec="llllrrr", note=note))


# --- encoder -----------------------------------------------------------------
def gen_encoder():
    rows = []
    for key in ("bertic", "mbert"):
        r = read_csv(RESULTS / f"encoder_{key}_results.csv")
        if r:
            rows += r
    out = TABLES / "encoder.tex"
    if not rows:
        write(out, placeholder("Enkoderski modeli --- rezultati.",
                               "tab:encoder",
                               "Pokreni Fazu 3b (finetune.py) na Colab-u."))
        return
    cols = ["model", "epochs", "f1_kb", "accuracy", "precision_kb",
            "recall_kb", "roc_auc"]
    head = ["Model", "Epohe", "F1$_{kb}$", "Acc.", "P$_{kb}$", "R$_{kb}$",
            "AUC"]
    body = [[r.get(c, "—") for c in cols] for r in rows]
    write(out, latex_table("Enkoderski LLM --- BERTić vs mBERT, varijante epoha.",
                           "tab:encoder", head, body, colspec="lrrrrrr",
                           note="10-slojna stratifikovana CV."))


# --- decoder -----------------------------------------------------------------
def gen_decoder():
    rows = read_csv(RESULTS / "decoder_results.csv")
    out = TABLES / "decoder.tex"
    if not rows:
        write(out, placeholder("Dekoderski model --- rezultati.", "tab:decoder",
                               "Pokreni Fazu 3c (chatgpt_eval.py)."))
        return
    cols = ["variant", "lang", "shots", "f1_kb", "accuracy", "precision_kb",
            "recall_kb"]
    head = ["Varijanta", "Jezik", "Shots", "F1$_{kb}$", "Acc.", "P$_{kb}$",
            "R$_{kb}$"]
    body = [[r.get(c, "—") for c in cols] for r in rows]
    write(out, latex_table("Dekoderski LLM (ChatGPT) --- SR vs EN, zero/few-shot.",
                           "tab:decoder", head, body, colspec="lllrrrr",
                           note="Evaluacija na celom skupu."))


# --- master poređenje --------------------------------------------------------
def _best(rows, key="f1_kb"):
    def num(r):
        v = str(r.get(key, "0")).split("±")[0]
        try:
            return float(v)
        except ValueError:
            return -1.0
    return max(rows, key=num) if rows else None


def gen_poredjenje():
    out = TABLES / "poredjenje.tex"
    body = []
    b = read_csv(RESULTS / "baseline_results.csv")
    if b:
        x = _best(b)
        body.append([f"Baseline ({x['model']}, {x['scheme']})", x.get("f1_kb"),
                     x.get("accuracy"), x.get("roc_auc", "—")])
    enc = []
    for key in ("bertic", "mbert"):
        r = read_csv(RESULTS / f"encoder_{key}_results.csv")
        if r:
            x = _best(r)
            body.append([f"Enkoderski ({key})", x.get("f1_kb"),
                         x.get("accuracy"), x.get("roc_auc", "—")])
    d = read_csv(RESULTS / "decoder_results.csv")
    if d:
        x = _best(d)
        body.append([f"ChatGPT ({x.get('variant')})", x.get("f1_kb"),
                     x.get("accuracy"), x.get("roc_auc", "—")])
    if not body:
        write(out, placeholder("Uporedni pregled modela.", "tab:poredjenje",
                               "Pokreni Fazu 3 (baseline + enkoderski + dekoderski)."))
        return
    head = ["Najbolji po tipu", "F1$_{kb}$", "Acc.", "AUC"]
    write(out, latex_table("Uporedni pregled --- najbolja varijanta po tipu modela.",
                           "tab:poredjenje", head, body, colspec="lrrr"))


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    gen_baseline()
    gen_encoder()
    gen_decoder()
    gen_poredjenje()
    print("\n✅ Tabele u report/tables/. Prekompajliraj izvestaj.tex.")


if __name__ == "__main__":
    main()
