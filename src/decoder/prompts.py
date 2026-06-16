#!/usr/bin/env python3
"""Faza 3c — prompt varijante za dekoderski LLM (ChatGPT).

Poredimo (zahtev postavke):
  • jezik prompta: srpski (SR) vs engleski (EN)
  • format: zero-shot vs few-shot
  • sa/bez definicije klikbejta

Svaka varijanta vraća (system_prompt, user_prompt_template). Template ima
{naslov} koji se popunjava. Model treba da odgovori SAMO sa 1 (klikbejt) ili
0 (regularan) — parsiranje je u chatgpt_eval.py.
"""

# --- definicije klikbejta (iz annotation/guidelines.md, skraćeno) ------------
DEF_SR = (
    "Klikbejt naslov namerno manipuliše čitaoca da klikne, kroz: izostavljanje "
    "ključne informacije (kognitivni jaz), preuveličavanje važnosti događaja, "
    "veštački emocionalni naboj, ili senzacionalističke fraze "
    "(npr. „nećete verovati“, „a onda se desilo ovo“). Regularan naslov jasno i "
    "informativno prenosi suštinu vesti."
)
DEF_EN = (
    "A clickbait headline deliberately manipulates the reader into clicking by: "
    "withholding key information (a curiosity gap), exaggerating the importance "
    "of an event, manufacturing an emotional charge, or using sensational "
    "phrasing (e.g. 'you won't believe', 'and then this happened'). A regular "
    "headline clearly and informatively conveys the gist of the news."
)

# few-shot primeri (sportski domen; biraju se da NE budu u eval skupu — vidi
# chatgpt_eval.py --holdout-fewshot). 1 = klikbejt, 0 = regularan.
FEWSHOT = [
    ("Nećete verovati šta je kapiten uradio posle utakmice!", 1),
    ("Partizan pobedio Crvenu zvezdu 2:1 u 165. večitom derbiju", 0),
    ("Ovaj potez je SVE promenio — navijači u neverici", 1),
    ("Novak Đoković prošao u finale Rolan Garosa", 0),
    ("Tajna koju kriju u svlačionici: evo šta se zaista desilo", 1),
    ("Real Madrid potpisao ugovor sa mladim veznjakom do 2030.", 0),
]


def _fewshot_block(lang: str) -> str:
    lines = []
    for naslov, lab in FEWSHOT:
        if lang == "sr":
            lines.append(f'Naslov: "{naslov}"\nOdgovor: {lab}')
        else:
            lines.append(f'Headline: "{naslov}"\nAnswer: {lab}')
    return "\n\n".join(lines)


def build_prompt(lang: str, shots: str, with_def: bool):
    """lang ∈ {sr,en}; shots ∈ {zero,few}; with_def: uključi definiciju.
    Vrati (system, user_template)."""
    assert lang in ("sr", "en") and shots in ("zero", "few")

    if lang == "sr":
        system = "Ti si precizan klasifikator sportskih novinskih naslova."
        task = ("Odredi da li je sledeći sportski naslov KLIKBEJT (1) ili "
                "REGULARAN (0).")
        definicija = (DEF_SR + "\n\n") if with_def else ""
        examples = (_fewshot_block("sr") + "\n\n") if shots == "few" else ""
        rule = ("Odgovori ISKLJUČIVO jednom cifrom: 1 (klikbejt) ili 0 "
                "(regularan). Bez objašnjenja.")
        user = (f"{task}\n\n{definicija}{examples}"
                f'Naslov: "{{naslov}}"\nOdgovor:')
    else:
        system = "You are a precise classifier of sports news headlines."
        task = ("Decide whether the following sports headline is CLICKBAIT (1) "
                "or REGULAR (0).")
        definicija = (DEF_EN + "\n\n") if with_def else ""
        examples = (_fewshot_block("en") + "\n\n") if shots == "few" else ""
        rule = ("Answer with EXACTLY one digit: 1 (clickbait) or 0 (regular). "
                "No explanation.")
        user = (f"{task}\n\n{definicija}{examples}"
                f'Headline: "{{naslov}}"\nAnswer:')

    return f"{system}\n{rule}", user


# kanonski skup varijanti koje evaluiramo
VARIANTS = [
    {"id": "sr_zero_nodef", "lang": "sr", "shots": "zero", "with_def": False},
    {"id": "sr_zero_def",   "lang": "sr", "shots": "zero", "with_def": True},
    {"id": "sr_few_def",    "lang": "sr", "shots": "few",  "with_def": True},
    {"id": "en_zero_nodef", "lang": "en", "shots": "zero", "with_def": False},
    {"id": "en_zero_def",   "lang": "en", "shots": "zero", "with_def": True},
    {"id": "en_few_def",    "lang": "en", "shots": "few",  "with_def": True},
]
