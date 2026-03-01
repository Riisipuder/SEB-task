from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime
from typing import Dict, Iterable, List
from urllib.request import urlopen

DAILY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip"
HISTORICAL_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"
TARGET_CURRENCIES = ("USD", "SEK", "GBP", "JPY")


def download_csv_rows_from_zip(url: str) -> List[Dict[str, str]]:
    """Download a ZIP from URL, read first CSV in it, and return rows."""
    with urlopen(url, timeout=30) as response:
        archive_bytes = response.read()

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(f"No CSV file found in archive: {url}")
        csv_content = archive.read(csv_names[0]).decode("utf-8")

    reader = csv.DictReader(io.StringIO(csv_content), skipinitialspace=True)
    return [dict(row) for row in reader]


def parse_daily_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, object]]:
    parsed: List[Dict[str, object]] = []
    for row in rows:
        date_value = row["Date"].strip()
        date_obj = datetime.strptime(date_value, "%d %B %Y").date()
        rates: Dict[str, float] = {}
        for currency in TARGET_CURRENCIES:
            raw_value = row.get(currency, "").strip()
            if raw_value and raw_value != "N/A":
                rates[currency] = float(raw_value)
        parsed.append({"date": date_obj.isoformat(), "rates": rates})
    return parsed


def parse_historical_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, object]]:
    parsed: List[Dict[str, object]] = []
    for row in rows:
        date_value = row["Date"].strip()
        date_obj = datetime.strptime(date_value, "%Y-%m-%d").date()
        rates: Dict[str, float] = {}
        for currency in TARGET_CURRENCIES:
            raw_value = row.get(currency, "").strip()
            if raw_value and raw_value != "N/A":
                rates[currency] = float(raw_value)
        parsed.append({"date": date_obj.isoformat(), "rates": rates})

    parsed.sort(key=lambda item: item["date"])
    return parsed


def calculate_historical_means(rows: Iterable[Dict[str, object]]) -> Dict[str, float]:
    totals = {currency: 0.0 for currency in TARGET_CURRENCIES}
    counts = {currency: 0 for currency in TARGET_CURRENCIES}

    for row in rows:
        rates = row["rates"]  # type: ignore[assignment]
        for currency in TARGET_CURRENCIES:
            value = rates.get(currency)  # type: ignore[union-attr]
            if value is not None:
                totals[currency] += float(value)
                counts[currency] += 1

    means: Dict[str, float] = {}
    for currency in TARGET_CURRENCIES:
        if counts[currency]:
            means[currency] = totals[currency] / counts[currency]
    return means


def write_exchange_rates_html(
    *,
    out_path: str,
    as_of_date: str,
    daily_rates: Dict[str, float],
    historical_means: Dict[str, float],
) -> None:
    def fmt(x: float | None) -> str:
        return "" if x is None else f"{x:.6f}"

    rows_html = []
    for ccy in TARGET_CURRENCIES:
        rows_html.append(
            "<tr>"
            f"<td>{ccy}</td>"
            f"<td>{fmt(daily_rates.get(ccy))}</td>"
            f"<td>{fmt(historical_means.get(ccy))}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Exchange Rates</title>
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; padding: 24px; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 720px; }}
    th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; }}
    th {{ background: #f6f6f6; }}
    caption {{ caption-side: top; text-align: left; font-weight: 700; margin-bottom: 10px; }}
    .meta {{ color: #555; margin: 0 0 14px 0; }}
  </style>
</head>
<body>
  <h1>Exchange Rates</h1>
  <p class="meta">Daily rates as of {as_of_date} (base: EUR). Historical mean from ECB historical dataset.</p>

  <table>
    <thead>
      <tr>
        <th>Currency Code</th>
        <th>Rate</th>
        <th>Mean Historical Rate</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


def main() -> None:
    daily_raw = download_csv_rows_from_zip(DAILY_URL)
    historical_raw = download_csv_rows_from_zip(HISTORICAL_URL)

    daily_data = parse_daily_rows(daily_raw)
    historical_data = parse_historical_rows(historical_raw)
    historical_means = calculate_historical_means(historical_data)

    latest = daily_data[0] if daily_data else {"date": "", "rates": {}}
    as_of_date = str(latest.get("date", ""))
    daily_rates = latest.get("rates", {})  

    write_exchange_rates_html(
        out_path="exchange_rates.html",  
        as_of_date=as_of_date,
        daily_rates=daily_rates,
        historical_means=historical_means,
    )


if __name__ == "__main__":
    main()