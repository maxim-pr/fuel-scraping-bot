import pandas as pd
from styleframe import StyleFrame, Styler, utils


def save_as_xl(df: pd.DataFrame, path: str):
    writer = StyleFrame.ExcelWriter(path)
    frame = StyleFrame(df)

    frame.apply_column_style(
        cols_to_style=frame.columns,
        styler_obj=Styler(bg_color=utils.colors.white,
                          font=utils.fonts.arial,
                          font_size=12),
        style_header=True
    )

    frame.apply_headers_style(
        styler_obj=Styler(
            bold=True,
            font_size=14,
        )
    )

    frame.set_column_width(columns=frame.columns, width=40)
    frame.set_row_height(rows=frame.row_indexes, height=30)

    frame.to_excel(excel_writer=writer, sheet_name='Sheet1')
    writer.save()
