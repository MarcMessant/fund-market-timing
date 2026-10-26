# Data

## Source

Daily data from 2 January 2024 to 22 September 2026, extracted from a Bloomberg terminal at Université Paris-Dauphine:

| Sheet | Fund | ISIN | Benchmark (Net Return) | Currency |
|---|---|---|---|---|
| `VICEX` | USA Mutuals Vice Fund, Investor class | US66538H3369 | MSCI ACWI NR USD | USD |
| `iShares ACWI` | iShares MSCI ACWI UCITS ETF (Acc) | IE00B6R52259 | MSCI ACWI NR USD | USD |
| `ODDO High Dividend` | ODDO BHF European High Dividend CR-EUR | FR0000989758 | MSCI Europe NR EUR | EUR |
| `Fundsmith` | Fundsmith Equity T Acc | GB00B4Q5X527 | MSCI World NR GBP | GBP |
| `Comgest` | Comgest Growth Emerging Markets EUR R Acc | IE00B65D2871 | MSCI EM NR EUR | EUR |

Risk-free rate in the fund's currency: SOFR (USD), €STR (EUR), SONIA (GBP).

**The raw data are not included.** Bloomberg and MSCI data are licensed and cannot be redistributed. The repository only contains estimates and aggregated statistics computed from them (`results/`).

## Expected format

One Excel workbook, one sheet per fund (sheet names as above), one row per business day, nine columns in this order (headers are ignored):

| # | Column | Used |
|---|---|---|
| 1 | Date | yes |
| 2 | Fund NAV | yes |
| 3 | Fund simple return | no |
| 4 | Fund log return | no |
| 5 | Benchmark level | yes |
| 6 | Benchmark simple return | no |
| 7 | Benchmark log return | no |
| 8 | Risk-free rate, annualised | no |
| 9 | Risk-free return over the interval since the previous row | yes |

Weekly and monthly returns are rebuilt from levels (exact compounding), not by summing daily returns.

## Adjustments applied to the real data

Both are set in `src/market_timing/config.py` (`Settings`) and switched off with `--raw`.

- **VICEX distributions.** The fund distributes and its published NAV is a price NAV: it drops by 3.0% on 9 Dec 2024 and 12.4% on 8 Dec 2025 with no market move. Distributions of USD 0.5814 and 2.8728 per share are reinvested at the ex-date. Check: on those days the adjusted fund return is −0.32% and −0.44% for an index return of −0.32% and −0.26%. Without the adjustment, the CAPM alpha falls from +1.5% to −5.8% a year against a Net Return index.
- **Fundsmith NAV timing.** The NAV is struck at noon UK time. In daily data its correlation with the benchmark is 0.21 same-day and 0.38 with the previous day. Shifting the NAV by one day does not fix weekly returns (correlation falls from 0.56 to 0.44), because the noon NAV mixes the previous US close and the current European morning. Weekly returns are therefore used, and the one-day shift only in the daily April 2025 event study.

## Synthetic data

`synthetic_fund_data.xlsx` has the same layout, with simulated funds whose timing is known (see `scripts/make_synthetic_data.py`). It lets the pipeline and the tests run without the licensed data:

```bash
python scripts/make_synthetic_data.py --out data/synthetic_fund_data.xlsx
python scripts/run_analysis.py --data data/synthetic_fund_data.xlsx --out results_synthetic --raw
```

The synthetic market includes a stylised April 2025 crash. As in the real data, that single week has a large leverage on the convexity terms: with this seed the passive control shows a Treynor-Mazuy γ with |t| > 2 that is worth 0.1% a year. This is why the passive control is checked on the economic value of timing, not on t-statistics.
