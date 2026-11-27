from __future__ import annotations

import os
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import pandas as pd
import requests


COINGECKO = "https://api.coingecko.com/api/v3"
BINANCE = "https://api.binance.com/api/v3"


def _request(method: str, url: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", "PolkaInsight/1.0 educational project")
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = requests.request(method, url, headers=headers, timeout=(4, 7), **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt == 0:
                time.sleep(0.6)
    detail = f"HTTP {last_error.response.status_code}" if isinstance(last_error, requests.HTTPError) and last_error.response is not None else type(last_error).__name__
    raise RuntimeError(f"Внешний API недоступен ({detail})") from None


def _chart_frame(payload: dict) -> pd.DataFrame:
    prices = payload.get("prices", [])
    volumes = {int(item[0]): float(item[1]) for item in payload.get("total_volumes", [])}
    if not prices:
        raise RuntimeError("CoinGecko вернул пустой временной ряд")
    rows = []
    for timestamp, price in prices:
        close = float(price)
        rows.append({
            "date": pd.to_datetime(int(timestamp), unit="ms", utc=True),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": volumes.get(int(timestamp), 0.0),
        })
    return pd.DataFrame(rows)


def _coingecko(days: int, compare: bool) -> dict:
    ids = "polkadot,bitcoin" if compare else "polkadot"
    markets_response = _request("GET", f"{COINGECKO}/coins/markets", params={
        "vs_currency": "usd", "ids": ids, "price_change_percentage": "24h"
    }).json()
    if not isinstance(markets_response, list) or not markets_response:
        raise RuntimeError("CoinGecko не вернул рыночные показатели")
    market_by_id = {item["id"]: item for item in markets_response}
    dot = _request("GET", f"{COINGECKO}/coins/polkadot/market_chart", params={
        "vs_currency": "usd", "days": days
    }).json()
    result = {"market": _chart_frame(dot), "current_raw": market_by_id["polkadot"], "compare_market": None, "compare_current_raw": None}
    if compare:
        btc = _request("GET", f"{COINGECKO}/coins/bitcoin/market_chart", params={
            "vs_currency": "usd", "days": days
        }).json()
        result["compare_market"] = _chart_frame(btc)
        result["compare_current_raw"] = market_by_id.get("bitcoin")
    return result


def _binance(days: int) -> pd.DataFrame:
    payload = _request("GET", f"{BINANCE}/klines", params={
        "symbol": "DOTUSDT", "interval": "1d", "limit": min(1000, max(35, days))
    }).json()
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("Binance вернул пустой набор свечей")
    return pd.DataFrame([{
        "date": pd.to_datetime(int(row[0]), unit="ms", utc=True),
        "open": float(row[1]),
        "high": float(row[2]),
        "low": float(row[3]),
        "close": float(row[4]),
        "volume": float(row[5]),
    } for row in payload])


def _fear_greed() -> dict:
    payload = _request("GET", "https://api.alternative.me/fng/", params={"limit": 30}).json()
    current = payload["data"][0]
    return {"value": int(current["value"]), "label": current.get("value_classification", "")}


def _rss_news(url: str, default_source: str, params: dict | None = None) -> list[dict]:
    response = _request("GET", url, params=params or {})
    root = ET.fromstring(response.text)
    news = []
    for item in root.findall(".//item")[:20]:
        published = item.findtext("pubDate", "")
        if published:
            try:
                published = parsedate_to_datetime(published).isoformat()
            except (TypeError, ValueError):
                pass
        news.append({
            "title": item.findtext("title", ""),
            "url": item.findtext("link", ""),
            "source": item.findtext("source", default_source),
            "published": published,
        })
    return news


def _google_news() -> list[dict]:
    return _rss_news("https://news.google.com/rss/search", "Google News", {
        "q": "Polkadot DOT", "hl": "en-US", "gl": "US", "ceid": "US:en"
    })


def _cointelegraph_news() -> list[dict]:
    return _rss_news("https://cointelegraph.com/rss/tag/polkadot", "Cointelegraph")


def _news() -> tuple[list[dict], str]:
    providers = []
    if os.getenv("CRYPTOPANIC_API_KEY"):
        def cryptopanic() -> list[dict]:
            payload = _request("GET", "https://cryptopanic.com/api/developer/v2/posts/", params={
                "auth_token": os.getenv("CRYPTOPANIC_API_KEY"), "public": "true", "currencies": "DOT", "kind": "news"
            }).json()
            return [{
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": (item.get("source") or {}).get("title", "CryptoPanic"),
                "published": item.get("published_at", ""),
            } for item in payload.get("results", [])[:20]]
        providers.append(("CryptoPanic", cryptopanic))
    providers.extend([
        ("Google News RSS", _google_news),
        ("Cointelegraph Polkadot RSS", _cointelegraph_news),
    ])
    for name, provider in providers:
        try:
            news = provider()
            if news:
                return news, name
        except Exception:
            continue
    raise RuntimeError("Внешние новостные источники недоступны")


def educational_news() -> list[dict]:
    titles = [
        "Учебный пример: обновление технологии Polkadot",
        "Учебный пример: развитие приложений в экосистеме",
        "Учебный пример: изменение активности стейкинга DOT",
        "Учебный пример: обсуждение предложения OpenGov",
        "Учебный пример: рост рыночной волатильности",
        "Учебный пример: риски внешнего криптовалютного рынка",
    ]
    return [{
        "title": title,
        "url": "https://polkadot.com/",
        "source": "Локальный учебный набор",
        "published": "",
        "sentiment": "not_used",
    } for title in titles]


def _rpc_batch(endpoint: str, calls: list[tuple[str, list]]) -> list:
    payload = [
        {"jsonrpc": "2.0", "id": index, "method": method, "params": params}
        for index, (method, params) in enumerate(calls)
    ]
    response = _request("POST", endpoint, json=payload).json()
    responses = response if isinstance(response, list) else [response]
    by_id = {item.get("id"): item for item in responses if isinstance(item, dict)}
    results = []
    for index in range(len(calls)):
        item = by_id.get(index)
        if not item or "result" not in item:
            raise RuntimeError("Polkadot RPC вернул ошибку или неполный ответ")
        results.append(item["result"])
    return results


def _polkadot_rpc() -> dict:
    endpoints = (
        "https://rpc.polkadot.io",
        "https://polkadot-rpc.publicnode.com",
        "https://polkadot.api.onfinality.io/public",
    )
    last_error = None
    for endpoint in endpoints:
        try:
            header = _rpc_batch(endpoint, [("chain_getHeader", [])])[0]
            block_number = int(header["number"], 16)
            heights = [block_number - offset for offset in range(10)]
            heights += [block_number - 1000 - offset for offset in range(10)]
            hashes = _rpc_batch(endpoint, [("chain_getBlockHash", [height]) for height in heights])
            blocks = _rpc_batch(endpoint, [("chain_getBlock", [block_hash]) for block_hash in hashes])
            counts = [len(block["block"]["extrinsics"]) for block in blocks]
            current_average = sum(counts[:10]) / 10
            previous_average = sum(counts[10:]) / 10
            return {
                "current": {"extrinsics_per_block": current_average},
                "previous": {"extrinsics_per_block": previous_average},
                "block_number": block_number,
                "sample_blocks": 10,
                "comparison_offset": 1000,
                "source_type": "rpc",
                "endpoint": endpoint,
            }
        except Exception as error:
            last_error = error
    raise RuntimeError(f"Открытые узлы Polkadot RPC недоступны ({last_error})")


def educational_onchain() -> dict:
    return {
        "current": {"extrinsics": 185_000, "active_addresses": 23_400, "transfer_volume": 4_800_000, "staking_ratio": 0.52, "validators": 297},
        "previous": {"extrinsics": 171_000, "active_addresses": 21_900, "transfer_volume": 4_500_000, "staking_ratio": 0.50, "validators": 297},
        "source_type": "educational",
    }


def _current(raw: dict) -> dict:
    return {
        "price": raw.get("current_price"),
        "market_cap": raw.get("market_cap"),
        "volume": raw.get("total_volume"),
        "change_24h": raw.get("price_change_percentage_24h"),
        "circulating_supply": raw.get("circulating_supply"),
        "updated_at": raw.get("last_updated"),
    }


def collect_online(days: int, compare: bool = True) -> dict:
    tasks = {
        "coingecko": ("CoinGecko", "Рыночные данные", lambda: _coingecko(days, compare)),
        "binance": ("Binance", "OHLCV", lambda: _binance(days)),
        "fear_greed": ("Alternative.me", "Настроения", _fear_greed),
        "news": ("CryptoPanic / Google News / Cointelegraph", "Новости", _news),
        "onchain": ("Polkadot Public RPC", "Ончейн", _polkadot_rpc),
    }
    values = {}
    sources = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {key: executor.submit(task[2]) for key, task in tasks.items()}
        for key, future in futures.items():
            name, category, _ = tasks[key]
            try:
                values[key] = future.result()
                message = "Данные получены"
                if key == "news":
                    message = values[key][1]
                if key == "onchain":
                    message = f"Блок № {values[key]['block_number']}; среднее число extrinsics в двух выборках по 10 блоков; ключ не требуется"
                sources.append({"name": name, "category": category, "status": "ok", "message": message, "updated_at": datetime.now(timezone.utc).isoformat()})
            except Exception as error:
                values[key] = None
                sources.append({"name": name, "category": category, "status": "unavailable", "message": str(error), "updated_at": datetime.now(timezone.utc).isoformat()})

    if values["coingecko"] is None:
        raise RuntimeError("Не удалось получить базовые данные CoinGecko. Проверьте интернет или используйте демонстрационный режим.")
    coingecko = values["coingecko"]
    market = values["binance"] if values["binance"] is not None else coingecko["market"]
    if values["binance"] is not None and coingecko["current_raw"].get("current_price"):
        binance_price = float(market.iloc[-1]["close"])
        cg_price = float(coingecko["current_raw"]["current_price"])
        discrepancy = abs(binance_price / cg_price - 1) * 100
        for source in sources:
            if source["name"] == "Binance":
                source["message"] = f"Расхождение последней цены с CoinGecko: {discrepancy:.2f}%"
                if discrepancy > 1:
                    source["status"] = "warning"
    news, _ = values["news"] if values["news"] is not None else ([], "")
    fear = values["fear_greed"] or {}
    return {
        "market": market,
        "compare_market": coingecko["compare_market"],
        "current": _current(coingecko["current_raw"]),
        "compare_current": _current(coingecko["compare_current_raw"]) if coingecko["compare_current_raw"] else None,
        "news": news,
        "fear_greed": fear.get("value"),
        "fear_greed_label": fear.get("label", ""),
        "onchain": values["onchain"],
        "sources": sources,
    }
