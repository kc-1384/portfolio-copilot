"""Tests for FIFO lot accounting. Every number here can be checked by hand."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.portfolio import TransactionType
from app.services.fifo import OversellError, SplitEvent, Trade, run_fifo, split_currency_gain

BUY = TransactionType.BUY
SELL = TransactionType.SELL
D = Decimal


def test_sale_uses_oldest_shares_first() -> None:
    trades = [
        Trade(date(2024, 1, 10), BUY, D("10"), D("100"), fees=D("10")),  # cost 1,010
        Trade(date(2024, 2, 10), BUY, D("10"), D("120"), fees=D("10")),  # cost 1,210
        Trade(date(2024, 3, 10), SELL, D("15"), D("150"), fees=D("15")),  # proceeds 2,235
    ]

    result = run_fifo(trades)

    first, second = result.realized
    assert (first.quantity, first.cost, first.proceeds) == (D("10"), D("1010"), D("1490.0000"))
    assert (second.quantity, second.cost, second.proceeds) == (D("5"), D("605.0000"), D("745"))
    assert result.realized_gain == D("620")
    # 5 shares of the second lot remain, carrying the other half of its cost.
    assert result.quantity == D("5")
    assert result.cost_basis == D("605")


def test_unrealized_gain_uses_remaining_cost() -> None:
    result = run_fifo([Trade(date(2024, 1, 10), BUY, D("4"), D("250"), fees=D("5"))])

    assert result.unrealized_gain(current_price=D("300")) == D("195")  # 1,200 - 1,005


def test_rounding_never_loses_money() -> None:
    # 301 / 3 doesn't divide evenly; the three sales must still add up to exactly 301 of cost.
    trades = [Trade(date(2024, 1, 1), BUY, D("3"), D("100"), fees=D("1"))]
    trades += [Trade(date(2024, 2, day), SELL, D("1"), D("100")) for day in (1, 2, 3)]

    result = run_fifo(trades)

    costs = [r.cost for r in result.realized]
    assert sum(costs) == D("301")
    # Each piece is within 0.0001 of the exact 100.333...
    assert all(abs(cost - D("301") / 3) < D("0.0001") for cost in costs)
    assert result.open_lots == []


def test_selling_more_than_held_is_rejected() -> None:
    trades = [
        Trade(date(2024, 1, 1), BUY, D("5"), D("100")),
        Trade(date(2024, 1, 2), SELL, D("6"), D("100")),
    ]

    with pytest.raises(OversellError):
        run_fifo(trades)


def test_same_day_buy_and_sell_work_in_any_listed_order() -> None:
    trades = [
        Trade(date(2024, 5, 6), SELL, D("2"), D("110")),
        Trade(date(2024, 5, 6), BUY, D("2"), D("100")),
    ]

    result = run_fifo(trades)

    assert result.realized_gain == D("20")
    assert result.quantity == D("0")


def test_split_doubles_shares_and_keeps_cost() -> None:
    trades = [
        Trade(date(2024, 1, 1), BUY, D("10"), D("100")),  # cost 1,000
        Trade(date(2024, 9, 1), SELL, D("20"), D("60")),  # after the split
    ]
    splits = [SplitEvent(date(2024, 6, 1), ratio_old=D("1"), ratio_new=D("2"))]

    result = run_fifo(trades, splits)

    assert result.realized[0].quantity == D("20")
    assert result.realized_gain == D("200")  # 1,200 - 1,000


def test_holding_period_is_counted_per_lot() -> None:
    trades = [
        Trade(date(2023, 1, 1), BUY, D("1"), D("100")),
        Trade(date(2024, 1, 1), BUY, D("1"), D("100")),
        Trade(date(2024, 6, 30), SELL, D("2"), D("120")),
    ]

    old_lot, new_lot = run_fifo(trades).realized

    assert old_lot.holding_days == 546  # over a year: long-term in India for listed shares
    assert new_lot.holding_days == 181


def test_currency_gain_is_separated_from_price_gain() -> None:
    price_gain, currency_gain = split_currency_gain(
        cost=D("1000"), value=D("1100"), fx_at_cost=D("80"), fx_now=D("85")
    )

    assert price_gain == D("8500")
    assert currency_gain == D("5000")
    assert price_gain + currency_gain == D("1100") * D("85") - D("1000") * D("80")
