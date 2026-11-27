from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
PINK = "#E6007A"
PURPLE = "#5E17EB"
DARK = "#29202E"


def box(ax, x, y, width, height, text, color="#F8EAF3", size=10):
    patch = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.015,rounding_size=0.02", facecolor=color, edgecolor=PURPLE, linewidth=1.3)
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=size, color=DARK, wrap=True)
    return (x + width / 2, y + height / 2)


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14, linewidth=1.2, color="#756B7C"))


def architecture():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    sources = box(ax, .02, .29, .15, .42, "ВНЕШНИЕ ИСТОЧНИКИ\n\nCoinGecko · Binance\nPolkadot Public RPC\nAlternative.me\nCryptoPanic / RSS\nPolkadot Docs", "#F3F0F7", 10)
    collection = box(ax, .23, .47, .14, .16, "Сбор данных\nи повторные\nзапросы", size=11)
    processing = box(ax, .23, .19, .14, .16, "Проверка,\nочистка и\nнормализация", size=11)
    modules = []
    for y, text in zip((.78, .59, .40, .21), ("Технический\nанализ", "Фундаментальный\nанализ", "Ончейн-\nанализ", "Анализ\nнастроений")):
        modules.append(box(ax, .46, y, .16, .12, text, size=10))
    integrated = box(ax, .70, .47, .13, .17, "Комплексная\nоценка и\nпротиворечия", "#FCE0EF", 10)
    report = box(ax, .87, .62, .11, .15, "Отчёт и\nдашборд\nStreamlit", size=10)
    database = box(ax, .70, .16, .13, .13, "SQLite\nИстория\nисследований", "#E9E2F5", 10)
    arrow(ax, (sources[0] + .075, sources[1]), (collection[0] - .07, collection[1]))
    arrow(ax, (collection[0], collection[1] - .08), (processing[0], processing[1] + .08))
    for module in modules:
        arrow(ax, (processing[0] + .07, processing[1]), (module[0] - .08, module[1]))
        arrow(ax, (module[0] + .08, module[1]), (integrated[0] - .065, integrated[1]))
    arrow(ax, (integrated[0] + .065, integrated[1]), (report[0] - .055, report[1]))
    arrow(ax, (integrated[0], integrated[1] - .085), (database[0], database[1] + .065))
    arrow(ax, (database[0] + .065, database[1]), (report[0] - .055, report[1] - .04))
    ax.set_title("Архитектура PolkaInsight", fontsize=18, fontweight="bold", color=DARK, pad=14)
    fig.tight_layout()
    fig.savefig(BUILD / "architecture.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def erd():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    history = box(ax, .07, .31, .29, .40, "ANALYSIS_HISTORY\n────────────────\nPK  id\ncreated_at\nasset\nperiod_days\nmode\nintegrated_score\nalgorithm_version\nresult_json", "#E9E2F5", 11)
    result = box(ax, .58, .31, .34, .40, "РЕЗУЛЬТАТ (JSON)\n────────────────\nРыночные показатели\nОценки четырёх модулей\nВременные ряды\nПротиворечия и риски\nИсточники и их статусы\nЗаключение", "#F8EAF3", 11)
    arrow(ax, (history[0] + .145, history[1]), (result[0] - .17, result[1]))
    ax.text(.5, .48, "1 : 1", fontsize=11, color=DARK)
    ax.text(.5, .22, "Упрощённая схема: исходные данные и результаты исследования\nхранятся в JSON внутри записи истории. Это позволяет восстановить отчёт без потери данных.", ha="center", fontsize=11, color=DARK)
    ax.set_title("Модель хранения данных", fontsize=18, fontweight="bold", color=DARK, pad=14)
    fig.tight_layout()
    fig.savefig(BUILD / "erd.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def analysis_figures(result):
    series = pd.DataFrame(result["series"])
    series["date"] = pd.to_datetime(series["date"])
    fig, (ax, rsi_ax) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax.plot(series["date"], series["close"], label="DOT/USD", color=PINK, linewidth=2.2)
    ax.plot(series["date"], series["sma"], label="SMA 20", color=PURPLE)
    ax.plot(series["date"], series["ema"], label="EMA 20", color="#F39C12")
    ax.fill_between(series["date"], series["bb_lower"], series["bb_upper"], color="#CFC5D4", alpha=.25, label="Bollinger Bands")
    ax.set_ylabel("USD")
    ax.legend(ncol=4, loc="upper left")
    ax.grid(alpha=.2)
    ax.set_title("Демонстрационный временной ряд и индикаторы", fontsize=15, fontweight="bold")
    rsi_ax.plot(series["date"], series["rsi"], color=PURPLE)
    rsi_ax.axhline(30, color="gray", linestyle="--", linewidth=.8)
    rsi_ax.axhline(70, color="gray", linestyle="--", linewidth=.8)
    rsi_ax.set_ylim(0, 100)
    rsi_ax.set_ylabel("RSI")
    rsi_ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(BUILD / "price_indicators.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    labels = ["Технический", "Фундаментальный", "Ончейн", "Настроения"]
    keys = ["technical", "fundamental", "onchain", "sentiment"]
    scores = [result["modules"][key]["score"] or 0 for key in keys]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    bars = ax.barh(labels, scores, color=[PINK, PURPLE, "#8E44AD", "#F39C12"])
    ax.bar_label(bars, fmt="%.1f")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Балл из 100")
    ax.set_title(f"Оценки модулей · интегральный результат {result['integrated']['score']}/100", fontsize=15, fontweight="bold")
    ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(BUILD / "module_scores.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    BUILD.mkdir(exist_ok=True)
    result = json.loads((BUILD / "demo_result.json").read_text(encoding="utf-8"))
    architecture()
    erd()
    analysis_figures(result)
    print("Figures created in", BUILD)


if __name__ == "__main__":
    main()
