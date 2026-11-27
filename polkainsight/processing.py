from __future__ import annotations

import pandas as pd


def prepare_market(frame: pd.DataFrame, stale_after_days: int = 3) -> tuple[pd.DataFrame, list[str]]:
    """Нормализует дневной ряд и возвращает список обнаруженных проблем."""
    if frame is None or frame.empty:
        return pd.DataFrame(), ["Рыночный временной ряд отсутствует."]
    data = frame.copy()
    issues = []
    data["date"] = pd.to_datetime(data["date"], utc=True, errors="coerce")
    duplicated = int(data.duplicated("date").sum())
    if duplicated:
        issues.append(f"Удалено повторяющихся временных меток: {duplicated}.")
    data = data.dropna(subset=["date"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)
    for column in ("open", "high", "low", "close", "volume"):
        if column not in data:
            data[column] = data["close"] if column != "volume" else 0.0
        data[column] = pd.to_numeric(data[column], errors="coerce")

    missing_close = int(data["close"].isna().sum())
    invalid_close = int((data["close"] <= 0).sum())
    data.loc[data["close"] <= 0, "close"] = pd.NA
    returns = data["close"].pct_change(fill_method=None)
    anomalies = returns.abs() > 0.80
    anomaly_count = int(anomalies.sum())
    if anomaly_count:
        data.loc[anomalies, "close"] = pd.NA
        issues.append(f"Аномальных скачков более 80% заменено интерполяцией: {anomaly_count}.")
    if missing_close or invalid_close:
        issues.append(f"Пропущенных или неположительных цен обработано: {missing_close + invalid_close}.")
    data["close"] = data["close"].interpolate(method="linear", limit=2, limit_direction="both")
    remaining = int(data["close"].isna().sum())
    if remaining:
        issues.append(f"Удалено записей с невосстановимой ценой: {remaining}.")
    data = data.dropna(subset=["close"]).reset_index(drop=True)
    for column in ("open", "high", "low"):
        data[column] = data[column].fillna(data["close"])
        data.loc[data[column] <= 0, column] = data["close"]
    data["volume"] = data["volume"].fillna(0).clip(lower=0)
    if not data.empty:
        age = pd.Timestamp.now(tz="UTC") - data.iloc[-1]["date"]
        if age > pd.Timedelta(days=stale_after_days):
            issues.append(f"Последнее рыночное наблюдение устарело: {age.days} дн.")
    return data, issues
