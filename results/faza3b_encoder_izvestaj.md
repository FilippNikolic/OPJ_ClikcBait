# Faza 3b — Enkoderski modeli (izveštaj)

> Fine-tuning **BERTić** (`classla/bcms-bertic`, monolingvalni) i **mBERT**
> (`bert-base-multilingual-cased`, multilingvalni) na balansiranom skupu **2200**
> naslova (1100/1100). Protokol: **10-slojna stratifikovana CV**, varijante po
> **broju epoha (2/3/4)**, batch 64, max_len 64, lr 2e-5. Metrike identične
> baseline-u radi poređenja. Pokrenuto na Google Colab (T4 GPU).
> Sirovi rezultati: `results/encoder_bertic_results.csv`, `results/encoder_mbert_results.csv`.

## Rezultati (mean ± std preko 10 foldova)

### BERTić
| Epohe | F1(klikbejt) | Accuracy | Preciznost | Odziv | Macro-F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| **2** | **0.695** | **0.713** | 0.740 | 0.658 | 0.711 | 0.795 |
| 3 | 0.687 | 0.709 | 0.747 | 0.639 | 0.707 | 0.795 |
| 4 | 0.677 | 0.704 | 0.742 | 0.625 | 0.701 | 0.796 |

### mBERT
| Epohe | F1(klikbejt) | Accuracy | Preciznost | Odziv | Macro-F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| **2** | **0.707** | 0.690 | 0.672 | 0.759 | 0.685 | 0.757 |
| 3 | 0.676 | 0.690 | 0.713 | 0.651 | 0.689 | 0.760 |
| 4 | 0.666 | 0.686 | 0.714 | 0.626 | 0.684 | 0.759 |

## Diskusija

- **Broj epoha:** za oba modela **2 epohe daju najbolji F1**; sa 3 i 4 epohe F1 i
  odziv opadaju (overfitting na malom skupu), dok AUC ostaje ravan. Zaključak:
  kratak fine-tuning je optimalan.
- **Mono vs multi:** mBERT ima nešto viši F1 (0.707 vs 0.695), ali **BERTić je
  ukupno jači i stabilniji** — viša accuracy (0.713), AUC (0.795 vs 0.757),
  preciznost i macro-F1. mBERT postiže visok odziv (0.759) ali uz veliku
  nestabilnost (±0.117) i nižu preciznost (više lažno-pozitivnih). Monolingvalni
  BCMS model donosi uravnoteženiju odluku, što je očekivano za srpski.

## Poређење sa baseline-om (Faza 3a)

| Model | F1(klikbejt) | ROC-AUC |
|---|---|---|
| Baseline (MNB + stem + TF-IDF) | 0.646 | 0.676 |
| BERTić (2 epohe) | 0.695 | **0.795** |
| mBERT (2 epohe) | **0.707** | 0.757 |

Oba enkodera nadmašuju najbolji baseline, posebno po ROC-AUC (BERTić +0.12). Ovo
potvrđuje glavnu tezu: linearni/bag-of-words modeli teško hvataju suptilni
klikbejt, dok kontekstualni enkoderi znатно bolje razdvajaju klase.
