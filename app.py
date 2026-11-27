from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from polkainsight.analysis import MODULE_NAMES, score_label
from polkainsight.pipeline import run_analysis
from polkainsight.report import html_report, markdown_report
from polkainsight.storage import HistoryStorage


st.set_page_config(page_title="PolkaInsight", page_icon="●", layout="wide")
st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {background: #fff; border: 1px solid #e8e2eb; border-radius: 14px; padding: 14px 16px;}
    [data-testid="stMetricValue"] {color: #25202b; font-size: 1.65rem;}
    [data-testid="stMetricLabel"] {font-size: .9rem;}
    .hero {background: linear-gradient(110deg, #29142d, #681342 70%, #e6007a); color: white;
           padding: 24px 28px; border-radius: 18px; margin-bottom: 18px;}
    .hero h1 {margin: 0; font-size: 2rem;} .hero p {margin: 6px 0 0; color: #f4dce9;}
    .score-box {border-left: 5px solid #e6007a; background: #fff2f8; padding: 14px 18px; border-radius: 8px;}
    .small-note {color: #746d79; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

storage = HistoryStorage()
if "result" not in st.session_state:
    st.session_state.result = run_analysis(90, "demo", True)
    st.session_state.history_id = storage.save(st.session_state.result)

st.sidebar.title("PolkaInsight")
st.sidebar.caption("Команда «Поцелуй Комара»")
mode_label = st.sidebar.radio("Режим данных", ["Демонстрационный", "Онлайн"], help="Демо работает без интернета и использует синтетические данные.")
days = st.sidebar.select_slider("Период анализа", options=[30, 90, 180, 365], value=90, format_func=lambda value: f"{value} дней")
compare = st.sidebar.checkbox("Сравнить DOT с BTC", value=True)
run_clicked = st.sidebar.button("Запустить анализ", type="primary", width="stretch")
with st.sidebar.expander("Онлайн-источники без ключей"):
    st.caption("Регистрация и API-ключи не нужны. Используются CoinGecko, Binance, Alternative.me, открытые RSS-ленты и Polkadot Public RPC.")
    st.caption("Если новостные сайты или RPC недоступны, соответствующий раздел показывает явно обозначенный локальный учебный резерв.")

if run_clicked:
    mode = "online" if mode_label == "Онлайн" else "demo"
    try:
        with st.spinner("Собираем данные и рассчитываем показатели…"):
            new_result = run_analysis(days, mode, compare)
            history_id = storage.save(new_result)
        st.session_state.result = new_result
        st.session_state.history_id = history_id
        st.success(f"Анализ завершён и сохранён в истории под № {history_id}.")
    except Exception as error:
        st.error(str(error))
        st.info("Показан предыдущий результат. Для работы без внешних API выберите демонстрационный режим.")

result = st.session_state.result
metadata = result["metadata"]
market = result["market"]
modules = result["modules"]
series = pd.DataFrame(result["series"])
series["date"] = pd.to_datetime(series["date"], utc=True)

st.markdown(f"""
<div class="hero"><h1>PolkaInsight</h1>
<p>Интеллектуальная система комплексного анализа Polkadot (DOT) · {metadata['start_date']} — {metadata['end_date']}</p></div>
""", unsafe_allow_html=True)
if metadata["mode"] == "demo":
    st.warning("Демонстрационный режим: все значения синтетические и нужны только для проверки работы системы. Это не актуальные котировки.")
else:
    st.success(f"Онлайн-анализ выполнен: {metadata['created_at']}. Перед интерпретацией проверьте статусы источников.")

price = market.get("price")
change_24h = market.get("change_24h")
period_change = market.get("period_change")
metric_columns = st.columns(5)
metric_columns[0].metric("Цена DOT", f"${price:,.4f}" if price is not None else "н/д", f"{change_24h:+.2f}% / 24 ч" if change_24h is not None else None)
metric_columns[1].metric(f"Изменение / {metadata['period_days']} дн.", f"{period_change:+.2f}%" if period_change is not None else "н/д")
metric_columns[2].metric("Капитализация", f"${market['market_cap'] / 1e9:.2f} млрд" if market.get("market_cap") else "н/д")
metric_columns[3].metric("Объём торгов", f"${market['volume'] / 1e6:.1f} млн" if market.get("volume") else "н/д")
integrated_score = result["integrated"]["score"]
metric_columns[4].metric("Интегральная оценка", f"{integrated_score:.1f}/100" if integrated_score is not None else "н/д", result["integrated"]["label"])

st.subheader("Результаты аналитических модулей")
score_columns = st.columns(4)
for column, (key, title) in zip(score_columns, MODULE_NAMES.items()):
    score = modules[key]["score"]
    column.metric(title, f"{score:.1f}/100" if score is not None else "н/д", score_label(score))
    column.progress((score or 0) / 100)

st.markdown(f'<div class="score-box"><b>Заключение.</b> {result["conclusion"]}</div>', unsafe_allow_html=True)

tabs = st.tabs(["Обзор", "Технический анализ", "Фундамент и сеть", "Новости и отчёт", "История"])

with tabs[0]:
    st.subheader("Цена DOT и технические индикаторы")
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=series["date"], y=series["close"], name="DOT/USD", line=dict(color="#e6007a", width=2.5)))
    figure.add_trace(go.Scatter(x=series["date"], y=series["sma"], name="SMA 20", line=dict(color="#5e17eb")))
    figure.add_trace(go.Scatter(x=series["date"], y=series["ema"], name="EMA 20", line=dict(color="#ff9f1c")))
    figure.add_trace(go.Scatter(x=series["date"], y=series["bb_upper"], name="Верхняя BB", line=dict(color="#b8adb9", dash="dot")))
    figure.add_trace(go.Scatter(x=series["date"], y=series["bb_lower"], name="Нижняя BB", line=dict(color="#b8adb9", dash="dot"), fill="tonexty", fillcolor="rgba(184,173,185,.10)"))
    figure.update_layout(height=450, hovermode="x unified", yaxis_title="USD", legend_orientation="h", margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(figure, width="stretch")

    if result["comparison_series"]:
        comparison = pd.DataFrame(result["comparison_series"])
        comparison["date"] = pd.to_datetime(comparison["date"], utc=True)
        compare_figure = go.Figure()
        compare_figure.add_trace(go.Scatter(x=series["date"], y=series["close"] / series["close"].iloc[0] * 100, name="DOT", line=dict(color="#e6007a")))
        compare_figure.add_trace(go.Scatter(x=comparison["date"], y=comparison["close"] / comparison["close"].iloc[0] * 100, name="BTC", line=dict(color="#f7931a")))
        compare_figure.update_layout(title="Сравнительная динамика: начало периода = 100", height=360, hovermode="x unified", legend_orientation="h")
        st.plotly_chart(compare_figure, width="stretch")

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Качество данных")
        quality = result["quality"]
        quality_frame = pd.DataFrame([
            {"Показатель": "Полнота данных", "Значение, %": quality["completeness"]},
            {"Показатель": "Согласованность модулей", "Значение, %": quality["consistency"]},
            {"Показатель": "Индекс уверенности", "Значение, %": quality["confidence"]},
        ])
        st.dataframe(quality_frame, hide_index=True, width="stretch")
        st.caption("Индекс уверенности — учебная сводная характеристика полноты и согласованности, а не вероятность прибыли.")
    with right:
        st.subheader("Противоречия")
        if result["conflicts"]:
            for conflict in result["conflicts"]:
                st.error(f"{conflict['module_1']} ↔ {conflict['module_2']}: {conflict['description']}")
        else:
            st.success("Существенных противоречий не обнаружено.")

with tabs[1]:
    st.subheader("Текущие значения индикаторов")
    indicators = modules["technical"].get("indicators", {})
    if indicators:
        indicator_frame = pd.DataFrame({"Индикатор": list(indicators.keys()), "Значение": list(indicators.values())})
        st.dataframe(indicator_frame, hide_index=True, width="stretch")
        for text in modules["technical"]["explanations"]:
            st.write(f"- {text}")
        left, right = st.columns(2)
        rsi_figure = go.Figure(go.Scatter(x=series["date"], y=series["rsi"], line=dict(color="#5e17eb"), name="RSI"))
        rsi_figure.add_hrect(y0=0, y1=30, fillcolor="rgba(0,180,120,.08)", line_width=0)
        rsi_figure.add_hrect(y0=70, y1=100, fillcolor="rgba(230,0,122,.08)", line_width=0)
        rsi_figure.add_hline(y=30, line_dash="dot", line_color="gray")
        rsi_figure.add_hline(y=70, line_dash="dot", line_color="gray")
        rsi_figure.update_layout(title="RSI (14)", height=330, yaxis_range=[0, 100])
        left.plotly_chart(rsi_figure, width="stretch")
        macd_figure = go.Figure()
        macd_figure.add_trace(go.Bar(x=series["date"], y=series["macd_hist"], name="Гистограмма", marker_color="#b8adb9"))
        macd_figure.add_trace(go.Scatter(x=series["date"], y=series["macd"], name="MACD", line=dict(color="#e6007a")))
        macd_figure.add_trace(go.Scatter(x=series["date"], y=series["macd_signal"], name="Signal", line=dict(color="#5e17eb")))
        macd_figure.update_layout(title="MACD (12, 26, 9)", height=330, hovermode="x unified")
        right.plotly_chart(macd_figure, width="stretch")
    else:
        st.warning("Недостаточно наблюдений для технического анализа.")

with tabs[2]:
    left, right = st.columns(2)
    with left:
        st.subheader("Фундаментальная оценка")
        fundamental = modules["fundamental"]
        criteria = pd.DataFrame(fundamental["criteria"])[["criterion", "score", "weight"]]
        criteria.columns = ["Критерий", "Балл", "Вес"]
        st.dataframe(criteria, hide_index=True, width="stretch")
        for item in fundamental["criteria"]:
            st.markdown(f"**{item['criterion']}** — [{item['basis']}]({item['url']})")
        for text in fundamental["explanations"]:
            st.caption(text)
    with right:
        st.subheader("Ончейн-показатели")
        onchain = modules["onchain"]
        data_mode = onchain.get("data_mode")
        if data_mode == "rpc":
            st.success("Данные получены напрямую из открытого Polkadot RPC. Ключ не нужен.")
        elif data_mode == "educational":
            st.warning("RPC сети недоступен. Показан локальный учебный набор — это не реальная статистика блокчейна.")
        if onchain["metrics"]:
            onchain_frame = pd.DataFrame(onchain["metrics"])[["metric", "current", "previous", "change_pct", "score"]]
            onchain_frame.columns = ["Показатель", "Текущее", "Предыдущее", "Изменение, %", "Балл"]
            st.dataframe(onchain_frame, hide_index=True, width="stretch")
        else:
            st.warning("Недостаточно данных для расчёта ончейн-показателей.")
        for text in onchain["explanations"]:
            st.write(f"- {text}")

with tabs[3]:
    sentiment = modules["sentiment"]
    left, right = st.columns([1, 2])
    with left:
        st.subheader("Рыночные настроения")
        st.metric("Fear & Greed", sentiment.get("fear_greed") if sentiment.get("fear_greed") is not None else "н/д", sentiment.get("fear_greed_label") or None)
        counts = sentiment["counts"]
        sentiment_figure = go.Figure(go.Bar(x=["Позитивные", "Нейтральные", "Негативные"], y=[counts["positive"], counts["neutral"], counts["negative"]], marker_color=["#16a085", "#b8adb9", "#e6007a"]))
        sentiment_figure.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(sentiment_figure, width="stretch")
        for text in sentiment["explanations"]:
            st.caption(text)
    with right:
        st.subheader("Новости")
        news_display = result.get("news_display", sentiment["news"])
        news_status = result.get("news_status", "ok" if sentiment["news"] else "fallback")
        if news_status == "fallback":
            st.info("Внешние новостные сайты недоступны. Показаны локальные учебные примеры; они не участвуют в онлайн-оценке.")
        elif news_status == "stale":
            st.info("Свежих публикаций нет. Показан архив новостей Polkadot; актуальная оценка настроений использует только Fear & Greed.")
        elif news_status == "partial":
            st.info("Публикации старше 30 дней показаны как архив и не участвуют в оценке актуальных настроений.")
        if news_display:
            news_frame = pd.DataFrame(news_display)[["title", "source", "published", "sentiment", "url"]]
            news_frame.columns = ["Заголовок", "Источник", "Дата", "Тональность", "Ссылка"]
            news_frame["Тональность"] = news_frame["Тональность"].map({"positive": "Позитивная", "negative": "Негативная", "neutral": "Нейтральная", "not_used": "Не учитывается"}).fillna("Не учитывается")
            st.dataframe(news_frame, hide_index=True, width="stretch", column_config={"Ссылка": st.column_config.LinkColumn("Ссылка", display_text="Открыть")})
        else:
            st.warning("Новости не получены; использован только доступный индекс настроений.")

    st.divider()
    st.subheader("Автоматический аналитический отчёт")
    st.markdown(f"**Формула расчёта:** {result['integrated']['formula']}")
    st.write(result["conclusion"])
    st.write("**Основные риски:**")
    for risk in result["risks"]:
        st.write(f"- {risk}")
    st.write("**Источники:**")
    source_frame = pd.DataFrame(result["sources"])[["name", "category", "status", "message", "updated_at"]]
    source_frame.columns = ["Источник", "Категория", "Статус", "Сообщение", "Время получения"]
    st.dataframe(source_frame, hide_index=True, width="stretch")
    download_left, download_right = st.columns(2)
    download_left.download_button("Скачать отчёт Markdown", markdown_report(result), file_name="PolkaInsight_report.md", mime="text/markdown", width="stretch")
    download_right.download_button("Скачать отчёт HTML", html_report(result), file_name="PolkaInsight_report.html", mime="text/html", width="stretch")

with tabs[4]:
    st.subheader("История исследований")
    st.caption("Результаты сохраняются в data/polkainsight.db и остаются доступными после перезапуска.")
    history = storage.list()
    if history:
        history_frame = pd.DataFrame(history)
        history_frame.columns = ["№", "Дата", "Актив", "Период, дн.", "Режим", "Итог", "Версия"]
        st.dataframe(history_frame, hide_index=True, width="stretch")
        selected = st.selectbox("Открыть сохранённый анализ", options=[item["id"] for item in history], format_func=lambda item: f"№ {item}")
        if st.button("Загрузить выбранный результат"):
            loaded = storage.get(selected)
            if loaded:
                st.session_state.result = loaded
                st.session_state.history_id = selected
                st.rerun()
        current_id = st.session_state.get("history_id")
        previous = next((item for item in history if item["id"] != current_id and item["integrated_score"] is not None), None)
        if previous and integrated_score is not None:
            delta = integrated_score - previous["integrated_score"]
            st.metric(f"Изменение относительно анализа № {previous['id']}", f"{integrated_score:.1f}", f"{delta:+.1f} балла")
    else:
        st.info("История пока пуста. Запустите анализ.")

st.divider()
st.caption("PolkaInsight · учебный проект команды «Поцелуй Комара» · Не является индивидуальной инвестиционной рекомендацией.")
