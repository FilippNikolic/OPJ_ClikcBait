#!/usr/bin/env python3
"""Faza 3c — Dekoderski LLM (Google Gemini, BESPLATAN tier): eval na celom skupu.

Besplatna alternativa ChatGPT-u (vidi chatgpt_eval.py). Bez fine-tuninga
(zatvoren model) → samo evaluacija. Poredimo iste prompt varijante (SR/EN,
zero/few-shot, sa/bez definicije) iz prompts.py — identičan protokol i metrike
kao ChatGPT i baseline, radi uporedne tabele.

Zašto Gemini: Google AI Studio daje BESPLATAN API ključ. Modeli `gemini-*-flash`
imaju besplatan tier (uz rate-limit, npr. ~10-15 zahteva/min). Zato:
  • keš odgovora u results/decoder_cache/<model>__<varijanta>.jsonl — prekid/
    nastavak bez ponovnih poziva (re-run preskače već urađene naslove). Ceo skup
    se po potrebi odradi kroz VIŠE sesija/dana u okviru besplatnih limita.
  • throttle (--rpm) + eksponencijalni backoff na 429 (rate limit).

Ključ (besplatno: https://aistudio.google.com/apikey):
  export GEMINI_API_KEY=...          # ili GOOGLE_API_KEY
Pokretanje:
  pip install -r requirements-decoder.txt        # google-genai
  python src/decoder/gemini_eval.py --limit 50                  # smoke-test
  python src/decoder/gemini_eval.py                             # sve varijante, ceo skup
  python src/decoder/gemini_eval.py --variants sr_zero_def en_zero_def
  python src/decoder/gemini_eval.py --model gemini-2.0-flash --rpm 15
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from baseline import common  # noqa: E402
from decoder import prompts  # noqa: E402
# deli keš/parsiranje sa ChatGPT verzijom (DRY)
from decoder.chatgpt_eval import CACHE_DIR, load_cache, parse_label  # noqa: E402


def classify_one(client, genai_types, model, system, user_prompt):
    """Jedan poziv Gemini-ja. Vrati (tekst, (prompt_tok, completion_tok))."""
    resp = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction=system,
            temperature=0,
            max_output_tokens=5,
        ),
    )
    text = resp.text or ""
    um = getattr(resp, "usage_metadata", None)
    pt = getattr(um, "prompt_token_count", 0) or 0
    ct = getattr(um, "candidates_token_count", 0) or 0
    return text, (pt, ct)


def run_variant(client, genai_types, model, variant, texts, labels, limit,
                holdout, min_interval):
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
    n_pt = n_ct = n_calls = skipped = 0
    last_call = 0.0
    consec_fail = 0
    for i, (naslov, lab) in enumerate(pairs):
        if naslov in cache:
            pred = cache[naslov]["pred"]
        else:
            user = template.format(naslov=naslov)
            msg, ok = "", False
            for attempt in range(5):
                # throttle: poštuj minimalni razmak između NOVIH poziva (free RPM)
                wait = min_interval - (time.time() - last_call)
                if wait > 0:
                    time.sleep(wait)
                try:
                    msg, (pt, ct) = classify_one(
                        client, genai_types, model, system, user)
                    last_call = time.time()
                    n_pt += pt
                    n_ct += ct
                    n_calls += 1
                    ok = True
                    break
                except Exception as e:  # rate limit / transient
                    last_call = time.time()
                    if attempt == 4:
                        print(f"\n   ⚠️  neuspeh '{naslov[:40]}…': {e}")
                    else:
                        time.sleep(min(2 ** attempt * 3, 60))  # 429 → backoff
            pred = parse_label(msg) if ok else None
            if pred is not None:
                # keširamo SAMO uspešne → re-run kasnije dopuni neuspele/preskočene
                common.append_jsonl(
                    {"naslov": naslov, "true": lab, "pred": pred, "raw": msg},
                    cache_path)
                consec_fail = 0
            else:
                consec_fail += 1
                if consec_fail >= 20:
                    print(f"\n   ⛔ 20 uzastopnih neuspeha (verovatno DNEVNI "
                          f"limit) — prekidam '{variant['id']}'. Pokreni ponovo "
                          f"kasnije; keš nastavlja gde je stao.")
                    break
        if pred is None:
            skipped += 1
            continue
        y_true.append(lab)
        y_pred.append(pred)
        if (i + 1) % 25 == 0:
            sys.stdout.write(f"\r   {variant['id']}: {i+1}/{len(pairs)} "
                             f"(novih: {n_calls}, preskočeno: {skipped})")
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


def main():
    ap = argparse.ArgumentParser(description="Faza 3c Gemini eval (besplatno).")
    ap.add_argument("--model", default="gemini-2.5-flash",
                    help="npr. gemini-2.5-flash, gemini-2.0-flash, "
                         "gemini-2.0-flash-lite")
    ap.add_argument("--variants", nargs="+", default=None,
                    help="id-jevi iz prompts.VARIANTS (podrazumevano sve)")
    ap.add_argument("--limit", type=int, default=None,
                    help="evaluiraj samo prvih N (smoke-test)")
    ap.add_argument("--rpm", type=float, default=12,
                    help="maks. NOVIH zahteva/min (besplatan tier ~10-15)")
    ap.add_argument("--holdout-fewshot", action="store_true", default=True,
                    help="izbaci few-shot primere iz eval skupa")
    ap.add_argument("--out", default=str(common.RESULTS / "decoder_results.csv"))
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("❌ Postavi GEMINI_API_KEY (besplatno: "
                 "https://aistudio.google.com/apikey).")
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        sys.exit("❌ Nedostaje SDK: pip install -r requirements-decoder.txt "
                 "(google-genai).")
    client = genai.Client(api_key=api_key)
    min_interval = 60.0 / args.rpm if args.rpm > 0 else 0.0

    variants = prompts.VARIANTS
    if args.variants:
        variants = [v for v in prompts.VARIANTS if v["id"] in args.variants]
        if not variants:
            sys.exit(f"Nepoznate varijante. Dostupne: "
                     f"{[v['id'] for v in prompts.VARIANTS]}")

    texts, labels = common.load_dataset()
    print(f"Eval skup: {len(texts)} naslova | model={args.model} | "
          f"varijanti={len(variants)} | rpm≈{args.rpm}")

    rows, tot_pt, tot_ct = [], 0, 0
    for v in variants:
        print(f"\n=== {v['id']} ===")
        row, (pt, ct) = run_variant(
            client, genai_types, args.model, v, texts, labels,
            args.limit, args.holdout_fewshot, min_interval)
        rows.append(row)
        tot_pt += pt
        tot_ct += ct
        print(f"   F1_kb={row['f1_kb']} acc={row['accuracy']} "
              f"(neparsiranih={row['n_unparsed']})")

    rows.sort(key=lambda r: r["f1_kb"], reverse=True)
    common.write_results_csv(rows, args.out)

    print(f"\n🆓 Gemini besplatan tier — bez naplate. Potrošeni tokeni ove "
          f"sesije: prompt={tot_pt}, completion={tot_ct}.")
    print("ℹ️  Keširani odgovori se ne pozivaju ponovo (results/decoder_cache/) "
          "— ceo skup se može odraditi kroz više sesija u okviru free limita.")


if __name__ == "__main__":
    main()
