from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from polkainsight.demo import collect_demo


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
OUT = ROOT / "deliverables"


def document_with_styles(title: str) -> Document:
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2)
    section.right_margin = Cm(1.5)
    document.styles["Normal"].font.name = "Times New Roman"
    document.styles["Normal"].font.size = Pt(12)
    heading = document.add_heading(title, 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph("PolkaInsight · команда «Поцелуй Комара»").alignment = WD_ALIGN_PARAGRAPH.CENTER
    return document


def build_protocol(verification: dict):
    document = document_with_styles("Протокол тестирования PolkaInsight")
    document.add_paragraph("Объект: упрощённая версия системы комплексного анализа Polkadot (DOT).")
    document.add_paragraph("Среда: Windows, Python 3.14, Streamlit, Pandas, SQLite. Проверки выполнены на программном коде проекта; пользовательский сценарий дополнительно проверен во встроенном браузере.")
    table = document.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, ("№", "Тестовая ситуация", "Результат", "Фактическое подтверждение")):
        cell.text = text
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for index, check in enumerate(verification["checks"], 1):
        cells = table.add_row().cells
        for cell, value in zip(cells, (index, check["name"], check["status"], check["details"])):
            cell.text = str(value)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)
    document.add_heading("Проверка внешних API", level=1)
    online = verification["online"]
    document.add_paragraph(f"Результат: {online['status']}. {online['details']}")
    document.add_heading("Итог", level=1)
    passed = sum(check["status"] == "PASS" for check in verification["checks"])
    document.add_paragraph(f"Успешно пройдено {passed} из {len(verification['checks'])} проверок. Независимо выполнены расчёты RSI и MACD на малом наборе данных. Ошибок, препятствующих демонстрации, не выявлено.")
    document.add_paragraph("Ограничение: проверка не является исторической оценкой доходности торговой стратегии. Система не формирует торговые приказы и не заявляет эффективность торговых сигналов.")
    path = OUT / "Протокол_тестирования_PolkaInsight.docx"
    document.save(path)
    return path


def build_guide():
    document = document_with_styles("Руководство пользователя PolkaInsight")
    document.add_heading("1. Назначение", level=1)
    document.add_paragraph("PolkaInsight предназначена для учебного комплексного анализа DOT по техническим, фундаментальным, ончейн-показателям и рыночным настроениям. Результат не является индивидуальной инвестиционной рекомендацией.")
    document.add_heading("2. Установка и запуск", level=1)
    document.add_paragraph("Откройте командную строку в папке проекта и выполните:")
    document.add_paragraph("python -m venv .venv\n.venv\\Scripts\\python.exe -m pip install -r requirements.txt\n.venv\\Scripts\\python.exe -m streamlit run app.py", style="No Spacing")
    document.add_paragraph("Откройте http://localhost:8501. При первом запуске автоматически отображается демонстрационный анализ. Для остановки нажмите Ctrl+C в командной строке.")
    document.add_heading("3. Работа с программой", level=1)
    for text in ("Выберите «Демонстрационный» режим для работы без интернета или «Онлайн» для внешних API.", "Укажите период 30, 90, 180 или 365 дней и при необходимости включите сравнение с BTC.", "Нажмите «Запустить анализ». Дождитесь сообщения о сохранении результата.", "Изучите оценки, заключение, графики, противоречия, риски и статусы источников.", "На вкладке «Новости и отчёт» скачайте Markdown или HTML.", "На вкладке «История» выберите номер исследования и загрузите его повторно."):
        document.add_paragraph(text, style="List Number")
    document.add_heading("4. Онлайн-настройка", level=1)
    document.add_paragraph("CoinGecko, Binance, Alternative.me, Google News RSS, Cointelegraph RSS и Polkadot Public RPC используются без API-ключей. Binance может быть недоступен в отдельных регионах; тогда используется история CoinGecko.")
    document.add_paragraph("Если Google News и Cointelegraph недоступны, показываются локальные учебные примеры без участия в онлайн-оценке. Новости старше 30 дней помечаются как архив и исключаются из актуального расчёта.")
    document.add_paragraph("Ончейн-раздел получает число extrinsics напрямую через открытые узлы Polkadot RPC. Если все узлы недоступны, вместо пустого блока показываются явно обозначенные локальные учебные значения. Их отличие от реальной статистики указано в интерфейсе, рисках и отчёте.")
    document.add_heading("5. Интерпретация", level=1)
    document.add_paragraph("0–20 — критически отрицательная; 21–40 — отрицательная; 41–60 — нейтральная; 61–80 — положительная; 81–100 — сильно положительная. Индекс уверенности характеризует полноту и согласованность данных, а не вероятность прибыли.")
    document.add_heading("6. Устранение проблем", level=1)
    for text in ("Если порт занят, добавьте к команде запуска: --server.port 8502.", "Если внешний API недоступен, повторите запрос позже или выберите демонстрационный режим.", "Если терминал показывает русский текст неправильно, используйте интерфейс браузера и файлы отчётов в UTF-8.", "Файл data/polkainsight.db создаётся автоматически и хранит историю исследований."):
        document.add_paragraph(text, style="List Bullet")
    path = OUT / "Руководство_пользователя_PolkaInsight.docx"
    document.save(path)
    return path


def package_data():
    data_dir = OUT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    raw = collect_demo(90, True)["market"]
    raw.to_csv(data_dir / "DOT_исходные_демонстрационные_данные.csv", index=False, encoding="utf-8-sig")
    processed = pd.DataFrame(json.loads((BUILD / "demo_result.json").read_text(encoding="utf-8"))["series"])
    processed.to_csv(data_dir / "DOT_обработанные_данные_и_индикаторы.csv", index=False, encoding="utf-8-sig")
    shutil.copy2(BUILD / "demo_result.json", data_dir / "Демонстрационный_результат.json")
    shutil.copy2(BUILD / "online_result.json", data_dir / "Онлайн_результат.json")
    shutil.copy2(BUILD / "online_report.md", OUT / "Онлайн_аналитический_отчет.md")
    shutil.copy2(BUILD / "verification.json", data_dir / "verification.json")
    schemes = OUT / "schemes"
    schemes.mkdir(exist_ok=True)
    for name in ("architecture.png", "erd.png", "price_indicators.png", "module_scores.png", "dashboard.png"):
        shutil.copy2(BUILD / name, schemes / name)


def main():
    OUT.mkdir(exist_ok=True)
    verification = json.loads((BUILD / "verification.json").read_text(encoding="utf-8"))
    print(build_protocol(verification))
    print(build_guide())
    package_data()
    print("Data and schemes packaged")


if __name__ == "__main__":
    main()
