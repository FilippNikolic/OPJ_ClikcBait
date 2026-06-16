#!/usr/bin/env python3
"""Faza 3 — pretprocesiranje srpskog teksta za baseline modele.

Sve transformacije su uključive/isključive da bismo merili EFEKAT svake
varijante (zahtev profesora). Jedna funkcija `make_preprocessor(...)` vraća
callable `str -> str` koji vektorizator (CountVectorizer/TfidfVectorizer) dobija
kao već normalizovan, razmakom-razdvojen niz tokena.

Varijante normalizacije reči (`normalize`):
  - "none"  : bez stemovanja/lematizacije
  - "stem"  : lagani heuristički suffix-stripping stemmer (bez zavisnosti)
  - "lemma" : classla lematizacija (prava, ali zahteva `classla` + model)

Napomena o redosledu: pretprocesiranje NE zavisi od fold-a (stem/lemma su
deterministički po tokenu), pa ga radimo JEDNOM nad celim skupom pre CV-a.
IDF/vokabular se i dalje uče UNUTAR svakog fold-a u vektorizatoru, tako da
nema curenja informacija.
"""
from __future__ import annotations

import re
import unicodedata

# --- ćirilica -> latinica (SportKlub je latinica, ali za svaki slučaj) -------
_CIR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ђ": "đ", "е": "e",
    "ж": "ž", "з": "z", "и": "i", "ј": "j", "к": "k", "л": "l", "љ": "lj",
    "м": "m", "н": "n", "њ": "nj", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "ћ": "ć", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "č",
    "џ": "dž", "ш": "š",
}
_CIR2LAT.update({k.upper(): v for k, v in _CIR2LAT.items()})

# token: slova (uklj. srpske dijakritike) + cifre; ostalo je separator
_TOKEN_RE = re.compile(r"[0-9a-zžćčđšА-Ша-ш]+", re.UNICODE)


def cyr_to_lat(text: str) -> str:
    return "".join(_CIR2LAT.get(ch, ch) for ch in text)


def basic_normalize(text: str, lowercase: bool = True) -> str:
    """NFC normalizacija + transliteracija ćirilice (+ opciono lowercase)."""
    text = unicodedata.normalize("NFC", text)
    text = cyr_to_lat(text)
    if lowercase:
        text = text.lower()
    return text


def tokenize(text: str, strip_punct: bool = True) -> list[str]:
    """Tokenizacija. strip_punct=True → interpunkcija je separator (uklonjena);
    strip_punct=False → interpunkcija ostaje kao zaseban token."""
    if strip_punct:
        return _TOKEN_RE.findall(text)
    # zadrži interpunkciju kao tokene
    return re.findall(r"[0-9a-zžćčđšА-Ша-ш]+|[^\s\w]", text, re.UNICODE)


# --- heuristički stemmer (suffix stripping) ----------------------------------
# Lista nastavaka, od najdužeg ka kraćem (greedy longest-match). Pokriva česte
# imeničke/pridevske/glagolske nastavke u srpskom (latinica). Ovo je SVESNO
# jednostavan, transparentan stemmer — ne zameni morfološki analizator, ali je
# dovoljan kao baseline-varijanta i radi bez ijedne zavisnosti.
_SUFFIXES = sorted(
    [
        # pridevski / komparativ
        "ijima", "ijega", "ijemu", "ijim", "ijih", "ijem", "iji", "ije", "ija",
        "ošću", "oga", "ome", "omu", "ima", "ama",
        # imenički padeži
        "ovima", "evima", "ovi", "evi", "ova", "eva", "ове", "ima",
        "ama", "om", "em", "im", "ih", "og", "eg", "u", "e", "a", "i", "o",
        # glagolski
        "ujemo", "ujete", "uju", "jemo", "jete", "ahu", "ćemo", "ćete",
        "smo", "ste", "še", "li", "la", "lo", "le", "ti", "ći", "mo", "te",
        "m", "š", "ti",
    ],
    key=len,
    reverse=True,
)
_MIN_STEM = 3  # ne skraćuj ispod ovoliko slova


def stem(token: str) -> str:
    if len(token) <= _MIN_STEM or token.isdigit():
        return token
    for suf in _SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= _MIN_STEM:
            return token[: -len(suf)]
    return token


# --- classla lematizacija (opciono, lazy) ------------------------------------
_CLASSLA_PIPE = None


def _get_classla():
    """Lazy init classla pipeline-a. Prvi poziv preuzima model (~jednom)."""
    global _CLASSLA_PIPE
    if _CLASSLA_PIPE is None:
        import classla  # type: ignore

        try:
            _CLASSLA_PIPE = classla.Pipeline(
                "sr", processors="tokenize,lemma", use_gpu=False, verbose=False
            )
        except Exception:
            # model nije preuzet — preuzmi pa probaj ponovo
            classla.download("sr")
            _CLASSLA_PIPE = classla.Pipeline(
                "sr", processors="tokenize,lemma", use_gpu=False, verbose=False
            )
    return _CLASSLA_PIPE


def lemmatize_text(text: str) -> list[str]:
    nlp = _get_classla()
    doc = nlp(text)
    return [w.lemma or w.text for s in doc.sentences for w in s.words]


# --- fabrika preprocesora ----------------------------------------------------
def make_preprocessor(normalize: str = "none", lowercase: bool = True,
                      strip_punct: bool = True):
    """Vrati funkciju `str -> str` (razmakom razdvojeni tokeni).

    normalize ∈ {"none", "stem", "lemma"}.
    """
    if normalize not in ("none", "stem", "lemma"):
        raise ValueError(f"nepoznata normalize varijanta: {normalize}")

    def _prep(text: str) -> str:
        text = basic_normalize(text, lowercase=lowercase)
        if normalize == "lemma":
            toks = lemmatize_text(text)
            if strip_punct:
                toks = [t for t in toks if _TOKEN_RE.fullmatch(t)]
        else:
            toks = tokenize(text, strip_punct=strip_punct)
            if normalize == "stem":
                toks = [stem(t) for t in toks]
        return " ".join(toks)

    return _prep


def preprocess_corpus(texts, normalize="none", lowercase=True, strip_punct=True):
    """Pretprocesira ceo korpus jednom. Za 'lemma' radi batch kroz classla."""
    if normalize == "lemma":
        # batch je mnogo brži od poziva po naslovu
        nlp = _get_classla()
        out = []
        for t in texts:
            t = basic_normalize(t, lowercase=lowercase)
            doc = nlp(t) if t.strip() else None
            if doc is None:
                out.append("")
                continue
            toks = [w.lemma or w.text for s in doc.sentences for w in s.words]
            if strip_punct:
                toks = [w for w in toks if _TOKEN_RE.fullmatch(w)]
            out.append(" ".join(toks))
        return out
    prep = make_preprocessor(normalize, lowercase, strip_punct)
    return [prep(t) for t in texts]


if __name__ == "__main__":
    # mini demo
    primeri = [
        "Nećete verovati šta je uradio kapiten Crvene zvezde!",
        "Partizan pobedio Zvezdu rezultatom 2:1 u derbiju",
        "(VIDEO) Drama u penal seriji: CSKA osvojio Kup Bugarske",
    ]
    for nm in ("none", "stem"):
        print(f"\n== normalize={nm} ==")
        for p in preprocess_corpus(primeri, normalize=nm):
            print(" ", p)
