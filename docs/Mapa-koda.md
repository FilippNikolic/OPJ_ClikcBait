# Mapa koda — gde se šta radi u projektu

> Vodič kroz izvorni kod projekta *Detekcija klikbejt naslova u sportskim vestima*.
> Prati tok podataka kroz četiri faze i za svaki korak kaže **koji fajl** to radi,
> **šta** radi i **šta proizvodi**. Komande za pokretanje su u
> [`docs/Komande.md`](./Komande.md).

## Tok podataka na jednom mestu

```
Faza 1: scraping ─► data/raw/*.csv
Faza 2: anotacija ─► data/annotated/dataset.tsv (1100/1100)  + IAA (κ)
Faza 3: modeli    ─► results/*.csv  (baseline / enkoder / dekoder)
Faza 4: izveštaj  ─► report/tables/*.tex + figures/*.png ─► izvestaj.pdf
```

## Struktura direktorijuma

| Folder | Sadržaj |
|---|---|
| `src/` | sav izvorni kod (Python), podeljen po fazama |
| `data/` | `raw/` sirovi naslovi, `calibration/` kalibracioni skup, `annotated/` finalni skup |
| `results/` | izlazi modela (`*.csv`), logovi, IAA izveštaji, keš dekodera |
| `report/` | LaTeX izveštaj (`izvestaj.tex`), generisane tabele i grafici |
| `docs/` | dokumentacija (ovaj fajl, opis obrade teksta, komande, zahtevi) |
| `plans/` | planovi po fazama (runbook-ovi) |
| `annotation/` | `guidelines.md` — uputstvo za anotaciju |
| `requirements/` | `requirements-*.txt` — zavisnosti razdvojene po fazi |

---

## Faza 1 — Prikupljanje podataka (`src/scraping/`)

| Fajl | Uloga |
|---|---|
| **`sportklub_api.py`** | **Glavni skraper.** Povlači naslove sa SportKlub WordPress REST API-ja (`/wp-json/wp/v2/posts`, arhiva ~449k članaka). Beleži `id`, naslov, datum, kategoriju, URL. |
| `common.py` | Zajedničke pomoćne stvari: `Headline` struktura, `HEADERS`, `save_csv`, putanje (`DATA_RAW`). |
| `merge.py` | Spaja i deduplikuje sirove naslove iz više povlačenja (egzaktna + približna deduplikacija). |
| `rss_scraper.py` | Alternativni izvor preko RSS-a (rezerva). |
| `mozzart_bulk.py` | Skraper za Mozzart (napušten — radimo samo SportKlub). |

**Izlaz:** sirovi CSV-ovi u `data/raw/` (višak od ~3000–4000 naslova radi kasnijeg balansiranja).

---

## Faza 2 — Anotacija (`src/annotation/`)

Redosled korišćenja skripti:

| # | Fajl | Šta radi | Izlaz |
|---|---|---|---|
| 1 | **`make_splits.py`** | Deli skup (2994) tačno na pola (Filip/Danilo, seed 42) i izdvaja 220 kalibracionih naslova koje anotiraju **oba** člana (unakrsno). | `data/annotated/*_glavna.csv`, `data/calibration/*_unakrsna.csv` |
| 2 | *(ručna anotacija)* | Oba člana nezavisno upisuju `labela` (1/0) po uputstvu `annotation/guidelines.md`. | popunjeni CSV-ovi |
| 3 | **`iaa.py`** | **Međuanotatorska saglasnost.** Računa procentualno slaganje, **Cohen's kappa**, matricu konfuzije i listu neslaganja nad 220 kalibracionih. | `results/faza2_iaa.txt`, `results/neslaganja.csv` |
| 4 | `reconcile_iaa.py` | Pomaže pri adjudikaciji spornih naslova (predlozi za usaglašavanje). | `results/poredjenje_*.csv` |
| 5 | **`build_dataset.py`** | Spaja anotirane polovine, **balansira** na 1100/1100 (seed 42) i izvozi finalni skup. | **`data/annotated/dataset.tsv`** (ulaz za Fazu 3), `dataset_full.csv` |
| 6 | `stats.py` | Deskriptivna statistika finalnih oznaka (raspodela klasa, dužine). | `results/faza2_statistika.txt` |

**Ključni izlaz Faze 2:** `data/annotated/dataset.tsv` — balansiran skup `naslov \t labela`.

> Šema oznaka i pravila su u `annotation/guidelines.md`; analiza saglasnosti u
> `results/faza2_iaa_izvestaj.md`.

---

## Pretprocesiranje teksta (`src/preprocessing/serbian.py`)

**Ovde se rade tokenizacija, stemovanje i lematizacija.** Koristi ga Faza 3a (baseline).
Detaljno objašnjenje tehnika: [`docs/Obrada-teksta.md`](./Obrada-teksta.md).

| Funkcija | Šta radi |
|---|---|
| `basic_normalize(text)` | NFC + transliteracija ćirilice → latinica + lowercase. |
| `tokenize(text, strip_punct)` | **Tokenizacija** regularnim izrazom (slova sa dijakriticima + cifre; interpunkcija = razdvajač). |
| `stem(token)` | **Stemovanje** — heuristički suffix-stripping (greedy longest-match, bez zavisnosti, min. 3 slova osnove). |
| `lemmatize_text(text)` | **Lematizacija** — `classla` pipeline (`tokenize,pos,lemma`) za srpski; morfološki ispravna lema. |
| `make_preprocessor(normalize=...)` | Fabrika: vraća `str→str` funkciju za `normalize ∈ {none, stem, lemma}`. |
| `preprocess_corpus(texts, ...)` | Pretprocesira ceo korpus odjednom (batch za `lemma`). |

Pokretanjem fajla direktno (`python src/preprocessing/serbian.py`) dobija se mini-demo
koji ispiše `none` i `stem` varijantu za par primera.

---

## Faza 3a — Osnovni (baseline) modeli (`src/baseline/`)

| Fajl | Uloga |
|---|---|
| **`run_baseline.py`** | **Glavni grid.** Logistička regresija + Multinomijalni naivni Bajes, **10-struka stratifikovana CV** sa **ugnežđenom (nested) CV** za hiperparametre. Vrti grid: `normalize` (none/stem/lemma) × `scheme` (bow/tf/idf/tfidf) × `ngram` (1-1/1-2). |
| `common.py` | Učitavanje `dataset.tsv`, metrike (accuracy, P/R/F1 za klikbejt, macro-F1, ROC-AUC). |
Vektorizacija (`scikit-learn`): preprocesor iz `serbian.py` daje tokenizovan tekst,
a `CountVectorizer`/`TfidfVectorizer` (sa `token_pattern=\S+`, `min_df=2`) gradi
obeležja **unutar svakog fold-a** (bez curenja informacija).

**Izlaz:** `results/baseline_results.csv` (sve varijante grida sa metrikama).
**Najbolja varijanta:** naivni Bajes + stemovanje + TF-IDF (1–2 grami).

---

## Faza 3b — Enkoderski LLM (`src/transformers/`)

| Fajl | Uloga |
|---|---|
| **`finetune.py`** | **Fine-tuning** dva enkodera preko HuggingFace `Trainer`: **BERTić** (`classla/bcms-bertic`, monolingvalni) i **mBERT** (`bert-base-multilingual-cased`, višejezični). 10-struka CV, variranje epoha (2/3/4). |
| `colab_train.py` | Verzija za Google Colab / GPU (BERTić/mBERT traže ≥8GB GPU). |

**Izlaz:** `results/encoder_bertic_results.csv`, `results/encoder_mbert_results.csv`.
**Zaključak:** BERTić > mBERT; 3–4 epohe najbolje (F1 0,703, ROC-AUC 0,788).

---

## Faza 3c — Dekoderski LLM (`src/decoder/`)

| Fajl | Uloga |
|---|---|
| **`claude_eval.py`** | **Glavna evaluacija dekodera.** Anthropic Claude (Haiku), **zero-shot** nad celim skupom (2200). Keš u `results/decoder_cache/` (prekid/nastavak bez ponovnih poziva). |
| **`prompts.py`** | Prompt varijante: jezik (SR/EN), zero/few-shot, sa/bez definicije klikbejta. Definicije izvučene iz `guidelines.md`. |
| `gemini_eval.py` | Alternativa preko Google Gemini-ja (free rate-limit). |
| `chatgpt_eval.py` | Alternativa preko OpenAI ChatGPT-a. |

**Ključ:** `ANTHROPIC_API_KEY` (u `.env`). **Izlaz:** `results/decoder_results.csv`,
log `results/claude_run.log`.
**Zaključak:** najviši F1 na klikbejt klasi u celom radu (0,715), ali samo tvrde 0/1 odluke (bez ROC-AUC).

---

## Faza 4 — Izveštaj (`src/report/` + `report/`)

| Fajl | Uloga | Izlaz |
|---|---|---|
| **`src/report/make_tables.py`** | Čita `results/*.csv` i piše `booktabs` LaTeX tabele. | `report/tables/{baseline,encoder,decoder,poredjenje}.tex` |
| **`src/report/make_figures.py`** | Pravi PNG grafike (raspodela klasa, dužina naslova, poređenje modela). | `report/figures/*.png` |
| **`report/izvestaj.tex`** | Glavni LaTeX izveštaj; `\input`-uje tabele, `\includegraphics` grafike. | `report/izvestaj.pdf` |
| `report/references.bib` | Bibliografija (BERTić, mBERT, scikit-learn, classla, Claude…). | — |

Tabele/grafici su otporni na nedostajuće ulaze: ako CSV ne postoji, pišu placeholder
da bi se skelet izveštaja svejedno kompajlirao.

---

## Pomoćni materijali

| Putanja | Sadržaj |
|---|---|
| `plans/Faza{1..4}-plan.md` | Detaljan runbook svake faze (koraci, odluke). |
| `docs/Obrada-teksta.md` | Objašnjenje tokenizacije/stemovanja/lematizacije. |
| `docs/Komande.md` | Sve komande za pokretanje + očekivani izlaz. |
| `docs/Tehnicki-vodic.md` | Tehnički vodič kroz projekat. |
| `results/faza3_sinteza.md` | Sinteza rezultata sve tri grupe modela. |
| `requirements/requirements-*.txt` | Zavisnosti razdvojene po fazi (baseline/ml/decoder/report). |
