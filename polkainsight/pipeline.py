from __future__ import annotations

import math
from datetime import datetime, timezone

import pandas as pd

from . import ALGORITHM_VERSION
from .analysis import (
    build_conclusion,
    build_risks,
    classify_sentiment,
    find_conflicts,
    fundamental_analysis,
    integrated_analysis,
    onchain_analysis,
    quality_metrics,
    sentiment_analysis,
)
from .demo import collect_demo
from .indicators import technical_analysis
from .processing import prepare_market
from .sources import collect_online, educational_news, educational_onchain


def _records(frame: pd.DataFrame) -> list[dict]:
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        {key: (None if isinstance(value, float) and math.isnan(value) else value) for key, value in row.items()}
        for row in data.to_dict(orient="records")
    ]


def _recent_news(news: list[dict], max_age_days: int = 30) -> list[dict]:
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=max_age_days)
    recent = []
    for item in news:
        published = pd.to_datetime(item.get("published"), utc=True, errors="coerce")
        if not pd.isna(published) and published >= cutoff:
            recent.append(item)
    return recent


def _news_for_display(news: list[dict], analyzed: list[dict]) -> list[dict]:
    analyzed_titles = {item.get("title") for item in analyzed}
    display = []
    for item in news:
        enriched = dict(item)
        enriched["sentiment"] = classify_sentiment(item.get("title", "")) if item.get("title") in analyzed_titles else "not_used"
        display.append(enriched)
    return display


def run_analysis(days: int = 90, mode: str = "demo", compare: bool = True) -> dict:
    if days not in (30, 90, 180, 365):
        raise ValueError("Допустимые периоды: 30, 90, 180 и 365 дней")
    if mode not in ("demo", "online"):
        raise ValueError("Неизвестный режим анализа")
    collected = collect_demo(max(days, 60), compare) if mode == "demo" else collect_online(max(days, 60), compare)
    market_frame, processing_issues = prepare_market(collected["market"])
    if market_frame.empty:
        raise RuntimeError("Нет корректных рыночных данных для анализа")

    technical = technical_analysis(market_frame)
    if mode == "demo":
        analyzed_news = collected["news"]
        news_status = "demo"
        news_display = _news_for_display(collected["news"], analyzed_news)
    else:
        analyzed_news = _recent_news(collected["news"])
        if not collected["news"]:
            news_status = "fallback"
            news_display = educational_news()
        elif not analyzed_news:
            news_status = "stale"
            news_display = _news_for_display(collected["news"], analyzed_news)
        else:
            news_status = "ok" if len(analyzed_news) == len(collected["news"]) else "partial"
            news_display = _news_for_display(collected["news"], analyzed_news)
    if mode == "online" and not collected["onchain"]:
        collected["onchain"] = educational_onchain()
    modules = {
        "technical": technical,
        "fundamental": fundamental_analysis(),
        "onchain": onchain_analysis(collected["onchain"]),
        "sentiment": sentiment_analysis(analyzed_news, collected["fear_greed"], collected["fear_greed_label"]),
    }
    integrated = integrated_analysis(modules)
    conflicts = find_conflicts(modules)
    sources = collected["sources"] + [
        {
            "name": "Data Processor",
            "category": "Контроль качества",
            "status": "warning" if processing_issues else "ok",
            "message": " ".join(processing_issues) if processing_issues else "Пропуски, дубликаты, аномалии и актуальность проверены",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "name": "Polkadot Docs / Wiki",
            "category": "Фундаментальные данные",
            "status": "reference",
            "message": "Официальные материалы; экспертные баллы по методике",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    if news_status in ("fallback", "stale", "partial"):
        messages = {
            "fallback": "Внешние новости недоступны; показаны локальные учебные примеры, которые не участвуют в оценке.",
            "stale": "Найдены только публикации старше 30 дней; они показаны как архив и не участвуют в оценке актуальных настроений.",
            "partial": "Публикации старше 30 дней показаны в таблице, но исключены из оценки актуальных настроений.",
        }
        sources.append({
            "name": "News Quality Control",
            "category": "Контроль новостей",
            "status": "warning",
            "message": messages[news_status],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    if modules["onchain"].get("data_mode") == "educational":
        sources.append({
            "name": "Локальный учебный набор",
            "category": "Резервные ончейн-данные",
            "status": "warning",
            "message": "Открытые RPC недоступны; значения учебные и явно отмечены в интерфейсе и отчёте.",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    quality = quality_metrics(modules, conflicts, sources)
    conclusion = build_conclusion(integrated, modules, conflicts)
    market = collected["current"]
    display = technical["series"].tail(days).copy()
    first_price = float(display.iloc[0]["close"])
    last_price = float(display.iloc[-1]["close"])
    market["price"] = market.get("price") or last_price
    market["period_change"] = (last_price / first_price - 1) * 100 if first_price else None
    comparison = None
    if compare and collected.get("compare_market") is not None:
        comparison_frame, _ = prepare_market(collected["compare_market"])
        comparison = comparison_frame.tail(days).copy()

    serializable_technical = {key: value for key, value in technical.items() if key != "series"}
    result = {
        "metadata": {
            "asset": "Polkadot",
            "symbol": "DOT",
            "compare_symbol": "BTC" if comparison is not None else None,
            "period_days": days,
            "start_date": str(display.iloc[0]["date"].date()),
            "end_date": str(display.iloc[-1]["date"].date()),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": mode,
            "algorithm_version": ALGORITHM_VERSION,
        },
        "market": market,
        "compare_market": collected.get("compare_current"),
        "modules": {**modules, "technical": serializable_technical},
        "integrated": integrated,
        "conflicts": conflicts,
        "quality": quality,
        "risks": build_risks(modules, conflicts, mode),
        "conclusion": conclusion,
        "sources": sources,
        "news_display": news_display,
        "news_status": news_status,
        "news_analyzed_count": len(analyzed_news),
        "series": _records(display),
        "comparison_series": _records(comparison) if comparison is not None else [],
    }
    return result
