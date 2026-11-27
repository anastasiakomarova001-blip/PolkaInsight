from __future__ import annotations

from itertools import combinations
from statistics import mean


MODULE_NAMES = {
    "technical": "Технический анализ",
    "fundamental": "Фундаментальный анализ",
    "onchain": "Ончейн-анализ",
    "sentiment": "Анализ настроений",
}


def score_label(score: float | None) -> str:
    if score is None:
        return "Недостаточно данных"
    if score <= 20:
        return "Критически отрицательная"
    if score <= 40:
        return "Отрицательная"
    if score <= 60:
        return "Нейтральная"
    if score <= 80:
        return "Положительная"
    return "Сильно положительная"


def fundamental_analysis() -> dict:
    criteria = [
        {
            "criterion": "Технологическая архитектура",
            "score": 88,
            "weight": 0.25,
            "basis": "Relay Chain, общая безопасность, парачейны и XCM.",
            "url": "https://wiki.polkadot.network/docs/learn-architecture",
        },
        {
            "criterion": "Развитие экосистемы",
            "score": 78,
            "weight": 0.25,
            "basis": "Многосетевая экосистема и инструменты разработки; балл является учебной экспертной оценкой.",
            "url": "https://polkadot.com/ecosystem/",
        },
        {
            "criterion": "Экономическая модель DOT",
            "score": 68,
            "weight": 0.20,
            "basis": "DOT используется в стейкинге, управлении и оплате ресурсов; учитывается инфляционный риск.",
            "url": "https://wiki.polkadot.network/docs/learn-DOT",
        },
        {
            "criterion": "Активность разработки",
            "score": 85,
            "weight": 0.15,
            "basis": "Открытые репозитории и регулярно обновляемая документация; для упрощения балл задан методикой.",
            "url": "https://github.com/paritytech/polkadot-sdk",
        },
        {
            "criterion": "Управление OpenGov",
            "score": 90,
            "weight": 0.15,
            "basis": "Децентрализованные референдумы и непосредственное участие держателей DOT.",
            "url": "https://wiki.polkadot.network/docs/learn-polkadot-opengov",
        },
    ]
    score = round(sum(item["score"] * item["weight"] for item in criteria), 1)
    return {
        "score": score,
        "criteria": criteria,
        "explanations": [
            "Оценка рассчитана по пяти критериям с весами 25%, 25%, 20%, 15% и 15%.",
            "Это учебная экспертная оценка по официальной документации, а не автоматический прогноз стоимости.",
        ],
    }


def _growth_score(current: float, previous: float) -> float | None:
    if previous <= 0:
        return None
    change = (current / previous - 1) * 100
    return max(0, min(100, 50 + change * 2))


def onchain_analysis(data: dict | None) -> dict:
    if not data or not data.get("current"):
        return {
            "score": None,
            "metrics": {},
            "data_mode": "unavailable",
            "explanations": ["Ончейн-данные временно недоступны; оценка не сформирована."],
        }
    current = data["current"]
    previous = data.get("previous", {})
    definitions = [
        ("extrinsics", "Количество extrinsics", 0.25),
        ("extrinsics_per_block", "Extrinsics на блок (среднее)", 0.25),
        ("active_addresses", "Активные адреса", 0.25),
        ("transfer_volume", "Объём переводов DOT", 0.15),
    ]
    metrics = []
    weighted = []
    for key, title, weight in definitions:
        value = current.get(key)
        old = previous.get(key)
        if value is None or old is None:
            continue
        part = _growth_score(float(value), float(old))
        if part is None:
            continue
        change = (float(value) / float(old) - 1) * 100 if float(old) else None
        metrics.append({"metric": title, "current": value, "previous": old, "change_pct": change, "score": round(part, 1), "weight": weight})
        weighted.append((part, weight))

    staking = current.get("staking_ratio")
    if staking is not None:
        staking_part = max(0, min(100, 100 - abs(float(staking) - 0.5) * 200))
        metrics.append({"metric": "Доля DOT в стейкинге", "current": staking, "previous": previous.get("staking_ratio"), "change_pct": None, "score": round(staking_part, 1), "weight": 0.20})
        weighted.append((staking_part, 0.20))
    validators = current.get("validators")
    if validators is not None:
        validator_part = max(0, min(100, float(validators) / 297 * 100))
        metrics.append({"metric": "Активные валидаторы", "current": validators, "previous": previous.get("validators"), "change_pct": None, "score": round(validator_part, 1), "weight": 0.15})
        weighted.append((validator_part, 0.15))

    score = round(sum(value * weight for value, weight in weighted) / sum(weight for _, weight in weighted), 1) if weighted else None
    data_mode = data.get("source_type", "unknown")
    if data_mode == "rpc":
        explanations = [
            f"Открытый Polkadot RPC: блок № {data.get('block_number')}; среднее число extrinsics в 10 блоках сравнивается с выборкой на 1000 блоков раньше.",
            "Данные получены напрямую из сети Polkadot без регистрации и API-ключа.",
            "Это упрощённый показатель активности Relay Chain, а не полная статистика всех парачейнов.",
        ]
    elif data_mode == "educational":
        explanations = [
            "Открытые узлы Polkadot RPC недоступны, поэтому показаны локальные учебные значения, а не реальная статистика сети.",
            "Учебный резерв позволяет проверить расчёты; его использование отмечено предупреждением и в рисках отчёта.",
        ]
    else:
        explanations = [
            "Динамика операций, адресов и переводов сравнивается с предыдущим аналогичным периодом.",
            "Extrinsics, обычные переводы и события сети не объединяются: это разные виды активности.",
            "Для упрощённой версии стейкинг оценивается относительно ориентира 50%, а активный набор — относительно 297 валидаторов.",
        ]
    return {
        "score": score,
        "metrics": metrics,
        "data_mode": data_mode,
        "explanations": explanations,
    }


POSITIVE_WORDS = {
    "adoption", "approval", "bullish", "expands", "gain", "growth", "improvement", "improves",
    "launch", "positive", "record", "stable", "success", "surge", "upgrade", "partnership", "рост", "запуск",
}
NEGATIVE_WORDS = {
    "bearish", "concern", "concerns", "correction", "crash", "decline", "downside", "drop", "fall",
    "fraud", "hack", "loss", "negative", "risk", "sell-off", "uncertain", "volatility", "падение", "риск",
}


def classify_sentiment(title: str) -> str:
    words = set(title.lower().replace(":", " ").replace(",", " ").split())
    positive = len(words & POSITIVE_WORDS)
    negative = len(words & NEGATIVE_WORDS)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def sentiment_analysis(news: list[dict], fear_greed: int | None, fear_greed_label: str = "") -> dict:
    unique = []
    seen = set()
    for item in news:
        key = item.get("title", "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            enriched = dict(item)
            enriched["sentiment"] = classify_sentiment(key)
            unique.append(enriched)
    counts = {name: sum(item["sentiment"] == name for item in unique) for name in ("positive", "negative", "neutral")}
    total = len(unique)
    news_score = 50.0
    dynamics_score = 50.0
    if total:
        news_score = 50 + 50 * (counts["positive"] - counts["negative"]) / total
        if total >= 4:
            midpoint = total // 2
            recent = unique[:midpoint]
            older = unique[midpoint:]
            value = {"positive": 1, "neutral": 0, "negative": -1}
            recent_mean = mean(value[item["sentiment"]] for item in recent)
            older_mean = mean(value[item["sentiment"]] for item in older)
            dynamics_score = max(0, min(100, 50 + (recent_mean - older_mean) * 50))
    if total:
        parts = [(news_score, 0.50), (dynamics_score, 0.30)]
        if fear_greed is not None:
            parts.append((float(fear_greed), 0.20))
        score = round(sum(value * weight for value, weight in parts) / sum(weight for _, weight in parts), 1)
    elif fear_greed is not None:
        score = float(fear_greed)
    else:
        score = None
    return {
        "score": score,
        "news_score": round(news_score, 1),
        "dynamics_score": round(dynamics_score, 1),
        "fear_greed": fear_greed,
        "fear_greed_label": fear_greed_label,
        "counts": counts,
        "news": unique,
        "explanations": [
            "Тональность заголовков определяется учебным словарным классификатором; нейтральные публикации учитываются в знаменателе.",
            "Оценка новостей: 50 + 50 × (позитивные − негативные) / все публикации.",
            "Fear & Greed характеризует преимущественно общий рынок и Bitcoin, а не только Polkadot.",
        ],
    }


def integrated_analysis(modules: dict) -> dict:
    weights = {"technical": 0.30, "fundamental": 0.25, "onchain": 0.25, "sentiment": 0.20}
    available = {name: float(module["score"]) for name, module in modules.items() if module.get("score") is not None}
    if len(available) < 3:
        return {"score": None, "label": "Недостаточно данных", "available_modules": len(available), "formula": "Для итоговой оценки нужны минимум три модуля."}
    weight_sum = sum(weights[name] for name in available)
    score = round(sum(available[name] * weights[name] for name in available) / weight_sum, 1)
    formula = " + ".join(f"{weights[name]:.2f} × {available[name]:.1f}" for name in available)
    return {
        "score": score,
        "label": score_label(score),
        "available_modules": len(available),
        "formula": f"({formula}) / {weight_sum:.2f} = {score:.1f}",
        "weights": weights,
    }


def find_conflicts(modules: dict) -> list[dict]:
    available = {name: float(module["score"]) for name, module in modules.items() if module.get("score") is not None}
    conflicts = []
    for first, second in combinations(available, 2):
        difference = abs(available[first] - available[second])
        directed = (available[first] <= 40 and available[second] >= 61) or (available[second] <= 40 and available[first] >= 61)
        if difference >= 30 or directed:
            conflicts.append({
                "module_1": MODULE_NAMES[first],
                "module_2": MODULE_NAMES[second],
                "difference": round(difference, 1),
                "severity": "Высокая" if difference >= 40 else "Средняя",
                "description": f"Оценки различаются на {difference:.1f} балла" + ("; сигналы имеют противоположную направленность." if directed else "."),
            })
    return conflicts


def quality_metrics(modules: dict, conflicts: list[dict], sources: list[dict]) -> dict:
    available = sum(module.get("score") is not None for module in modules.values())
    completeness = available / 4 * 100
    scores = [module["score"] for module in modules.values() if module.get("score") is not None]
    spread = max(scores) - min(scores) if len(scores) > 1 else 0
    consistency = max(0, 100 - spread)
    live = sum(source.get("status") == "ok" for source in sources)
    confidence = round(0.7 * completeness + 0.3 * consistency, 1)
    return {"completeness": round(completeness, 1), "consistency": round(consistency, 1), "confidence": confidence, "live_sources": live}


def build_risks(modules: dict, conflicts: list[dict], mode: str) -> list[str]:
    risks = []
    if modules["technical"].get("score") is not None and modules["technical"]["score"] < 45:
        risks.append("Технические индикаторы указывают на слабую краткосрочную рыночную динамику.")
    if modules["sentiment"].get("fear_greed") is not None and modules["sentiment"]["fear_greed"] < 25:
        risks.append("Общий рыночный индекс находится в зоне сильного страха.")
    if modules["sentiment"].get("score") is not None and modules["sentiment"]["score"] < 45:
        risks.append("Преобладает негативный или неопределённый информационный фон.")
    if modules["onchain"].get("data_mode") == "educational":
        risks.append("Ончейн-раздел использует локальные учебные значения: открытые узлы Polkadot RPC были недоступны.")
    if modules["onchain"].get("score") is None:
        risks.append("Ончейн-оценка отсутствует: полнота комплексного анализа снижена.")
    if conflicts:
        risks.append("Между аналитическими модулями есть существенные противоречия.")
    if mode == "demo":
        risks.append("Расчёт выполнен на синтетических данных и демонстрирует только работу алгоритмов.")
    risks.append("Высокая волатильность криптовалют и возможные ошибки внешних API ограничивают точность оценки.")
    return risks


def build_conclusion(integrated: dict, modules: dict, conflicts: list[dict]) -> str:
    if integrated["score"] is None:
        return "Недостаточно достоверных данных для итоговой оценки. Необходимо повторить сбор информации или настроить недоступные источники."
    conclusion = f"Интегральная оценка Polkadot составляет {integrated['score']:.1f}/100 — {integrated['label'].lower()}. "
    strongest = max((module for module in modules.values() if module.get("score") is not None), key=lambda item: item["score"])
    weakest = min((module for module in modules.values() if module.get("score") is not None), key=lambda item: item["score"])
    strongest_name = next(name for name, module in modules.items() if module is strongest)
    weakest_name = next(name for name, module in modules.items() if module is weakest)
    conclusion += f"Наиболее сильный сигнал даёт направление «{MODULE_NAMES[strongest_name]}» ({strongest['score']:.1f}), наиболее слабый — «{MODULE_NAMES[weakest_name]}» ({weakest['score']:.1f}). "
    if conflicts:
        conclusion += "Обнаружены расхождения между направлениями, поэтому итог следует трактовать осторожно и учитывать разные временные горизонты. "
    else:
        conclusion += "Существенных противоречий между доступными модулями не выявлено. "
    conclusion += "Результат носит учебный информационно-аналитический характер и не является индивидуальной инвестиционной рекомендацией."
    return conclusion
