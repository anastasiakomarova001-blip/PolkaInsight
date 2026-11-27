from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_analysis
from .report import markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="PolkaInsight — комплексный анализ Polkadot")
    parser.add_argument("--mode", choices=("demo", "online"), default="demo")
    parser.add_argument("--days", type=int, choices=(30, 90, 180, 365), default=90)
    parser.add_argument("--output", type=Path, help="Сохранить отчёт в Markdown")
    parser.add_argument("--json", type=Path, help="Сохранить полный результат в JSON")
    args = parser.parse_args()
    result = run_analysis(args.days, args.mode)
    score = result["integrated"]["score"]
    print(f"Polkadot (DOT): {result['integrated']['label']}")
    print(f"Интегральная оценка: {score if score is not None else 'н/д'}/100")
    print(f"Полнота данных: {result['quality']['completeness']}%")
    print(result["conclusion"])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown_report(result), encoding="utf-8")
        print(f"Отчёт: {args.output}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON: {args.json}")


if __name__ == "__main__":
    main()
