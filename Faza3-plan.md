# Faza 3 — Obučavanje i evaluacija modela (40p) — plan, to-do i RUNBOOK

> Kod je **pripremljen unapred** (dok traje anotacija u Fazi 2). Čeka samo
> `data/annotated/dataset.tsv` koji proizvodi `build_dataset.py` na kraju Faze 2.
> Do tada sve skripte rade na `data/annotated/dataset.sample.tsv` (20 naslova,
> smoke-test) — automatski fallback ako pravi skup ne postoji.

---

## Šta je Faza 3 (iz `Projekat-zahtevi.md` + `Plan-izrade-projekta.md`)

| Pod-faza | Modeli | Validacija | Varijante | Gde se vrti |
|---|---|---|---|---|
| **3a Baseline** (20p) | Logistička regresija + Naivni Bajes | 10-fold stratif. + **nested CV** | preprocessing × TF/IDF/TF-IDF × n-gram | lokalno (CPU) |
| **3b Enkoderski** (deo 20p) | BERTić (mono) + mBERT (multi) | 10-fold stratif. | **broj epoha** (2/3/4) | Colab/Azure (GPU) |
| **3c Dekoderski** (deo 20p) | ChatGPT (bez fine-tuninga) | ceo skup | SR vs EN, zero/few-shot, sa/bez def. | API (bez GPU) |

Metrike (sve tri, identično — radi uporedne tabele): accuracy, **precision/recall/F1
za klikbejt klasu**, macro-F1, ROC-AUC (gde ima verovatnoća).

---

## Pripremljen kod (struktura po `Plan-izrade-projekta.md`)

```
src/
├── preprocessing/serbian.py     # normalizacija + heuristički stemmer + classla lematizacija
├── baseline/
│   ├── common.py                # učitavanje skupa, metrike, IO (DELE sve tri pod-faze)
│   └── run_baseline.py          # LR + NB, nested 10-fold CV, grid preprocessing varijanti
├── transformers/
│   ├── finetune.py              # BERTić + mBERT, HF Trainer, 10-fold, epohe
│   └── README.md                # Colab uputstvo
└── decoder/
    ├── prompts.py               # 6 prompt varijanti (SR/EN × zero/few × def)
    └── chatgpt_eval.py          # eval na celom skupu, keš, procena cene

requirements-baseline.txt        # sklearn (CPU, lokalno)
requirements-ml.txt              # torch/transformers (Colab/GPU)
requirements-decoder.txt         # openai
results/                         # *_results.csv izlazi
data/annotated/dataset.sample.tsv  # 20 naslova za smoke-test
```

Status smoke-testa (na sample skupu): ✅ baseline radi (nested CV + metrike + CSV),
✅ stemmer radi, ✅ prompt-ovi se grade. Enkoderski se testira na Colab-u (GPU).

---

## To-do lista

### Preduslov (kraj Faze 2)
- [ ] `build_dataset.py` → `data/annotated/dataset.tsv` (balans 1100/1100) postoji

### 3a — Baseline (lokalno)
- [ ] `pip install -r requirements-baseline.txt` (sklearn je već u .venv)
- [ ] (opc.) `pip install classla` ako želimo `normalize=lemma`
- [ ] Pun grid: `python src/baseline/run_baseline.py --full --normalize none stem lemma`
- [ ] Pregledati `results/baseline_results.csv` (sortirano po F1_kb)
- [ ] Tabela: efekat svake preprocessing/feature varijante za izveštaj

### 3b — Enkoderski (Colab/GPU)
- [ ] Otpremiti `dataset.tsv` + kod na Colab (vidi `src/transformers/README.md`)
- [ ] BERTić: `--model bertic --epochs 2 3 4`
- [ ] mBERT: `--model mbert --epochs 2 3 4`
- [ ] Skinuti `results/encoder_*_results.csv`
- [ ] Tabela: mono vs multi vs baseline + efekat broja epoha

### 3c — Dekoderski (API)
- [ ] `pip install -r requirements-decoder.txt`; `export OPENAI_API_KEY=...`
- [ ] Smoke: `python src/decoder/chatgpt_eval.py --limit 50`
- [ ] Pun eval: `python src/decoder/chatgpt_eval.py` (sve 6 varijanti, ceo skup)
- [ ] Tabela: SR vs EN, zero vs few-shot, sa/bez definicije + diskusija cene/limita

### Sinteza za dokumentaciju (Faza 4)
- [ ] Jedna uporedna tabela: baseline (najbolji) vs BERTić vs mBERT vs ChatGPT
- [ ] Diskusija: šta najbolje radi i zašto, ograničenja, dalji rad

---

## RUNBOOK (kad `dataset.tsv` bude gotov)

```bash
# 3a — baseline (lokalno, .venv)
.venv/bin/python src/baseline/run_baseline.py --full --normalize none stem lemma
#   → results/baseline_results.csv
#   varijante: --normalize {none,stem,lemma} --scheme {bow,tf,idf,tfidf}
#              --ngram 1-1 1-2  --models {logreg,mnb,bnb}
#   brzo:  --quick     |  jedan model:  --models logreg

# 3b — enkoderski (Google Colab, GPU) — vidi src/transformers/README.md
python src/transformers/finetune.py --model bertic --epochs 2 3 4
python src/transformers/finetune.py --model mbert  --epochs 2 3 4
#   → results/encoder_{bertic,mbert}_results.csv

# 3c — dekoderski (API)
export OPENAI_API_KEY=sk-...
python src/decoder/chatgpt_eval.py --model gpt-4o-mini
#   → results/decoder_results.csv  (keš u results/decoder_cache/, prekid/nastavak)
#   smoke:  --limit 50   |   izbor varijanti:  --variants sr_zero_def en_zero_def
```

### Važne napomene
- **Sample fallback**: dok nema `dataset.tsv`, sve skripte rade na
  `dataset.sample.tsv` i ispisuju upozorenje. Brojevi su besmisleni (20 naslova) —
  služe samo da kod „prođe".
- **Nema curenja**: preprocessing (stem/lemma) se radi jednom nad celim skupom,
  ali vektorizator (vokabular + IDF) se uči **unutar svakog fold-a**.
- **Stemmer je heuristički** (suffix-stripping, bez zavisnosti) — za „pravu"
  lematizaciju koristi `--normalize lemma` (classla, povlači torch).
- **Enkoderski je skup**: 10-fold × 3 epohe × 2 modela = 60 treninga (sati na T4).
  Za probu smanji foldove (`--quick`) ili broj epoha.
- **Dekoderski keš**: odgovori se snimaju u `results/decoder_cache/*.jsonl` —
  ponovni run preskače već klasifikovane naslove (ne plaća se 2×).
- Radimo samo sa **SportKlub** izvorom (vidi memoriju `single-source-sportklub`).
```
