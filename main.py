# main.py
"""
Еженедельный KPI-отчёт:

1. Загружает данные пользователей и платежей из CSV.
2. Считает дневные KPI и итог за период.
3. Строит Excel-отчёт.
4. (Опционально) отправляет краткое резюме + файл в Telegram.

Примеры запуска:

    # Использовать sample-данные за последнюю неделю по данным
    python main.py

    # Явно задать период
    python main.py --start-date 2025-03-10 --end-date 2025-03-16

    # Указать свои CSV и путь к отчёту
    python main.py --users-csv data/users.csv --payments-csv data/payments.csv --output reports/report.xlsx

    # Отключить отправку в Telegram (даже если включено в config.py)
    python main.py --no-telegram
"""

import argparse

import pandas as pd

import config
from loader import load_all
from transform import compute_date_range, compute_kpis, summary_to_dict
from report_builder import build_excel_report
from notifier import send_telegram_message


def format_summary_for_message(summary_dict: dict) -> str:
    """
    Делает красивый текст для отправки в Telegram.
    """
    start = summary_dict["start_date"]
    end = summary_dict["end_date"]
    total_new_users = summary_dict["total_new_users"]
    total_paying_users = summary_dict["total_paying_users"]
    total_revenue = summary_dict["total_revenue"]
    conversion = summary_dict["conversion"]
    avg_check = summary_dict["avg_check"]

    lines = [
        f"📊 <b>Weekly KPI Report</b>",
        f"{start} — {end}",
        "",
        f"👥 Новых пользователей: <b>{total_new_users}</b>",
        f"💳 Оплативших пользователей: <b>{total_paying_users}</b>",
    ]

    if total_new_users > 0:
        lines.append(f"📈 Конверсия: <b>{conversion * 100:.1f}%</b>")

    lines.append(f"💰 Выручка: <b>{total_revenue:,.2f}</b>")

    if avg_check is not None:
        lines.append(f"🏷 Средний чек: <b>{avg_check:,.2f}</b>")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Еженедельный KPI-отчёт (данные из CSV, отчёт в Excel)."
    )
    parser.add_argument(
        "--users-csv",
        default=str(config.DEFAULT_USERS_CSV),
        help=f"Путь к CSV с пользователями (по умолчанию {config.DEFAULT_USERS_CSV}).",
    )
    parser.add_argument(
        "--payments-csv",
        default=str(config.DEFAULT_PAYMENTS_CSV),
        help=f"Путь к CSV с платежами (по умолчанию {config.DEFAULT_PAYMENTS_CSV}).",
    )
    parser.add_argument(
        "--start-date",
        help="Дата начала периода (YYYY-MM-DD). Если не задана, берётся последняя неделя по данным.",
    )
    parser.add_argument(
        "--end-date",
        help="Дата окончания периода (YYYY-MM-DD). Если не задана, берётся последняя неделя по данным.",
    )
    parser.add_argument(
        "--output",
        default=str(config.DEFAULT_REPORT_PATH),
        help=f"Путь к Excel-отчёту (по умолчанию {config.DEFAULT_REPORT_PATH}).",
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Не отправлять отчёт в Telegram, даже если ENABLE_TELEGRAM=True.",
    )

    args = parser.parse_args()

    # 1. Загружаем данные
    print(f"Загружаю пользователей из: {args.users_csv}")
    print(f"Загружаю платежи из: {args.payments_csv}")
    users_df, payments_df = load_all(args.users_csv, args.payments_csv)

    if users_df.empty and payments_df.empty:
        print("Нет данных ни по пользователям, ни по платежам — отчёт не имеет смысла.")
        return

    # 2. Определяем период
    start_date, end_date = compute_date_range(
        users_df, payments_df, start_date=args.start_date, end_date=args.end_date
    )
    print(f"Период отчёта: {start_date.date().isoformat()} — {end_date.date().isoformat()}")

    # 3. Считаем KPI
    daily_df, summary = compute_kpis(users_df, payments_df, start_date, end_date)
    summary_dict = summary_to_dict(summary)

    # Немного консольного вывода
    print("\nИтого за период:")
    print(f"  Новых пользователей: {summary.total_new_users}")
    print(f"  Оплативших пользователей: {summary.total_paying_users}")
    print(f"  Выручка: {summary.total_revenue:.2f}")
    if summary.total_new_users > 0:
        print(f"  Конверсия: {summary.conversion * 100:.1f}%")
    if summary.avg_check is not None:
        print(f"  Средний чек: {summary.avg_check:.2f}")

    # 4. Строим Excel-отчёт
    report_path = build_excel_report(
        users_df=users_df,
        payments_df=payments_df,
        daily_df=daily_df,
        summary_dict=summary_dict,
        output_path=args.output,
    )
    print(f"\nExcel-отчёт сохранён: {report_path}")

    # 5. (Опционально) отправляем в Telegram
    if not args.no_telegram and config.ENABLE_TELEGRAM:
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print(
                "\n[Telegram] ENABLE_TELEGRAM=True, но не заданы TELEGRAM_BOT_TOKEN/CHAT_ID "
                "— отправка пропущена."
            )
        else:
            print("\n[Telegram] Отправляю отчёт...")
            text = format_summary_for_message(summary_dict)
            send_telegram_message(
                token=config.TELEGRAM_BOT_TOKEN,
                chat_id=config.TELEGRAM_CHAT_ID,
                text=text,
                file_path=report_path,
            )
            print("[Telegram] Готово.")


if __name__ == "__main__":
    main()
