"""Tests for affordable loss and the risk score."""

from dataclasses import replace
from decimal import Decimal

from app.models.user import RiskType
from app.services.onboarding import QuestionnaireAnswers, affordable_loss, assess_risk

D = Decimal

# A typical answer set (₹): 10 lakh savings, 3 lakh emergency fund, 2 lakh needed soon.
BASE = QuestionnaireAnswers(
    monthly_income=D("100000"),
    monthly_expenses=D("50000"),
    investable_savings=D("1000000"),
    emergency_fund=D("300000"),
    money_needed_within_3_years=D("200000"),
    stated_max_loss=D("200000"),
    dependents=1,
    horizon_years=10,
)


def test_affordable_loss_is_the_stated_loss_when_savings_allow() -> None:
    # Free savings = 10L - 3L - 2L = 5L, more than the 2L stated.
    assert affordable_loss(BASE) == D("200000")


def test_affordable_loss_is_capped_by_free_savings() -> None:
    answers = replace(BASE, stated_max_loss=D("800000"))

    assert affordable_loss(answers) == D("500000")


def test_affordable_loss_is_never_negative() -> None:
    answers = replace(BASE, emergency_fund=D("900000"))  # more is spoken for than saved

    assert affordable_loss(answers) == D("0")


def test_risk_score_adds_up_from_each_answer() -> None:
    # horizon 10/15 x 35 = 23.33; loss 0.2/0.3 x 35 = 23.33; emergency 6/6 x 15 = 15;
    # dependents 15 - 5 = 10; total 71.67 -> 72
    result = assess_risk(BASE)

    assert result.risk_score == 72
    assert result.risk_type == RiskType.AGGRESSIVE


def test_no_free_money_means_conservative() -> None:
    answers = replace(
        BASE, emergency_fund=D("900000"), horizon_years=2, dependents=3, monthly_expenses=D("0")
    )
    # horizon 2/15 x 35 = 4.67; loss 0; emergency 15; dependents 0 -> 19.67 -> 20
    result = assess_risk(answers)

    assert result.affordable_loss == D("0")
    assert result.risk_score == 20
    assert result.risk_type == RiskType.CONSERVATIVE


def test_score_stays_within_0_and_100() -> None:
    extreme = replace(BASE, horizon_years=50, dependents=0, stated_max_loss=D("9999999"))

    assert 0 <= assess_risk(extreme).risk_score <= 100
