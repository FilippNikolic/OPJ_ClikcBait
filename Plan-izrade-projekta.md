# Plan izrade projekta — Detekcija klikbejt naslova (sportske vesti)

> Detaljan plan rada zasnovan na dogovoru sa prof. Vukom Batanovićem (`Prof conversation.rtf`) i zahtevima iz `Projekat-zahtevi.md`.
> **Status:** ✅ **ODOBRENO** — profesor je potvrdio plan ("Sve dogovoreno"). Možemo krenuti sa prikupljanjem podataka.
> Jedina finalna izmena: u preprocesiranju **umesto uklanjanja stop-reči** razmotriti **TF/IDF/TF-IDF ponderisanje**.

---

## 0. Sažetak dogovora (ono što je usaglašeno)

| Stavka | Dogovoreno |
|---|---|
| **Tim** | Filip Nikolić (25/3234), Danilo Nikolić (25/3235) — par (odobreno) |
| **Zadatak** | Detekcija klikbejt naslova — **binarna klasifikacija** (klikbejt / regularan) |
| **Domen** | **Sportske vesti** — izvor **samo SportKlub** (Mozzart i B92 odbačeni; vidi napomenu u Fazi 1) |
| **Definicija klikbejta** | Očigledne fraze **+** suptilne manipulacije: kognitivni jaz (izostavljanje ključnih info), preuveličavanje važnosti, veštački emocionalni naboj |
| **Veličina skupa** | **2200 jedinstvenih naslova** = 1100 klikbejt + 1100 regularnih (balansirano) |
| **Kalibracija** | 10% (~220 naslova) izdvojeno, anotiraju oba člana nezavisno |
| **Baseline modeli** | **Logistička regresija + Naivni Bajes** (SVM zamenjen NB-om po preporuci) |
| **Preprocessing** | lowercasing, uklanjanje interpunkcije, lematizacija/stemovanje + **TF/IDF/TF-IDF ponderisanje** (umesto stop-reči — preporuka profesora) |
| **Enkoderski LLM** | **BERTić** (mono) + **mBERT** (multi) — fine-tuning |
| **Dekoderski LLM** | **samo ChatGPT** — poređenje SR vs EN promptova |

> ⚠️ Profesorova napomena: par je dozvoljen ali je obim posla teži. Oba člana rade **sve faze** (uslov projekta).

---

## 1. Pregled radnih paketa i rokovi

| # | Faza | Poeni | Procena trajanja | Ključni izlaz |
|---|---|---|---|---|
| 1 | Prikupljanje podataka | 25 | ~1.5 nedelje | `data/raw/` korpus 2200+ naslova + metapodaci |
| 2 | Anotacija podataka | 25 | ~2 nedelje | `data/annotated/` + IAA izveštaj |
| 3a | Baseline modeli | 20 | ~1 nedelja | rezultati LR + NB (10-fold, nested CV) |
| 3b | Enkoderski LLM | 20 (deli sa 3a) | ~1.5 nedelje | BERTić + mBERT rezultati |
| 3c | Dekoderski LLM | (deo Faze 3) | ~0.5 nedelje | ChatGPT SR vs EN |
| 4 | Dokumentacija | 15 | paralelno + ~1 nedelja | finalni izveštaj (PDF) |

> Rokovi sa fakulteta: prijava grupe do **01.08.2026**; rešenje + dokumentacija **do početka ispitnog roka** u kom se brani.

---

## 2. Predložena struktura repozitorijuma

```
OPJ/
├── data/
│   ├── raw/                  # sirovi prikupljeni naslovi (UTF-8 TXT)
│   ├── interim/              # posle deduplikacije/čišćenja
│   ├── calibration/          # ~220 naslova, anotacija oba člana zasebno
│   │   ├── filip.tsv
│   │   └── danilo.tsv
│   ├── annotated/            # finalni anotiran skup (2200)
│   └── metadata.csv          # url/id izvora, datum, sajt, anotator, labela
├── annotation/
│   └── guidelines.md         # uputstvo za anotaciju (definicije + granični slučajevi)
├── src/
│   ├── scraping/             # skraperi + RSS parseri
│   ├── preprocessing/        # normalizacija, stop-reči, lematizacija
│   ├── baseline/             # LR + NB, nested 10-fold CV
│   ├── transformers/         # fine-tuning BERTić, mBERT
│   └── decoder/              # ChatGPT prompt eval (SR/EN)
├── results/                  # tabele, metrike, grafici
├── report/                   # projektna dokumentacija
├── Projekat-zahtevi.md
└── Plan-izrade-projekta.md
```

---

## FAZA 1 — Prikupljanje podataka (25p)

**Cilj:** 2200 jedinstvenih sportskih naslova spremnih za anotaciju.

### 1.1 Izvor
- **SportKlub** (`sportklub.n1info.rs`) — **jedini izvor**. Mozzart i B92 odbačeni.
- Metod: **WordPress REST API** (~449k članaka; naslov/URL/datum/rubrika bez HTML parsiranja).
- **Obrazloženje jednog izvora:** obe klase (klikbejt + regularan) dolaze sa istog
  portala → model uči stvarni klikbejt signal, a ne stil portala. (Izmena u odnosu
  na prijavu profesoru gde su pomenuta tri izvora — vidi napomenu u `Faza1-plan.md`.)

### 1.2 Šta skupljati
- Za svaki naslov beležiti: **tekst naslova**, **URL članka**, **sajt/izvor**, **datum**, **rubrika** (ako dostupna).
- Skupiti **višak** (npr. 3000–4000) jer se kasnije odbacuje za balans i kvalitet.

### 1.3 Čišćenje
- Uklanjanje **duplikata** (egzaktnih i near-duplicate — npr. isti naslov sa više portala).
- Uklanjanje praznih/oštećenih unosa, čisto promo/oglasnih naslova ako se ne smatraju vestima.
- Normalizacija encoding-a → **UTF-8**.

### 1.4 Balansiranje
- Cilj: **1100 klikbejt + 1100 regularnih** = 2200.
- Napomena: balans se finalizuje **posle anotacije** (labela se ne zna unapred) — zato skupiti višak i po potrebi dodatno prikupiti naslove kandidate za manje zastupljenu klasu.

### 1.5 Format izlaza
- Naslovi kao **UTF-8 TXT** (ili TSV/CSV pogodan za klasifikaciju).
- `metadata.csv` sa **URL/ID izvora** za svaki naslov (zahtev iz postavke).

### ✅ Checklist
- [ ] Skraperi/RSS parseri za sva 3 izvora
- [ ] Prikupljen višak naslova (3000+)
- [ ] Deduplikacija (egzaktna + near-duplicate)
- [ ] UTF-8 čuvanje + `metadata.csv` sa URL/izvorom
- [ ] Dogovoren min. broj sa predavačem potvrđen (2200)

---

## FAZA 2 — Anotacija podataka (25p)

**Cilj:** ručno obeležiti svaki naslov (klikbejt = 1 / regularan = 0) po jasnoj šemi.

### 2.1 Šema oznaka
- Binarna: `1 = klikbejt`, `0 = regularan`.
- (Opciono za analizu) pod-tipovi klikbejta kao pomoćne oznake: *kognitivni jaz, preuveličavanje, emocionalni naboj, senzacionalistička fraza* — korisno za diskusiju, čak i ako se finalni model uči binarno.

### 2.2 Uputstvo za anotaciju (`annotation/guidelines.md`)
Mora sadržati (zahtev profesora — klikbejt NIJE samo uzvičnik/fraza):
- **Jasna definicija klikbejta** kroz mehanizme manipulacije:
  - namerno **izostavljanje ključnih informacija** radi kognitivnog jaza;
  - **preuveličavanje** važnosti događaja;
  - **veštačko stvaranje emocionalnog naboja**;
  - očigledne forme (uzvičnici, „Nećete verovati…", „a onda se desilo ovo").
- **Granični slučajevi** i kako ih rešavati (npr. legitimno uzbudljiv sportski rezultat vs. lažna napetost).
- Primeri **za** i **protiv** svake kategorije.

### 2.3 Kalibracija (~10% = ~220 naslova)
- Oba člana anotiraju **isti** kalibracioni skup **nezavisno**, bez konsultacija.
- Čuva se **zasebno** (`calibration/filip.tsv`, `calibration/danilo.tsv`) u **istom formatu**.
- Ako je slaganje slabo → revizija uputstva/oznaka → ponovna kalibracija.

### 2.4 Merenje saglasnosti (IAA)
- Pošto su 2 anotatora: **Cohen's kappa** + procentualno slaganje (postavka traži par-saglasnost i grupni prosek; sa 2 člana to je jedan par).
- Diskusija neslaganja → finalizacija uputstva.

### 2.5 Glavna anotacija
- Preostalih ~1980 naslova **ravnomerno** podeljeno (svako ~pola).
- Jednostruka anotacija (dovoljno po postavci); sporne slučajeve rešavati zajedničkim pregledom.

### 2.6 Analiza
- Statistika finalnog skupa: raspodela klasa, dužina naslova po klasi, učestalost mehanizama, izvori po klasi.

### 2.7 Format izlaza
- Finalni anotiran skup: **UTF-8 TXT/TSV**, standardni format za klasifikaciju (`naslov \t labela`).

### ✅ Checklist
- [ ] Napisano `guidelines.md` (definicije + granični slučajevi + primeri)
- [ ] Kalibracioni skup (~220) anotiran nezavisno od oba člana
- [ ] Izračunat Cohen's kappa + % slaganje
- [ ] Revizija uputstva po potrebi
- [ ] Glavna anotacija završena (balans ~1100/1100)
- [ ] Deskriptivna statistika skupa
- [ ] Kalibracioni i glavni skup sačuvani zasebno (isti format, UTF-8)

---

## FAZA 3 — Obučavanje i evaluacija modela (40p)

### 3a. Baseline modeli — Logistička regresija + Naivni Bajes (20p)

#### Preprocessing (testirati efekte — zahtev profesora)
Varijante koje poredimo:
- **lowercasing** (normalizacija na mala slova),
- **uklanjanje interpunkcije**,
- **lematizacija ili stemovanje** (za srpski — npr. classla/stanza ili stemmer).

> ⚠️ Profesor je eksplicitno preporučio da se **umesto uklanjanja stop-reči**
> razmotri **TF / IDF / TF-IDF ponderisanje** (vidi sledeću sekciju). Stop-reči
> NE uvrštavamo kao preprocessing varijantu.

#### Reprezentacija odlika (TF/IDF/TF-IDF — naglašeno od strane profesora)
- **BoW / TF / IDF / TF-IDF** — uporediti efekte različitih ponderisanja,
- n-grami (uni/bigram) kao dodatna varijanta.

#### Validacija
- **10-slojna stratifikovana unakrsna validacija**.
- **Ugnežđena (nested) CV** za hiperparametre:
  - LR: jačina regularizacije `C`;
  - NB: `alpha` (Laplace smoothing), tip (Multinomial/Bernoulli).

#### Metrike
- Accuracy, **Precision/Recall/F1** (binarno, fokus na klikbejt klasu), po potrebi ROC-AUC.

#### ✅ Checklist
- [ ] Implementiran preprocessing pipeline (sve varijante uključuju/isključuju)
- [ ] TF/IDF/TFIDF feature varijante
- [ ] LR + NB sa nested 10-fold CV
- [ ] Tabela: efekat svake preprocessing varijante

---

### 3b. Enkoderski LLM — BERTić + mBERT (deo 20p)

- **BERTić** (monolingvalni, srpski/HBS) + **mBERT** (multilingvalni) — zahtev: bar 1 mono + 1 multi.
- Biblioteka: **Huggingface Transformers** (ili Simple Transformers).
- **Fine-tuning** za binarnu klasifikaciju.
- **10-slojna stratifikovana CV**.
- Evaluacija **varijanti po broju epoha** (npr. 2/3/4 epohe) — zahtev postavke.
- **GPU** potreban (≥8 GB) → **Google Colab** ili **MS Azure studentski krediti**.
- Iste metrike kao baseline radi poređenja.

#### ✅ Checklist
- [ ] Fine-tuning skripta (HF Trainer)
- [ ] BERTić: 10-fold CV + varijante epoha
- [ ] mBERT: 10-fold CV + varijante epoha
- [ ] Tabela poređenja mono vs multi vs baseline

---

### 3c. Dekoderski LLM — ChatGPT (deo 20p)

- **Samo ChatGPT** (po dogovoru — jedan dekoderski dovoljan).
- Bez fine-tuninga → **evaluacija na celom skupu podataka**.
- Eksperimenti:
  - **prompt engineering** (zero-shot, few-shot, sa/bez definicije klikbejta),
  - **jezik prompta: srpski vs engleski** (uporediti efekat).
- Metrike iste; diskusija o ceni/limitima API-ja.

#### ✅ Checklist
- [ ] Definisane prompt varijante (zero/few-shot, SR/EN)
- [ ] Evaluacija na celom skupu
- [ ] Tabela: SR vs EN, zero vs few-shot

---

## FAZA 4 — Dokumentacija (15p)

Struktura izveštaja:
1. **Uvod** — zadatak, motivacija, definicija klikbejta u sportskom domenu.
2. **Faza 1** — izvori, kriterijumi, tehnika scraping/RSS, čišćenje, deduplikacija.
3. **Faza 2** — šema oznaka, **uputstvo za anotaciju**, kalibracija, **IAA (kappa)**, tehnika anotacije.
4. **Deskriptivna statistika** prikupljenih i anotiranih podataka (tabele/grafici).
5. **Faza 3** — baseline (preprocessing efekti), enkoderski (epohe), dekoderski (SR/EN) — **pregledne tabele rezultata** + analiza i diskusija.
6. **Zaključak** — šta je najbolje radilo, ograničenja, dalji rad.

> ❌ Ne kopirati objašnjenja algoritama iz nastavnih materijala.

---

## 3. Podela posla (oba člana rade SVE faze)

> Postavka zabranjuje podelu po fazama. Podela je samo na **paralelne taskove unutar iste faze**, ravnomerno.

| Aktivnost | Filip | Danilo |
|---|---|---|
| Prikupljanje (SportKlub API) | zajednički | zajednički |
| Anotacija (glavna) | ~pola naslova | ~pola naslova |
| Kalibracija | nezavisno ceo skup | nezavisno ceo skup |
| Baseline | LR | NB |
| Enkoderski | BERTić | mBERT |
| Dekoderski ChatGPT | prompt dizajn | evaluacija/skor |
| Dokumentacija | naizmenično po sekcijama | naizmenično po sekcijama |

*(Podela je orijentaciona — oba člana učestvuju i razumeju ceo pipeline.)*

---

## 4. Sledeći konkretni koraci

1. ✅ Profesor odobrio — krećemo sa prikupljanjem.
2. ✅ Postavljena repo struktura + Python okruženje + skraperi (vidi `src/scraping/`).
3. ✅ Puni run prikupljanja: SportKlub (WP REST API) → 2994 naslova u `data/interim/headlines.csv`.
4. Paralelno: prvi nacrt `annotation/guidelines.md` (kritično — definiše ceo zadatak).
5. Mini-pilot: anotirati 30–50 naslova da se uputstvo testira pre prave kalibracije.

> Izvor: **samo SportKlub** (Mozzart i B92 odbačeni). Vidi `Faza1-plan.md` za obrazloženje.
