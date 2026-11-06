"""FIFO lot accounting: turns a list of buys and sells into open lots and realised gains.

FIFO = "first in, first out": a sale uses up the oldest shares first. This is the rule Indian tax
law uses for listed shares, and the US default.

All money is Decimal. Partial amounts are rounded to 4 decimal places and the last piece always
takes the remainder, so totals add up to the paisa/cent with nothing lost to rounding.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.models.portfolio import TransactionType

FOUR_PLACES = Decimal("0.0001")


@dataclass(frozen=True)
class Trade:
    trade_date: date
    side: TransactionType
    quantity: Decimal
    price: Decimal  # per share
    fees: Decimal = Decimal("0")  # total for the trade: brokerage, taxes, charges


@dataclass(frozen=True)
class SplitEvent:
    """A split or bonus: every `ratio_old` shares become `ratio_new` shares; total cost unchanged.

    For tax, Indian bonus shares are treated differently (zero cost, own date); the tax module
    (Phase 5) handles that. For portfolio P&L, spreading the cost is the standard view.
    """

    ex_date: date
    ratio_old: Decimal
    ratio_new: Decimal


@dataclass
class Lot:
    """Shares bought together, still held."""

    buy_date: date
    quantity: Decimal
    cost: Decimal  # total cost of these shares, fees included

    @property
    def unit_cost(self) -> Decimal:
        return self.cost / self.quantity


@dataclass(frozen=True)
class RealizedGain:
    """Part of a sale matched against one lot."""

    buy_date: date
    sell_date: date
    quantity: Decimal
    cost: Decimal
    proceeds: Decimal  # sale value after fees

    @property
    def gain(self) -> Decimal:
        return self.proceeds - self.cost

    @property
    def holding_days(self) -> int:
        return (self.sell_date - self.buy_date).days


@dataclass
class FifoResult:
    open_lots: list[Lot] = field(default_factory=list)
    realized: list[RealizedGain] = field(default_factory=list)

    @property
    def quantity(self) -> Decimal:
        return sum((lot.quantity for lot in self.open_lots), Decimal("0"))

    @property
    def cost_basis(self) -> Decimal:
        return sum((lot.cost for lot in self.open_lots), Decimal("0"))

    @property
    def realized_gain(self) -> Decimal:
        return sum((r.gain for r in self.realized), Decimal("0"))

    def unrealized_gain(self, current_price: Decimal) -> Decimal:
        return self.quantity * current_price - self.cost_basis


class OversellError(ValueError):
    """A sale of more shares than are held (short selling isn't supported)."""


def _share(amount: Decimal, part: Decimal, whole: Decimal) -> Decimal:
    return (amount * part / whole).quantize(FOUR_PLACES)


def run_fifo(trades: list[Trade], splits: list[SplitEvent] | None = None) -> FifoResult:
    """Replay trades for ONE instrument in date order and return open lots and realised gains.

    Same-day order: splits first (they take effect at the open), then buys, then sells, so an
    intraday buy-and-sell works whatever order the broker file lists it in.
    """
    events: list[tuple[date, int, Trade | SplitEvent]] = [(s.ex_date, 0, s) for s in splits or []]
    for trade in trades:
        if trade.quantity <= 0:
            raise ValueError(f"Trade quantity must be positive, got {trade.quantity}")
        order = 1 if trade.side == TransactionType.BUY else 2
        events.append((trade.trade_date, order, trade))
    events.sort(key=lambda event: (event[0], event[1]))

    result = FifoResult()
    for _, _, event in events:
        if isinstance(event, SplitEvent):
            for lot in result.open_lots:
                lot.quantity = lot.quantity * event.ratio_new / event.ratio_old
        elif event.side == TransactionType.BUY:
            cost = event.quantity * event.price + event.fees
            result.open_lots.append(Lot(event.trade_date, event.quantity, cost))
        else:
            _sell(result, event)
    return result


def _sell(result: FifoResult, sale: Trade) -> None:
    if sale.quantity > result.quantity:
        raise OversellError(
            f"Sale of {sale.quantity} on {sale.trade_date} exceeds holding of {result.quantity}"
        )
    total_proceeds = sale.quantity * sale.price - sale.fees
    to_match = sale.quantity
    proceeds_left = total_proceeds

    while to_match > 0:
        lot = result.open_lots[0]
        matched = min(lot.quantity, to_match)

        cost = lot.cost if matched == lot.quantity else _share(lot.cost, matched, lot.quantity)
        is_last_piece = matched == to_match
        proceeds = (
            proceeds_left if is_last_piece else _share(total_proceeds, matched, sale.quantity)
        )

        result.realized.append(RealizedGain(lot.buy_date, sale.trade_date, matched, cost, proceeds))
        lot.quantity -= matched
        lot.cost -= cost
        if lot.quantity == 0:
            result.open_lots.pop(0)
        to_match -= matched
        proceeds_left -= proceeds


def split_currency_gain(
    cost: Decimal, value: Decimal, fx_at_cost: Decimal, fx_now: Decimal
) -> tuple[Decimal, Decimal]:
    """Split a foreign holding's gain (in the home currency) into price gain and currency gain.

    Example: bought for $1,000 when $1 = ₹80, worth $1,100 now with $1 = ₹85.
    Total gain = 1,100 × 85 − 1,000 × 80 = ₹13,500, of which
      price gain    = (1,100 − 1,000) × 85 = ₹8,500  (the stock went up)
      currency gain = 1,000 × (85 − 80)   = ₹5,000  (the dollar went up)
    """
    price_gain = (value - cost) * fx_now
    currency_gain = cost * (fx_now - fx_at_cost)
    return price_gain, currency_gain
