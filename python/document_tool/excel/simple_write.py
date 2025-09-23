import os

import openpyxl


def write_excel(colums: list, rows: list, out_path: str) -> None:
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append(colums)
    for row in rows:
        sheet.append(row)
    wb.save(out_path)
