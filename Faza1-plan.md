# Faza 1 — Prikupljanje podataka (detaljan plan)

> Cilj: prikupiti **višak sirovih sportskih naslova (~3000–4000)** sa SportKlub portala, očistiti i deduplikovati, i pripremiti ih za anotaciju (Faza 2). Finalni balansiran skup je 2200 (1100/1100), ali se balans finalizuje tek posle anotacije — zato sada skupljamo višak.

**Izvor:** **SportKlub** (WP REST API, ~449k članaka). Mozzart i B92 odbačeni.
**Izlaz faze:** `data/interim/headlines.csv` (deduplikovan) + `data/metadata.csv` + kratak izveštaj o prikupljanju.

> ⚠️ **Odluka o jednom izvoru (izmena u odnosu na prijavu).** U prijavi profesoru
> pomenuti su Mozzart Sport, Sport Klub i B92. Konačno radimo **samo sa SportKlub**.
> Profesor je tražio *jedan tematski domen* (sportske vesti), ne broj izvora, a
> postavka dozvoljava bilo koji javno dostupan sajt. **Obrazloženje:** obe klase
> (klikbejt + regularan) dolaze sa istog portala → model uči stvarni klikbejt
> signal, a ne stil portala. Ovo obavezno navesti u dokumentaciji (Faza 4) i
> idealno kratko javiti profesoru.

---

## 1. Tehnološki stek

| Namena | Alat |
|---|---|
| HTTP zahtevi | `requests` (+ `time.sleep` za rate-limit) |
| HTML parsiranje | `beautifulsoup4` + `lxml` |
| RSS | `feedparser` |
| Veći crawl (opciono) | `Scrapy` |
| Dinamičke stranice (ako treba) | `playwright` ili `selenium` |
| Obrada podataka | `pandas` |
| Deduplikacija (fuzzy) | `rapidfuzz` |

`requirements.txt`:
```
requests
beautifulsoup4
lxml
feedparser
pandas
rapidfuzz
playwright        # samo ako sajt zahteva JS rendering
```

---

## 2. Šema podataka

Svaki red = jedan naslov. Polja:

| Polje | Opis | Primer |
|---|---|---|
| `id` | jedinstveni ID (npr. hash naslova ili redni broj) | `mz_000123` |
| `naslov` | tekst naslova (raw, UTF-8) | `Šok u Humskoj!...` |
| `izvor` | sajt | `sportklub` |
| `url` | puni URL članka | `https://...` |
| `datum` | datum objave (ako dostupan, ISO 8601) | `2026-06-10` |
| `rubrika` | sport/podsekcija ako postoji | `fudbal` |
| `datum_scrape` | kada je prikupljeno | `2026-06-15` |
| `labela` | **prazno** — popunjava se u Fazi 2 | `` |

> Postavka eksplicitno traži da se u metapodacima zabeleži **URL ili jedinstveni identifikator izvora** — pokriveno poljima `url` + `id`.

---

## 3. Strategija prikupljanja po izvoru

### 3.1 RSS feed-ovi (prvi izbor — najčistije)
Proveriti da li sajtovi imaju RSS za sport:
- Tipične putanje: `/rss`, `/feed`, `/rss/sport`, `/sport/rss`.
- RSS daje čist `title`, `link`, `pubDate` bez parsiranja HTML-a.
- **Ograničenje:** RSS obično vraća samo skorije vesti (zadnjih ~20–50) → nedovoljno za 3000+. Zato RSS koristiti za **sveže** naslove + dopuniti scraping-om/arhivom.

```python
import feedparser
feed = feedparser.parse("https://www.b92.net/info/rss/sport.xml")
for e in feed.entries:
    print(e.title, e.link, e.get("published"))
```

### 3.2 Web scraping listing/arhiva stranica (glavni izvor količine)
- Naći **listing stranice** po rubrikama (fudbal, košarka, tenis…) sa paginacijom.
- Iterirati kroz stranice (`?page=2`, `/strana/2`, infinite scroll → API poziv).
- Izvući naslove iz kartica (`<h2>`, `<h3>`, `<a class="title">` — selektor zavisi od sajta).
- **Proveriti da li je sadržaj u HTML-u ili se učitava JS-om** (DevTools → Network). Ako JS → `playwright`.

### 3.3 Izvor (SportKlub — jedini korišćeni)
| Izvor | Pristup | Napomena |
|---|---|---|
| **SportKlub** | **WP REST API** (`sportklub.n1info.rs`) | ~449k članaka, čist sportski sadržaj; API daje naslov/URL/datum/rubriku bez HTML parsiranja |

> Mozzart (`mozzart_bulk.py`) i B92 ostaju u kodu istorijski, ali se **ne koriste**.
> Pošto je izvor jedan, scraping je zajednički task (oba člana razumeju ceo pipeline);
> podela posla je na anotaciju i kasnije faze.

---

## 4. Etika i tehnička higijena scrapinga

- Poštovati **`robots.txt`** svakog sajta.
- **Rate limiting**: pauza 1–3 s između zahteva, ne paralelizovati agresivno.
- Postaviti **User-Agent** header (ne pretvarati se da nismo bot bezveze; razuman UA).
- Skupljati **samo naslove + metapodatke** (ne ceo članak) — manji otisak, dovoljno za zadatak.
- Sačuvati **raw HTML/RSS snapshot** opciono, radi reproducibilnosti.
- Podaci se koriste isključivo u akademske svrhe (navesti u dokumentaciji).

---

## 5. Čišćenje i normalizacija

Redosled koraka (`src/scraping/clean.py`):
1. **Trim** whitespace, ukloniti višestruke razmake, newline u naslovu.
2. Ukloniti **prefikse/sufikse portala** ako se pojave (npr. „ | SportKlub").
3. Normalizovati navodnike/crtice (opciono — paziti da ne uništimo signal klikbejta!).
   - ⚠️ **Ne uklanjati uzvičnike, velika slova, emoji ovde** — to su potencijalni klikbejt signali; čuvati raw naslov, normalizaciju raditi tek u preprocessing-u Faze 3.
4. **UTF-8** encoding na snimanju (eksplicitno `encoding="utf-8"`).
5. Odbaciti unose: prazne, prekratke (<3 reči? — proceniti), čisto oglasne („SUPER PONUDA", kvote) ako nisu vesti.

---

## 6. Deduplikacija

Dva nivoa:
1. **Egzaktni duplikati** — `df.drop_duplicates(subset="naslov_normalizovan")`.
2. **Near-duplicate** (isti događaj sa više portala, sitne razlike) — `rapidfuzz`:
   ```python
   from rapidfuzz import fuzz
   # uporedi parove, prag npr. token_sort_ratio > 90 → duplikat
   ```
   - Za 3–4k naslova O(n²) je ~9–16M poređenja → izvodljivo, ali grupisati po prvih par reči/blokovati radi brzine.

> Beležiti koliko je duplikata uklonjeno (ide u dokumentaciju).

---

## 7. Količina i balans

- **Skupiti višak: 3000–4000 sirovih** naslova pre anotacije.
- Razlog: labela (klikbejt/regularan) se ne zna unapred → ne možemo garantovati 1100/1100 dok ne anotiramo.
- Ako se posle anotacije pokaže manjak klikbejt klase (verovatno ređa) → **ciljano doskupljati** kandidate (npr. naslovi sa senzacionalističkim obrascima) da se dostigne 1100.
- Finalni cilj: **2200 (1100 klikbejt + 1100 regularnih)**.

> ⚠️ Pažnja na bias: ako klikbejt skupljamo ciljanim filterom „ima uzvičnik", model će naučiti samo to. Zato i klikbejt i regularne uzimati iz istog opšteg toka vesti gde god moguće.

---

## 8. Plan rada (redosled)

1. [ ] Postaviti repo strukturu + `requirements.txt` + virtuelno okruženje.
2. [ ] Za svaki sajt: ručno istražiti (DevTools) — RSS? listing URL? paginacija? JS?
3. [ ] Napisati `src/scraping/<izvor>.py` za svaki izvor (vraća listu redova po šemi).
4. [ ] Pokrenuti prikupljanje → `data/raw/<izvor>_raw.csv`.
5. [ ] `clean.py` → normalizacija → `data/interim/<izvor>_clean.csv`.
6. [ ] Spojiti sve izvore → globalna deduplikacija → `data/interim/headlines.csv`.
7. [ ] Generisati `data/metadata.csv` (id, url, izvor, datum…).
8. [ ] Sanity provera: broj po izvoru, dužine naslova, primeri, encoding.
9. [ ] Kratak izveštaj o prikupljanju (za dokumentaciju): izvori, kriterijumi, broj pre/posle dedup.

---

## 9. Provere kvaliteta (pre prelaska na Fazu 2)

- [ ] ≥ 3000 jedinstvenih naslova posle deduplikacije
- [ ] Svi fajlovi UTF-8 (otvoriti, proveriti dijakritike: č ć ž š đ)
- [ ] Svaki naslov ima validan `url`/`id` izvora
- [ ] Nema praznih/duplih naslova
- [ ] Raspodela po izvorima nije ekstremno neujednačena
- [ ] Ručno pregledati ~50 nasumičnih naslova — da li su stvarno sportske vesti

---

## 10. Rizici i mitigacije

| Rizik | Mitigacija |
|---|---|
| Sajt učitava naslove JS-om | `playwright`/`selenium` headless |
| RSS vraća premalo naslova | dopuniti listing/arhiva scraping-om |
| Premalo klikbejt naslova posle anotacije | ciljano doskupljanje kandidata |
| Blokiranje IP-a (rate limit) | sleep, manji batch, UA header |
| Near-duplicate preživi egzaktni dedup | `rapidfuzz` fuzzy prolaz |
| Gubitak klikbejt signala u čišćenju | čuvati raw naslov, normalizovati tek u Fazi 3 |

---

### Sledeći korak
Kad kažeš, mogu da **postavim repo strukturu i napišem prvi skraper** (npr. za jedan izvor sa RSS-om kao najbrži dokaz koncepta), pa da vidimo realan format naslova pre nego što skaliramo na sva tri sajta.
