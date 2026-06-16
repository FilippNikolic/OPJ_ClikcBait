# Faza 2 — Izveštaj o međuanotatorskoj saglasnosti (IAA)

> Kalibracioni skup: **220 naslova** (110 Filipovih + 110 Danilovih), svaki nezavisno
> anotiran od oba člana. Mera: Cohen's kappa (za 2 anotatora). Sve vrednosti se
> reprodukuju sa `python src/annotation/iaa.py` nad aktuelnim fajlovima u `data/`.

## 1. Rezultat

| Mera | Vrednost |
|---|---|
| Kalibracionih parova | 220 / 220 |
| Procentualno slaganje (Po) | **82.7 %** (182/220) |
| **Cohen's kappa** | **0.640** (dobro / *good*) |
| Neslaganja | 38 / 220 (17.3 %) |

Interna ciljana granica iz plana je **κ ≥ 0.6** → **ispunjena**.

## 2. Matrica konfuzije (Filip × Danilo)

|  | Danilo = 0 | Danilo = 1 | Σ Filip |
|---|---|---|---|
| **Filip = 0** | 114 | 13 | 127 |
| **Filip = 1** | **25** | 68 | 93 |
| **Σ Danilo** | 139 | 81 | 220 |

- Oba „klikbejt": 68 · Oba „regularan": 114 · Neslaganja: 38
- **Filip = 1 / Danilo = 0: 25** · Filip = 0 / Danilo = 1: 13

## 3. Analiza — preostala razlika u pragu (suptilni slučajevi)

- Filip označava **93/220 (42 %)** naslova kao klikbejt, Danilo **81/220 (37 %)**.
- **66 % neslaganja (25/38) je u istom smeru**: Filip = klikbejt, Danilo = ne.
- Razlika je **umerena i dosledna**: Filip kao klikbejt računa i blaži
  senzacionalizam / emotivni naboj, dok Danilo zahteva jaču manipulaciju
  (uskraćivanje ključne informacije, preuveličavanje). Ovaj jednosmerni pomeraj je
  tipičan za semantičke (a ne površinske) granice i ne obara κ ispod praga.

## 4. Tipični preostali sporni naslovi (Filip=1 / Danilo=0)

- „**Sedmica za istoriju**: Nemačka na vrhu preskočila Brazil" — emotivni naboj
- „Branko Lazić **otkrio**: Čuo sam da me je Dule baš želeo u Partizanu" — najava otkrića
- „Janik Siner **šokantno** ispao sa Rolan Garosa! Pozlilo mu je…" — senzacionalni ton
- „(VIDEO) Nije samo majstor za asistencije: **Kakva golčina Bruna!**" — emotivni epitet

→ Sve su to **granični „suptilni" slučajevi**: jezik je pomalo senzacionalan, ali bez
tvrde manipulacije. Tu se prag dvojice anotatora i dalje neznatno razilazi.

## 5. Operativno pravilo za suptilni klikbejt (u `guidelines.md`)

1. **Teaser / radoznalost (KJ)** je klikbejt **samo ako naslov namerno uskraćuje
   ključnu informaciju** koja se mogla navesti („Otkrio…", „Ovo niko nije očekivao").
   Ako je informacija prisutna → regularan.
2. **Emotivni/senzacionalni epiteti** („za istoriju", „šok", „golčina") **sami po sebi
   nisu dovoljni** — moraju biti praćeni preuveličavanjem ili uskraćivanjem.
3. Granični primeri iz tačke 4 služe kao referentni rešeni slučajevi.

## 6. Tretman neslaganja u finalnom skupu

38 spornih (preklapajućih) naslova rešava se **adjudikacijom** — usaglašena labela ide
u `data/annotated/dataset_full.csv` / `dataset.tsv`. Cohen's kappa (0.640) prijavljuje
se kao mera **nezavisne** saglasnosti, pre adjudikacije.

## 7. Artefakti

- `results/faza2_iaa.txt` — sažeti IAA izlaz (matrica + κ)
- `results/faza2_iaa_izvestaj.md` — ovaj izveštaj
- `results/faza2_statistika.txt` — deskriptivna statistika finalnih oznaka
- `data/annotated/dataset.tsv` — balansiran skup (1100/1100), ulaz za Fazu 3
