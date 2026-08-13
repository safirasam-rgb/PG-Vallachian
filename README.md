# Valassky PG index

Ranni paraglidingovy report pro Valassko.

Umi:

- stahnout cerstvou predpoved z Open-Meteo,
- vygenerovat PG index pro dnes, zitra a pozitri,
- vytvorit webova data pro GitHub Pages,
- kazde rano automaticky nasadit aktualni web.

## Manualni spusteni workflow

V GitHubu otevri:

```text
Actions -> Daily PG forecast -> Run workflow
```

Workflow stahne nova data, vytvori:

```text
docs/data/latest.json
```

a nasadi obsah slozky `docs` na GitHub Pages.

## Automaticka obnova

Workflow bezi denne v:

```text
05:00 UTC
```

To odpovida 07:00 v Cesku behem letniho casu.

## Omezeni

Toto neni bezpecnostni autorita. Je to lokalni index pro trideni dnu. Bourky nejsou automaticky stop; jsou samostatna rizikova poznamka.
