# report/ — finalni izveštaj (Faza 4)

LaTeX izveštaj na srpskom (latinica). `izvestaj.tex` je glavni fajl.

## Workflow

```bash
# 1) grafici (posle Faze 2 za statistiku, posle Faze 3 za poređenje)
.venv/bin/pip install -r ../requirements-report.txt
.venv/bin/python ../src/report/make_figures.py     # -> figures/*.png

# 2) tabele rezultata (posle Faze 3)
.venv/bin/python ../src/report/make_tables.py       # -> tables/*.tex

# 3) kompajliranje
#  Overleaf:  otpremi ceo report/ folder, glavni fajl = izvestaj.tex (pdfLaTeX)
#  Lokalno:
pdflatex izvestaj.tex && bibtex izvestaj && pdflatex izvestaj.tex && pdflatex izvestaj.tex
```

## Napomene
- Skelet se **kompajlira odmah** — `tables/*.tex` imaju placeholder sadržaj, a
  slike su zaštićene `\IfFileExists` (ako PNG ne postoji, pokaže se okvir).
- Sadržaj sekcija se najvećim delom **prepisuje** iz `Faza1-plan.md`,
  `Faza2-plan.md`, `Faza3-plan.md` i `annotation/guidelines.md`.
- `tables/` i `figures/` se **regenerišu** skriptama — ne uređuj ručno.
- `\section`/`\subsection` već postavljeni; traži `% TODO` u `izvestaj.tex`.
