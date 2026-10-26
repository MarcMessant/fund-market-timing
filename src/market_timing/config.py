"""Study configuration: funds, benchmarks, sample window and plotting palette."""
from dataclasses import dataclass, field

# Sheet names in the input workbook, in display order.
FUNDS = ["VICEX", "iShares ACWI", "ODDO High Dividend", "Fundsmith", "Comgest"]

SHORT = {
    "VICEX": "VICEX",
    "iShares ACWI": "ETF ACWI",
    "ODDO High Dividend": "ODDO HD",
    "Fundsmith": "Fundsmith",
    "Comgest": "Comgest EM",
}

LONG = {
    "VICEX": "USA Mutuals Vice Fund (VICEX)",
    "iShares ACWI": "iShares MSCI ACWI UCITS ETF (passive control)",
    "ODDO High Dividend": "ODDO BHF European High Dividend CR",
    "Fundsmith": "Fundsmith Equity T Acc",
    "Comgest": "Comgest Growth Emerging Markets R Acc",
}

BENCH = {
    "VICEX": "MSCI ACWI NR USD",
    "iShares ACWI": "MSCI ACWI NR USD",
    "ODDO High Dividend": "MSCI Europe NR EUR",
    "Fundsmith": "MSCI World NR GBP",
    "Comgest": "MSCI EM NR EUR",
}

CCY = {"VICEX": "USD", "iShares ACWI": "USD", "ODDO High Dividend": "EUR",
       "Fundsmith": "GBP", "Comgest": "EUR"}

PASSIVE_CONTROL = "iShares ACWI"

# Main sample: the two most recent years (weekly returns, Wednesday to Wednesday).
START, END = "2024-09-22", "2026-09-22"
PRE_WINDOW = ("2024-01-02", "2024-09-18")
CRASH_WEEK = "2025-04-09"
EPISODE = dict(start="2025-04-02", end="2025-04-23")

# One colour per fund, used on every figure.
PALETTE = {
    "VICEX": "#e34948",
    "iShares ACWI": "#8a8984",
    "ODDO High Dividend": "#2a78d6",
    "Fundsmith": "#008300",
    "Comgest": "#4a3aa7",
}
COMPONENTS = {
    "net_selectivity": "#eb6834",
    "diversification": "#1baf7a",
    "manager_risk": "#eda100",
    "investor_risk": "#c3c2b7",
}


@dataclass
class Settings:
    """Data adjustments that depend on the real data set.

    distributions : cash distributions reinvested at the ex-date, {fund: {ex_date: amount per share}}.
        VICEX publishes a price NAV that excludes distributions (source: VICEX dividend history).
    nav_lag : number of business days by which the fund NAV is shifted in the daily event study
        (Fundsmith values its NAV at noon UK time, so it lags the benchmark close by about one day).
    """
    distributions: dict = field(default_factory=lambda: {
        "VICEX": {"2024-12-09": 0.5814, "2025-12-08": 2.8728},
    })
    nav_lag: dict = field(default_factory=lambda: {"Fundsmith": 1})

    @classmethod
    def raw(cls):
        """No adjustment at all (used with synthetic data)."""
        return cls(distributions={}, nav_lag={})
