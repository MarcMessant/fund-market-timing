"""Market timing of fund managers: Treynor-Mazuy, Henriksson-Merton and Fama decomposition."""
from .config import FUNDS, Settings
from .data import FundData

__all__ = ["FUNDS", "Settings", "FundData"]
__version__ = "1.0.0"
