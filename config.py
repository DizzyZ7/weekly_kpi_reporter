# config.py
"""
Конфиг для проекта: настройки путей и Telegram.

Для реального использования:
  - выставьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID через переменные окружения
    или пропиши прямо в этом файле (но так хуже с точки зрения безопасности).
"""

import os
from pathlib import Path

# Пути по умолчанию
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_USERS_CSV = BASE_DIR / "data_sample" / "users_sample.csv"
DEFAULT_PAYMENTS_CSV = BASE_DIR / "data_sample" / "payments_sample.csv"
DEFAULT_REPORT_PATH = BASE_DIR / "reports" / "weekly_kpi_report.xlsx"

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Включать ли отправку отчёта в Telegram (по умолчанию выключено)
ENABLE_TELEGRAM = False
