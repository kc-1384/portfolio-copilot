"""Tests for XIRR."""

from datetime import date
from decimal import Decimal

import pytest

from app.services.xirr import xirr

D = Decimal


def test_one_year_ten_percent() -> None:
    flows = [(date(2023, 1, 1), D("-1000")), (date(2024, 1, 1), D("1100"))]

    assert xirr(flows) == pytest.approx(0.10, abs=1e-9)


def test_matches_excel_documentation_example() -> None:
    # The worked example from Microsoft's XIRR documentation; Excel gives 0.373362535.
    flows = [
        (date(2008, 1, 1), D("-10000")),
        (date(2008, 3, 1), D("2750")),
        (date(2008, 10, 30), D("4250")),
        (date(2009, 2, 15), D("3250")),
        (date(2009, 4, 1), D("2750")),
    ]

    assert xirr(flows) == pytest.approx(0.373362535, abs=1e-6)


def test_losing_investment_gives_negative_rate() -> None:
    flows = [(date(2023, 1, 1), D("-1000")), (date(2024, 1, 1), D("800"))]

    assert xirr(flows) == pytest.approx(-0.20, abs=1e-9)


def test_order_of_cash_flows_does_not_matter() -> None:
    flows = [
        (date(2024, 1, 1), D("1100")),
        (date(2023, 1, 1), D("-1000")),
    ]

    assert xirr(flows) == pytest.approx(0.10, abs=1e-9)


def test_needs_money_in_and_out() -> None:
    assert xirr([(date(2023, 1, 1), D("-1000"))]) is None
    assert xirr([(date(2023, 1, 1), D("500")), (date(2024, 1, 1), D("600"))]) is None
