#!/usr/bin/env python3
"""Faza 3c — Dekoderski LLM (ChatGPT): evaluacija na CELOM skupu.

Bez fine-tuninga (zatvoren model) → samo evaluacija. Poredimo prompt varijante
(SR/EN, zero/few-shot, sa/bez definicije) iz prompts.py.

Karakteristike:
  • keš odgovora u results/decoder_cache/<varijanta>.jsonl — prekid/nastavak
    bez ponovnog plaćanja API poziva (re-run preskače već urađene naslove).
  • few-shot primeri se po želji izbacuju iz eval skupa (--holdout-fewshot) da
    ne bi bilo curenja.
  • procena cene (broj poziva × tokeni) na kraju.

Podešavanje ključa:
  export OPENAI_API_KEY=sk-...
Pokretanje:
  pip install -r requirements-decoder.txt
  python src/decoder/chatgpt_eval.py --model gpt-4o-mini            # sve varijante
  python src/decoder/chatgpt_eval.py --variants sr_zero_def en_zero_def
  python src/decoder/chatgpt_eval.py --limit 50                     # smoke-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from baseline import common  # noqa: E402
from decoder import prompts  # noqa: E402

CACHE_DIR = common.RESULTS / "decoder_cache"


def load_cache(path: Path) -> dict:
    cache = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                    cache[o["naslov"]] = o
                except json.JSONDecodeError:
                    continue
    return cache


def parse_label(text: str):
    """Izvuci 0/1 iz odgovora modela. Vrati None ako ne može."""
    t = (text or "").strip()
    for ch in t:
        if ch == "1":
            return 1
        if ch == "0":
            return 0
    low = t.lower()
    if "klikbejt" in low or "clickbait" in low:
        return 1
    if "regular" in low or "regularan" in low:
        return 0
    return None


def classify_one(client, model, system, user_prompt):
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user_prompt}],
        temperature=0,
        max_tokens=5,
    )
    msg = resp.choices[0].message.content
    usage = resp.usage
    return msg, (usage.prompt_tokens, usage.completion_tokens)


def run_variant(client, model, variant, texts, labels, limit, holdout):
    system, template = prompts.build_prompt(
        variant["lang"], variant["shots"], variant["with_def"])
    cache_path = CACHE_DIR / f"{model}__{variant['id']}.jsonl"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = load_cache(cache_path)

    fewshot_naslovi = {n for n, _ in prompts.FEWSHOT}
    pairs = list(zip(texts, labels))
    if holdout and variant["shots"] == "few":
        pairs = [(t, y) for t, y in pairs if t not in fewshot_naslovi]
    if limit:
        pairs = pairs[:limit]

    y_true, y_pred = [], []
    n_pt = n_ct = 0
    n_calls = 0
    skipped = 0
    for i, (naslov, lab) in enumerate(pairs):
        if naslov in cache:
            pred = cache[naslov]["pred"]
        else:
            user = template.format(naslov=naslov)
            for attempt in range(4):
                try:
                    msg, (pt, ct) = classify_one(client, model, system, user)
                    n_pt += pt
                    n_ct += ct
                    n_calls += 1
                    break
                except Exception as e:  # rate limit / transient
                    if attempt == 3:
                        print(f"\n   ⚠️  preskačem '{naslov[:40]}…': {e}")
                        msg = ""
                        break
                    time.sleep(2 ** attempt)
            pred = parse_label(msg)
            common.append_jsonl(
                {"naslov": naslov, "true": lab, "pred": pred, "raw": msg},
                cache_path)
        if pred is None:
            skipped += 1
            continue
        y_true.append(lab)
        y_pred.append(pred)
        if (i + 1) % 50 == 0:
            sys.stdout.write(f"\r   {variant['id']}: {i+1}/{len(pairs)}")
            sys.stdout.flush()
    print()

    m = common.compute_metrics(y_true, y_pred) if y_true else {}
    row = {"model": model, "variant": variant["id"], "lang": variant["lang"],
           "shots": variant["shots"], "with_def": variant["with_def"],
           "n_eval": len(y_true), "n_unparsed": skipped,
           "new_api_calls": n_calls}
    for k in ("accuracy", "precision_kb", "recall_kb", "f1_kb", "f1_macro"):
        row[k] = f"{m[k]:.3f}" if k in m else "—"
    return row, (n_pt, n_ct)


# približne cene ($/1M tokena) — proveri aktuelne pre konačne procene
PRICING = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.0),
}


def main():
    ap = argparse.ArgumentParser(description="Faza 3c ChatGPT eval.")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--variants", nargs="+", default=None,
                    help="id-jevi iz prompts.VARIANTS (podrazumevano sve)")
    ap.add_argument("--limit", type=int, default=None,
                    help="evaluiraj samo prvih N (smoke-test)")
    ap.add_argument("--holdout-fewshot", action="store_true", default=True,
                    help="izbaci few-shot primere iz eval skupa")
    ap.add_argument("--out", default=str(common.RESULTS / "decoder_results.csv"))
    args = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("❌ Postavi OPENAI_API_KEY (export OPENAI_API_KEY=sk-...).")
    from openai import OpenAI
    client = OpenAI()

    variants = prompts.VARIANTS
    if args.variants:
        variants = [v for v in prompts.VARIANTS if v["id"] in args.variants]
        if not variants:
            sys.exit(f"Nepoznate varijante. Dostupne: "
                     f"{[v['id'] for v in prompts.VARIANTS]}")

    texts, labels = common.load_dataset()
    print(f"Eval skup: {len(texts)} naslova | model={args.model} | "
          f"varijanti={len(variants)}")

    rows, tot_pt, tot_ct = [], 0, 0
    for v in variants:
        print(f"\n=== {v['id']} ===")
        row, (pt, ct) = run_variant(client, args.model, v, texts, labels,
                                    args.limit, args.holdout_fewshot)
        rows.append(row)
        tot_pt += pt
        tot_ct += ct
        print(f"   F1_kb={row['f1_kb']} acc={row['accuracy']} "
              f"(neparsiranih={row['n_unparsed']})")

    rows.sort(key=lambda r: r["f1_kb"], reverse=True)
    common.write_results_csv(rows, args.out)

    if args.model in PRICING and (tot_pt or tot_ct):
        pin, pout = PRICING[args.model]
        cost = tot_pt / 1e6 * pin + tot_ct / 1e6 * pout
        print(f"\n💰 Novi API pozivi ove sesije: prompt={tot_pt} "
              f"completion={tot_ct} tok → ~${cost:.4f} ({args.model}).")
    print("ℹ️  Keširani odgovori se ne plaćaju ponovo (results/decoder_cache/).")


if __name__ == "__main__":
    main()
