# Stock Master CSV Import

## Convert overseas raw files to CSV

From `backend/`:

```bash
python -m scripts.convert_overseas_master_to_csv \
  ../stock_master_data/overseas/NASMST.COD \
  ../stock_master_data/overseas/NYSMST.COD \
  ../stock_master_data/overseas/AMSMST.COD \
  -o data/samples/stock_master_overseas.csv
```

Notes:

- This converter currently supports **overseas tab-delimited `.COD` raw files only**.
- It intentionally does **not** parse domestic `.mst` files yet.
- It reads source files as `ISO-8859-1` and writes UTF-8 CSV.

## Run import

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
