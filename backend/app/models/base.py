"""Shared building blocks for all tables."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from sqlalchemy import DateTime, Enum, MetaData, Numeric, func
from sqlalchemy.orm import DeclarativeBase, mapped_column

# Predictable constraint names, so Alembic migrations can find and change them later.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Brief rule 2: money is exact. NUMERIC(18,4) in the database, Decimal in Python.
Money = Annotated[Decimal, mapped_column(Numeric(18, 4))]
# Share quantities can be fractional (US brokers sell fractional shares).
Quantity = Annotated[Decimal, mapped_column(Numeric(18, 6))]
# Exchange rates need more decimal places than money.
Rate = Annotated[Decimal, mapped_column(Numeric(18, 8))]


CreatedAt = Annotated[datetime, mapped_column(server_default=func.now())]
UpdatedAt = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=func.now())]


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Brief rule 3: every timestamp is stored with its time zone (PostgreSQL keeps it as UTC).
    type_annotation_map = {datetime: DateTime(timezone=True)}


def str_enum(enum_class: type[enum.StrEnum], name: str | None = None) -> Enum:
    """Store a Python enum as text plus a CHECK constraint (easier to migrate than a PG enum).

    `name` names the CHECK constraint; pass one when a table has two columns of the same enum.
    """
    return Enum(
        enum_class,
        name=name or enum_class.__name__.lower(),
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
        length=20,
        validate_strings=True,
    )


class Currency(enum.StrEnum):
    INR = "INR"
    USD = "USD"


class Exchange(enum.StrEnum):
    NSE = "NSE"
    BSE = "BSE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
