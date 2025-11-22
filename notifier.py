# notifier.py
"""
Отправка отчёта в Telegram через Bot API (опционально).

Чтобы заработало:
  1. Создай бота через @BotFather и получи токен.
  2. Узнай свой CHAT_ID (через отдельный маленький скрипт или бота).
  3. Пропиши TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в config.py
     или через переменные окружения.
"""

from pathlib import Path
from typing import Optional

import requests


def send_telegram_message(
    token: str,
    chat_id: str,
    text: str,
    file_path: Optional[str | Path] = None,
) -> None:
    if not token or not chat_id:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID")

    base_url = f"https://api.telegram.org/bot{token}"

    # Сначала отправляем текст
    resp = requests.post(
        f"{base_url}/sendMessage",
        data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=15,
    )
    resp.raise_for_status()

    # Если есть файл — отправляем как документ
    if file_path is not None:
        file_path = Path(file_path)
        with file_path.open("rb") as f:
            resp = requests.post(
                f"{base_url}/sendDocument",
                data={"chat_id": chat_id},
                files={"document": (file_path.name, f)},
                timeout=30,
            )
        resp.raise_for_status()
