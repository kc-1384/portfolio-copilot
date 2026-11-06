"""XIRR: the annual return of investments made at different dates.

A plain "% gain" ignores time: 10% in one month and 10% in five years look the same. XIRR finds
the yearly rate r that makes the cash flows' present value zero:

    sum( cash_flow_i / (1 + r) ^ (days_since_first_i / 365) ) = 0

Money goes in as Decimal; the returned rate is a float because it's a ratio, not money, and the
solver works in floating point. Convention: money you put in is negative, money you get back
(sales, dividends, today's value) is positive.
"""

from datetime import date
from decimal import Decimal

from scipy.optimize import brentq

LOWEST_RATE = -0.9999  # -100% would divide by zero
HIGHEST_RATE = 100.0  # +10,000% a year; anything above is treated as "can't compute"


def xirr(cash_flows: list[tuple[date, Decimal]]) -> float | None:
    """Annualised return, e.g. 0.12 for 12% a year, or None if it can't be computed."""
    if not any(amount > 0 for _, amount in cash_flows) or not any(
        amount < 0 for _, amount in cash_flows
    ):
        return None  # need money both in and out

    start = min(day for day, _ in cash_flows)
    flows = [((day - start).days / 365.0, float(amount)) for day, amount in cash_flows]

    def net_present_value(rate: float) -> float:
        return sum(amount / (1.0 + rate) ** years for years, amount in flows)

    low_value = net_present_value(LOWEST_RATE)
    high_value = net_present_value(HIGHEST_RATE)
    if low_value * high_value > 0:
        return None  # no sign change in range, so no root to find

    return float(brentq(net_present_value, LOWEST_RATE, HIGHEST_RATE, xtol=1e-12, maxiter=500))
