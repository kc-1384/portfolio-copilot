"""Database tables.

Importing this package registers every model on Base.metadata, which Alembic needs.
"""

from app.models.base import Base
from app.models.instrument import CorporateAction, Instrument
from app.models.market import FxRate, PriceDaily, PriceIntraday
from app.models.portfolio import Holding, Portfolio, Transaction, Upload
from app.models.user import Goal, InvestorProfile, User

__all__ = [
    "Base",
    "CorporateAction",
    "FxRate",
    "Goal",
    "Holding",
    "Instrument",
    "InvestorProfile",
    "Portfolio",
    "PriceDaily",
    "PriceIntraday",
    "Transaction",
    "Upload",
    "User",
]
