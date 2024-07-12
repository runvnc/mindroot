from ..commands import command
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt
import json
import io
import re

# Module-level cache for the presentation
_presentation_cache = None

def _get_presentation():
    global _presentation_cache
    if _presentation_cache is None:
        raise ValueError("No presentation is currently cached. Use open_presentation first.")
    return Presentation(io.BytesIO(_presentation_cache))

def _save_presentation_cache(prs):
    global _presentation_cache
    buffer = io.BytesIO()
    prs.save(buffer)
    _presentation_cache = buffer.getvalue()

@command()
async def open_presentation(filename, context=None):
    """Open a PowerPoint presentation and cache it in memory.
    Example:
    { "open_presentation": { "filename": "example.pptx" } }
    """
    prs = Presentation(filename)
    _save_presentation_cache(prs)
    context.data['current_presentation'] = filename
    slides_info = [{'number': i+1, 'layout': slide.slide_layout.name} for i, slide in enumerate(prs.slides)]
    return f"Opened and cached presentation {filename}. Slides: {json.dumps(slides_info)}"

@command()
async def save_presentation(filename=None, context=None):
    """Save the presentation to disk, optionally with a new filename.
    Example:
    { "save_presentation": { "filename": "updated_presentation.pptx" } }
    """
    prs = _get_presentation()
    if filename is None:
        filename = context.data['current_presentation']
    prs.save(filename)
    context.data['current_presentation'] = filename
    return f"Saved presentation as {filename}"

@command()
async def replace_all(replacements=None, case_sensitive=True, whole_word=False, context=None):
    """Replace all occurrences of specified strings in the presentation.
    
    Examples:
    1. Simple text replacement:
    { "replace_all": { "replacements": [{"match": "old text", "replace": "new text"}], "case_sensitive": true, "whole_word": false } }
    
    2. Multiple replacements including percentages:
    { "replace_all": { "replacements": [
        {"match": "total: 5%", "replace": "total: 10%"},
        {"match": "revenue", "replace": "income"}
      ], 
      "case_sensitive": false, 
      "whole_word": true 
    } }
    
    3. Using regex (new feature):
    { "replace_all": { "replacements": [
        {"match": "total: \d+%", "replace": "total: 15%", "is_regex": true},
        {"match": "Q[1-4]", "replace": "Quarter ", "is_regex": true}
      ], 
      "case_sensitive": true
    } }
    """
    if replacements is None:
        return "No replacements provided"

    prs = _get_presentation()
    total_replacements = 0

    # Compile regex patterns for each replacement
    patterns = []
    for rep in replacements:
        if rep.get('is_regex', False):
            pattern = rep['match']
        else:
            pattern = re.escape(rep['match'])
        
        if whole_word and not rep.get('is_regex', False):
            pattern = r'\b' + pattern + r'\b'
        
        flags = 0 if case_sensitive else re.IGNORECASE
        patterns.append((re.compile(pattern, flags), rep['replace']))

    def replace_text(text):
        nonlocal total_replacements
        for pattern, replacement in patterns:
            new_text, count = pattern.subn(replacement, text)
            total_replacements += count
            text = new_text
        return text

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.text = replace_text(run.text)
            elif shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        for paragraph in cell.text_frame.paragraphs:
                            for run in paragraph.runs:
                                run.text = replace_text(run.text)
            #elif shape.has_chart:
            #    if shape.chart.has_title:
            #        shape.chart.chart_title.text_frame.text = replace_text(shape.chart.chart_title.text_frame.text)
            #    for series in shape.chart.series:
            #        series.name = replace_text(series.name)
            #    for category in shape.chart.categories:
            #        category.label = replace_text(category.label)

    _save_presentation_cache(prs)
    return f"Completed {total_replacements} replacements across the presentation."

@command()
async def replace_image(original_image_fname=None, replace_with_image_fname=None, context=None):
    """Replace an image in the presentation based on image file names.
    
    Example:
    { "replace_image": { "original_image_fname": "old_logo.png", "replace_with_image_fname": "/absolute/path/to/new_logo.png" } }
    """
    if original_image_fname is None or replace_with_image_fname is None:
        return "Both original_image_fname and replace_with_image_fname must be provided"

    prs = _get_presentation()
    replacements_count = 0

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                if shape.image.filename == original_image_fname:
                    with open(replace_with_image_fname, 'rb') as f:
                        image_bytes = f.read()
                    shape.element.blip.embed = prs.part.get_or_add_image_part(image_bytes)
                    replacements_count += 1

    _save_presentation_cache(prs)
    return f"Replaced {replacements_count} instance(s) of {original_image_fname} with {replace_with_image_fname}"


@command()
async def read_slide_content(slide_number, context=None):
    """Read and return the content of a slide.
    Example:
    { "read_slide_content": { "slide_number": 1 } }
    """
    prs = _get_presentation()
    slide = prs.slides[slide_number - 1]
    content = {}
    for shape in slide.shapes:
        if shape.has_text_frame:
            content[shape.name] = shape.text_frame.text
        elif shape.has_table:
            content[shape.name] = [[cell.text for cell in row.cells] for row in shape.table.rows]
        elif shape.has_chart:
            content[shape.name] = "Chart: " + shape.chart.chart_type
    return json.dumps(content)

@command()
async def update_slide_content(slide_number, content_json, context=None):
    """Update a slide with content provided in JSON format.
    Example:
    { "update_slide_content": { "slide_number": 1, "content_json": {"title": "New Title", "subtitle": "New Subtitle"} } }
    """
    prs = _get_presentation()
    slide = prs.slides[slide_number - 1]
    content = json.loads(content_json)
    for shape in slide.shapes:
        if shape.name in content:
            if shape.has_text_frame:
                shape.text_frame.text = content[shape.name]
            elif shape.has_table:
                if isinstance(content[shape.name], list) and all(isinstance(row, list) for row in content[shape.name]):
                    for i, row in enumerate(content[shape.name]):
                        for j, cell_content in enumerate(row):
                            if i < len(shape.table.rows) and j < len(shape.table.columns):
                                shape.table.cell(i, j).text = str(cell_content)
                else:
                    raise ValueError(f"Content for table '{shape.name}' must be a 2D list")
            elif shape.has_chart:
                if isinstance(content[shape.name], dict) and 'categories' in content[shape.name] and 'values' in content[shape.name]:
                    chart_data = CategoryChartData()
                    chart_data.categories = content[shape.name]['categories']
                    chart_data.add_series('Series 1', content[shape.name]['values'])
                    shape.chart.replace_data(chart_data)
                else:
                    raise ValueError(f"Content for chart '{shape.name}' must be a dict with 'categories' and 'values' keys")
    _save_presentation_cache(prs)
    return f"Updated content of slide {slide_number}"

@command()
async def create_chart(slide_number, chart_type, data, position, context=None):
    """Create a chart on the specified slide.
    Example:
    { "create_chart": { "slide_number": 1, "chart_type": "BAR_CLUSTERED", "data": {"categories": ["A", "B", "C"], "values": [1, 2, 3]}, "position": {"left": 1, "top": 2, "width": 8, "height": 5} } }
    """
    prs = _get_presentation()
    slide = prs.slides[slide_number - 1]
    chart_data = CategoryChartData()
    chart_data.categories = data['categories']
    chart_data.add_series('Series 1', data['values'])
    x, y, cx, cy = [Inches(position[key]) for key in ['left', 'top', 'width', 'height']]
    chart = slide.shapes.add_chart(
        getattr(XL_CHART_TYPE, chart_type), x, y, cx, cy, chart_data
    ).chart
    _save_presentation_cache(prs)
    return f"Created {chart_type} chart on slide {slide_number}"

