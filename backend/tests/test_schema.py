"""Tests that the migrated database enforces the project's rules."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Instrument, Portfolio, Transaction, User
from app.models.base import Currency, Exchange
from app.models.portfolio import TransactionType


def make_instrument(session: Session) -> Instrument:
    instrument = Instrument(
        exchange=Exchange.NSE,
        symbol="RELIANCE",
        isin="INE002A01018",
        name="Reliance Industries Ltd",
        currency=Currency.INR,
        country="IN",
    )
    session.add(instrument)
    session.flush()
    return instrument


def make_portfolio(session: Session) -> Portfolio:
    user = User(email="test@example.com", password_hash="not-a-real-hash")
    session.add(user)
    session.flush()
    portfolio = Portfolio(user_id=user.id, name="Main")
    session.add(portfolio)
    session.flush()
    return portfolio


def test_migration_creates_every_model_table(db_session: Session) -> None:
    tables = set(inspect(db_session.connection()).get_table_names())

    assert set(Base.metadata.tables) <= tables


def test_price_tables_are_timescale_hypertables(db_session: Session) -> None:
    rows = db_session.execute(
        text("SELECT hypertable_name FROM timescaledb_information.hypertables")
    ).scalars()

    assert set(rows) == {"prices_daily", "prices_intraday"}


def test_money_is_stored_exactly(db_session: Session) -> None:
    instrument = make_instrument(db_session)
    portfolio = make_portfolio(db_session)
    db_session.add(
        Transaction(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            type=TransactionType.BUY,
            trade_date=date(2024, 1, 15),
            quantity=Decimal("3"),
            price=Decimal("2456.1234"),
            fees=Decimal("20.0100"),
            currency=Currency.INR,
        )
    )
    db_session.flush()

    price = db_session.execute(select(Transaction.price)).scalar_one()

    # A float would come back as 2456.1233999999...; NUMERIC gives back exactly what went in.
    assert price == Decimal("2456.1234")
    assert isinstance(price, Decimal)


def test_database_rejects_negative_quantity(db_session: Session) -> None:
    instrument = make_instrument(db_session)
    portfolio = make_portfolio(db_session)
    db_session.add(
        Transaction(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            type=TransactionType.BUY,
            trade_date=date(2024, 1, 15),
            quantity=Decimal("-1"),
            price=Decimal("100"),
            currency=Currency.INR,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_rejects_unknown_exchange(db_session: Session) -> None:
    # Bypass the Python enum on purpose: the CHECK constraint must still stop bad data.
    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO instruments (exchange, symbol, name, currency, asset_type, country,"
                " is_active) VALUES ('LSE', 'X', 'X', 'INR', 'equity', 'IN', true)"
            )
        )
