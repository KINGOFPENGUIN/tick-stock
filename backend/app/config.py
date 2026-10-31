"""全局配置 — 从环境变量 / .env 读取。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.markets.registry import MarketCode, MarketRegistry

# ── 运行环境检测 ──────────────────────────────────────────
# PyInstaller 打包后: __file__ 指向临时解压目录 _MEIPASS, 不能作为路径基准。
# 此时:
#   - 只读资源 (tiers.yaml / 前端 dist) 放在 _MEIPASS 内
#   - 可写用户数据 (data_dir) 放在可执行文件旁的用户目录
# 非 frozen 模式 (开发/Docker): 保持原有 __file__ 推导, 行为完全不变。
_IS_FROZEN = getattr(sys, "frozen", False)


def _user_data_root() -> Path:
    """桌面版用户数据根目录。"""
    if _IS_FROZEN:
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "TSP"
        exe_dir = Path(sys.executable).resolve().parent
        return exe_dir / "data"

    return _PROJECT_ROOT / "data"


def _resource_root() -> Path:
    """只读资源根目录。"""
    if _IS_FROZEN:
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent.parent


def _project_root() -> Path:
    """项目根目录 (非 frozen 用)。"""
    return Path(__file__).resolve().parent.parent.parent


_PROJECT_ROOT = _project_root()
_RESOURCE_ROOT = _resource_root()
_ENV_FILE = Path(
    os.environ.get(
        "TICKFLOW_ENV_FILE",
        str(_RESOURCE_ROOT / ".env") if not _IS_FROZEN else ".env",
    )
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Market
    default_market: str = Field(
        default=MarketCode.CN.value,
        description="Default market: CN or US",
    )
    us_data_source: str = Field(
        default="none",
        description="US market data source: none | yfinance | polygon | finnhub | alpaca",
    )

    # US market data providers
    polygon_api_key: str = ""
    finnhub_api_key: str = ""
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""

    # TickFlow
    tickflow_api_key: str = Field(default="", description="留空启用 free 模式")

    # AI
    ai_provider: str = "openai_compat"
    ai_protocol: str = "chat_completions"
    ai_base_url: str = "https://llm.runninghub.ai/v1"
    ai_api_key: str = ""
    ai_model: str = "openai/gpt-6-astra-saver"
    ai_codex_command: str = "codex"
    ai_codex_reasoning_effort: str = ""
    ai_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    ai_max_output_tokens: int = 16384
    ai_context_window: int = 128000
    ai_round_checkpoint: int = 100

    # Server
    host: str = "0.0.0.0"
    port: int = 3018
    log_level: str = "INFO"
    backtest_range_guard: bool = False
    backtest_matrix_disk_cache_enabled: bool = True
    backtest_matrix_cache_max_mb: int = 512
    backtest_matrix_cache_prewarm: bool = True
    backtest_matrix_cache_prewarm_years: int = 5

    polars_collect_permits: int = 4
    polars_collect_background_permits: int = 2

    watchdog_enabled: bool = True
    watchdog_interval_s: float = 30.0
    watchdog_probe_timeout_s: float = 15.0
    watchdog_failure_threshold: int = 2

    strategy_run_all_workers: int = 1
    strategy_run_all_first_return_s: float = 15.0
    api_sync_thread_pool: int = 100

    auth_password: str = ""

    data_dir: Path = _user_data_root()
    tiers_yaml: Path = _RESOURCE_ROOT / "tiers.yaml" if _IS_FROZEN else _PROJECT_ROOT / "tiers.yaml"
    static_dir: Path = _RESOURCE_ROOT / "static" if _IS_FROZEN else (_PROJECT_ROOT / "frontend" / "dist")

    @model_validator(mode="after")
    def _resolve_paths(self) -> Settings:
        """Validate market settings and ensure data_dir is absolute."""
        self.default_market = self.default_market.upper()
        if not MarketRegistry.is_supported(self.default_market):
            raise ValueError(
                f"Unsupported default_market: {self.default_market}; expected CN or US"
            )

        self.us_data_source = self.us_data_source.lower()
        allowed_sources = {"none", "yfinance", "polygon", "finnhub", "alpaca"}
        if self.us_data_source not in allowed_sources:
            raise ValueError(
                f"Unsupported us_data_source: {self.us_data_source}; "
                f"expected one of {sorted(allowed_sources)}"
            )

        if not self.data_dir.is_absolute():
            self.data_dir = (_PROJECT_ROOT / self.data_dir).resolve()
        if self.backtest_matrix_cache_max_mb <= 0:
            raise ValueError("backtest_matrix_cache_max_mb must be positive")
        if self.backtest_matrix_cache_prewarm_years <= 0:
            raise ValueError("backtest_matrix_cache_prewarm_years must be positive")
        if self.ai_max_output_tokens <= 0:
            raise ValueError("ai_max_output_tokens must be positive")
        if self.ai_context_window <= 0:
            raise ValueError("ai_context_window must be positive")
        if self.polars_collect_permits < 2:
            raise ValueError("polars_collect_permits must be >= 2")
        if not 1 <= self.polars_collect_background_permits < self.polars_collect_permits:
            raise ValueError(
                "polars_collect_background_permits must be in [1, polars_collect_permits)"
            )
        if self.watchdog_interval_s <= 0 or self.watchdog_probe_timeout_s <= 0:
            raise ValueError("watchdog intervals must be positive")
        if self.watchdog_failure_threshold < 1:
            raise ValueError("watchdog_failure_threshold must be >= 1")
        if self.strategy_run_all_workers < 1:
            raise ValueError("strategy_run_all_workers must be >= 1")
        if self.strategy_run_all_first_return_s < 0:
            raise ValueError("strategy_run_all_first_return_s must be >= 0")
        return self

    @property
    def use_free_mode(self) -> bool:
        """是否走 Free 模式。优先看 secrets.json,其次看 .env。"""
        from app import secrets_store
        return not secrets_store.get_tickflow_key()

    @property
    def is_us_market(self) -> bool:
        return self.default_market == MarketCode.US.value

    @property
    def is_cn_market(self) -> bool:
        return self.default_market == MarketCode.CN.value


def get_default_market() -> str:
    return settings.default_market


def is_us_market() -> bool:
    return settings.is_us_market


def is_cn_market() -> bool:
    return settings.is_cn_market


settings = Settings()
