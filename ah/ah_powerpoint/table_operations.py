from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Pt

def read_slide_table(presentation, slide_number, table_name):
    """Read a table from a specific slide and return its content in a compact JSON format."""
    slide = presentation.slides[slide_number - 1]
    table = None
    for shape in slide.shapes:
        if shape.has_table and shape.name == table_name:
            table = shape.table
            break
    
    if not table:
        raise ValueError(f"Table '{table_name}' not found on slide {slide_number}")
    
    table_data = {
        "name": table_name,
        "data": [],
        "styles": [],
        "merged_cells": []
    }
    
    style_map = {}
    style_counter = 1
    
    for row in table.rows:
        row_data = []
        for cell in row.cells:
            style_id = get_or_create_style(cell, style_map, style_counter)
            row_data.append([style_id, cell.text])
        table_data["data"].append(row_data)
    
    table_data["styles"] = list(style_map.values())
    table_data["merged_cells"] = get_merged_cells(table)
    
    return table_data

def update_slide_table(presentation, slide_number, table_name, table_data):
    """Update a table on a specific slide using the provided JSON data."""
    slide = presentation.slides[slide_number - 1]
    table = None
    for shape in slide.shapes:
        if shape.has_table and shape.name == table_name:
            table = shape.table
            break
    
    if not table:
        raise ValueError(f"Table '{table_name}' not found on slide {slide_number}")
    
    # Clear existing table content
    while len(table.rows) > 0:
        table._tbl.remove(table._tbl.tr_lst[0])
    
    # Recreate table with new data
    for row_data in table_data["data"]:
        row = table.add_row()
        for cell_data in row_data:
            cell = row.cells[len(row.cells) - 1]
            style_id, text = cell_data
            cell.text = text
            apply_style(cell, table_data["styles"][style_id - 1])
    
    # Apply merged cells
    for merge_range in table_data["merged_cells"]:
        start_row, start_col, end_row, end_col = merge_range
        table.cell(start_row, start_col).merge(table.cell(end_row, end_col))

def get_or_create_style(cell, style_map, style_counter):
    """Get an existing style ID or create a new one for the given cell."""
    style = extract_cell_style(cell)
    style_key = tuple(style.items())
    
    if style_key not in style_map:
        style_map[style_key] = {"id": style_counter, **style}
        style_counter += 1
    
    return style_map[style_key]["id"]

def extract_cell_style(cell):
    """Extract the style information from a cell."""
    paragraph = cell.text_frame.paragraphs[0]
    run = paragraph.runs[0] if paragraph.runs else None
    
    style = {
        "bg": rgb_to_hex(cell.fill.fore_color.rgb) if cell.fill.fore_color.rgb else None,
        "font": f"{run.font.name},{run.font.size.pt},{run.font.bold},{rgb_to_hex(run.font.color.rgb)}" if run else None,
        "align": paragraph.alignment.name if paragraph.alignment else None,
    }
    
    border = extract_border_style(cell)
    if border:
        style["border"] = border
    
    return {k: v for k, v in style.items() if v is not None}

def extract_border_style(cell):
    """Extract the border style from a cell."""
    borders = cell._tc.tcPr.tcBorders
    if not borders:
        return None
    
    border_sides = ["top", "right", "bottom", "left"]
    border_styles = []
    
    for side in border_sides:
        border = getattr(borders, side)
        if border and border.val:
            width = border.sz.pt if border.sz else 1
            style = border.val
            color = rgb_to_hex(border.color.rgb) if border.color and border.color.rgb else "#000000"
            border_styles.append(f"{side[0]}:{width}px {style} {color}")
    
    return "; ".join(border_styles) if border_styles else None

def apply_style(cell, style):
    """Apply the given style to a cell."""
    if "bg" in style:
        cell.fill.solid()
        cell.fill.fore_color.rgb = hex_to_rgb(style["bg"])
    
    if "font" in style:
        name, size, bold, color = style["font"].split(",")
        paragraph = cell.text_frame.paragraphs[0]
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        run.font.name = name
        run.font.size = Pt(float(size))
        run.font.bold = bold.lower() == "true"
        run.font.color.rgb = hex_to_rgb(color)
    
    if "align" in style:
        cell.text_frame.paragraphs[0].alignment = getattr(PP_ALIGN, style["align"])
    
    if "border" in style:
        apply_border_style(cell, style["border"])

def apply_border_style(cell, border_string):
    """Apply the border style to a cell."""
    borders = cell._tc.tcPr.get_or_add_tcBorders()
    for border_part in border_string.split(";"):
        side, style = border_part.strip().split(":")
        width, style, color = style.split()
        border = getattr(borders, side_map[side[0]])
        border.val = style
        border.sz = Pt(float(width[:-2]))  # Remove 'px' and convert to points
        border.color.rgb = hex_to_rgb(color)

def get_merged_cells(table):
    """Get the merged cell ranges in the table."""
    merged_cells = []
    for row_idx, row in enumerate(table.rows):
        for col_idx, cell in enumerate(row.cells):
            if cell.is_merge_origin:
                end_row = row_idx + cell.span_height - 1
                end_col = col_idx + cell.span_width - 1
                merged_cells.append([row_idx, col_idx, end_row, end_col])
    return merged_cells

def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color string."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return RGBColor(int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16))

side_map = {"t": "top", "r": "right", "b": "bottom", "l": "left"}
