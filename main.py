"""Rank A-share stocks by P/B and dividend yield.

This script reads tickers from ``tickers.csv`` and retrieves the previous
trading day's closing price, book value per share, basic EPS and dividend
per share from a public API. It then computes P/B and dividend yield,
assigns ranks for each metric, sums the ranks to form a composite score and
exports the ranking to ``ranking.csv``.

The data source used here is Eastmoney's stock API. Network access is
required for the script to return data. When the API cannot be reached or a
particular field is missing, the script skips that metric for the affected
stock.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass
class StockRecord:
    """Basic stock information and calculated metrics."""

    ticker: str
    close: Optional[float] = None
    net_asset: Optional[float] = None
    eps: Optional[float] = None
    dividend: Optional[float] = None
    pb: Optional[float] = None
    dividend_yield: Optional[float] = None
    pb_rank: Optional[int] = None
    dy_rank: Optional[int] = None
    total_rank: Optional[int] = None


def load_tickers(path: str) -> List[str]:
    """Read a CSV file containing tickers and return the list."""

    tickers: List[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header_skipped = False
        for row in reader:
            if not header_skipped:
                header_skipped = True
                continue
            if row:
                tickers.append(row[0].strip())
    return tickers


def fetch_stock_data(ticker: str) -> StockRecord:
    """Fetch raw financial data for ``ticker`` from Eastmoney."""

    # Eastmoney uses ``secid`` consisting of market code and ticker without
    # suffix (1 for SH, 0 for SZ markets).
    code = ticker.split(".")[0]
    market = "1" if ticker.endswith("SH") or code.startswith("6") else "0"
    url = (
        "https://push2.eastmoney.com/api/qt/stock/get?fltt=2&" f"secid={market}.{code}&"
        "fields=f43,f170,f169,f168"
    )

    record = StockRecord(ticker=ticker)

    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8")).get("data", {})
    except URLError as err:
        print(f"Network error for {ticker}: {err}")
        return record

    record.close = _safe_float(data.get("f43"))
    record.net_asset = _safe_float(data.get("f170"))
    record.eps = _safe_float(data.get("f169"))
    record.dividend = _safe_float(data.get("f168"))

    if record.close and record.net_asset:
        record.pb = record.close / record.net_asset
    if record.close and record.dividend:
        record.dividend_yield = record.dividend / record.close

    return record


def _safe_float(value: Optional[str]) -> Optional[float]:
    """Convert ``value`` to float, returning ``None`` on failure."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rank_records(records: List[StockRecord]) -> List[StockRecord]:
    """Assign ranks based on P/B (ascending) and dividend yield (descending)."""

    pb_sorted = sorted(
        [r for r in records if r.pb is not None], key=lambda r: r.pb
    )
    for rank, record in enumerate(pb_sorted, 1):
        record.pb_rank = rank

    dy_sorted = sorted(
        [r for r in records if r.dividend_yield is not None],
        key=lambda r: r.dividend_yield,
        reverse=True,
    )
    for rank, record in enumerate(dy_sorted, 1):
        record.dy_rank = rank

    for record in records:
        ranks = [r for r in [record.pb_rank, record.dy_rank] if r is not None]
        if ranks:
            record.total_rank = sum(ranks)

    ranked = [r for r in records if r.total_rank is not None]
    ranked.sort(key=lambda r: r.total_rank)
    return ranked


def export_csv(records: List[StockRecord], path: str) -> None:
    """Write ``records`` to ``path`` in CSV format."""

    fieldnames = [
        "ticker",
        "close",
        "net_asset",
        "eps",
        "dividend",
        "pb",
        "dividend_yield",
        "pb_rank",
        "dy_rank",
        "total_rank",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r.__dict__)


def main() -> None:
    tickers = load_tickers("tickers.csv")
    records = [fetch_stock_data(t) for t in tickers]
    ranked = rank_records(records)
    export_csv(ranked, "ranking.csv")
    print(f"Processed {len(ranked)} stocks. Output written to ranking.csv")


if __name__ == "__main__":
    main()
