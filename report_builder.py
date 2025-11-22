# report_builder.py
"""
Создание Excel-отчёта с несколькими листами:
  - raw_users
  - raw_payments
  - daily_kpi
  - summary
"""

from pathlib import Path
from typing import Dict

import pandas as pd


def build_excel_report(
    users_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    daily_df: pd.DataFrame,
    summary_dict: Dict[str, object],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for key, value in summary_dict.items():
        summary_rows.append({"metric": key, "value": value})
    summary_df = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        users_df.to_excel(writer, sheet_name="raw_users", index=False)
        payments_df.to_excel(writer, sheet_name="raw_payments", index=False)
        daily_df.to_excel(writer, sheet_name="daily_kpi", index=False)
        summary_df.to_excel(writer, sheet_name="summary", index=False)

        # Здесь можно дополнительно через openpyxl добавить графики,
        # стили форматирования и т.п. — оставим как будущий апгрейд.

    return output_path
