# Obrada teksta: tokenizacija, stemovanje i lematizacija

> Prateći tehnički dokument uz izveštaj (sekcija *Pretprocesiranje teksta*).
> Objašnjava **šta** je svaka tehnika, **zašto** je koristimo i **kako je tačno
> implementirana** u ovom projektu.
> Izvorni kod: [`src/preprocessing/serbian.py`](../src/preprocessing/serbian.py).

Cilj pretprocesiranja je da sirovi naslov pretvori u niz **normalizovanih tokena**
koje onda vektorizator (`CountVectorizer` / `TfidfVectorizer` iz `scikit-learn`)
pretvara u brojeve. Lanac je:

```
sirov naslov ─► osnovna normalizacija ─► TOKENIZACIJA ─► (STEMOVANJE | LEMATIZACIJA | ništa) ─► tokeni
```

Sve tri tehnike su uključive/isključive (`normalize ∈ {none, stem, lemma}`) da bismo
mogli da izmerimo **efekat svake** u baseline gridu.

---

## 0. Osnovna normalizacija (prethodi svemu)

Pre tokenizacije, tekst se čisti u funkciji `basic_normalize`:

1. **Unicode NFC** — ujednačava različite Unicode zapise istog karaktera (npr. „č"
   kao jedan kod vs. „c" + kvačica).
2. **Transliteracija ćirilice → latinica** — SportKlub je latinični, ali radi
   robusnosti `вест → vest`.
3. **Mala slova (lowercase)** — `ZVEZDA`, `Zvezda`, `zvezda` postaju isti token.

```python
"Партизан POBEDIO!" ─► "partizan pobedio!"
```

---

## 1. Tokenizacija

### Šta je
Tokenizacija je deljenje neprekinutog stringa na **tokene** — najmanje jedinice koje
model posmatra (kod nas: reči i brojevi). To je prvi korak svake obrade teksta jer
modelu ne dajemo string, već listu jedinica.

### Kako se radi kod nas
Token = neprekinut niz **slova** (uključujući srpske dijakritike `ž ć č đ š`) i
**cifara**. Sve ostalo (razmaci, interpunkcija) su **razdvajači** i podrazumevano se
izbacuju. Implementirano regularnim izrazom:

```python
_TOKEN_RE = re.compile(r"[0-9a-zžćčđšА-Ша-ш]+", re.UNICODE)

def tokenize(text, strip_punct=True):
    if strip_punct:
        return _TOKEN_RE.findall(text)        # interpunkcija = razdvajač (uklonjena)
    return re.findall(r"[0-9a-zžćčđšА-Ша-ш]+|[^\s\w]", text)  # interpunkcija ostaje kao token
```

Primer:

```
"Partizan pobedio 2:1 u derbiju!"  ─►  ["partizan", "pobedio", "2", "1", "u", "derbiju"]
```

### Dve varijante
- `strip_punct=True` (podrazumevano) — interpunkcija se uklanja. Za klasifikaciju po
  rečima to je obično dovoljno.
- `strip_punct=False` — interpunkcija ostaje kao zaseban token. Korisno jer su `…`,
  `?`, `!` često signali klikbejta.

### Veza sa vektorizatorom
Bitan detalj o tome kako se izbegava **dvostruka tokenizacija**: mi naslov već
tokenizujemo i spojimo nazad razmakom, pa `scikit-learn` vektorizatoru kažemo da
**ne** tokenizuje ponovo, već samo da deli po razmaku:

```python
TfidfVectorizer(lowercase=False, token_pattern=r"(?u)\S+", ngram_range=(1,2), min_df=2)
```

Tako mi kontrolišemo tokenizaciju (uz srpske dijakritike), a vektorizator samo gradi
$n$-grame (1–1 i 1–2) i izbacuje tokene koji se javljaju u manje od 2 naslova
(`min_df=2`).

---

## 2. Stemovanje (stemming)

### Šta je
Stemovanje svodi reč na njenu **osnovu (stem)** mehaničkim sečenjem nastavaka. Osnova
**ne mora** biti prava reč — bitno je samo da se sve oblike iste reči svede na isti
niz. Srpski je morfološki bogat (jedna reč ima mnogo padežnih/glagolskih oblika), pa
bez stemovanja vektorizator `pobeda`, `pobede`, `pobedom`, `pobedi` tretira kao
**četiri različita** obeležja — to raspršuje signal.

```
pobeda, pobede, pobedom, pobedu  ─►  pobed   (ista osnova)
```

### Kako se radi kod nas — heuristički suffix-stripping
Napisali smo **lagani stemer bez ijedne spoljne zavisnosti**. Princip:

1. Imamo listu poznatih srpskih **nastavaka** (`_SUFFIXES`): imenički padeži
   (`-ima`, `-ama`, `-om`, `-u`…), pridevski/komparativni (`-iji`, `-ije`, `-oga`…) i
   glagolski (`-ujemo`, `-smo`, `-ti`, `-li`…).
2. Lista je sortirana **od najdužeg ka najkraćem** nastavku (pohlepno najduže
   poklapanje — *greedy longest-match*).
3. Za token uklonimo **prvi nastavak** koji se poklopi sa krajem reči.

Zaštitne mere:
- **`_MIN_STEM = 3`** — osnova se nikad ne skraćuje ispod 3 slova (da `psi` ne postane
  prazno).
- **Cifre se ne diraju** (`token.isdigit()`).

```python
_MIN_STEM = 3
def stem(token):
    if len(token) <= _MIN_STEM or token.isdigit():
        return token
    for suf in _SUFFIXES:                       # od najdužeg nastavka
        if token.endswith(suf) and len(token) - len(suf) >= _MIN_STEM:
            return token[:-len(suf)]
    return token
```

Primer:

```
"igrača"  ─► "igr"      (uklonjen -ača? ne — uklonjen najduži poklopljeni nastavak)
"pobedom" ─► "pobed"
"velikih" ─► "velik"
```

### Prednosti i mane
- ✅ Brz, transparentan, bez zavisnosti i modela.
- ✅ Smanjuje raštrkanost vokabulara → pomaže baseline modelima (u rezultatima
  stemovanje stabilno poboljšava F1).
- ⚠️ Heuristički — može da **preseče previše** ili **premalo** (npr. nepravilni
  oblici). Svesno je jednostavan: nije zamena za pravi morfološki analizator.

---

## 3. Lematizacija (lemmatization)

### Šta je
Lematizacija takođe svodi reč na osnovni oblik, ali na **lemu** — pravu rečničku reč
(oblik koji bi stajao u rečniku). Za razliku od stemovanja, ona je **morfološki
ispravna** i koristi gramatičko znanje (vrstu reči — POS), pa ume i nepravilne oblike:

```
stem:   "najbolji" ─► "najbolj"     (mehaničko sečenje)
lemma:  "najbolji" ─► "dobar"       (prava osnova prideva)
        "igrača"   ─► "igrač"
        "pobedili" ─► "pobediti"
```

### Kako se radi kod nas — `classla`
Koristimo biblioteku **[`classla`](https://github.com/clarinsi/classla)** (varijanta
Stanza pipeline-a specijalizovana za južnoslovenske jezike) sa modelom za **srpski**:

```python
import classla
pipe = classla.Pipeline("sr", processors="tokenize,pos,lemma", use_gpu=False)
doc = pipe("najbolji igrači su pobedili")
[w.lemma for s in doc.sentences for w in s.words]   # ['dobar', 'igrač', 'biti', 'pobediti']
```

Ključno:
- Procesori `tokenize,pos,lemma` se izvršavaju redom. **POS (vrsta reči) je obavezan**
  jer lematizator za srpski koristi POS oznaku da bi razrešio dvosmislenost (npr. ista
  reč kao imenica vs. glagol daje različitu lemu).
- Model se **preuzima jednom** pri prvom pokretanju (`classla.download("sr")`), pa se
  pipeline **lazy-inicijalizuje** i kešira (`_get_classla()`), a korpus se obrađuje
  **batch**-om radi brzine.
- Inicijalizacija je obavijena `try/except`: ako model nije preuzet, automatski se
  preuzima pa se pokušava ponovo.

### Prednosti i mane
- ✅ Morfološki ispravno, hvata nepravilne oblike, POS-svesno.
- ✅ Tačnija normalizacija od stemovanja.
- ⚠️ Zahteva spoljnu biblioteku + preuzimanje modela; **sporija** je (neuronski
  pipeline) i teža za reprodukciju.

---

## 4. Stemovanje vs. lematizacija — sažeto

| | **Stemovanje** | **Lematizacija** |
|---|---|---|
| Rezultat | osnova (ne mora biti reč) | lema (prava rečnička reč) |
| Metod | sečenje nastavaka (heuristika) | morfološka analiza + POS |
| Nepravilni oblici | ne hvata | hvata |
| Brzina | vrlo brzo | sporije (model) |
| Zavisnosti | nikakve | `classla` + model za srpski |
| Kod kod nas | `serbian.stem()` | `serbian.lemmatize_text()` (classla) |

Obe tehnike rešavaju isti problem — **morfološku raznolikost srpskog** — ali pravimo
kompromis tačnost↔cena. U projektu obe (plus „bez normalizacije") tretiramo kao
**hiperparametar** i empirijski biramo najbolju varijantu u baseline gridu.

---

## 5. Zašto je ovo bitno baš za srpski klikbejt

Srpski ima izraženu fleksiju (padeži, rod, broj, glagolska vremena), pa isti pojam
ima desetine površinskih oblika. Bez normalizacije, baseline model (vreća reči) bi
svaki oblik učio zasebno i brzo bi mu ponestalo primera po obeležju. Stemovanje i
lematizacija sažimaju te oblike u jednu osnovu, smanjuju dimenzionalnost i poboljšavaju
generalizaciju — što se vidi i u rezultatima (stemovanje je deo najbolje baseline
varijante: *naivni Bajes + stemovanje + TF-IDF*).

> **Napomena o curenju informacija:** pošto su stemovanje i lematizacija
> deterministički po tokenu (ne uče se iz podataka), pretprocesiranje radimo **jednom**
> nad celim skupom. Vokabular i IDF težine vektorizatora se i dalje uče **unutar
> svakog fold-a** unakrsne validacije, pa nema curenja iz test u train skup.
