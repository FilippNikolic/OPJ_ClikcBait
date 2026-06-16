# Faza 4 — Dokumentacija (15p) — plan, to-do i RUNBOOK

> Dokumentacija se piše **paralelno** sa radom, ali finalni izveštaj se sklapa
> tek kad postoje rezultati Faze 3. Ovde je **sve pripremljeno unapred**: LaTeX
> skelet sa svim sekcijama + skripte koje automatski generišu tabele i grafikone
> iz `results/*.csv`. Kad Faza 3 da rezultate → pokreneš 2 skripte i prekompajliraš.

---

## Šta Faza 4 podrazumeva (iz `Projekat-zahtevi.md`)

Detaljan opis **svake faze** + **deskriptivna statistika** + **pregledne tabele
rezultata** sa analizom i diskusijom. Bodovanje: **15p** za kvalitet i potpunost.

> ❌ NE kopirati objašnjenja algoritama/tehnika iz nastavnih materijala.

Obavezne sekcije:
1. **Uvod** — zadatak, motivacija, definicija klikbejta u sportskom domenu
2. **Faza 1** — izvori, kriterijumi, scraping/RSS, čišćenje, deduplikacija
3. **Faza 2** — šema oznaka, uputstvo za anotaciju, kalibracija, **IAA (Cohen's kappa)**
4. **Deskriptivna statistika** — raspodela klasa, dužina naslova, pod-tipovi, rubrike (tabele + grafici)
5. **Faza 3** — baseline (efekti preprocessinga), enkoderski (epohe), dekoderski (SR/EN) — **uporedne tabele** + analiza i diskusija
6. **Zaključak** — šta najbolje radi, ograničenja, dalji rad

---

## Pripremljen materijal

```
report/
├── izvestaj.tex            # LaTeX skelet — SVE sekcije, srpski (latinica), kompajlira se odmah
├── references.bib          # bibliografija (BERTić, mBERT, klikbejt radovi — popuniti)
├── README.md               # kako kompajlirati (Overleaf / pdflatex) + workflow
├── tables/                 # auto-generisane LaTeX tabele (make_tables.py)
│   ├── baseline.tex        # placeholder dok nema rezultata → prepisuje skripta
│   ├── encoder.tex
│   ├── decoder.tex
│   └── poredjenje.tex      # master tabela: najbolji po tipu modela
└── figures/                # auto-generisani PNG grafici (make_figures.py)

src/report/
├── make_tables.py          # results/*.csv → report/tables/*.tex (LaTeX tabulari)
└── make_figures.py         # dataset + results → report/figures/*.png (matplotlib)

requirements-report.txt     # matplotlib (+ numpy/pandas već u .venv)
```

Skripte su otporne na nedostajuće ulaze: ako `results/*.csv` još ne postoje,
ispišu upozorenje i naprave placeholder tabele/grafike (skelet se svejedno kompajlira).

---

## To-do lista

### Piše se paralelno (može odmah, ne čeka Fazu 3)
- [ ] Uvod (zadatak, motivacija, definicija klikbejta)
- [ ] Faza 1 sekcija — prepisati iz `Faza1-plan.md` (izvori, scraping, čišćenje)
- [ ] Faza 2 sekcija — prepisati iz `Faza2-plan.md` + `annotation/guidelines.md`
- [ ] Ubaciti finalni **Cohen's kappa** (iz `iaa.py`) u Faza 2 sekciju

### Posle Faze 2 (kad postoji `dataset_full.csv` / `dataset.tsv`)
- [ ] `python src/annotation/stats.py` → deskriptivna statistika
- [ ] `python src/report/make_figures.py` → grafici (raspodela klasa, dužina naslova)

### Posle Faze 3 (kad postoje `results/*.csv`)
- [ ] `python src/report/make_tables.py` → sve LaTeX tabele rezultata
- [ ] `python src/report/make_figures.py` → grafik poređenja modela
- [ ] Napisati analizu/diskusiju 3a/3b/3c (šta i zašto najbolje radi)
- [ ] Master tabela poređenja: baseline vs BERTić vs mBERT vs ChatGPT

### Finalizacija
- [ ] Popuniti `references.bib` (BERTić, mBERT, klikbejt literatura)
- [ ] Zaključak (najbolji model, ograničenja, dalji rad)
- [ ] Kompajlirati `izvestaj.tex` → PDF, pregledati, lektorisati
- [ ] Poslati rešenje + PDF prof. Batanoviću pre ispitnog roka

---

## Napomene za doslednost sa zahtevima (obavezno u izveštaju)

Tačke gde se naš pristup razlikuje od prijave/postavke — eksplicitno obrazložiti
u dokumentaciji da se izbegnu zamerke na odbrani:

- [ ] **Jedan izvor (SportKlub) umesto tri.** Profesoru su pomenuti Mozzart, SportKlub,
  B92. Obrazložiti: postavka traži *jedan domen* (ne broj izvora); obe klase sa
  istog portala → model uči klikbejt signal, a ne stil portala. (Vidi `Faza1-plan.md`.)
- [ ] **Format TSV, ne „TXT".** Postavka kaže „UTF-8 TXT". Navesti da je `dataset.tsv`
  (`naslov⇥labela`) standardni UTF-8 tekstualni format za klasifikaciju teksta.
- [ ] **IAA „grupni prosek" sa 2 anotatora.** Navesti da sa dva člana postoji jedan
  par (Cohen's kappa), pa je grupni prosek jednak tom paru.
- [ ] **Pretprocesiranje bez stop-reči.** Po preporuci profesora koristimo
  TF/IDF/TF-IDF ponderisanje umesto izbacivanja stop-reči (navesti eksplicitno).

## RUNBOOK (kad rezultati budu gotovi)

```bash
# 1) statistika + grafici (posle Faze 2 / 3)
.venv/bin/python src/annotation/stats.py            # results/faza2_statistika.txt
.venv/bin/pip install -r requirements-report.txt    # matplotlib
.venv/bin/python src/report/make_figures.py         # report/figures/*.png

# 2) tabele rezultata (posle Faze 3)
.venv/bin/python src/report/make_tables.py          # report/tables/*.tex

# 3) kompajliranje izveštaja
#    Opcija A — Overleaf: otpremi ceo report/ folder, glavni fajl izvestaj.tex
#    Opcija B — lokalno (treba TeX distribucija):
cd report && pdflatex izvestaj.tex && bibtex izvestaj && pdflatex izvestaj.tex && pdflatex izvestaj.tex
```

### Napomene
- `izvestaj.tex` je na **srpskom (latinica)**, `babel` opcija `serbian`. Radi sa
  **pdflatex** na Overleaf-u bez dodatnog podešavanja.
- Skelet se **kompajlira odmah** (placeholder tabele/grafici postoje) — puniš ga
  postepeno, ne čekaš sve rezultate.
- Tabele/grafici se **regenerišu** pokretanjem skripti — ne diraj ručno fajlove u
  `report/tables/` i `report/figures/`, prepisuju se.
- Sve faze imaju svoj plan: `Faza1-plan.md`, `Faza2-plan.md`, `Faza3-plan.md` —
  sekcije izveštaja se najvećim delom prepisuju odatle.
```
