from __future__ import annotations

from datetime import datetime


def _number(value: object, digits: int = 2) -> str:
    if value is None:
        return "н/д"
    return f"{float(value):,.{digits}f}".replace(",", " ")


def markdown_report(result: dict) -> str:
    metadata = result["metadata"]
    market = result["market"]
    modules = result["modules"]
    lines = [
        "# PolkaInsight — аналитический отчёт",
        "",
        f"**Команда:** «Поцелуй Комара»  ",
        f"**Актив:** Polkadot (DOT)  ",
        f"**Период:** {metadata['period_days']} дней  ",
        f"**Дата расчёта:** {metadata['created_at']}  ",
        f"**Режим:** {'Демонстрационный (синтетические данные)' if metadata['mode'] == 'demo' else 'Онлайн-источники'}  ",
        f"**Версия алгоритма:** {metadata['algorithm_version']}",
        "",
        "## 1. Рыночные показатели",
        "",
        f"- Цена DOT: **${_number(market.get('price'), 4)}**",
        f"- Изменение за 24 часа: {_number(market.get('change_24h'))}%",
        f"- Изменение за выбранный период: {_number(market.get('period_change'))}%",
        f"- Рыночная капитализация: ${_number(market.get('market_cap'), 0)}",
        f"- Объём торгов: ${_number(market.get('volume'), 0)}",
        "",
        "## 2. Технический анализ",
        "",
        f"Оценка: **{_number(modules['technical']['score'], 1)}/100**.",
        "",
    ]
    for key, value in modules["technical"].get("indicators", {}).items():
        lines.append(f"- {key}: {_number(value, 4)}")
    lines.extend(["", *[f"- {text}" for text in modules["technical"]["explanations"]]])
    lines.extend(["", "## 3. Фундаментальный анализ", "", f"Оценка: **{_number(modules['fundamental']['score'], 1)}/100**.", ""])
    for item in modules["fundamental"]["criteria"]:
        lines.append(f"- {item['criterion']}: {item['score']}/100, вес {item['weight']:.0%}. {item['basis']} [Источник]({item['url']})")
    lines.extend(["", "## 4. Ончейн-анализ", "", f"Оценка: **{_number(modules['onchain']['score'], 1)}/100**.", ""])
    for item in modules["onchain"].get("metrics", []):
        lines.append(f"- {item['metric']}: текущее значение {_number(item['current'], 4)}, предыдущее {_number(item['previous'], 4)}, балл {_number(item['score'], 1)}.")
    lines.extend([f"- {text}" for text in modules["onchain"]["explanations"]])
    sentiment = modules["sentiment"]
    news_notes = {
        "fallback": "Внешние новости недоступны. В интерфейсе показаны локальные учебные примеры; они не участвуют в оценке. Оценка настроений основана только на Fear & Greed.",
        "stale": "Доступные публикации старше 30 дней отображаются как архив и не участвуют в оценке. Оценка настроений основана только на Fear & Greed.",
        "partial": "Публикации старше 30 дней исключены из расчёта актуальных настроений и отмечены в интерфейсе как архивные.",
        "demo": "Новости являются синтетическими демонстрационными данными.",
    }
    news_note = news_notes.get(result.get("news_status"), "")
    lines.extend([
        "",
        "## 5. Анализ рыночных настроений",
        "",
        f"Оценка: **{_number(sentiment['score'], 1)}/100**. Fear & Greed: {_number(sentiment.get('fear_greed'), 0)} ({sentiment.get('fear_greed_label') or 'н/д'}).",
        "",
        f"Позитивных новостей: {sentiment['counts']['positive']}; негативных: {sentiment['counts']['negative']}; нейтральных: {sentiment['counts']['neutral']}.",
        "",
        news_note,
        "",
        "## 6. Комплексная оценка",
        "",
        f"**{_number(result['integrated']['score'], 1)}/100 — {result['integrated']['label']}**",
        "",
        result["integrated"]["formula"],
        "",
        f"Полнота данных: {result['quality']['completeness']}%; согласованность: {result['quality']['consistency']}%; индекс уверенности: {result['quality']['confidence']}%.",
        "",
        "## 7. Выявленные противоречия",
        "",
    ])
    lines.extend([f"- {item['module_1']} ↔ {item['module_2']}: {item['description']}" for item in result["conflicts"]] or ["- Существенных противоречий не выявлено."])
    lines.extend(["", "## 8. Основные риски", "", *[f"- {risk}" for risk in result["risks"]]])
    lines.extend(["", "## 9. Источники и качество данных", ""])
    for source in result["sources"]:
        lines.append(f"- {source['name']} ({source['category']}): {source['status']} — {source.get('message', '')}; {source.get('updated_at', '')}")
    lines.extend(["", "## 10. Итоговое заключение", "", result["conclusion"], "", "---", "Отчёт сформирован автоматически на основании рассчитанных показателей. Не является инвестиционной рекомендацией."])
    return "\n".join(lines)


def html_report(result: dict) -> str:
    import html

    markdown = markdown_report(result)
    body = []
    for line in markdown.splitlines():
        escaped = html.escape(line)
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<p>• {escaped[2:]}</p>")
        elif line:
            body.append(f"<p>{escaped}</p>")
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    return f"<!doctype html><html lang='ru'><meta charset='utf-8'><title>PolkaInsight</title><style>body{{font-family:Arial,sans-serif;max-width:960px;margin:40px auto;line-height:1.5;color:#202124}}h1,h2{{color:#b52b86}}@media print{{body{{margin:10mm}}}}</style><body>{''.join(body)}<small>HTML создан {generated}</small></body></html>"
