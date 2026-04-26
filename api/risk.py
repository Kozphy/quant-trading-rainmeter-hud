"""Risk metric calculations for monitoring-only market history."""

from __future__ import annotations

import math
import statistics


def calculate_returns(values: list[float]) -> list[float]:
    """Calculate simple period returns from price history.

    Args:
        values: Ordered price values from oldest to newest.

    Returns:
        List of period returns expressed as decimals.
    """

    returns: list[float] = []
    for previous, current in zip(values, values[1:]):
        if previous != 0:
            returns.append((current - previous) / previous)
    return returns


def calculate_volatility(values: list[float]) -> float:
    """Calculate simple historical volatility from recent returns.

    Args:
        values: Ordered price values from oldest to newest.

    Returns:
        Return standard deviation as a percentage.
    """

    returns = calculate_returns(values)
    if len(returns) < 2:
        return 0.0

    return statistics.stdev(returns) * 100.0


def calculate_max_drawdown(values: list[float]) -> float:
    """Calculate maximum drawdown from a price path.

    Args:
        values: Ordered price values from oldest to newest.

    Returns:
        Largest peak-to-trough drawdown as a negative percentage.
    """

    if not values:
        return 0.0

    peak = values[0]
    max_drawdown = 0.0

    for price in values:
        peak = max(peak, price)
        if peak == 0:
            continue
        drawdown = (price - peak) / peak
        max_drawdown = min(max_drawdown, drawdown)

    return max_drawdown * 100.0


def calculate_sharpe_like_score(values: list[float]) -> float:
    """Calculate a simple Sharpe-like score from recent returns.

    Args:
        values: Ordered price values from oldest to newest.

    Returns:
        Mean return divided by return standard deviation, scaled by the square
        root of sample size. Returns 0 when insufficient data is available.
    """

    returns = calculate_returns(values)
    if len(returns) < 2:
        return 0.0

    volatility = statistics.stdev(returns)
    if volatility == 0:
        return 0.0

    return (statistics.mean(returns) / volatility) * math.sqrt(len(returns))


def build_risk_payload(values: list[float]) -> dict[str, float]:
    """Build monitoring risk metrics from market history.

    Args:
        values: Ordered price values from oldest to newest.

    Returns:
        Dictionary with volatility, max drawdown, Sharpe-like score, and zero
        exposure because this system does not trade.
    """

    return {
        "volatility": calculate_volatility(values),
        "drawdown": calculate_max_drawdown(values),
        "sharpe": calculate_sharpe_like_score(values),
        "exposure": 0.0,
    }
