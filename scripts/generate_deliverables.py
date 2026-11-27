from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt as PptPt


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
OUT = ROOT / "deliverables"
PINK = "E6007A"
PURPLE = "5E17EB"
DARK = "29202E"


def load_data():
    result = json.loads((BUILD / "demo_result.json").read_text(encoding="utf-8"))
    verification = json.loads((BUILD / "verification.json").read_text(encoding="utf-8"))
    return result, verification


def set_cell_text(cell, text, bold=False, size=10):
    cell.text = str(text)
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(size)
            run.bold = bold


def add_table(document, headers, rows, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, True)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value)
    return table


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    run._r.append(field)


def paragraph(document, text, bold_prefix=None):
    item = document.add_paragraph()
    item.paragraph_format.space_after = Pt(5)
    item.paragraph_format.line_spacing = 1.08
    if bold_prefix and text.startswith(bold_prefix):
        item.add_run(bold_prefix).bold = True
        item.add_run(text[len(bold_prefix):])
    else:
        item.add_run(text)
    return item


def bullets(document, items):
    for text in items:
        item = document.add_paragraph(style="List Bullet")
        item.paragraph_format.space_after = Pt(3)
        item.add_run(text)


def new_page(document, title):
    document.add_page_break()
    heading = document.add_heading(title, level=1)
    heading.paragraph_format.space_after = Pt(10)


def build_report(result, verification):
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(1.7)
    section.bottom_margin = Cm(1.7)
    section.left_margin = Cm(2)
    section.right_margin = Cm(1.5)
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    for name, size in (("Title", 24), ("Heading 1", 17), ("Heading 2", 14)):
        styles[name].font.name = "Times New Roman"
        styles[name].font.size = Pt(size)
        styles[name].font.color.rgb = RGBColor.from_string(DARK)
    add_page_number(section.footer.paragraphs[0])

    for _ in range(3):
        document.add_paragraph()
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("ПРАКТИЧЕСКАЯ РАБОТА № 3–2\n").bold = True
    title.add_run("Разработка интеллектуальной аналитической системы\nкомплексного анализа криптовалюты Polkadot (DOT)").bold = True
    for run in title.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(18)
    document.add_paragraph()
    project = document.add_paragraph()
    project.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = project.add_run("PolkaInsight")
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor.from_string(PINK)
    for _ in range(5):
        document.add_paragraph()
    for text in ("Команда: «Поцелуй Комара»", "Объект исследования: Polkadot (DOT)", "Дополнительный объект: Bitcoin (BTC)", "Вариант: упрощённая учебная реализация"):
        item = document.add_paragraph(text)
        item.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph("\n2026").alignment = WD_ALIGN_PARAGRAPH.CENTER

    new_page(document, "Содержание")
    contents = [
        "1. Цель, объект и предметная область", "2. Функциональные требования и сценарий работы",
        "3. Архитектура системы", "4. Источники данных и контроль качества", "5. Методика технического анализа",
        "6. Фундаментальный и ончейн-анализ", "7. Анализ настроений и комплексная оценка",
        "8. Хранение данных и история исследований", "9. Пользовательский интерфейс",
        "10. Тестирование", "11. Результаты демонстрационного исследования", "12. Заключение и источники",
    ]
    for index, item in enumerate(contents, 2):
        paragraph(document, f"{item} ........................................................ {index}")
    document.add_heading("Состав комплекта", level=2)
    bullets(document, ["Программный проект на Python со Streamlit-интерфейсом.", "Настоящий отчёт и презентация на 15 слайдов.", "README с инструкцией запуска и настройки внешних API.", "Демонстрационный и онлайн-режимы работы."])

    new_page(document, "1. Цель, объект и предметная область")
    paragraph(document, "Цель работы — разработать и проверить упрощённую версию интеллектуальной аналитической системы PolkaInsight для комплексного исследования криптовалюты Polkadot (DOT). Система получает рыночную, фундаментальную, ончейн-информацию и новости, рассчитывает показатели, выявляет противоречия и формирует объяснимое заключение.")
    paragraph(document, "Объект исследования — криптовалюта DOT и экосистема Polkadot. Polkadot включает Relay Chain, парачейны, механизм Nominated Proof of Stake, средства межсетевого взаимодействия XCM и управление OpenGov. Поэтому анализ ограничиваться ценой не должен.")
    document.add_heading("Задачи", level=2)
    bullets(document, ["Автоматизировать сбор и проверку данных из независимых источников.", "Рассчитать RSI, MACD, SMA, EMA и Bollinger Bands.", "Оценить технологию, экономику, сетевую активность и настроения.", "Объединить оценки с учётом полноты данных и выявить расхождения.", "Сохранить исследование, показать графики и сформировать отчёт."])
    paragraph(document, "Система предназначена для учебных и исследовательских целей. Она не совершает сделок и не гарантирует прогноз будущей цены. Результат не является индивидуальной инвестиционной рекомендацией.")

    new_page(document, "2. Функциональные требования и сценарий работы")
    add_table(document, ["Функция", "Реализация"], [
        ("Выбор актива и периода", "DOT; сравнение с BTC; 30, 90, 180 или 365 дней"),
        ("Получение данных", "Параллельные запросы, повтор при ошибке, статусы источников"),
        ("Четыре модуля", "Технический, фундаментальный, ончейн, настроения"),
        ("Комплексная оценка", "Веса, нормализация при пропусках, минимум три модуля"),
        ("Визуализация", "Plotly-графики, таблицы, индикаторы и пояснения"),
        ("История", "SQLite; открытие результата после перезапуска"),
        ("Отчёт", "Автоматические Markdown и HTML"),
        ("Контроль качества", "Полнота, согласованность, расхождения и ошибки API"),
    ])
    document.add_heading("Сценарий пользователя", level=2)
    bullets(document, ["Выбрать режим, период и необходимость сравнения с BTC.", "Запустить анализ и дождаться параллельного сбора информации.", "Изучить итог, четыре оценки, графики и пояснения.", "Проверить противоречия, риски и статусы источников.", "Скачать отчёт либо открыть исследование из истории."])
    paragraph(document, "Для упрощения вместо PostgreSQL и FastAPI используются SQLite и монолитный Streamlit-запуск. Модульность логики сохранена, поэтому серверный слой и СУБД могут быть заменены без изменения формул.")

    new_page(document, "3. Архитектура системы")
    paragraph(document, "Приложение разделено на уровень источников, предварительную обработку, четыре независимых аналитических модуля, комплексную оценку, хранилище и интерфейс. Аналитические функции не обращаются к API напрямую, а получают подготовленные структуры данных.")
    document.add_picture(str(BUILD / "architecture.png"), width=Cm(17))
    paragraph(document, "Файл pipeline.py реализует единый сценарий исследования. Модуль sources.py отвечает за внешние источники, indicators.py — за временные ряды, analysis.py — за оценки, storage.py — за историю, report.py — за отчёт, app.py — за представление.")

    new_page(document, "4. Источники данных и контроль качества")
    add_table(document, ["Источник", "Данные", "Поведение при недоступности"], [
        ("CoinGecko", "Цена, история, капитализация, объём, BTC", "Базовый источник; ошибка с предложением демо"),
        ("Binance", "Дневные OHLCV DOTUSDT", "Используется история CoinGecko"),
        ("Polkadot Public RPC", "Extrinsics в текущей и предыдущей выборках блоков", "Открытые узлы без ключа; при сбое — явно отмеченный учебный набор"),
        ("Polkadot Docs / Wiki", "Архитектура, DOT, OpenGov", "Сохраняются ссылки на первичные материалы"),
        ("Alternative.me", "Fear & Greed", "Показатель исключается из настроений"),
        ("CryptoPanic / Google News / Cointelegraph", "Новости о DOT", "Без ключа применяются RSS; при полном сбое — учебный набор вне оценки"),
    ])
    paragraph(document, "Каждый запрос ограничен временем ожидания и выполняется повторно один раз. Независимые запросы запускаются параллельно. Статус, категория, сообщение и время получения показываются пользователю и попадают в отчёт. Все основные источники работают без регистрации и API-ключей.")
    paragraph(document, "Если цена Binance и CoinGecko различается более чем на 1%, источник получает предупреждение. Недоступный модуль не получает нулевую оценку. Полнота определяется долей доступных модулей, согласованность — обратной величиной диапазона их оценок.")

    new_page(document, "5. Методика технического анализа")
    paragraph(document, "SMA20 — среднее закрытий за 20 наблюдений. EMA20 придаёт больший вес последним ценам. RSI14 рассчитывается по сглаженным средним роста и падения: RSI = 100 − 100 / (1 + RS). MACD равен EMA12 − EMA26, сигнальная линия — EMA9 от MACD. Полосы Боллинджера строятся как SMA20 ± 2σ.")
    add_table(document, ["Индикатор", "Вес", "Интерпретация"], [
        ("RSI", "20%", "Перепроданность/перекупленность без гарантии разворота"),
        ("MACD", "25%", "Направление и изменение импульса"),
        ("SMA", "20%", "Положение цены относительно среднего уровня"),
        ("EMA", "20%", "Краткосрочный тренд с весом последних цен"),
        ("Bollinger Bands", "15%", "Отклонение цены и волатильность"),
    ])
    paragraph(document, "TA = 0,20 × RSIₛ + 0,25 × MACDₛ + 0,20 × SMAₛ + 0,20 × EMAₛ + 0,15 × BBₛ. Все компоненты нормализуются к диапазону 0–100. Для периода 30 дней дополнительно загружаются данные для разогрева индикаторов, но отображается выбранный интервал.")
    document.add_picture(str(BUILD / "price_indicators.png"), width=Cm(16.5))
    paragraph(document, "На рисунке использованы синтетические демонстрационные данные, а не актуальные котировки.")

    new_page(document, "6. Фундаментальный и ончейн-анализ")
    fundamental = result["modules"]["fundamental"]
    paragraph(document, f"Фундаментальная оценка в демонстрации составляет {fundamental['score']}/100. Она рассчитывается по заранее определённым критериям: технология 25%, экосистема 25%, токеномика 20%, разработка 15%, OpenGov 15%. Баллы являются учебной экспертной оценкой, а не автоматически полученными рекомендациями.")
    add_table(document, ["Критерий", "Балл", "Вес"], [(item["criterion"], item["score"], f"{item['weight']:.0%}") for item in fundamental["criteria"]])
    paragraph(document, "В демонстрации ончейн-модуль сравнивает количество extrinsics, активные адреса и объём переводов, а также оценивает долю стейкинга и валидаторов. В онлайн-режиме упрощённая версия получает через открытый Polkadot RPC среднее число extrinsics в 10 текущих блоках и сравнивает его с выборкой на 1000 блоков раньше. Данные Relay Chain и парачейнов не смешиваются.")
    onchain = result["modules"]["onchain"]
    add_table(document, ["Показатель", "Текущее", "Предыдущее", "Балл"], [(item["metric"], f"{item['current']:.4g}", f"{item['previous']:.4g}" if item["previous"] is not None else "н/д", item["score"]) for item in onchain["metrics"]])
    paragraph(document, "Для доступа к Polkadot Public RPC ключ не нужен. Если все открытые узлы недоступны, ончейн-раздел заполняется локальными учебными значениями с явным предупреждением в интерфейсе, рисках и отчёте. Учебный резерв не выдаётся за реальную статистику сети.")

    new_page(document, "7. Анализ настроений и комплексная оценка")
    sentiment = result["modules"]["sentiment"]
    paragraph(document, "Заголовки новостей очищаются от дубликатов и классифицируются словарным алгоритмом как позитивные, нейтральные или негативные. NS₁₀₀ = 50 + 50 × (P − N) / (P + N + Z). Динамика сравнивает среднюю тональность свежей и более ранней половин выборки. Итог настроений: 50% новости + 30% динамика + 20% Fear & Greed.")
    paragraph(document, f"Демонстрационная выборка: позитивных — {sentiment['counts']['positive']}, нейтральных — {sentiment['counts']['neutral']}, негативных — {sentiment['counts']['negative']}; Fear & Greed = {sentiment['fear_greed']}. Оценка направления — {sentiment['score']}/100.")
    paragraph(document, "Комплексная оценка рассчитывается как IA = 0,30TA + 0,25FA + 0,25OA + 0,20SA. Если модуль отсутствует, применяется IA = ΣwᵢSᵢ / Σwᵢ. При наличии менее трёх модулей итог не формируется. Шкала: 0–20 критически отрицательная, 21–40 отрицательная, 41–60 нейтральная, 61–80 положительная, 81–100 сильно положительная.")
    paragraph(document, "Противоречие фиксируется при разнице не менее 30 баллов либо при противоположных отрицательном и положительном сигналах. Автоматическое заключение использует фактические оценки, сильное и слабое направления, конфликты и режим данных.")

    new_page(document, "8. Хранение данных и история исследований")
    paragraph(document, "В упрощённой реализации применяется SQLite. Таблица analysis_history содержит дату, актив, период, режим, итоговый балл, версию алгоритма и полный JSON результата. JSON включает исходные рыночные ряды, индикаторы, новости, оценки, источники, противоречия, риски и заключение.")
    document.add_picture(str(BUILD / "erd.png"), width=Cm(16.5))
    paragraph(document, "Такой вариант позволяет восстановить исследование без повторных запросов и различать демонстрационный и онлайн-режимы. Версия алгоритма сохраняется отдельно. Для промышленного варианта JSON можно нормализовать в таблицы PostgreSQL из технического задания, не меняя аналитические функции.")

    new_page(document, "9. Пользовательский интерфейс")
    paragraph(document, "Главная страница содержит рыночные метрики, четыре оценки, интегральный результат и заключение. Вкладки открывают обзор, технические индикаторы, фундаментальные и ончейн-данные, новости с отчётом и историю. Боковая панель управляет периодом, режимом и сравнением с BTC.")
    screenshot = BUILD / "dashboard.png"
    if screenshot.exists():
        document.add_picture(str(screenshot), width=Cm(17))
    else:
        document.add_picture(str(BUILD / "module_scores.png"), width=Cm(16.5))
    paragraph(document, "Демонстрационный режим выделяется предупреждением. Ошибки API не скрываются. Отчёт выгружается в Markdown и HTML, а сохранённый результат можно открыть повторно. Интерфейс рассчитан на широкое окно браузера и не требует отдельной клиентской установки кроме Python-зависимостей.")

    new_page(document, "10. Тестирование")
    paragraph(document, "Проверка выполнена на реальном программном коде проекта. Проверялись формулы, граничные условия, периоды, сохранение и восстановление, сериализация и формирование отчёта. Дополнительно выполнялся запуск Streamlit и проверка пользовательского сценария в браузере.")
    rows = [(str(index), check["name"], check["status"], check["details"]) for index, check in enumerate(verification["checks"], 1)]
    add_table(document, ["№", "Проверка", "Результат", "Подтверждение"], rows)
    online = verification.get("online", {})
    paragraph(document, f"Онлайн-проверка: {online.get('status', 'не выполнялась')}. {online.get('details', '')}")
    paragraph(document, "Тестирование подтверждает работоспособность учебной версии, но не доказывает инвестиционную эффективность методики. Словарный анализ тональности ограничен, а внешние API могут менять формат и ограничения доступа.")

    new_page(document, "11. Результаты демонстрационного исследования")
    market = result["market"]
    paragraph(document, f"Для проверки выбран период {result['metadata']['period_days']} дней. Синтетическая цена DOT на конец периода — ${market['price']:.4f}, изменение за период — {market['period_change']:+.2f}%. Значения нужны исключительно для проверки программных расчётов.")
    document.add_picture(str(BUILD / "module_scores.png"), width=Cm(16.5))
    paragraph(document, f"Интегральный результат: {result['integrated']['score']}/100 — {result['integrated']['label'].lower()}. Полнота данных — {result['quality']['completeness']}%, согласованность — {result['quality']['consistency']}%, индекс уверенности — {result['quality']['confidence']}%. {result['integrated']['formula']}.")
    paragraph(document, result["conclusion"])
    document.add_heading("Основные риски", level=2)
    bullets(document, result["risks"])

    new_page(document, "12. Заключение и источники")
    paragraph(document, "В результате работы создана упрощённая, но функционирующая система PolkaInsight. Реализован полный цикл: получение или генерация данных, проверка источников, расчёт четырёх направлений, нормализация весов, поиск противоречий, визуализация, сохранение и формирование отчёта. Проект можно продемонстрировать без интернета, а при наличии сети — на актуальных публичных данных.")
    paragraph(document, "Дальнейшее развитие: переход на PostgreSQL и FastAPI, добавление полноценной NLP-модели, автоматический расчёт фундаментальных метрик, сбор данных парачейнов и XCM, расширение набора активов и проведение исторической проверки методики.")
    document.add_heading("Основные источники", level=2)
    references = [
        "Практическая работа № 3–2 и техническое задание PolkaInsight (материалы задания).",
        "Polkadot Wiki — Architecture: https://wiki.polkadot.network/docs/learn-architecture",
        "Polkadot Wiki — DOT: https://wiki.polkadot.network/docs/learn-DOT",
        "Polkadot Wiki — OpenGov: https://wiki.polkadot.network/docs/learn-polkadot-opengov",
        "CoinGecko API: https://docs.coingecko.com/",
        "Binance Spot API — Klines: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints",
        "Alternative.me Fear & Greed: https://alternative.me/crypto/fear-and-greed-index/",
        "Polkadot Public RPC: https://rpc.polkadot.io",
    ]
    bullets(document, references)
    paragraph(document, "Дата обращения к внешним сервисам фиксируется в каждом онлайн-анализе. Демонстрационный отчёт не содержит актуальных котировок.")

    OUT.mkdir(exist_ok=True)
    path = OUT / "Отчет_PolkaInsight_Поцелуй_Комара.docx"
    document.save(path)
    return path


def ppt_text(slide, text, left, top, width, height, size=22, color=DARK, bold=False, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = shape.text_frame
    frame.word_wrap = True
    frame.clear()
    lines = text.split("\n")
    for index, line in enumerate(lines):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = line
        p.font.name = "Calibri"
        p.font.size = PptPt(size)
        p.font.bold = bold
        p.font.color.rgb = PptColor.from_string(color)
        p.alignment = align
        p.space_after = PptPt(10)
    return shape


def base_slide(prs, title, number):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = PptColor(250, 249, 252)
    band = slide.shapes.add_shape(1, 0, 0, Inches(.13), prs.slide_height)
    band.fill.solid()
    band.fill.fore_color.rgb = PptColor.from_string(PINK)
    band.line.fill.background()
    ppt_text(slide, title, .55, .32, 12.1, .65, 28, DARK, True)
    ppt_text(slide, f"PolkaInsight · «Поцелуй Комара»                                      {number:02d}", .58, 7.08, 12.0, .25, 10, "746D79")
    return slide


def bullet_slide(prs, title, number, items, note=None):
    slide = base_slide(prs, title, number)
    shape = slide.shapes.add_textbox(Inches(.72), Inches(1.25), Inches(11.7), Inches(4.9))
    frame = shape.text_frame
    frame.word_wrap = True
    for index, item in enumerate(items):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = item
        p.font.name = "Calibri"
        p.font.size = PptPt(22)
        p.font.color.rgb = PptColor.from_string(DARK)
        p.space_after = PptPt(16)
        p.level = 0
        p.text = "• " + p.text
    if note:
        ppt_text(slide, note, .75, 6.3, 11.7, .55, 15, PINK, True)
    return slide


def build_presentation(result, verification):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = PptColor.from_string(DARK)
    ppt_text(slide, "PolkaInsight", .75, 1.25, 11.8, 1.0, 48, PINK, True, PP_ALIGN.CENTER)
    ppt_text(slide, "Интеллектуальная система комплексного анализа\nкриптовалюты Polkadot (DOT)", 1.0, 2.45, 11.3, 1.5, 28, "FFFFFF", False, PP_ALIGN.CENTER)
    ppt_text(slide, "Практическая работа № 3–2\nКоманда «Поцелуй Комара»\n2026", 1.0, 4.55, 11.3, 1.3, 20, "E8DDE7", False, PP_ALIGN.CENTER)

    bullet_slide(prs, "Актуальность и проблема", 2, ["Цена DOT не отражает всё состояние экосистемы Polkadot.", "Технические, фундаментальные, ончейн и новостные сигналы могут противоречить друг другу.", "Ручной сбор данных занимает время и затрудняет повторяемость исследования.", "Нужна система с объяснимыми расчётами и контролем качества данных."])
    bullet_slide(prs, "Цель и задачи", 3, ["Собирать рыночные, сетевые, фундаментальные и новостные данные.", "Рассчитывать RSI, MACD, SMA, EMA и Bollinger Bands.", "Формировать четыре оценки и единый показатель от 0 до 100.", "Выявлять противоречия и риски, строить графики и сохранять историю.", "Сравнивать динамику DOT и BTC."], "Результат — аналитическая информация, а не торговая рекомендация.")
    slide = base_slide(prs, "Архитектура решения", 4)
    slide.shapes.add_picture(str(BUILD / "architecture.png"), Inches(.7), Inches(1.05), width=Inches(11.9))
    bullet_slide(prs, "Источники и надёжность", 5, ["CoinGecko — цена, капитализация, объём и история DOT/BTC.", "Binance — дневные OHLCV; открытый Polkadot RPC — активность сети.", "Polkadot Docs / Wiki — технология, токеномика и OpenGov.", "Alternative.me — Fear & Greed; открытые RSS — новости.", "Повтор запроса, тайм-аут, параллельный сбор, статусы и время получения."], "Все основные источники работают без регистрации и API-ключей.")
    slide = base_slide(prs, "Технический анализ", 6)
    slide.shapes.add_picture(str(BUILD / "price_indicators.png"), Inches(.75), Inches(1.1), width=Inches(8.0))
    ppt_text(slide, "TA = 20% RSI\n   + 25% MACD\n   + 20% SMA\n   + 20% EMA\n   + 15% Bollinger Bands\n\nИндикаторы рассчитываются\nпо дневным данным.\nДля 30 дней используется\nразогрев временного ряда.", 9.0, 1.45, 3.5, 4.5, 18)
    bullet_slide(prs, "Фундаментальный и ончейн-анализ", 7, ["Фундамент: технология 25%, экосистема 25%, токеномика 20%, разработка 15%, OpenGov 15%.", "Онлайн-ончейн: среднее число extrinsics в двух выборках блоков Polkadot.", "Открытый RPC работает без регистрации и API-ключа.", "При сбое RPC показывается явно обозначенный локальный учебный резерв.", "Фундаментальные баллы — прозрачная учебная экспертная методика."])
    bullet_slide(prs, "Анализ рыночных настроений", 8, ["Удаление повторяющихся новостей.", "Словарная классификация: позитивная, нейтральная, негативная.", "NS = 50 + 50 × (P − N) / (P + N + Z).", "SA = 50% новости + 30% динамика + 20% Fear & Greed.", "Fear & Greed отражает преимущественно общий рынок, а не только DOT."], "Ограничение: словарный метод не заменяет полноценную NLP-модель.")
    bullet_slide(prs, "Комплексная оценка и противоречия", 9, ["IA = 0,30 × TA + 0,25 × FA + 0,25 × OA + 0,20 × SA.", "При пропусках: IA = ΣwᵢSᵢ / Σwᵢ; нужны минимум три модуля.", "Противоречие — расхождение оценок на 30 и более баллов.", "Дополнительно фиксируются противоположные рыночные сигналы.", "Заключение создаётся по фактическим результатам, а не по неизменному шаблону."])
    slide = base_slide(prs, "Пользовательский интерфейс", 10)
    screenshot = BUILD / "dashboard.png"
    slide.shapes.add_picture(str(screenshot if screenshot.exists() else BUILD / "module_scores.png"), Inches(.75), Inches(1.05), width=Inches(11.8))
    bullet_slide(prs, "Хранение и история", 11, ["SQLite не требует отдельной установки сервера.", "Каждое исследование сохраняет период, режим, балл и версию алгоритма.", "Полный JSON содержит ряды, индикаторы, источники, риски и заключение.", "Сохранённый анализ можно открыть после перезапуска.", "Отчёт выгружается в Markdown и HTML."])
    passed = sum(check["status"] == "PASS" for check in verification["checks"])
    bullet_slide(prs, "Тестирование", 12, [f"Выполнено проверок: {len(verification['checks'])}; успешно: {passed}.", "Формулы RSI, MACD и нормализации интегральной оценки.", "Периоды 30/90/180/365 дней и граничные условия.", "SQLite: сохранение, чтение и восстановление JSON.", "Streamlit: реальный запуск и пользовательский сценарий в браузере."], f"Онлайн-проверка: {verification.get('online', {}).get('status', 'не выполнялась')}")
    slide = base_slide(prs, "Демонстрационный результат", 13)
    slide.shapes.add_picture(str(BUILD / "module_scores.png"), Inches(.7), Inches(1.15), width=Inches(7.6))
    ppt_text(slide, f"Итог\n{result['integrated']['score']}/100\n{result['integrated']['label']}\n\nПолнота: {result['quality']['completeness']}%\nСогласованность: {result['quality']['consistency']}%\n\nДанные синтетические —\nне актуальные котировки.", 8.65, 1.45, 3.8, 4.7, 20, DARK, True)
    bullet_slide(prs, "Ограничения и риски", 14, ["Криптовалютный рынок волатилен; оценка не предсказывает цену.", "API могут ограничивать запросы или менять формат данных.", "Фундаментальные баллы требуют периодической экспертной ревизии.", "Словарь тональности чувствителен к формулировкам заголовков.", "Для полноценного анализа нужны данные парачейнов и XCM.", "Система не выполняет покупку или продажу активов."])
    bullet_slide(prs, "Итоги", 15, ["Создана работающая упрощённая система PolkaInsight.", "Реализованы все четыре аналитических направления.", "Есть комплексная оценка, противоречия, риски и объяснения.", "Работают демо и онлайн-режимы, история и выгрузка отчётов.", "Проект готов к демонстрации и дальнейшему расширению."], "Спасибо за внимание!")

    OUT.mkdir(exist_ok=True)
    path = OUT / "Презентация_PolkaInsight_Поцелуй_Комара.pptx"
    prs.save(path)
    return path


def main():
    result, verification = load_data()
    report = build_report(result, verification)
    presentation = build_presentation(result, verification)
    print(report)
    print(presentation)


if __name__ == "__main__":
    main()
