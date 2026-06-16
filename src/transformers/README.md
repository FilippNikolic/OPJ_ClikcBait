# Faza 3b — Enkoderski LLM (BERTić + mBERT) na Google Colab

Fine-tuning zahteva GPU (≥8 GB VRAM). Lokalni Mac (CPU) je presporo —
pokrećemo na **Google Colab** (besplatni T4 GPU) ili Azure studentskim kreditima.

## Brzi recept (Colab)

1. Colab → `Runtime → Change runtime type → GPU (T4)`.
2. U ćeliji:

   ```python
   !pip -q install transformers datasets accelerate scikit-learn
   from google.colab import files
   files.upload()   # otpremi dataset.tsv  (iz data/annotated/)
   ```

3. Otpremi i `finetune.py`, `__init__.py` iz `src/transformers/`, kao i ceo
   `src/baseline/` (zbog `common.py`). Ili kloniraj repo:

   ```python
   !git clone <repo-url> OPJ && cd OPJ
   # stavi dataset.tsv u data/annotated/
   ```

4. Pokreni oba modela sa varijantama epoha (2/3/4):

   ```python
   !python src/transformers/finetune.py --model bertic --epochs 2 3 4
   !python src/transformers/finetune.py --model mbert  --epochs 2 3 4
   ```

   Rezultati → `results/encoder_bertic_results.csv` i `..._mbert_results.csv`.
   Skini ih (`files.download(...)`) i ubaci u finalnu uporednu tabelu.

## Napomene

- **10-fold × 3 varijante epoha × 2 modela = 60 treninga.** Na T4 je to više
  sati. Za probu: `--quick` (2 fold-a) ili smanji `--epochs` na jednu vrednost.
- `--max-len 64`: naslovi su kratki, 64 tokena pokriva ~sve → brže i jeftinije.
- Metrike su IDENTIČNE baseline-u (`src/baseline/common.compute_metrics`) da bi
  tabela mono vs multi vs baseline bila direktno uporediva.
- BERTić = `classla/bcms-bertic` (mono, BCMS). mBERT = `bert-base-multilingual-cased`.
- Ako VRAM puca: smanji `--batch-size` (npr. 8) ili `--max-len`.
