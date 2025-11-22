# loader.py
"""
Загрузка данных из CSV.

Ожидаемые форматы:

users:
    user_id,registered_at,source

payments:
    payment_id,user_id,amount,currency,paid_at
"""

from pathlib import Path
from typing import Tuple

import pandas as pd


def load_users(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["registered_at"] = pd.to_datetime(df["registered_at"])
    return df


def load_payments(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["paid_at"] = pd.to_datetime(df["paid_at"])
    return df


def load_all(
    users_path: str | Path,
    payments_path: str | Path,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    users = load_users(users_path)
    payments = load_payments(payments_path)
    return users, payments
