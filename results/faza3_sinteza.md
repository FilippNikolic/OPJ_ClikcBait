# Faza 3 — Sinteza i poređenje modela

> Završna uporedna tabela sva tri tipa modela na istom balansiranom skupu (2200,
> 1100/1100), iste metrike. Ulaz za finalnu dokumentaciju (Faza 4).
> Pojedinačni izveštaji: `faza3a_baseline_izvestaj.md`, `faza3b_encoder_izvestaj.md`,
> `faza3c_decoder_izvestaj.md`. Grafik: `report/figures/poredjenje_modela.png`.

## Uporedna tabela (najbolja varijanta po modelu)

| Model | Tip | F1(klikbejt) | Accuracy | ROC-AUC |
|---|---|---|---|---|
| MNB + stem + TF-IDF | baseline (linearni) | 0.646 | 0.622 | 0.676 |
| mBERT (3 epohe) | enkoder, multilingvalni | 0.690 | 0.687 | 0.753 |
| **BERTić (3–4 epohe)** | enkoder, monolingvalni | 0.703 | **0.704** | **0.788** |
| Claude — SR prompt | dekoder (zero-shot) | 0.710 | 0.695 | — |
| **Claude — EN prompt** | dekoder (zero-shot) | **0.715** | 0.691 | — |

(Dekoder vraća tvrdu odluku 0/1 → nema ROC-AUC.)

## Glavni nalazi

1. **Svi modeli nadmašuju baseline.** Najslabiji transformer (mBERT, F1 0.690) je
   +0.044 iznad najboljeg baseline-a (0.646); po ROC-AUC razlika je još veća
   (BERTić 0.788 vs 0.676 = **+0.11**). → bag-of-words teško hvata suptilni klikbejt,
   kontekstualni modeli ga hvataju.
2. **Dekoder bez treninga je iznenađujuće jak.** Claude (zero-shot) ima **najviši F1
   (~0.71–0.715)**, blago iznad fino-podešenog BERTića (0.703) — bez ijednog primera
   za trening. Ali: po **accuracy** je BERTić najbolji (0.704), a po **ROC-AUC**
   enkoderi su jedini koji daju kalibrisane verovatnoće.
3. **Mono > multi:** BERTić nadmašuje mBERT na svim metrikama (monolingvalni BCMS
   model bolji za srpski).
4. **Broj epoha:** 3–4 epohe optimalno; 2 epohe nedovoljno (vidi `kriva_ucenja.png`).
5. **Jezik upita (SR vs EN):** zanemarljiva razlika (F1 0.710 vs 0.715).
6. **Ponderisanje (baseline):** TF/IDF/TF-IDF slab efekat na kratkim naslovima;
   TF-IDF u vrhu ali ne dominira nad pukim brojanjem.

## Preporuka / trade-off

- **Za produkciju:** **BERTić** — mali, besplatan, lokalan (CPU/GPU), daje
  kalibrisane verovatnoće (AUC 0.788), najbolja accuracy. Najbolji odnos cena/kvalitet.
- **Kad nema podataka za trening:** **Claude (zero-shot)** — konkurentan F1 bez ijednog
  označenog primera, ali plaćeni API i bez verovatnoća.
- **Baseline** ostaje koristan kao brza, transparentna referenca.

## Ograničenja i dalji rad

- **Ograničenja:** relativno mali skup (2200), jedan domen (sport), jedan izvor
  (SportKlub); dekoder daje samo tvrde labele (nema AUC); evaluirane 2 prompt
  varijante (SR/EN zero-shot + definicija).
- **Dalji rad:** više domena i izvora; veći skup; few-shot prompting i kalibracija
  dekodera; ansambl (BERTić + dekoder); analiza tipova grešaka po pod-tipovima klikbejta.

## Status
Faza 3 (sva tri tipa modela + sinteza) — **ZAVRŠENA.** Sledi Faza 4 (dokumentacija):
`izvestaj.tex` + tabele/grafici iz `report/`.
