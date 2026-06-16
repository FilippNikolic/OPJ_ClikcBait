# Faza 2 — Izveštaj o međuanotatorskoj saglasnosti (IAA)

> Kalibracioni skup: **220 naslova** (110 Filipovih + 110 Danilovih), svaki nezavisno
> anotiran od oba člana. Mera: Cohen's kappa (za 2 anotatora = i parni i grupni prosek).

## 1. Rezultat

| Mera | Vrednost |
|---|---|
| Kalibracionih parova | 220 / 220 |
| Procentualno slaganje (Po) | **64.5 %** |
| **Cohen's kappa** | **0.322** (slabo / *fair*) |
| Neslaganja | 78 / 220 (35.5 %) |

Interna ciljana granica iz plana je **κ ≥ 0.6** → trenutno **NIJE dostignuta**.

## 2. Matrica konfuzije (Filip × Danilo)

|  | Danilo = 0 | Danilo = 1 |
|---|---|---|
| **Filip = 0** | 76 | 15 |
| **Filip = 1** | **63** | 66 |

- Oba „klikbejt": 66 · Oba „regularan": 76 · Neslaganja: 78
- **Filip = 1 / Danilo = 0: 63** · Filip = 0 / Danilo = 1: 15

## 3. Korenski uzrok — sistematska razlika u pragu (NIJE šum)

- Filip označava **129/220 (59 %)** naslova kao klikbejt, Danilo **81/220 (37 %)**.
- **81 % svih neslaganja (63/78) je u istom smeru**: Filip = klikbejt, Danilo = ne.
- Zaključak: ne radi se o slučajnim greškama, već o **doslednom pomeraju granice** —
  Filip kao klikbejt računa i **blagu senzaciju / teaser / emotivni naboj**, dok Danilo
  zahteva **jaču manipulaciju** (izostavljanje ključne informacije, preuveličavanje).
- Ovakav jednosmerni bias **veštački obara kappa** (kappa kažnjava sistematsku razliku),
  ali je upravo zato **rešiv preciziranjem uputstva** — bez diranja postojećih labela.

## 4. Gde se najviše razilazimo (po rubrici)

| Neslaganja / ukupno | Rubrika |
|---|---|
| 10 / 26 | SP u fudbalu |
| 8 / 27 | Roland Garros |
| 6 / 20 | Euroleague |
| 6 / 17 | Superliga Srbije |
| 6 / 18 | ABA liga |
| 5 / 11 | Premier League |

Dužina naslova ne razlikuje sporne od složnih (≈54 vs ≈53 karaktera) → granica je
**semantička (ton/implikacija), ne površinska (dužina/interpunkcija)**. To je u skladu
sa zahtevom prof. Batanovića da task ne sme da se svede na površne signale.

## 5. Tipični sporni naslovi (Filip=1 / Danilo=0)

- „Ferari poslao **jaku poruku** u Monte Karlu" — blagi senzacionalizam
- „**Sedmica za istoriju**: Nemačka na vrhu preskočila Brazil" — emotivni naboj
- „**Šta će reći kum**: Terzić detaljno o rekonstrukciji Marakane" — teaser / radoznalost
- „Branko Lazić **otkrio**: Čuo sam da me je Dule baš želeo u Partizanu" — najava otkrića

→ Sve su to **granični „suptilni" slučajevi**: jezik je pomalo senzacionalan, ali bez
tvrde manipulacije. Tu se prag dvojice anotatora razilazi.

## 6. Preporučena dorada `guidelines.md` (Korak 4)

Da bi se prag ujednačio, dodati **operativno pravilo za suptilni klikbejt**:

1. **Teaser / radoznalost (KJ)** se računa kao klikbejt **samo ako naslov namerno
   uskraćuje ključnu informaciju** koja se inače mogla navesti („Šta će reći kum…",
   „Otkrio…", „Ovo niko nije očekivao"). Ako je informacija prisutna → regularan.
2. **Emotivni/senzacionalni epiteti** („za istoriju", „jaka poruka", „šok") **sami po
   sebi nisu dovoljni** — moraju biti praćeni preuveličavanjem ili uskraćivanjem.
3. Dodati **3–5 rešenih graničnih primera** (gore navedeni) sa usaglašenom labelom.

## 7. Legitiman put do κ ≥ 0.6 (NE falsifikovanjem)

1. **Adjudikacija** — `results/neslaganja.csv` (78 spornih): zajedno popuniti kolonu
   `usaglaseno` i kratko `obrazlozenje`. Te usaglašene labele idu u finalni skup.
2. **Dorada uputstva** po tačci 6.
3. **Ponovna kalibracija na NOVOM uzorku** (~220 svežih naslova, opet nezavisno) →
   nova, *poštena* kappa. Uz jasniji prag očekivano prelazi 0.6.
4. U dokumentaciji prijaviti **obe vrednosti**: početnu (0.322) i posle revizije —
   to je tačno ono što metodologija (korak 5: „analiza anotacije") i traži.

> Napomena: početni κ = 0.322 se **prijavljuje kako jeste**. Cilj revizije nije da se
> prepravi taj broj, već da druga runda kalibracije pokaže poboljšanu saglasnost.

## 8. Artefakti

- `results/faza2_iaa_izvestaj.md` — ovaj izveštaj
- `results/neslaganja.csv` — 78 spornih naslova za adjudikaciju (kolone `usaglaseno`, `obrazlozenje`)
- `results/faza2_statistika.txt` — deskriptivna statistika finalnih oznaka
