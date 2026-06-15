# Uputstvo za anotaciju — Detekcija klikbejt naslova (sportske vesti)

> Verzija 1.0 • Domen: sportske vesti (SportKlub) • Binarna klasifikacija
> Anotatori: Filip Nikolić, Danilo Nikolić

---

## 1. Cilj i format oznaka

Svakom naslovu dodeljujemo **jednu** oznaku u koloni `labela`:

| Oznaka | Značenje |
|---|---|
| `1` | **klikbejt** |
| `0` | **regularan** (nije klikbejt) |

Naslov se ocenjuje **sam za sebe** — onako kako ga čitalac vidi u listi vesti, **bez** otvaranja članka. Pitanje koje sebi postavljamo:

> *„Da li ovaj naslov namerno manipuliše čitaocem da klikne — uskraćivanjem informacije, preuveličavanjem ili veštačkom emocijom — umesto da pošteno saopšti vest?"*

Ako DA → `1`. Ako naslov pošteno prenosi suštinu vesti → `0`.

---

## 2. Definicija klikbejta (mehanizmi manipulacije)

Klikbejt **NIJE** samo uzvičnik ili fraza „Nećete verovati". To je svaki naslov koji koristi bar jedan od sledećih mehanizama da natera na klik:

### (KJ) Kognitivni jaz — namerno izostavljanje ključne informacije
Naslov sakriva ono najvažnije (ko/šta/koliko/ishod) da bi te naterao da otvoriš članak.
- *„Real ozvaničio **veliko pojačanje**"* → ne kaže KOGA. (jaz)
- *„Dovodi li Zvezda đaka Parme? **Ovako stoje stvari…**"* → odgovor sakriven.
- *„Stigla podrška **sa stare adrese**"* → ko/odakle namerno zamagljeno.

### (PV) Preuveličavanje važnosti
Banalan ili rutinski događaj predstavljen kao senzacija, šok, bomba, drama.
- *„**Bomba iz Italije**: Diđa napušta Rosija i odlazi u KTM"* → običan transfer = „bomba".
- *„**Šok** u Humskoj"* → za uobičajenu vest.

### (EN) Veštački emocionalni naboj
Naslov gradi napetost, ogorčenje, sažaljenje ili oduševljenje koje ne proizilazi iz same vesti.
- *„**Skandal** u Parizu: Novakovom dželatu **poklonjen** set?"*
- *„Ovo još niste videli: Nejmar greškom zamenjen pa **pobesneo**!"*

### (SF) Senzacionalistička fraza / otvorena forma
Očigledni klikbejt obrasci: nedovršene rečenice s tri tačke, retorička pitanja čiji je cilj samo klik, „a onda se desilo ovo", „nećete verovati", direktno obraćanje čitaocu.
- *„…**Ovako stoje stvari…**"*, *„Turci kažu – **gotovo je!**"*

> Za klasu `1` dovoljan je **jedan** mehanizam. Više mehanizama = sigurniji klikbejt.

---

## 3. Šta NIJE klikbejt (oznaka `0`)

Da ne bismo preterali — sledeće samo po sebi **NE** čini naslov klikbejtom:

- **Uzvičnik ili velika slova** ako naslov i dalje pošteno prenosi vest.
  - *„Duplantis tri puta rušio na 6,32!"* → uzbudljivo, ali sve piše = `0`.
- **Stvarno velika vest** rečena direktno.
  - *„Real ozvaničio Mbapea"* (da piše ko) = `0`.
- **Rezultati, izveštaji, transferi, izjave** sa jasnim sadržajem.
  - *„Đirona pobegla od zone ispadanja, razlika sada dva boda"* = `0`.
  - *„Paunović pozvao još jednog debitanta"* = `0`.
- **Citat igrača/trenera** koji je sam po sebi informativan.
  - *„Arteta o tituli: Jedan od najlepših osećaja ikada"* = `0`.

**Ključni test:** ako posle čitanja naslova **znaš šta se desilo**, verovatno je `0`. Ako moraš da klikneš da bi saznao suštinu, verovatno je `1`.

---

## 4. Granični slučajevi — pravila odlučivanja

1. **Uzbudljiv sport ≠ klikbejt.** Sport je emotivan; prava drama na terenu rečena pošteno je `0`. Klikbejt je *veštačka* drama (PV/EN) ili *sakrivena* informacija (KJ).
2. **Retoričko pitanje:** `1` ako je cilj samo klik a odgovor je sakriven (*„Dovodi li Zvezda đaka Parme? Ovako stoje stvari…"*). `0` ako je legitimno otvoreno pitanje/anketa (*„Anketa: Ko osvaja Svetsko prvenstvo?"*).
3. **„Bomba/Šok/Skandal" + puna informacija:** ako naslov ipak kaže suštinu (*„Bomba: Diđa odlazi u KTM"*) — blaži slučaj. Ako je preuveličavanje očigledno → `1`; ako je vest stvarno velika → `0`. Kad si u dilemi, oslони se na to da li je emocija *veštačka*.
4. **(VIDEO)/(FOTO) prefiks** je neutralan — ne utiče na oznaku; gledaj tekst naslova.
5. **Kad si stvarno na pola-pola:** zapiši napomenu u kolonu `napomena` i odluči po dominantnom utisku. Ovakve slučajeve rešavamo zajednički kroz kalibraciju.

---

## 5. Primeri (iz našeg korpusa)

| Naslov | Oznaka | Zašto |
|---|---|---|
| Đirona pobegla od zone ispadanja, razlika sada dva boda | `0` | pun sadržaj, rezultat |
| Paunović pozvao još jednog debitanta | `0` | informativno, jasno |
| Beograd domaćin Kongresa Svetske skijaške federacije | `0` | čista vest |
| Arteta o tituli: Jedan od najlepših osećaja ikada | `0` | citat sa sadržajem |
| Real ozvaničio veliko pojačanje | `1` | KJ — ne kaže koga |
| Dovodi li Zvezda đaka Parme? Ovako stoje stvari… | `1` | KJ + SF |
| Turci kažu – gotovo je! Salah ima 39.000.000 razloga da dođe | `1` | PV + EN + SF |
| (VIDEO) Skandal u Parizu: Novakovom dželatu poklonjen set? | `1` | EN + PV |
| Ovo još niste videli: Nejmar greškom zamenjen pa pobesneo! | `1` | SF + EN |
| Stigla podrška sa stare adrese: Zvezda je uz Čovića! | `1` | KJ |

---

## 6. Postupak — kako i gde anotirati

1. Otvori svoju datoteku (vidi `Faza2-plan.md` za tačan put) u **Numbers** ili **Google Sheets**.
2. Čitaj kolonu `naslov`. U kolonu **`labela`** upiši `1` ili `0`.
3. (Opciono, samo za `1`) u kolonu **`podtip`** upiši mehanizam: `KJ`, `PV`, `EN`, `SF` (može više, npr. `PV,EN`). Korisno za analizu, nije obavezno.
4. Ako je granično — kratko obrazloženje u kolonu **`napomena`**.
5. **Ne menjaj** kolone `id` i `naslov`.
6. Snimaj redovno; čuvaj **UTF-8**.

### Pravila konzistentnosti
- Ne otvaraj članak; ocenjuj samo naslov.
- Tokom **kalibracije** anotiraj **nezavisno** — bez dogovaranja sa drugim anotatorom.
- Ako primetiš da ti je definicija nejasna na nekom obrascu, zapiši u `napomena` — doradićemo uputstvo posle kalibracije.

---

## 7. Pod-tipovi (legenda)

| Kod | Mehanizam |
|---|---|
| `KJ` | Kognitivni jaz (izostavljena ključna info) |
| `PV` | Preuveličavanje važnosti |
| `EN` | Veštački emocionalni naboj |
| `SF` | Senzacionalistička fraza / otvorena forma |
