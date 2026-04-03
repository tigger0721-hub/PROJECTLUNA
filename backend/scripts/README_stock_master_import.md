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

- Overseas converter supports tab-delimited `.COD` raw files.
- It reads source files as `ISO-8859-1` and writes UTF-8 CSV.

## Convert domestic raw files to CSV

From `backend/`:

```bash
python -m scripts.convert_domestic_master_to_csv \
  /home/ubuntu/stock-chart-tutor-dev/stock_master_data/domestic/kospi_code.mst \
  /home/ubuntu/stock-chart-tutor-dev/stock_master_data/domestic/kosdaq_code.mst \
  /home/ubuntu/stock-chart-tutor-dev/stock_master_data/domestic/konex_code.mst \
  /home/ubuntu/stock-chart-tutor-dev/stock_master_data/domestic/nxt_kospi_code.mst \
  /home/ubuntu/stock-chart-tutor-dev/stock_master_data/domestic/nxt_kosdaq_code.mst \
  -o data/samples/stock_master_domestic.csv
```

Domestic converter assumptions:

- Input `.mst` rows are fixed-width and CP949-compatible.
- Symbol is parsed from the leading 6-digit field.
- A 12-char ISIN-like value right after symbol is skipped when present.
- Korean name is extracted from the first text block before wide-spacing in each row.
- `country=KR`, `provider=naver`, `provider_symbol=symbol`, `name_en=name_ko` (temporary fallback).
- `elw_code.mst` is currently skipped by default because its row structure can differ.

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
