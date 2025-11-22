# transform.py
"""
Бизнес-логика: расчёт дневных KPI и агрегированного итога.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd


@dataclass
class SummaryKPI:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    total_new_users: int
    total_paying_users: int
    total_revenue: float
    conversion: float  # доля: 0.0..1.0
    avg_check: float | None


def compute_date_range(
    users: pd.DataFrame,
    payments: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    window_days: int = 7,
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Определяет период отчёта.

    Если start_date/end_date не заданы:
      - берём максимальную дату из пользователей/платежей
      - считаем окно длиной window_days (по умолчанию 7).
    """
    if start_date is not None and end_date is not None:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return start.normalize(), end.normalize()

    all_dates = []
    if not users.empty:
        all_dates.append(users["registered_at"].max())
    if not payments.empty:
        all_dates.append(payments["paid_at"].max())

    if not all_dates:
        raise ValueError("Невозможно определить диапазон дат: нет данных.")

    last_date = max(all_dates).normalize()
    first_date = last_date - pd.Timedelta(days=window_days - 1)
    return first_date, last_date


def compute_kpis(
    users: pd.DataFrame,
    payments: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> Tuple[pd.DataFrame, SummaryKPI]:
    """
    Рассчитывает дневные KPI + агрегированный итог.

    Возвращает:
      - daily_df: дата, new_users, paying_users, payments_count, revenue, conversion, avg_check
      - summary: SummaryKPI
    """
    # Фильтруем данные по диапазону
    users_period = users[
        (users["registered_at"] >= start_date) & (users["registered_at"] <= end_date)
    ].copy()
    payments_period = payments[
        (payments["paid_at"] >= start_date) & (payments["paid_at"] <= end_date)
    ].copy()

    # Преобразуем даты к "дате без времени"
    users_period["date"] = users_period["registered_at"].dt.normalize()
    payments_period["date"] = payments_period["paid_at"].dt.normalize()

    # Диапазон дат по дням
    all_dates = pd.date_range(start_date, end_date, freq="D")

    # Новые пользователи по дням
    new_users_by_day = (
        users_period.groupby("date")["user_id"].nunique().reindex(all_dates, fill_value=0)
    )

    # Платящие пользователи по дням (уникальные юзеры)
    paying_users_by_day = (
        payments_period.groupby("date")["user_id"].nunique().reindex(all_dates, fill_value=0)
    )

    # Кол-во платежей по дням
    payments_count_by_day = (
        payments_period.groupby("date")["payment_id"].nunique().reindex(all_dates, fill_value=0)
    )

    # Выручка по дням
    revenue_by_day = (
        payments_period.groupby("date")["amount"].sum().reindex(all_dates, fill_value=0.0)
    )

    # Конверсия по дням: платящие / новые (по зарегистрированным в этот же день)
    conversion_by_day = []
    for d in all_dates:
        new_u = new_users_by_day.loc[d]
        pay_u = paying_users_by_day.loc[d]
        if new_u > 0:
            conversion_by_day.append(pay_u / new_u)
        else:
            conversion_by_day.append(0.0)

    conversion_by_day = pd.Series(conversion_by_day, index=all_dates)

    # Средний чек по дням
    avg_check_by_day = []
    for d in all_dates:
        mask = payments_period["date"] == d
        day_payments = payments_period.loc[mask, "amount"]
        if not day_payments.empty:
            avg_check_by_day.append(day_payments.mean())
        else:
            avg_check_by_day.append(0.0)

    avg_check_by_day = pd.Series(avg_check_by_day, index=all_dates)

    daily_df = pd.DataFrame(
        {
            "date": all_dates,
            "new_users": new_users_by_day.values,
            "paying_users": paying_users_by_day.values,
            "payments_count": payments_count_by_day.values,
            "revenue": revenue_by_day.values,
            "conversion": conversion_by_day.values,  # доля
            "avg_check": avg_check_by_day.values,
        }
    )

    # Агрегированный итог
    total_new_users = int(new_users_by_day.sum())
    total_paying_users = int(payments_period["user_id"].nunique())
    total_revenue = float(revenue_by_day.sum())
    avg_check_overall = (
        float(payments_period["amount"].mean()) if not payments_period.empty else None
    )

    if total_new_users > 0:
        conversion_overall = total_paying_users / total_new_users
    else:
        conversion_overall = 0.0

    summary = SummaryKPI(
        start_date=start_date,
        end_date=end_date,
        total_new_users=total_new_users,
        total_paying_users=total_paying_users,
        total_revenue=total_revenue,
        conversion=conversion_overall,
        avg_check=avg_check_overall,
    )

    return daily_df, summary


def summary_to_dict(summary: SummaryKPI) -> Dict[str, object]:
    """Удобный helper для передачи в отчёт/уведомление."""
    return {
        "start_date": summary.start_date.date().isoformat(),
        "end_date": summary.end_date.date().isoformat(),
        "total_new_users": summary.total_new_users,
        "total_paying_users": summary.total_paying_users,
        "total_revenue": summary.total_revenue,
        "conversion": summary.conversion,
        "avg_check": summary.avg_check,
    }
