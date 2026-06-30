
# Komande — kako pokrenuti projekat

> Korak-po-korak komande za ceo projekat, **gde** se pokreću i **šta se očekuje**
> kao izlaz. Mapa koda (gde se šta radi) je u [`docs/Mapa-koda.md`](./Mapa-koda.md).
>
> Sve komande se pokreću iz **korena projekta**:
> `/Users/filipjackpot/MasterETF/OPJ`

---

## 0. Priprema okruženja (jednom)

```bash
cd /Users/filipjackpot/MasterETF/OPJ
python3 -m venv .venv                 # napravi virtuelno okruženje (ako ne postoji)
source .venv/bin/activate             # aktiviraj ga
pip install -r requirements/requirements.txt   # osnovne zavisnosti (scraping)
```

> U projektu se često poziva `.venv/bin/python ...` direktno (bez `activate`) — i to radi.
> Zavisnosti su razdvojene po fazi (`requirements/requirements-*.txt`); instaliraj
> onu koja ti treba za korak koji pokrećeš.

**API ključevi** (samo za dekoder, Faza 3c) idu u `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

---

## Faza 1 — Prikupljanje podataka

```bash
pip install -r requirements/requirements.txt
.venv/bin/python src/scraping/sportklub_api.py --broj 1500
```

- **Gde:** koren projekta.
- **Šta radi:** povlači ~1500 naslova sa SportKlub REST API-ja.
- **Očekivani izlaz:** CSV u `data/raw/` sa kolonama `id, naslov, datum, kategorija, url`;
  u konzoli broj povučenih/sačuvanih naslova.

Spajanje + deduplikacija više povlačenja:
```bash
.venv/bin/python src/scraping/merge.py
```
→ objedinjen, deduplikovan skup u `data/raw/`.

---

## Faza 2 — Anotacija

**1) Podela na anotatore + kalibracioni skup:**
```bash
.venv/bin/python src/annotation/make_splits.py
```
→ `data/annotated/{filip,danilo}_glavna.csv` + `data/calibration/*_unakrsna.csv`.
Prvih 110 redova svakog `*_glavna.csv` su kalibracioni — anotirati ih PRVE.

**2) Ručna anotacija** (Numbers / Google Sheets) — upiši `1`/`0` u kolonu `labela`
po `annotation/guidelines.md`. Snimaj kao **UTF-8**.

**3) Međuanotatorska saglasnost (IAA):**
```bash
.venv/bin/python src/annotation/iaa.py
```
- **Očekivani izlaz (konzola + `results/faza2_iaa.txt`):**
  ```
  Kalibracionih parova: 220 / 220
  Procentualno slaganje (Po): 82.7 %
  Cohen's kappa: 0.640
  Neslaganja: 38 / 220
  ```
  + matrica konfuzije i `results/neslaganja.csv`.

**4) Finalni balansiran skup:**
```bash
.venv/bin/python src/annotation/build_dataset.py --po-klasi 1100
```
→ **`data/annotated/dataset.tsv`** (1100/1100, `naslov \t labela`) + `dataset_full.csv`.

**5) (opciono) Statistika:**
```bash
.venv/bin/python src/annotation/stats.py
```
→ `results/faza2_statistika.txt` (raspodela klasa, prosečne dužine).

---

## Faza 3a — Baseline modeli (LR + Naivni Bajes)

```bash
pip install -r requirements/requirements-baseline.txt
# (za lemma varijantu još:)  pip install classla   # + prvi put preuzme model za srpski

python src/baseline/run_baseline.py                       # podrazumevani grid
python src/baseline/run_baseline.py --normalize none stem lemma   # sve tri normalizacije
```
- **Šta radi:** 10-struka CV sa nested CV za hiperparametre; grid
  `normalize × scheme × ngram`.
- **Očekivani izlaz:** tabela u konzoli (po varijanti `F1_kb` i `AUC`) i
  **`results/baseline_results.csv`**. Najbolje: *naivni Bajes + stem + TF-IDF (1–2)*,
  F1≈0,646.
- **Trajanje:** par minuta (lemma varijanta sporija zbog classla).

> Test demo pretprocesiranja: `python src/preprocessing/serbian.py` (ispiše none/stem).

---

## Faza 3b — Enkoderski LLM (BERTić + mBERT)

> Traži **GPU (≥8GB)** — pokretati na **Google Colab** ili Azure, ne lokalno na Mac-u.
> Vidi `src/transformers/README.md` i `colab_train.py`.

```bash
pip install -r requirements/requirements-ml.txt
python src/transformers/finetune.py --model bertic --epochs 2 3 4
python src/transformers/finetune.py --model mbert  --epochs 2 3 4
python src/transformers/finetune.py --model bertic --epochs 3 --quick   # brzi test (2 fold-a)
```
- **Očekivani izlaz:** `results/encoder_bertic_results.csv`,
  `results/encoder_mbert_results.csv` (metrike po epohi/fold-u).
  Najbolje: BERTić, 3–4 epohe, F1≈0,703, ROC-AUC≈0,788.

---

## Faza 3c — Dekoderski LLM (Claude)

```bash
pip install -r requirements/requirements-decoder.txt
export ANTHROPIC_API_KEY=sk-ant-...        # ili preko .env
python src/decoder/claude_eval.py --model claude-haiku-4-5
```
- **Šta radi:** zero-shot 0/1 klasifikacija celog skupa (2200), SR i EN prompt.
- **Keš:** `results/decoder_cache/` — prekid/nastavak bez ponovnih (plaćenih) poziva.
- **Očekivani izlaz:** `results/decoder_results.csv` + log `results/claude_run.log`.
  Najviši F1 na klikbejt klasi (≈0,715), bez ROC-AUC (tvrde odluke).

---

## Faza 4 — Izveštaj (tabele, grafici, PDF)

**1) Generiši tabele i grafike iz rezultata:**
```bash
pip install -r requirements/requirements-report.txt
.venv/bin/python src/report/make_tables.py     # -> report/tables/*.tex
.venv/bin/python src/report/make_figures.py     # -> report/figures/*.png
```

**2) Kompajliraj PDF.** Lokalno (Mac) sa **tectonic** (već instaliran):
```bash
cd report
tectonic izvestaj.tex          # -> report/izvestaj.pdf
open izvestaj.pdf
```
Alternativa (klasični TeX, ako instaliraš MacTeX):
```bash
cd report
pdflatex izvestaj && bibtex izvestaj && pdflatex izvestaj && pdflatex izvestaj
```
Alternativa bez instalacije: **Overleaf** — otpremi `report/` folder, glavni fajl
`izvestaj.tex`, kompajler pdfLaTeX, *Recompile*.

- **Očekivani izlaz:** `report/izvestaj.pdf` (~10 strana).

> Posle svake izmene `.tex` fajla **moraš ponovo kompajlirati** da bi se videle u PDF-u
> — PDF se ne menja sam.

---

## Brza referenca (cheat-sheet)

| Cilj | Komanda |
|---|---|
| Aktiviraj okruženje | `source .venv/bin/activate` |
| Prikupi naslove | `.venv/bin/python src/scraping/sportklub_api.py --broj 1500` |
| IAA (kappa) | `.venv/bin/python src/annotation/iaa.py` |
| Finalni skup | `.venv/bin/python src/annotation/build_dataset.py` |
| Baseline grid | `python src/baseline/run_baseline.py --normalize none stem lemma` |
| Enkoderi (Colab/GPU) | `python src/transformers/finetune.py --model bertic --epochs 2 3 4` |
| Dekoder (Claude) | `python src/decoder/claude_eval.py --model claude-haiku-4-5` |
| Tabele/grafici | `.venv/bin/python src/report/make_tables.py && .venv/bin/python src/report/make_figures.py` |
| PDF | `cd report && tectonic izvestaj.tex && open izvestaj.pdf` |
