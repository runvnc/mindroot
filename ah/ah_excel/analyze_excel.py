from openpyxl.styles import Font, Alignment, Border, Fill
from openpyxl.utils import get_column_letter, column_index_from_string
from collections import defaultdict
import traceback

def analyze_structure(ws):
    """Analyze the structure of the given worksheet."""
    try:
        structure = {
            "headers": [],
            "data_ranges": [],
            "empty_columns": [],
            "empty_rows": [],
            "merged_cells": [],
            "info_boxes": [],
            "text_cells": [],
            "numeric_cells": [],
        }

        # Helper function to check if a cell is likely a header
        def is_header(cell):
            return (
                cell.font.bold or
                cell.alignment.horizontal == 'center' or
                cell.fill.start_color.index != '00000000' or  # Has fill color
                any(cell.coordinate in merged_range for merged_range in ws.merged_cells.ranges)
            )

        # Analyze cells
        for row in range(1, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                if cell.value is not None:
                    if is_header(cell):
                        structure["headers"].append({
                            "cell": cell.coordinate,
                            "value": str(cell.value)
                        })
                    elif isinstance(cell.value, (int, float)):
                        structure["numeric_cells"].append(cell.coordinate)
                    else:
                        structure["text_cells"].append(cell.coordinate)

        # Analyze data ranges and empty columns/rows
        data_ranges = defaultdict(lambda: {"start": None, "end": None})
        for col in range(1, ws.max_column + 1):
            col_letter = get_column_letter(col)
            data_found = False
            for row in range(1, ws.max_row + 1):
                if ws.cell(row=row, column=col).value is not None:
                    data_found = True
                    if data_ranges[col_letter]["start"] is None:
                        data_ranges[col_letter]["start"] = row
                    data_ranges[col_letter]["end"] = row
            
            if not data_found:
                structure["empty_columns"].append(col_letter)
            elif data_ranges[col_letter]["start"] is not None:
                structure["data_ranges"].append(f"{col_letter}{data_ranges[col_letter]['start']}:{col_letter}{data_ranges[col_letter]['end']}")

        # Detect empty rows
        for row in range(1, ws.max_row + 1):
            if all(ws.cell(row=row, column=col).value is None for col in range(1, ws.max_column + 1)):
                structure["empty_rows"].append(row)

        # Detect merged cells
        structure["merged_cells"] = [str(merged_cell) for merged_cell in ws.merged_cells.ranges]

        # Identify info boxes based on borders and patterns
        current_box = None
        for row in range(1, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                if cell.border.left.style or cell.border.top.style:
                    if current_box is None:
                        current_box = {"start": cell.coordinate, "end": cell.coordinate}
                elif current_box is not None:
                    current_box["end"] = ws.cell(row=row-1, column=col-1).coordinate
                    structure["info_boxes"].append(f"{current_box['start']}:{current_box['end']}")
                    current_box = None

        return structure
    except Exception as e:
        # print full stack trace
        traceback.print_exc()
        return {"error": str(e)}

