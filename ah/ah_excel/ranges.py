import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

def list_ranges(filename, sheet=None):
    """
    Returns list of named ranges that are globally defined or sheet-specific.
    These are names that represent either a cell or range of cells.

    :param filename: Path to the Excel file
    :param sheet: Sheet name (optional). If provided, returns sheet-specific ranges
    :return: List of range names
    """
    try:
        workbook = openpyxl.load_workbook(filename, read_only=True, data_only=True)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filename}")
    except InvalidFileException:
        raise ValueError(f"Invalid Excel file: {filename}")

    if sheet:
        if sheet not in workbook.sheetnames:
            raise ValueError(f"Sheet '{sheet}' not found in the workbook")
        return [name for name, range_obj in workbook.defined_names.items() if range_obj.localSheetId == workbook.sheetnames.index(sheet)]
    else:
        return [name for name, range_obj in workbook.defined_names.items() if range_obj.localSheetId is None]

def is_merged_cell(cell, merged_ranges):
    for merged_range in merged_ranges:
        if cell.coordinate in merged_range:
            return True, str(merged_range)
    return False, None

def read_ranges(filename, range_list):
    """
    Reads data from specified ranges in the Excel file.

    :param filename: Path to the Excel file
    :param range_list: List of range names to read
    :return: Dictionary with range names as keys and data as values
    """
    try:
        workbook = openpyxl.load_workbook(filename, read_only=False, data_only=False)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filename}")
    except InvalidFileException:
        raise ValueError(f"Invalid Excel file: {filename}")

    result = {}
    for range_name in range_list:
        if range_name in workbook.defined_names:
            try:
                range_string = workbook.defined_names[range_name].attr_text
                print(f"Range string for {range_name}: {range_string}")
                
                # Handle invalid references
                if '#REF!' in range_string:
                    print(f"Warning: Invalid reference in range '{range_name}'")
                    result[range_name] = None
                    continue
                
                # Parse the range string
                if '!' in range_string:
                    sheet_name, cell_range = range_string.rsplit('!', 1)
                    sheet_name = sheet_name.strip("'")
                    if sheet_name.startswith('[') and sheet_name.endswith(']'):
                        sheet_name = sheet_name[1:-1]
                else:
                    sheet_name = workbook.active.title
                    cell_range = range_string

                if sheet_name in workbook.sheetnames:
                    ws = workbook[sheet_name]
                    merged_ranges = ws.merged_cells.ranges
                    cells = ws[cell_range]
                    
                    if isinstance(cells, (openpyxl.cell.read_only.ReadOnlyCell, openpyxl.cell.cell.Cell)):
                        merged, merge_range = is_merged_cell(cells, merged_ranges)
                        result[range_name] = [{
                            'address': cells.coordinate,
                            'value': None if cells.value == '#DIV/0!' else cells.value,
                            'merged': merged,
                            'merge_range': merge_range
                        }]
                    else:
                        result[range_name] = []
                        for row in cells:
                            row_data = []
                            for cell in row:
                                merged, merge_range = is_merged_cell(cell, merged_ranges)
                                row_data.append({
                                    'address': cell.coordinate,
                                    'value': None if cell.value == '#DIV/0!' else cell.value,
                                    'merged': merged,
                                    'merge_range': merge_range
                                })
                            result[range_name].append(row_data)
                else:
                    print(f"Warning: Sheet '{sheet_name}' not found for range '{range_name}'")
                    result[range_name] = None
            except Exception as e:
                print(f"Error processing range '{range_name}': {str(e)}")
                result[range_name] = None
        else:
            result[range_name] = None  # Range not found

    return result

def write_range(filename, range_name, values):
    """
    Writes values to a specified range in the Excel file.
    Range name must be absolute including the worksheet name.

    :param filename: Path to the Excel file
    :param range_name: Name of the range to write to
    :param values: List of lists in row-by-row grid, may include values or formulas
    :return: Boolean indicating success
    """
    try:
        workbook = openpyxl.load_workbook(filename)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filename}")
    except InvalidFileException:
        raise ValueError(f"Invalid Excel file: {filename}")

    if range_name not in workbook.defined_names:
        raise ValueError(f"Range '{range_name}' not found in the workbook")

    dests = workbook.defined_names[range_name].destinations
    for sheet, coord in dests:
        ws = workbook[sheet]
        cells = ws[coord]

        if isinstance(cells, openpyxl.cell.cell.Cell):
            if not isinstance(values, list) or len(values) != 1 or len(values[0]) != 1:
                raise ValueError("Input values do not match the range size (single cell)")
            cells.value = values[0][0]
        else:
            if len(values) != len(cells) or any(len(row) != len(cells[0]) for row in values):
                raise ValueError("Input values do not match the range size")
            for i, row in enumerate(cells):
                for j, cell in enumerate(row):
                    cell.value = values[i][j]

    try:
        workbook.save(filename)
        return True
    except PermissionError:
        raise PermissionError(f"Unable to save the file. It might be open in another application.")
    except Exception as e:
        raise Exception(f"An error occurred while saving the file: {str(e)}")

# Example usage:
if __name__ == "__main__":
    filename = "valuation.xlsx"
    print("Global ranges:", list_ranges(filename))

    # print out values in all global ranges
    #for name in list_ranges(filename):
    #    print(f"Reading '{name}':", read_ranges(filename, [name]))

    print("Reading 'ExpensesBox':", read_ranges(filename, ["ExpensesBox"]))
    #print("Writing to 'NamedRange2':", write_range(filename, "NamedRange2", [['=10*20']]))
