from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from .sources import educational_onchain


def _market(asset: str, days: int) -> pd.DataFrame:
    rng = np.random.default_rng(42 if asset == "DOT" else 43)
    dates = pd.date_range(pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(days=days - 1), periods=days)
    start, drift, volatility = (5.4, 0.0005, 0.025) if asset == "DOT" else (67000.0, 0.0007, 0.018)
    returns = rng.normal(drift, volatility, days)
    close = start * np.exp(np.cumsum(returns))
    open_price = np.r_[close[0] * 0.995, close[:-1]]
    spread = np.abs(rng.normal(0.012, 0.005, days))
    high = np.maximum(open_price, close) * (1 + spread)
    low = np.minimum(open_price, close) * (1 - spread)
    volume = rng.uniform(75_000_000, 180_000_000, days) if asset == "DOT" else rng.uniform(12_000_000_000, 30_000_000_000, days)
    return pd.DataFrame({
        "date": dates,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def collect_demo(days: int, compare: bool = True) -> dict:
    now = datetime.now(timezone.utc)
    market = _market("DOT", days)
    price = float(market.iloc[-1]["close"])
    titles = [
        ("Demo: Polkadot upgrade expands interoperability and developer adoption", "positive"),
        ("Demo: New parachain applications launch in the Polkadot ecosystem", "positive"),
        ("Demo: DOT staking participation shows stable growth", "positive"),
        ("Demo: Analysts discuss Polkadot governance improvements", "neutral"),
        ("Demo: Polkadot development update publishes technical documentation", "neutral"),
        ("Demo: DOT market volatility increases amid uncertain conditions", "negative"),
        ("Demo: Token unlock concerns create downside risk for DOT", "negative"),
        ("Demo: Crypto market correction affects Polkadot price", "negative"),
    ]
    news = [
        {
            "title": title,
            "url": "https://polkadot.com/",
            "source": "Демонстрационный набор",
            "published": (now - timedelta(hours=index * 9 + 2)).isoformat(),
            "expected_sentiment": expected,
        }
        for index, (title, expected) in enumerate(titles)
    ]
    return {
        "market": market,
        "compare_market": _market("BTC", days) if compare else None,
        "current": {
            "price": price,
            "market_cap": price * 1_520_000_000,
            "volume": float(market.iloc[-1]["volume"]),
            "change_24h": float((price / float(market.iloc[-2]["close"]) - 1) * 100),
            "circulating_supply": 1_520_000_000,
        },
        "compare_current": {"price": float(_market("BTC", 2).iloc[-1]["close"])} if compare else None,
        "news": news,
        "fear_greed": 47,
        "fear_greed_label": "Neutral",
        "onchain": {**educational_onchain(), "source_type": "demo"},
        "sources": [
            {"name": "Демонстрационный генератор", "category": "Все категории", "status": "demo", "message": "Синтетические данные, не котировки", "updated_at": now.isoformat()},
        ],
    }
