# Faza 3c — Dekoderski model (izveštaj)

> **Claude (`claude-haiku-4-5`, Anthropic API)** — bez fine-tuninga (zatvoren model),
> samo evaluacija na **celom skupu (2200)**. Poređenje **jezika upita: srpski (SR) vs
> engleski (EN) prompt**, oba zero-shot sa definicijom klikbejta. Naslovi su u oba
> slučaja srpski — menja se samo jezik uputstva.
> Reprodukcija: `python src/decoder/claude_eval.py --model claude-haiku-4-5 --variants sr_zero_def en_zero_def`
> Sirovo: `results/decoder_results.csv`, keš: `results/decoder_cache/`.

## Rezultati (ceo skup, n=2200, 0 neparsiranih)

| Prompt | F1(klikbejt) | Accuracy | Preciznost | Odziv | Macro-F1 |
|---|---|---|---|---|---|
| **SR** (srpsko uputstvo) | 0.710 | **0.695** | 0.676 | 0.748 | **0.694** |
| **EN** (englesko uputstvo) | **0.715** | 0.691 | 0.664 | 0.775 | 0.689 |

Cena evaluacije: ~$1.01 (Haiku). Bez ROC-AUC — dekoder vraća tvrdu odluku (0/1), ne verovatnoću.

## Diskusija

- **Jezik upita (SR vs EN) — gotovo bez razlike:** F1 0.710 vs 0.715. EN prompt daje
  nešto viši **odziv** (0.775 vs 0.748), SR nešto višu **preciznost** (0.676 vs 0.664)
  i macro-F1/accuracy. Praktično izjednačeno → Claude podjednako dobro razume
  i srpsko i englesko uputstvo nad srpskim naslovima. (Profesorovo pitanje o efektu
  jezika upita → odgovor: efekat je zanemarljiv za ovaj model/zadatak.)
- **Bez fine-tuninga, a konkurentan:** zero-shot dekoder (F1 ~0.71) je na nivou
  fino-podešenih enkodera — vidi sintezu.

## Napomena o izboru modela
Profesor je dozvolio „ChatGPT, Gemini **i drugi**". Besplatni Gemini tier nedostupan
za naš region (`limit: 0`); iskoristili smo **Claude** (plaćeni, ali jeftin ~$1).
Kod podržava i ChatGPT (`chatgpt_eval.py`) i Gemini (`gemini_eval.py`) sa istim promptima.
