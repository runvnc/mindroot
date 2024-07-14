import uno
import os
from com.sun.star.beans import PropertyValue
from pdf2image import convert_from_path
import tempfile

def excel_to_png(excel_file_path, sheet_name, output_png_path):
    try:
        # Connect to the running LibreOffice instance
        local_context = uno.getComponentContext()
        resolver = local_context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_context)
        context = resolver.resolve(
            "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
        desktop = context.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", context)

        # Open the Excel file
        url = uno.fileUrlToSystemPath(os.path.abspath(excel_file_path))
        doc = desktop.loadComponentFromURL(url, "_blank", 0, ())

        # Select the specific sheet
        sheet = doc.Sheets.getByName(sheet_name)
        
        # Set the sheet as active
        doc.getCurrentController().setActiveSheet(sheet)

        # Export to PDF (temporary file)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name
        
        output_url = uno.fileUrlToSystemPath(os.path.abspath(tmp_pdf_path))
        export_props = (
            PropertyValue("FilterName", 0, "calc_pdf_Export", 0),
            PropertyValue("PageRange", 0, "", 0),
        )
        doc.storeToURL(output_url, export_props)

        # Close the document
        doc.close(True)

        # Convert PDF to PNG
        images = convert_from_path(tmp_pdf_path)
        if images:
            images[0].save(output_png_path, 'PNG')
            print(f"Successfully exported {sheet_name} to {output_png_path}")
        else:
            print("Failed to convert PDF to PNG")

        # Remove temporary PDF file
        os.unlink(tmp_pdf_path)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the document is closed even if an error occurs
        if 'doc' in locals():
            doc.close(True)

# Example usage:
# excel_to_png('/path/to/your/excel_file.xlsx', 'Sheet1', '/path/to/output.png')
