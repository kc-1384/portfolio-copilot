"""Market data: daily and intraday prices (TimescaleDB hypertables) and exchange rates."""

import datetime as dt
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Currency, Rate, str_enum

Price = Numeric(18, 4)


class PriceDaily(Base):
    """One row per instrument per trading day. Turned into a hypertable in the migration."""

    __tablename__ = "prices_daily"

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), primary_key=True
    )
    date: Mapped[dt.date] = mapped_column(primary_key=True)
    open: Mapped[Decimal] = mapped_column(Price)
    high: Mapped[Decimal] = mapped_column(Price)
    low: Mapped[Decimal] = mapped_column(Price)
    close: Mapped[Decimal] = mapped_column(Price)
    # Close adjusted for splits, bonuses and dividends; used for return calculations.
    adj_close: Mapped[Decimal] = mapped_column(Price)
    volume: Mapped[int] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(30))


class PriceIntraday(Base):
    """Live prices during market hours. Turned into a hypertable in the migration."""

    __tablename__ = "prices_intraday"

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), primary_key=True
    )
    ts: Mapped[dt.datetime] = mapped_column(primary_key=True)
    price: Mapped[Decimal] = mapped_column(Price)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(30))


class FxRate(Base):
    """Daily exchange rate: 1 unit of `base` = `rate` units of `quote` (e.g. 1 USD = 84.1 INR)."""

    __tablename__ = "fx_rates"

    base: Mapped[Currency] = mapped_column(str_enum(Currency, "base_currency"), primary_key=True)
    quote: Mapped[Currency] = mapped_column(str_enum(Currency, "quote_currency"), primary_key=True)
    date: Mapped[dt.date] = mapped_column(primary_key=True)
    rate: Mapped[Rate]
    source: Mapped[str] = mapped_column(String(30))
