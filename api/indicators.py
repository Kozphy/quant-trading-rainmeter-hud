"""Technical indicator calculations for educational monitoring signals."""

from __future__ import annotations


def calculate_sma(values: list[float], period: int) -> float | None:
    """Calculate a simple moving average.

    Args:
        values: Ordered price values from oldest to newest.
        period: Number of latest values to average.

    Returns:
        The simple moving average, or None when there is not enough history.
    """

    if period <= 0 or len(values) < period:
        return None

    return sum(values[-period:]) / period


def calculate_rsi(values: list[float], period: int = 14) -> float | None:
    """Calculate the Relative Strength Index.

    Args:
        values: Ordered price values from oldest to newest.
        period: Number of recent price changes to use.

    Returns:
        RSI value from 0 to 100, or None when there is not enough history.
    """

    if period <= 0 or len(values) <= period:
        return None

    recent_values = values[-(period + 1) :]
    gains: list[float] = []
    losses: list[float] = []

    for previous, current in zip(recent_values, recent_values[1:]):
        change = current - previous
        if change >= 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))

    average_gain = sum(gains) / period
    average_loss = sum(losses) / period

    if average_loss == 0 and average_gain == 0:
        return 50.0
    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def calculate_price_change_percent(values: list[float], lookback: int = 24) -> float:
    """Calculate percentage price change over a lookback window.

    Args:
        values: Ordered price values from oldest to newest.
        lookback: Number of periods to compare against the latest value.

    Returns:
        Percentage change. Returns 0 when history is missing or invalid.
    """

    if len(values) < 2:
        return 0.0

    compare_index = max(0, len(values) - lookback - 1)
    start_price = values[compare_index]
    end_price = values[-1]
    if start_price == 0:
        return 0.0

    return ((end_price - start_price) / start_price) * 100.0


def classify_trend(price: float, sma20: float | None, sma50: float | None) -> str:
    """Classify the market regime from price and moving averages.

    Args:
        price: Latest market price.
        sma20: Latest 20-period simple moving average.
        sma50: Latest 50-period simple moving average.

    Returns:
        Regime label for the HUD: Trending, Sideways, or Risk-Off.
    """

    if sma20 is None or sma50 is None:
        return "Sideways"
    if price > sma20 > sma50:
        return "Trending"
    if price < sma20 < sma50:
        return "Risk-Off"
    return "Sideways"


def build_signal(price: float, sma20: float | None, sma50: float | None, rsi: float | None) -> str:
    """Build the educational monitoring signal.

    Args:
        price: Latest market price.
        sma20: Latest 20-period simple moving average.
        sma50: Latest 50-period simple moving average.
        rsi: Latest Relative Strength Index value.

    Returns:
        LONG, SHORT, or WAIT.
    """

    if sma20 is None or sma50 is None or rsi is None:
        return "WAIT"
    if price > sma20 > sma50 and 50.0 <= rsi <= 70.0:
        return "LONG"
    if price < sma20 < sma50 and rsi < 45.0:
        return "SHORT"
    return "WAIT"


def calculate_confidence(signal: str, price: float, sma20: float | None, sma50: float | None, rsi: float | None) -> float:
    """Calculate a simple confidence score for the educational signal.

    Args:
        signal: Signal label produced by build_signal.
        price: Latest market price.
        sma20: Latest 20-period simple moving average.
        sma50: Latest 50-period simple moving average.
        rsi: Latest Relative Strength Index value.

    Returns:
        Confidence score between 0 and 1.
    """

    if signal == "WAIT" or sma20 is None or sma50 is None or rsi is None or price == 0:
        return 0.5

    average_gap = abs(sma20 - sma50) / price
    trend_component = min(0.18, average_gap * 8.0)

    if signal == "LONG":
        rsi_component = max(0.0, min(0.12, (70.0 - rsi) / 100.0))
        return min(0.9, 0.62 + trend_component + rsi_component)

    rsi_component = max(0.0, min(0.12, (45.0 - rsi) / 100.0))
    return min(0.9, 0.60 + trend_component + rsi_component)


def build_indicator_payload(values: list[float]) -> dict[str, float | str]:
    """Build indicator values, signal, confidence, and regime.

    Args:
        values: Ordered price values from oldest to newest.

    Returns:
        Dictionary containing price, RSI, SMA values, price change, signal,
        confidence, and regime.
    """

    price = values[-1] if values else 0.0
    sma20 = calculate_sma(values, 20)
    sma50 = calculate_sma(values, 50)
    rsi = calculate_rsi(values)
    signal = build_signal(price, sma20, sma50, rsi)
    regime = classify_trend(price, sma20, sma50)

    return {
        "price": price,
        "price_change_percent": calculate_price_change_percent(values),
        "rsi": rsi if rsi is not None else 0.0,
        "sma20": sma20 if sma20 is not None else 0.0,
        "sma50": sma50 if sma50 is not None else 0.0,
        "signal": signal,
        "confidence": calculate_confidence(signal, price, sma20, sma50, rsi),
        "regime": regime,
    }
