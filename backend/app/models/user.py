"""Users, their investor profile (questionnaire answers) and goals."""

import enum
import uuid
from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    CreatedAt,
    Currency,
    Money,
    UpdatedAt,
    str_enum,
)


class RiskType(enum.StrEnum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Stored lower-cased by the auth code, so the unique index also blocks "A@x.com" vs "a@x.com".
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    is_email_verified: Mapped[bool] = mapped_column(default=False)
    # Optional TOTP two-factor secret (will be encrypted before storing).
    totp_secret: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    profile: Mapped["InvestorProfile | None"] = relationship(back_populates="user")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user")


class InvestorProfile(Base):
    """Onboarding questionnaire answers plus the derived affordable loss and risk score."""

    __tablename__ = "investor_profiles"
    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_score_range"),
        CheckConstraint("dependents >= 0", name="dependents_non_negative"),
        CheckConstraint("horizon_years >= 0", name="horizon_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # All money answers are in this currency.
    base_currency: Mapped[Currency] = mapped_column(str_enum(Currency))
    monthly_income: Mapped[Money]
    monthly_expenses: Mapped[Money]
    investable_savings: Mapped[Money]
    emergency_fund: Mapped[Money]
    money_needed_within_3_years: Mapped[Money]
    stated_max_loss: Mapped[Money]
    dependents: Mapped[int]
    horizon_years: Mapped[int]

    # Derived by app.services.onboarding; stored so every screen shows the same number.
    affordable_loss: Mapped[Money]
    risk_score: Mapped[int]
    risk_type: Mapped[RiskType] = mapped_column(str_enum(RiskType))
    updated_at: Mapped[UpdatedAt]

    user: Mapped[User] = relationship(back_populates="profile")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    target_amount: Mapped[Money]
    currency: Mapped[Currency] = mapped_column(str_enum(Currency))
    target_date: Mapped[date]
    created_at: Mapped[CreatedAt]

    user: Mapped[User] = relationship(back_populates="goals")
