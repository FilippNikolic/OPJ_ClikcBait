# Faza 2 — Anotacija podataka (25p) — plan izrade

> Ulaz: `data/interim/headlines.csv` (2994 SportKlub naslova).
> Izlaz: anotiran skup + IAA izveštaj (Cohen's kappa), balansiran na ~1100/1100.
> Anotatori: Filip, Danilo. Oba rade **sve** (uslov projekta).

---

## Pregled koraka

| # | Korak | Ko | Status |
|---|---|---|---|
| 0 | Uputstvo `annotation/guidelines.md` | zajedno | ✅ napisano |
| 1 | Priprema datoteka (`make_splits.py`) | skripta | ✅ urađeno |
| 2 | **Kalibracija** — 220 naslova, NEZAVISNO | Filip + Danilo | ▶️ ti si ovde |
| 3 | IAA — Cohen's kappa (`iaa.py`) | skripta | ⏳ |
| 4 | Revizija uputstva (ako kappa nizak) | zajedno | ⏳ |
| 5 | **Glavna anotacija** — po pola | Filip + Danilo | ⏳ |
| 6 | Spajanje + balans 1100/1100 | skripta | ⏳ |
| 7 | Deskriptivna statistika | skripta | ⏳ |

---

## GDE radiš klasifikaciju (ovo te zanima)

Datoteke su već napravljene. Otvaraš ih u **tabelarnom programu** i popunjavaš kolonu `labela`.

Skup je podeljen **50/50** — svaki član poseduje **1497 naslova** (tačno pola).
Kalibracija za kappa = 220 naslova (110 iz svake polovine), unakrsno anotirani.

### Tvoje datoteke (Filip)
| Datoteka | Broj | Šta je |
|---|---|---|
| `data/annotated/filip_glavna.csv` | 1497 | tvoja polovina; **prvih 110 redova su kalibracioni** (anotiraj ih prvo) |
| `data/calibration/filip_unakrsna.csv` | 110 | Danilovih kalibracionih naslova — ti ih anotiraš (za kappa) |

*(Danilo ima `danilo_glavna.csv` (1497) + `danilo_unakrsna.csv` (110).)*

> Tako ti poseduješ **1497** (pola skupa), a 220 naslova (110 tvojih + 110 Danilovih)
> ima po dve nezavisne anotacije → Cohen's kappa.

### Čime otvoriti — preporuka (Mac)
1. **Numbers** (najlakše na Mac-u): dvoklik na `.csv` → otvori se kao tabela. Popuni kolonu `labela`. Kad završiš: **File → Export To → CSV…**, i prebriši isti fajl (UTF-8). Diakritika (č ć ž š đ) radi.
2. **Google Sheets** (dobro za rad sa bilo gde): File → Import → Upload `.csv` → „Replace spreadsheet". Po želji dodaj *Data validation* na kolonu `labela` (dropdown 0/1). Na kraju: File → Download → CSV.
3. **Excel** takođe radi — fajlovi su sačuvani sa BOM-om pa se diakritika ispravno učita.

### Kolone u datoteci
| Kolona | Šta radiš |
|---|---|
| `id`, `naslov` | **ne diraj** |
| `labela` | upiši `1` (klikbejt) ili `0` (regularan) — **obavezno** |
| `podtip` | opciono, samo za `1`: `KJ` / `PV` / `EN` / `SF` (može više: `PV,EN`) |
| `napomena` | opciono, kratko obrazloženje za granične slučajeve |

> Pravila i definicije su u **`annotation/guidelines.md`** — drži ga otvoreno sa strane dok anotiraš.

---

## Korak 2 — Kalibracija (220 naslova, radi se PRVO)

- Cilj: proveriti slažemo li se po uputstvu **pre** nego što anotiramo svih ~3000.
- Filip anotira: **prvih 110 redova `filip_glavna.csv`** + ceo `filip_unakrsna.csv` (110).
- Danilo anotira: **prvih 110 redova `danilo_glavna.csv`** + ceo `danilo_unakrsna.csv` (110).
- Radi se **nezavisno** (bez dogovaranja!). Time je svaki od 220 kalibracionih
  naslova anotiran od oba člana → može se računati kappa.

## Korak 3 — IAA (Cohen's kappa)

Kad oba završite kalibracioni deo:
```bash
.venv/bin/python src/annotation/iaa.py
```
Ispisuje procentualno slaganje, **Cohen's kappa** i listu neslaganja.

- **kappa ≥ 0.6** (dobro) → nastavljamo na glavnu anotaciju.
- **kappa < 0.6** → zajedno pregledamo neslaganja, doradimo `guidelines.md`, po potrebi ponovimo kalibraciju na novom uzorku.

## Korak 5 — Glavna anotacija

- Svaki član dovrši **ostatak svoje polovine** (`*_glavna.csv`, redovi posle prvih 110).
- Sporne slučajeve označiš u `napomena` → rešavamo zajednički.

## Korak 6 — Spajanje + balans

- Spojimo obe glavne polovine (`filip_glavna` + `danilo_glavna` = 2994). Za 220
  kalibracionih naslova koristimo **usaglašenu** labelu (posle pregleda neslaganja).
- Balans na **1100 klikbejt + 1100 regularnih = 2200**. Ako klikbejt klase manjka → ciljano doskupljamo sa SportKluba (API ima ~449k članaka).
- Izlaz: `data/annotated/dataset.tsv` (`naslov \t labela`) — standardni format za Fazu 3.

## Korak 7 — Deskriptivna statistika

Raspodela klasa, dužina naslova po klasi, učestalost pod-tipova (KJ/PV/EN/SF), izvori/rubrike po klasi → ide u dokumentaciju (Faza 4).

---

## Reproducibilnost
- `make_splits.py` koristi fiksni seed (42) → svako dobije isti raspored.
- Sve datoteke UTF-8 (sa BOM radi Excel/Numbers). `iaa.py` čita nazad sa `utf-8-sig`.
