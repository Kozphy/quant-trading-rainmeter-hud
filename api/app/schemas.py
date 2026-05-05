"""Typed API schemas for the monitoring HUD contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MarketSnapshot(BaseModel):
    """Market prices and 24h changes used by the HUD."""

    btc_price: float = 0.0
    btc_change_24h: float = 0.0
    eth_price: float = 0.0
    eth_change_24h: float = 0.0


class SignalSnapshot(BaseModel):
    """Signal engine output for monitoring-only visibility."""

    action: Literal["LONG", "SHORT", "WAIT"] = "WAIT"
    confidence: float = 0.5
    regime: str = "Sideways"
    reason: str = "No signal rules triggered."
    rules_triggered: list[str] = Field(default_factory=list)


class RiskSnapshot(BaseModel):
    """Monitoring-safe risk metrics without account exposure data."""

    realized_volatility_24h: float = 0.0
    price_drawdown_from_recent_high: float = 0.0
    signal_flip_count_1h: int = 0
    data_staleness_seconds: int = 0


class SystemStatus(BaseModel):
    """System liveness and freshness metadata for HUD status states."""

    bot_status: Literal["RUNNING", "WARNING", "ERROR"] = "RUNNING"
    data_status: Literal["LIVE", "STALE", "ERROR"] = "LIVE"
    latency_ms: int = 0
    last_success_at: str | None = None
    updated_at: str


class HUDDataResponse(BaseModel):
    """Stable API contract consumed by Rainmeter HUD."""

    market: MarketSnapshot
    signal: SignalSnapshot
    risk: RiskSnapshot
    system: SystemStatus


class CalendarTask(BaseModel):
    """One calendar task row displayed on the HUD."""

    time: str
    name: str


class CalendarResponse(BaseModel):
    """Calendar endpoint response with static operations tasks."""

    date: str
    tasks: list[CalendarTask]

