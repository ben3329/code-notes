import os
from enum import Enum

import openpyxl
from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Border, Font, NamedStyle, Side
from openpyxl.utils import get_column_letter


class NamedStyleEnum(Enum):
    STYLE_CENTERED = "centered"
    STYLE_HEADER_CENTERED = "header_centered"
    STYLE_PERCENT_CENTERED = "percent_centered"
    STYLE_DATE_DAY_CENTERED = "date_day_centered"
    STYLE_DATE_MONTH_CENTERED = "date_month_centered"


def ensure_default_styles(wb: openpyxl.Workbook) -> None:
    """Register default NamedStyles on the given workbook if missing.

    Adds centered, header, percent, and date styles with a thin border and
    consistent font size for consistent formatting across generated sheets.
    """

    thin_side = Side(style="thin", color="000000")
    thin_border = Border(
        left=thin_side, right=thin_side, top=thin_side, bottom=thin_side
    )

    centered_style = NamedStyle(
        name=NamedStyleEnum.STYLE_CENTERED.value,
        alignment=Alignment(horizontal="center", vertical="center"),
        border=thin_border,
        font=Font(size=11),
    )
    header_centered_style = NamedStyle(
        name=NamedStyleEnum.STYLE_HEADER_CENTERED.value,
        alignment=Alignment(horizontal="center", vertical="center"),
        border=thin_border,
        font=Font(bold=True, color="000000", size=11),
    )
    percent_centered_style = NamedStyle(
        name=NamedStyleEnum.STYLE_PERCENT_CENTERED.value,
        alignment=Alignment(horizontal="center", vertical="center"),
        border=thin_border,
        font=Font(size=11),
        number_format="0.00%",
    )
    date_day_centered_style = NamedStyle(
        name=NamedStyleEnum.STYLE_DATE_DAY_CENTERED.value,
        alignment=Alignment(horizontal="center", vertical="center"),
        border=thin_border,
        font=Font(size=11),
        number_format="yyyy-mm-dd",
    )
    date_month_centered_style = NamedStyle(
        name=NamedStyleEnum.STYLE_DATE_MONTH_CENTERED.value,
        alignment=Alignment(horizontal="center", vertical="center"),
        border=thin_border,
        font=Font(size=11),
        number_format="yyyy-mm",
    )

    existing_styles = {getattr(s, "name", str(s)) for s in wb.named_styles}
    for style in (
        centered_style,
        header_centered_style,
        percent_centered_style,
        date_day_centered_style,
        date_month_centered_style,
    ):
        if style.name not in existing_styles:
            wb.add_named_style(style)


def set_style(cell: Cell, style: NamedStyleEnum) -> None:
    """Apply a NamedStyleEnum to a given cell."""
    cell.style = style.value
