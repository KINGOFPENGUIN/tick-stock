"""Market time utilities.

CN market uses fixed Beijing time (UTC+8, no DST).
US market uses America/New_York, including DST.
"""
from __future__ import annotations

from datetime import date, datetime, time as dt_time, timedelta, timezone
from zoneinfo import ZoneInfo

CN_TZ = timezone(timedelta(hours=8))
US_TZ = ZoneInfo("America/New_York")

# A 股交易时段 (北京时间): 上午 9:30-11:30 (120 分钟) + 下午 13:00-15:00 (120 分钟) = 240 分钟
_TRADING_TOTAL_MINUTES = 240
_MORNING_START = dt_time(9, 30)
_MORNING_END = dt_time(11, 30)
_AFTERNOON_START = dt_time(13, 0)
_AFTERNOON_END = dt_time(15, 0)

# US regular session (Eastern Time)
_US_PREMARKET_START = dt_time(4, 0)
_US_REGULAR_START = dt_time(9, 30)
_US_REGULAR_END = dt_time(16, 0)
_US_AFTERHOURS_END = dt_time(20, 0)


def cn_now() -> datetime:
    """当前北京时间 (带时区)。"""
    return datetime.now(CN_TZ)


def cn_today() -> date:
    """当前北京日期。"""
    return datetime.now(CN_TZ).date()


def us_now() -> datetime:
    """当前美东时间 (带时区)。"""
    return datetime.now(US_TZ)


def us_today() -> date:
    """当前美东日期。"""
    return datetime.now(US_TZ).date()


def in_continuous_session(now: datetime | None = None) -> bool:
    """A股连续竞价时段 (北京时间): 9:30-11:30 / 13:00-15:00, 仅工作日。"""
    now = now or cn_now()
    return now.weekday() < 5 and (
        _MORNING_START <= now.time() <= _MORNING_END
        or _AFTERNOON_START <= now.time() <= _AFTERNOON_END
    )


def us_session(now: datetime | None = None) -> str:
    """Return the current US session by Eastern Time.

    Returns one of: premarket, regular, afterhours, closed.
    Trading-day validation is handled by services.trading_day.
    """
    now = now or us_now()
    t = now.time()

    if _US_PREMARKET_START <= t < _US_REGULAR_START:
        return "premarket"
    if _US_REGULAR_START <= t < _US_REGULAR_END:
        return "regular"
    if _US_REGULAR_END <= t < _US_AFTERHOURS_END:
        return "afterhours"
    return "closed"


def market_now(market: str = "CN") -> datetime:
    """Return current time for a supported market."""
    market = market.upper()
    if market == "CN":
        return cn_now()
    if market == "US":
        return us_now()
    raise ValueError(f"Unsupported market: {market}")


def trading_minutes_elapsed_from_dt(dt: datetime) -> float:
    """根据北京时间 datetime 计算当日已交易分钟数。

    交易时段: 9:30-11:30 (0~120) + 13:00-15:00 (120~240)。
    - 开盘前 = 0; 午休(11:30-13:00) = 120(保持上午累计); 收盘后 = 240。
    - 非交易日(周末) = 240 (视作全天, 避免量比被折算成 0)。
    """
    if dt.weekday() >= 5:
        return float(_TRADING_TOTAL_MINUTES)
    t = dt.time()
    if t < _MORNING_START:
        return 0.0
    if t < _MORNING_END:
        return (dt.hour * 60 + dt.minute - 9 * 60 - 30) + dt.second / 60.0
    if t < _AFTERNOON_START:
        return 120.0  # 午休, 保持上午累计
    if t < _AFTERNOON_END:
        return 120.0 + (dt.hour * 60 + dt.minute - 13 * 60) + dt.second / 60.0
    return float(_TRADING_TOTAL_MINUTES)


def trading_minutes_elapsed() -> float:
    """当前已交易分钟数 (基于服务端北京时间)。"""
    return trading_minutes_elapsed_from_dt(cn_now())


def trading_minutes_elapsed_from_ts(ts_ms: int | float | None) -> float:
    """从行情时间戳(毫秒)计算当日已交易分钟数。"""
    if not ts_ms:
        return float(_TRADING_TOTAL_MINUTES)
    try:
        dt = datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=CN_TZ)
    except (ValueError, TypeError, OSError):
        return float(_TRADING_TOTAL_MINUTES)
    return trading_minutes_elapsed_from_dt(dt)
