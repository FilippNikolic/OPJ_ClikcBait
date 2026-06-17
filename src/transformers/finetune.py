#!/usr/bin/env python3
"""Faza 3b — Enkoderski LLM: fine-tuning BERTić (mono) + mBERT (multi).

Protokol (zahtev postavke):
  • 10-slojna stratifikovana unakrsna validacija
  • EVALUACIJA VARIJANTI PO BROJU EPOHA (npr. 2 / 3 / 4)
  • bar 1 monolingvalni (BERTić) + 1 multilingvalni (mBERT)
  • Huggingface Transformers (Trainer)
  • iste metrike kao baseline radi poređenja

GPU (≥8GB) — pokretati na Google Colab ili Azure. Vidi src/transformers/README.md.

Modeli (HF id):
  BERTić : classla/bcms-bertic
  mBERT  : bert-base-multilingual-cased

Pokretanje:
  pip install -r requirements-ml.txt
  python src/transformers/finetune.py --model bertic --epochs 2 3 4
  python src/transformers/finetune.py --model mbert  --epochs 2 3 4
  python src/transformers/finetune.py --model bertic --epochs 3 --quick   # 2 fold-a
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SRC = str(ROOT / "src")
_SELF = str(Path(__file__).resolve().parent)  # .../src/transformers — ISTO IME kao HF paket!

# --- sprečavanje sudara imena sa HuggingFace bibliotekom 'transformers' -------
# Ovaj folder se zove 'transformers'. Ako bi 'src' (ili ovaj folder) bio na
# POČETKU sys.path, `import transformers` bi učitao OVAJ lokalni paket umesto
# HF biblioteke (ImportError: cannot import name 'AutoModelForSequenceClassification').
# Zato: (1) skloni '', ovaj folder i 'src' sa početka putanje; (2) 'src' dodaj na
# KRAJ (da se 'baseline' i dalje nalazi); (3) izbaci eventualno već uvezen lokalni
# 'transformers' iz keša modula. Ovo radi bez obzira kako se skripta pokrene.
sys.path[:] = [p for p in sys.path if p not in ("", _SELF, _SRC)]
sys.path.append(_SRC)
for _m in [k for k in list(sys.modules) if k == "transformers" or k.startswith("transformers.")]:
    _f = getattr(sys.modules[_m], "__file__", None) or ""
    if _f.startswith(_SELF):
        del sys.modules[_m]

from baseline import common  # noqa: E402  (zajedničke metrike/IO)

HF_IDS = {
    "bertic": "classla/bcms-bertic",
    "mbert": "bert-base-multilingual-cased",
}


def build_compute_metrics():
    import numpy as np

    def _cm(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        # softmax za ROC-AUC (verovatnoća klikbejt klase)
        ex = np.exp(logits - logits.max(axis=-1, keepdims=True))
        proba = ex[:, 1] / ex.sum(axis=-1)
        return common.compute_metrics(labels, preds, proba)

    return _cm


def run_cv(model_key, epochs_list, n_folds, batch_size, lr, max_len, seed,
           quick, out_path, separate=True):
    import numpy as np
    import torch
    from datasets import Dataset
    from sklearn.model_selection import StratifiedKFold
    import inspect

    from transformers import (AutoModelForSequenceClassification,
                              AutoTokenizer, DataCollatorWithPadding, Trainer,
                              TrainingArguments)

    hf_id = HF_IDS[model_key]
    texts, labels = common.load_dataset()
    texts, labels = np.array(texts, dtype=object), np.array(labels)
    print(f"Model: {model_key} ({hf_id}) | {len(texts)} naslova | "
          f"GPU={torch.cuda.is_available()}")

    tokenizer = AutoTokenizer.from_pretrained(hf_id)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=max_len)

    n_folds = 2 if quick else n_folds
    outer = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    compute_metrics = build_compute_metrics()

    target_epochs = sorted(set(int(e) for e in epochs_list))
    per_epoch = {e: [] for e in target_epochs}  # epoch -> lista per-fold metrika

    def make_trainer(ds_tr, ds_te, n_epochs, tag):
        """Svež model + Trainer treniran TAČNO n_epochs (sopstveni LR schedule)."""
        model = AutoModelForSequenceClassification.from_pretrained(
            hf_id, num_labels=2)
        targs = TrainingArguments(
            output_dir=str(ROOT / "results" / "_hf_tmp" / tag),
            num_train_epochs=n_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size * 2,
            learning_rate=lr,
            seed=seed,
            eval_strategy="epoch",
            save_strategy="no",
            logging_steps=50,
            report_to=[],
            fp16=torch.cuda.is_available(),
        )
        kw = dict(model=model, args=targs, train_dataset=ds_tr,
                  eval_dataset=ds_te, compute_metrics=compute_metrics,
                  data_collator=DataCollatorWithPadding(tokenizer))
        # 'tokenizer=' preimenovan u 'processing_class=' u novom transformers
        _p = inspect.signature(Trainer.__init__).parameters
        if "processing_class" in _p:
            kw["processing_class"] = tokenizer
        elif "tokenizer" in _p:
            kw["tokenizer"] = tokenizer
        return model, Trainer(**kw)

    def cleanup(model, trainer):
        del model, trainer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    for fold, (tr, te) in enumerate(outer.split(texts, labels)):
        ds_tr = Dataset.from_dict({"text": list(texts[tr]),
                                   "label": [int(x) for x in labels[tr]]}
                                  ).map(tokenize, batched=True)
        ds_te = Dataset.from_dict({"text": list(texts[te]),
                                   "label": [int(x) for x in labels[te]]}
                                  ).map(tokenize, batched=True)

        if separate:
            # ZAHTEV: svaka dužina fine-tuninga je ZASEBAN trening (svoj LR
            # schedule). Skuplje (10×(2+3+4) epoha), ali metodološki ispravno.
            for e in target_epochs:
                model, trainer = make_trainer(ds_tr, ds_te, e,
                                              f"{model_key}_e{e}_f{fold}")
                t0 = time.time()
                trainer.train()
                m = {k.replace("eval_", ""): v
                     for k, v in trainer.evaluate().items()}
                per_epoch[e].append(m)
                print(f"  fold={fold+1}/{n_folds} epochs={e} "
                      f"F1_kb={m.get('f1_kb', float('nan')):.3f} "
                      f"({time.time()-t0:.0f}s)")
                cleanup(model, trainer)
        else:
            # BRZA (približna) varijanta: jedan trening do max epoha, eval posle
            # svake. NB: LR schedule je za max epoha → 2/3 su checkpoint-i, ne
            # zasebni fine-tuning-zi. Koristiti samo za brzu probu, NE za rad.
            max_epochs = max(target_epochs)
            model, trainer = make_trainer(ds_tr, ds_te, max_epochs,
                                          f"{model_key}_f{fold}")
            t0 = time.time()
            trainer.train()
            evals = {}
            for rec in trainer.state.log_history:
                if "eval_f1_kb" in rec:
                    ep = int(round(rec["epoch"]))
                    evals[ep] = {k.replace("eval_", ""): v
                                 for k, v in rec.items() if k.startswith("eval_")}
            for e in target_epochs:
                if e in evals:
                    per_epoch[e].append(evals[e])
            got = ", ".join(f"{e}ep:{evals[e]['f1_kb']:.3f}"
                            for e in target_epochs if e in evals)
            print(f"  fold={fold+1}/{n_folds} ({time.time()-t0:.0f}s)  {got}")
            cleanup(model, trainer)

    keys = ["accuracy", "precision_kb", "recall_kb", "f1_kb", "f1_macro",
            "roc_auc"]
    rows = []
    for e in target_epochs:
        row = {"model": model_key, "epochs": e, "folds": n_folds}
        for k in keys:
            vals = [fm[k] for fm in per_epoch[e] if k in fm]
            row[k] = common.fmt_mean_std(vals)
        rows.append(row)
        print(f"➡️  epochs={e}: F1_kb={row['f1_kb']}")

    common.write_results_csv(rows, out_path)
    abs_out = Path(out_path).resolve()
    print(f"\n✅ {model_key} GOTOVO → REZULTATI: {abs_out}")
    return rows


def main():
    ap = argparse.ArgumentParser(description="Faza 3b enkoderski fine-tuning.")
    ap.add_argument("--model", required=True, choices=list(HF_IDS))
    ap.add_argument("--epochs", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--folds", type=int, default=common.N_FOLDS)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-len", type=int, default=64,
                    help="naslovi su kratki — 64 tokena je dovoljno")
    ap.add_argument("--quick", action="store_true", help="2 fold-a (smoke)")
    ap.add_argument("--fast-epochs", action="store_true",
                    help="približno: jedan trening do max epoha + eval po epohi "
                         "(NIJE po zahtevu — samo za brzu probu)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = args.out or str(common.RESULTS / f"encoder_{args.model}_results.csv")
    run_cv(args.model, args.epochs, args.folds, args.batch_size, args.lr,
           args.max_len, common.SEED, args.quick, out,
           separate=not args.fast_epochs)


if __name__ == "__main__":
    main()
