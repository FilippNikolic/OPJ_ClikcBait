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
sys.path.insert(0, str(ROOT / "src"))

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
           quick, out_path):
    import numpy as np
    import torch
    from datasets import Dataset
    from sklearn.model_selection import StratifiedKFold
    from transformers import (AutoModelForSequenceClassification,
                              AutoTokenizer, Trainer, TrainingArguments)

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

    rows = []
    for n_epochs in epochs_list:
        fold_metrics = []
        for fold, (tr, te) in enumerate(outer.split(texts, labels)):
            ds_tr = Dataset.from_dict({"text": list(texts[tr]),
                                       "label": [int(x) for x in labels[tr]]})
            ds_te = Dataset.from_dict({"text": list(texts[te]),
                                       "label": [int(x) for x in labels[te]]})
            ds_tr = ds_tr.map(tokenize, batched=True)
            ds_te = ds_te.map(tokenize, batched=True)

            model = AutoModelForSequenceClassification.from_pretrained(
                hf_id, num_labels=2)
            targs = TrainingArguments(
                output_dir=str(ROOT / "results" / "_hf_tmp" /
                               f"{model_key}_e{n_epochs}_f{fold}"),
                num_train_epochs=n_epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size * 2,
                learning_rate=lr,
                seed=seed,
                eval_strategy="no",
                save_strategy="no",
                logging_steps=50,
                report_to=[],
                fp16=torch.cuda.is_available(),
            )
            trainer = Trainer(
                model=model, args=targs, train_dataset=ds_tr,
                eval_dataset=ds_te, compute_metrics=compute_metrics,
                tokenizer=tokenizer,
            )
            t0 = time.time()
            trainer.train()
            m = trainer.evaluate()
            m = {k.replace("eval_", ""): v for k, v in m.items()}
            fold_metrics.append(m)
            print(f"  epochs={n_epochs} fold={fold+1}/{n_folds} "
                  f"F1_kb={m.get('f1_kb', float('nan')):.3f} "
                  f"({time.time()-t0:.0f}s)")
            del model, trainer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        keys = ["accuracy", "precision_kb", "recall_kb", "f1_kb", "f1_macro",
                "roc_auc"]
        row = {"model": model_key, "epochs": n_epochs, "folds": n_folds}
        for k in keys:
            vals = [fm[k] for fm in fold_metrics if k in fm]
            row[k] = common.fmt_mean_std(vals)
        rows.append(row)
        print(f"➡️  epochs={n_epochs}: F1_kb={row['f1_kb']}")

    common.write_results_csv(rows, out_path)
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
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = args.out or str(common.RESULTS / f"encoder_{args.model}_results.csv")
    run_cv(args.model, args.epochs, args.folds, args.batch_size, args.lr,
           args.max_len, common.SEED, args.quick, out)


if __name__ == "__main__":
    main()
