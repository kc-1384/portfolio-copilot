"""Portfolios, transactions (the source of truth), cached holdings and file uploads."""

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    CreatedAt,
    Currency,
    Money,
    Quantity,
    Rate,
    UpdatedAt,
    str_enum,
)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[CreatedAt]


class TransactionType(enum.StrEnum):
    BUY = "buy"
    SELL = "sell"


class Transaction(Base):
    """One buy or sell. Brief rule 4: holdings are always recalculated from these rows."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint("fees >= 0", name="fees_non_negative"),
        Index(
            "ix_transactions_portfolio_instrument_date",
            "portfolio_id",
            "instrument_id",
            "trade_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"))
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"))
    type: Mapped[TransactionType] = mapped_column(str_enum(TransactionType))
    trade_date: Mapped[date]
    quantity: Mapped[Quantity]
    price: Mapped[Money]  # per share, in `currency`
    fees: Mapped[Money] = mapped_column(default=Decimal("0"))  # brokerage + taxes, in `currency`
    currency: Mapped[Currency] = mapped_column(str_enum(Currency))
    # Units of INR per 1 unit of `currency` on the trade date, if the broker reported it.
    fx_rate_to_inr: Mapped[Rate | None]
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("uploads.id", ondelete="SET NULL")
    )
    broker_reference: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[CreatedAt]


class Holding(Base):
    """Cache of current positions, rebuilt from transactions by the P&L engine.

    Never edited by hand: if it disagrees with the transactions, the transactions win.
    """

    __tablename__ = "holdings"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), primary_key=True
    )
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), primary_key=True)
    quantity: Mapped[Quantity]
    cost_basis: Mapped[Money]  # total cost of the open FIFO lots, in the instrument's currency
    updated_at: Mapped[UpdatedAt]


class UploadStatus(enum.StrEnum):
    RECEIVED = "received"
    PARSED = "parsed"
    NEEDS_REVIEW = "needs_review"
    IMPORTED = "imported"
    FAILED = "failed"


class Upload(Base):
    """A portfolio file a user uploaded, tracked through detect -> parse -> review -> save."""

    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    portfolio_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE")
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    detected_format: Mapped[str | None] = mapped_column(String(50))  # e.g. "zerodha_tradebook"
    status: Mapped[UploadStatus] = mapped_column(
        str_enum(UploadStatus), default=UploadStatus.RECEIVED
    )
    row_count: Mapped[int | None]
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
