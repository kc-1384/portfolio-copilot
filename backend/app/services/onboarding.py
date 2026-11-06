"""Onboarding maths: how much loss a user can afford, and a 0-100 risk score.

The score is a transparent heuristic, not a regulated suitability assessment. Every point can be
traced to one answer, which is what we show the user.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.models.user import RiskType

ZERO = Decimal("0")

# Score weights (they add up to 100).
HORIZON_POINTS = Decimal("35")  # full points at a 15+ year horizon
LOSS_CAPACITY_POINTS = Decimal("35")  # full points if you can afford to lose 30% of savings
EMERGENCY_FUND_POINTS = Decimal("15")  # full points at 6 months of expenses saved
DEPENDENTS_POINTS = Decimal("15")  # minus 5 per dependent

FULL_HORIZON_YEARS = Decimal("15")
FULL_LOSS_CAPACITY = Decimal("0.30")
FULL_EMERGENCY_MONTHS = Decimal("6")


@dataclass(frozen=True)
class QuestionnaireAnswers:
    monthly_income: Decimal
    monthly_expenses: Decimal
    investable_savings: Decimal
    emergency_fund: Decimal
    money_needed_within_3_years: Decimal
    stated_max_loss: Decimal
    dependents: int
    horizon_years: int


@dataclass(frozen=True)
class RiskAssessment:
    affordable_loss: Decimal
    risk_score: int
    risk_type: RiskType


def affordable_loss(answers: QuestionnaireAnswers) -> Decimal:
    """min(what you say you can lose, savings that aren't spoken for), never below zero.

    "Spoken for" = the emergency fund plus money you'll need within 3 years: losing that would
    hurt your life, whatever you say you can tolerate.
    """
    free_savings = (
        answers.investable_savings - answers.emergency_fund - answers.money_needed_within_3_years
    )
    return max(ZERO, min(answers.stated_max_loss, free_savings))


def _fraction(value: Decimal, full_at: Decimal) -> Decimal:
    """value / full_at, clipped to the range 0..1."""
    if full_at <= 0:
        return ZERO
    return min(Decimal("1"), max(ZERO, value / full_at))


def assess_risk(answers: QuestionnaireAnswers) -> RiskAssessment:
    loss = affordable_loss(answers)

    horizon = HORIZON_POINTS * _fraction(Decimal(answers.horizon_years), FULL_HORIZON_YEARS)
    loss_capacity = (
        LOSS_CAPACITY_POINTS * _fraction(loss / answers.investable_savings, FULL_LOSS_CAPACITY)
        if answers.investable_savings > 0
        else ZERO
    )
    months_covered = (
        answers.emergency_fund / answers.monthly_expenses
        if answers.monthly_expenses > 0
        else FULL_EMERGENCY_MONTHS  # no expenses means any fund covers them
    )
    emergency = EMERGENCY_FUND_POINTS * _fraction(months_covered, FULL_EMERGENCY_MONTHS)
    dependents = max(ZERO, DEPENDENTS_POINTS - 5 * answers.dependents)

    score = int((horizon + loss_capacity + emergency + dependents).to_integral_value())
    return RiskAssessment(affordable_loss=loss, risk_score=score, risk_type=risk_type_for(score))


def risk_type_for(score: int) -> RiskType:
    if score < 35:
        return RiskType.CONSERVATIVE
    if score < 65:
        return RiskType.BALANCED
    return RiskType.AGGRESSIVE
