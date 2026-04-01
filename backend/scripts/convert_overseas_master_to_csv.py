from __future__ import annotations

import argparse
import csv
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_COLUMNS = [
    "symbol",
    "name_ko",
    "name_en",
    "market",
    "country",
    "provider",
    "provider_symbol",
    "is_active",
]

TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")
PROVIDER_SYMBOL_PATTERN = re.compile(r"^(NAS|NYS|AMS)[A-Z0-9][A-Z0-9.\-]{0,14}$")
MARKET_PATTERN = re.compile(r"^(NAS|NYS|AMS)$")


class ParseStats:
    def __init__(self) -> None:
        self.total_lines = 0
        self.parsed_rows = 0
        self.skipped_blank = 0
        self.skipped_malformed = 0
        self.skipped_unusable = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert KIS overseas stock master raw files (e.g. NASMST.COD) into normalized CSV "
            "for stock master import."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Raw overseas files to parse (e.g. stock_master_data/overseas/NASMST.COD)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="data/samples/stock_master_overseas.csv",
        help="Output CSV path (default: data/samples/stock_master_overseas.csv)",
    )
    return parser.parse_args()


def normalize_field(value: str) -> str:
    return value.strip().lstrip("I").strip()


def resolve_market(fields: list[str], source_path: Path) -> str | None:
    if len(fields) > 2:
        candidate = normalize_field(fields[2]).upper()
        if MARKET_PATTERN.match(candidate):
            return candidate

    stem = source_path.stem.upper()
    if stem.startswith("NAS"):
        return "NAS"
    if stem.startswith("NYS"):
        return "NYS"
    if stem.startswith("AMS"):
        return "AMS"

    for field in fields:
        candidate = normalize_field(field).upper()
        if MARKET_PATTERN.match(candidate):
            return candidate

    return None


def resolve_symbols(fields: list[str]) -> tuple[str | None, str | None]:
    symbol = normalize_field(fields[4]).upper() if len(fields) > 4 else ""
    provider_symbol = normalize_field(fields[5]).upper() if len(fields) > 5 else ""

    if not TICKER_PATTERN.match(symbol):
        symbol = ""
    if not PROVIDER_SYMBOL_PATTERN.match(provider_symbol):
        provider_symbol = ""

    if symbol and not provider_symbol:
        provider_symbol = symbol

    if not symbol:
        for field in fields:
            candidate = normalize_field(field).upper()
            if TICKER_PATTERN.match(candidate):
                symbol = candidate
                break

    if not provider_symbol:
        for field in fields:
            candidate = normalize_field(field).upper()
            if PROVIDER_SYMBOL_PATTERN.match(candidate):
                provider_symbol = candidate
                break

    return (symbol or None, provider_symbol or None)


def resolve_names(fields: list[str]) -> tuple[str, str]:
    name_en = normalize_field(fields[7]) if len(fields) > 7 else ""
    if not name_en or len(name_en) < 2:
        for field in fields:
            candidate = normalize_field(field)
            if " " in candidate and any(ch.isalpha() for ch in candidate):
                name_en = candidate
                break

    if not name_en:
        name_en = "UNKNOWN"

    name_ko = name_en
    return name_ko, name_en


def parse_file(path: Path, stats: ParseStats) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    with path.open("r", encoding="iso-8859-1", errors="replace") as handle:
        for raw_line in handle:
            stats.total_lines += 1
            line = raw_line.strip("\n\r")
            if not line.strip():
                stats.skipped_blank += 1
                continue

            fields = line.split("\t")
            if len(fields) < 6:
                stats.skipped_malformed += 1
                continue

            market = resolve_market(fields, path)
            symbol, provider_symbol = resolve_symbols(fields)
            name_ko, name_en = resolve_names(fields)

            if not market or not symbol or not provider_symbol:
                stats.skipped_unusable += 1
                continue

            rows.append(
                {
                    "symbol": symbol,
                    "name_ko": name_ko,
                    "name_en": name_en,
                    "market": market,
                    "country": "US",
                    "provider": "kis",
                    "provider_symbol": provider_symbol,
                    "is_active": "true",
                }
            )
            stats.parsed_rows += 1

    return rows


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = parse_args()

    input_paths = [Path(value) for value in args.inputs]
    output_path = Path(args.output)

    stats = ParseStats()
    result_rows: list[dict[str, str]] = []

    for path in input_paths:
        if not path.exists() or not path.is_file():
            logger.warning("Skipping missing input file: %s", path)
            continue

        logger.info("Parsing overseas raw file: %s", path)
        result_rows.extend(parse_file(path, stats))

    if not result_rows:
        logger.error("No valid rows parsed. Nothing written.")
        return 1

    result_rows.sort(key=lambda row: (row["market"], row["symbol"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(result_rows)

    logger.info(
        "Overseas conversion complete: output=%s rows=%s total_lines=%s skipped_blank=%s skipped_malformed=%s skipped_unusable=%s",
        output_path,
        len(result_rows),
        stats.total_lines,
        stats.skipped_blank,
        stats.skipped_malformed,
        stats.skipped_unusable,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
