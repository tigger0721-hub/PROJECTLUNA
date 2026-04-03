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

# Assumption: domestic master rows start with a 6-digit numeric symbol.
SYMBOL_PATTERN = re.compile(r"^(\d{6})")
# Assumption: KRX ISIN-like code appears immediately after symbol (usually 12 chars).
ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{10}$")
# Keep broad Korean/latin punctuation footprint to avoid truncating valid names.
NAME_SANITIZE_PATTERN = re.compile(r"[^\w\s가-힣\-\.,&()\[\]/]+")

MARKET_BY_FILE = {
    "kospi_code.mst": "KOSPI",
    "kosdaq_code.mst": "KOSDAQ",
    "konex_code.mst": "KONEX",
    "nxt_kospi_code.mst": "NXT_KOSPI",
    "nxt_kosdaq_code.mst": "NXT_KOSDAQ",
    # ELW is intentionally skipped for now because the schema may differ.
    "elw_code.mst": None,
}


class ParseStats:
    def __init__(self) -> None:
        self.total_lines = 0
        self.parsed_rows = 0
        self.skipped_blank = 0
        self.skipped_no_symbol = 0
        self.skipped_no_name = 0
        self.skipped_unknown_market = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert domestic stock master fixed-width .mst files into normalized UTF-8 CSV "
            "for stock master import."
        )
    )
    parser.add_argument("inputs", nargs="+", help="Input domestic .mst files")
    parser.add_argument(
        "-o",
        "--output",
        default="data/samples/stock_master_domestic.csv",
        help="Output CSV path (default: data/samples/stock_master_domestic.csv)",
    )
    return parser.parse_args()


def decode_line(raw_line: bytes) -> str:
    """
    Decode one raw line.

    Assumption: upstream files are CP949-compatible. We fallback to EUC-KR and then
    replacement decoding to keep conversion robust during early rollout.
    """
    for encoding in ("cp949", "euc-kr"):
        try:
            return raw_line.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_line.decode("cp949", errors="replace")


def resolve_market(path: Path) -> str | None:
    return MARKET_BY_FILE.get(path.name.lower())


def extract_name(rest: str) -> str:
    """
    Extract Korean security name from the remainder of a fixed-width row.

    Assumptions:
    - `rest` begins after symbol(+optional ISIN-like code).
    - Name appears near the beginning of rest.
    - Two or more spaces usually separate the name from trailing fixed-width fields.
    """
    cleaned = rest.replace("\x00", " ").strip()
    if not cleaned:
        return ""

    first_block = re.split(r"\s{2,}", cleaned, maxsplit=1)[0].strip()
    first_block = NAME_SANITIZE_PATTERN.sub("", first_block).strip()

    if not first_block:
        return ""

    # In case the first block still contains extra single-space-delimited fields,
    # keep only a conservative leading window.
    tokens = first_block.split()
    if len(tokens) > 5:
        first_block = " ".join(tokens[:5])

    return first_block.strip()


def parse_line(raw_line: bytes) -> tuple[str | None, str | None]:
    line = decode_line(raw_line).rstrip("\r\n")
    if not line.strip():
        return None, None

    symbol_match = SYMBOL_PATTERN.match(line)
    if not symbol_match:
        return None, None

    symbol = symbol_match.group(1)
    remainder = line[symbol_match.end() :]

    # Assumption: domestic rows have an ISIN-like field right after symbol.
    maybe_isin = remainder[:12].strip().upper()
    if maybe_isin and ISIN_PATTERN.match(maybe_isin):
        remainder = remainder[12:]

    name_ko = extract_name(remainder)
    return symbol, (name_ko or None)


def parse_file(path: Path, market: str, stats: ParseStats) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    with path.open("rb") as handle:
        for raw_line in handle:
            stats.total_lines += 1

            if not raw_line.strip():
                stats.skipped_blank += 1
                continue

            symbol, name_ko = parse_line(raw_line)
            if not symbol:
                stats.skipped_no_symbol += 1
                continue
            if not name_ko:
                stats.skipped_no_name += 1
                continue

            rows.append(
                {
                    "symbol": symbol,
                    "name_ko": name_ko,
                    # Domestic source does not reliably provide English name yet.
                    "name_en": name_ko,
                    "market": market,
                    "country": "KR",
                    "provider": "naver",
                    "provider_symbol": symbol,
                    "is_active": "true",
                }
            )
            stats.parsed_rows += 1

    return rows


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = parse_args()

    result_rows: list[dict[str, str]] = []
    stats = ParseStats()

    for value in args.inputs:
        path = Path(value)
        if not path.exists() or not path.is_file():
            logger.warning("Skipping missing input file: %s", path)
            continue

        market = resolve_market(path)
        if not market:
            stats.skipped_unknown_market += 1
            logger.warning(
                "Skipping file with unknown or intentionally unsupported market mapping: %s",
                path,
            )
            continue

        logger.info("Parsing domestic raw file: %s (market=%s)", path, market)
        result_rows.extend(parse_file(path, market=market, stats=stats))

    if not result_rows:
        logger.error("No valid rows parsed. Nothing written.")
        return 1

    deduped_rows: dict[tuple[str, str], dict[str, str]] = {}
    for row in result_rows:
        key = (row["provider"], row["provider_symbol"])
        deduped_rows[key] = row

    output_rows = sorted(deduped_rows.values(), key=lambda row: (row["market"], row["symbol"]))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    logger.info(
        "Domestic conversion complete: output=%s rows=%s total_lines=%s parsed_rows=%s skipped_blank=%s skipped_no_symbol=%s skipped_no_name=%s skipped_unknown_market=%s",
        output_path,
        len(output_rows),
        stats.total_lines,
        stats.parsed_rows,
        stats.skipped_blank,
        stats.skipped_no_symbol,
        stats.skipped_no_name,
        stats.skipped_unknown_market,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
