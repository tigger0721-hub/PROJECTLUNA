# Stock Master CSV Import

## Run

From `backend/`:

```bash
python -m scripts.import_stock_master_csv data/samples/stock_master_sample.csv
```

Required DB env vars:

- `DB_USER`
- `DB_PASSWORD`
- `DB_DSN`

## CSV format

Required columns:

- `symbol`
- `name_ko`
- `name_en`
- `market`
- `country`
- `provider`
- `provider_symbol`

Optional column:

- `is_active` (defaults to `true` when omitted or blank)

## Upsert rule

The importer upserts by the unique key `(provider, provider_symbol)`:

- existing key: update row fields (`symbol`, `name_ko`, `name_en`, `market`, `country`, `is_active`)
- missing key: insert new row
