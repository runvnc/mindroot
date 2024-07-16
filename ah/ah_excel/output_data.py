import openpyxl
from openpyxl.utils import get_column_letter
from typing import List, Union

def excel_to_nested_lists(file_path: str, sheet_name: str, arrangement: str = 'row') -> List[List[Union[str, None, int, float]]]:
    if arrangement not in ['row', 'column']:
        raise ValueError("Arrangement must be either 'row' or 'column'")

    wb = openpyxl.load_workbook(file_path, data_only=False)
    wb_values = openpyxl.load_workbook(file_path, data_only=True)
    
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet_name}' not found in the workbook.")
    
    ws = wb[sheet_name]
    ws_values = wb_values[sheet_name]
    
    max_row = ws.max_row
    max_col = ws.max_column
    
    if arrangement == 'row':
        result = [[] for _ in range(max_row)]
        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                cell = ws.cell(row=row, column=col)
                cell_value = ws_values.cell(row=row, column=col).value
                cell_formula = cell.data_type == 'f' and cell.value or ''
                cell_ref = f"{get_column_letter(col)}{row}"
                result[row-1].append([cell_ref, cell_value, cell_formula])
    else:  # column-based arrangement
        result = [[] for _ in range(max_col)]
        for col in range(1, max_col + 1):
            for row in range(1, max_row + 1):
                cell = ws.cell(row=row, column=col)
                cell_value = ws_values.cell(row=row, column=col).value
                cell_formula = cell.data_type == 'f' and cell.value or ''
                cell_ref = f"{get_column_letter(col)}{row}"
                result[col-1].append([cell_ref, cell_value, cell_formula])
    
    return result

# Usage example:
# excel_file = 'path/to/your/spreadsheet.xlsx'
# sheet_name = 'Sheet1'
# output_row_based = excel_to_nested_lists(excel_file, sheet_name, 'row')
# output_column_based = excel_to_nested_lists(excel_file, sheet_name, 'column')
# print(output_row_based)
# print(output_column_based)
