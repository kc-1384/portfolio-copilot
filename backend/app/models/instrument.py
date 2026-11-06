"""Instrument master (every tradable stock/ETF) and corporate actions."""

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAt, Currency, Exchange, str_enum


class AssetType(enum.StrEnum):
    EQUITY = "equity"
    ETF = "etf"


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint("exchange", "symbol"),
        Index("ix_instruments_isin", "isin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange: Mapped[Exchange] = mapped_column(str_enum(Exchange))
    symbol: Mapped[str] = mapped_column(String(32))
    # ISIN is the global ID (e.g. INE002A01018). The same company on NSE and BSE shares one ISIN.
    isin: Mapped[str | None] = mapped_column(String(12))
    name: Mapped[str] = mapped_column(String(300))
    currency: Mapped[Currency] = mapped_column(str_enum(Currency))
    asset_type: Mapped[AssetType] = mapped_column(str_enum(AssetType), default=AssetType.EQUITY)
    country: Mapped[str] = mapped_column(String(2))  # ISO code: "IN", "US"
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(150))
    # Delisted stocks are kept (never deleted) so the ML data has no survivorship bias.
    is_active: Mapped[bool] = mapped_column(default=True)
    listed_on: Mapped[date | None]
    delisted_on: Mapped[date | None]
    created_at: Mapped[CreatedAt]


class CorporateActionType(enum.StrEnum):
    SPLIT = "split"
    BONUS = "bonus"
    DIVIDEND = "dividend"


class CorporateAction(Base):
    """A split, bonus issue or dividend.

    Splits and bonuses use a ratio: "ratio_new for ratio_old" shares. A 1:2 split (1 share
    becomes 2) is ratio_old=1, ratio_new=2. A 1:1 bonus (1 free share per share held) also gives
    2 shares for 1, so it is ratio_old=1, ratio_new=2.
    """

    __tablename__ = "corporate_actions"
    __table_args__ = (
        UniqueConstraint("instrument_id", "action_type", "ex_date"),
        CheckConstraint(
            "action_type = 'dividend' OR (ratio_old > 0 AND ratio_new > 0)", name="ratio_required"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="CASCADE"))
    action_type: Mapped[CorporateActionType] = mapped_column(str_enum(CorporateActionType))
    ex_date: Mapped[date]
    ratio_old: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ratio_new: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    dividend_per_share: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    source: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[CreatedAt]
