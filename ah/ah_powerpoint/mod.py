from ..commands import command
from pptx import Presentation, parts
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches
import json
from .read_slide import read_slide_content as new_read_slide_content
from .replace_all import slide_replace_all as new_slide_replace_all
from .slide_content_updater import update_slide_content as new_update_slide_content
from .pptx_stateless_editor import presentation_manager, extract_slide_xml, update_slide_xml, clear_slide, append_to_slide

@command()
async def slide_replace_all(context, filename, slide, replacements=None, case_sensitive=True, whole_word=False):
    """Replace all occurrences of specified strings on the presentation slide.

    Parameters:
        filename: string
        slide (int): slide number to update
        replacements: 

    Examples:
    1. Simple text replacement:
    { "slide_replace_all": { "filename": "example.pptx", "slide": 1, "replacements": [{"match": "old text", "replace": "new text"}], "case_sensitive": true, "whole_word": false } }
    
    2. Multiple replacements including percentages:
    { "slide_replace_all": { "filename": "example.pptx", "slide": 3, "replacements": [
        {"match": "total: 5%", "replace": "total: 10%"},
        {"match": "revenue", "replace": "income"}
      ], 
      "case_sensitive": false, 
      "whole_word": true 
    } }
    
    3. Using regex:
    { "slide_replace_all": { "filename": "example.pptx", "replacements": [
        {"match": "total: \d+%", "replace": "total: 15%", "is_regex": true},
        {"match": "Q[1-4]", "replace": "Quarter ", "is_regex": true}
      ], 
      "case_sensitive": true
    } }
    """
    if replacements is None:
        return "No replacements provided"

    try:
        prs = Presentation(filename)
        total_replacements = new_slide_replace_all(prs, replacements, case_sensitive, whole_word)
        prs.save(filename)
        return f"Completed {total_replacements} replacements across the presentation and saved to {filename}."
    except Exception as e:
        return f"Error during replacement: {str(e)}"

@command()
async def replace_image(context, filename, slide, name=None, replace_with_image_fname=None):
    """Replace an image in the presentation based on name.
    
    Example:
    { "replace_image": { "filename": "presentation.pptx", "name": "Picture 1", "replace_with_image_fname": "/absolute/path/to/new_logo.png" } }
    """
    if name is None or replace_with_image_fname is None:
        return "Both name and replace_with_image_fname must be provided"

    try:
        prs = Presentation(filename)
        replacements_count = 0

        slide = prs.slides[slide - 1]
        for shape in slide.shapes:
            if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                if shape.name == original_image_fname:
                    im = parts.image.Image.from_file(replace_with_image_fname)

                    slide_part, rId = shape.part, shape._element.blip_rId
                    image_part = slide_part.related_part(rId)
                    image_part.blob = im._blob

                    replacements_count += 1

        prs.save(filename)
        return f"Replaced {replacements_count} instance(s) of {name} with {replace_with_image_fname} in {filename}"
    except Exception as e:
        return f"Error replacing image: {str(e)}"

@command()
async def read_slide_content(context, filename, slide_number):
    """Read and return the content of a slide.
    Example:
    { "read_slide_content": { "filename": "presentation.pptx", "slide_number": 1 } }
    """
    try:
        prs = Presentation(filename)
        content = new_read_slide_content(prs, slide_number)
        return json.dumps(content)
    except Exception as e:
        return json.dumps({"error": str(e)})

@command()
async def update_slide_content(context, filename, slide_number, content):
    """Update a slide with content.
    For lists of text in groups or text that can be updated with search and replace, use
    slide_replace_all instead. Text frame updates can be string or list of strings.
    
    For tables, the number of rows in the provided data must match the existing table.
    Example:
    { "update_slide_content": { "filename": "presentation.pptx", "slide_number": 1, "content": {"title": "New Title", "subtitle": "New Subtitle", "Table 2": [["Header 1", "Header 2"], ["Row 1 Col 1", "Row 1 Col 2"]]} } }
    """
    try:
        return new_update_slide_content(context, filename, slide_number, content)
    except Exception as e:
        return f"Error updating slide content: {str(e)}"

@command()
async def create_chart(context, filename, slide_number, chart_type, data, position):
    """Create a chart on the specified slide.
    Example:
    { "create_chart": { "filename": "presentation.pptx", "slide_number": 1, "chart_type": "BAR_CLUSTERED", "data": {"categories": ["A", "B", "C"], "values": [1, 2, 3]}, "position": {"left": 1, "top": 2, "width": 8, "height": 5} } }
    """
    try:
        prs = Presentation(filename)
        slide = prs.slides[slide_number - 1]
        chart_data = CategoryChartData()
        chart_data.categories = data['categories']
        chart_data.add_series('Series 1', data['values'])
        x, y, cx, cy = [Inches(position[key]) for key in ['left', 'top', 'width', 'height']]
        chart = slide.shapes.add_chart(
            getattr(XL_CHART_TYPE, chart_type), x, y, cx, cy, chart_data
        ).chart
        prs.save(filename)
        return f"Created {chart_type} chart on slide {slide_number} in {filename}"
    except Exception as e:
        return f"Error creating chart: {str(e)}"

@command()
async def open_presentation_for_xml_edit(context, filename):
    """Open a presentation for XML editing.
    Example:
    { "open_presentation_for_xml_edit": { "filename": "example.pptx" } }
    """
    try:
        result = presentation_manager.open_presentation(filename)
        return f"Presentation {filename} opened for XML editing" if result else "Failed to open presentation"
    except Exception as e:
        return f"Error opening presentation: {str(e)}"

@command()
async def close_presentation_after_xml_edit(context, filename):
    """Close a presentation after XML editing.
    Example:
    { "close_presentation_after_xml_edit": { "filename": "example.pptx" } }
    """
    try:
        result = presentation_manager.close_presentation(filename)
        return f"Presentation {filename} closed after XML editing" if result else "Failed to close presentation"
    except Exception as e:
        return f"Error closing presentation: {str(e)}"

@command()
async def extract_slide_xml_content(context, filename, slide_number):
    """Extract XML content from a slide.
    Example:
    { "extract_slide_xml_content": { "filename": "example.pptx", "slide_number": 1 } }
    """
    try:
        xml_content = extract_slide_xml(filename, slide_number)
        return xml_content
    except Exception as e:
        return f"Error extracting slide XML: {str(e)}"

@command()
async def update_slide_xml_content(context, filename, slide_number, new_xml):
    """Update XML content of a slide.
    Example:
    { "update_slide_xml_content": { "filename": "example.pptx", "slide_number": 1, "new_xml": "<p:sld>...</p:sld>" } }
    """
    try:
        result = update_slide_xml(filename, slide_number, new_xml)
        return f"Updated XML content for slide {slide_number} in {filename}" if result else "Failed to update slide XML"
    except Exception as e:
        return f"Error updating slide XML: {str(e)}"

@command()
async def append_to_slide_xml_content(context, filename, slide_number, xml_fragment):
    """Append XML fragment to a slide's content.
    Example:
    { "append_to_slide_xml_content": { "filename": "example.pptx", "slide_number": 1, "xml_fragment": "<p:sp>...</p:sp>" } }
    """
    try:
        result = append_to_slide(filename, slide_number, xml_fragment)
        return f"Appended XML fragment to slide {slide_number} in {filename}" if result else "Failed to append to slide XML"
    except Exception as e:
        return f"Error appending to slide XML: {str(e)}"

@command()
async def clear_slide_xml_content(context, filename, slide_number):
    """Clear all XML content from a slide.
    Example:
    { "clear_slide_xml_content": { "filename": "example.pptx", "slide_number": 1 } }
    """
    try:
        result = clear_slide(filename, slide_number)
        return f"Cleared XML content from slide {slide_number} in {filename}" if result else "Failed to clear slide XML"
    except Exception as e:
        return f"Error clearing slide XML: {str(e)}"

@command()
async def save_presentation_after_xml_edit(context, filename):
    """Save the presentation after XML editing.
    Example:
    { "save_presentation_after_xml_edit": { "filename": "example.pptx" } }
    """
    try:
        result = presentation_manager.save_presentation(filename)
        return f"Saved presentation {filename} after XML editing" if result else "Failed to save presentation"
    except Exception as e:
        return f"Error saving presentation: {str(e)}"
