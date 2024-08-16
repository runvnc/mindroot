import openpyxl
from openpyxl.worksheet.properties import WorksheetProperties, PageSetupProperties
import subprocess
import os
import traceback
import sys

def format_excel(input_file):
    try:
        wb = openpyxl.load_workbook(input_file)
        for sheet in wb.worksheets:
            # Set to Landscape
            sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE
            # Turn on column and row headers
            sheet.print_options.headings = True
            # Set scaling mode to Fit
            if sheet.sheet_properties is None:
                sheet.sheet_properties = WorksheetProperties()
            if sheet.sheet_properties.pageSetUpPr is None:
                sheet.sheet_properties.pageSetUpPr = PageSetupProperties()
            #sheet.sheet_properties.pageSetUpPr.fitToPage = True
            #sheet.page_setup.fitToHeight = 1
            sheet.page_setup.fitToWidth = 1
        wb.save(input_file)
        print(f'Excel file {input_file} formatted successfully')
    except Exception as e:
        print(f'Error in format_excel: {str(e)}')
        print(traceback.format_exc())
        raise

def excel_to_pdf(input_file, output_pdf):
    try:
        cmd = ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', '.', input_file]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        os.rename(f'{os.path.splitext(input_file)[0]}.pdf', output_pdf)
        print(f'PDF created: {output_pdf}')
    except subprocess.CalledProcessError as e:
        print(f'Error in excel_to_pdf: {str(e)}')
        print(f'Command output: {e.output}')
        raise
    except Exception as e:
        print(f'Error in excel_to_pdf: {str(e)}')
        print(traceback.format_exc())
        raise

def pdf_to_pngs(input_pdf, output_prefix):
    try:
        cmd = ['pdftocairo', '-png', '-r', '300', input_pdf, output_prefix]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f'PNG images created with prefix: {output_prefix}')
    except subprocess.CalledProcessError as e:
        print(f'Error in pdf_to_pngs: {str(e)}')
        print(f'Command output: {e.output}')
        raise
    except Exception as e:
        print(f'Error in pdf_to_pngs: {str(e)}')
        print(traceback.format_exc())
        raise

def main():
    try:
        if len(sys.argv) != 3:
            print('Usage: xlsx_to_pngs.py <input_file> <output_pdf>')
            sys.exit(1)
        input_file = sys.argv[1]
        output_pdf = sys.argv[2]
        output_prefix = 'page'

        format_excel(input_file)
        excel_to_pdf(input_file, output_pdf)
        pdf_to_pngs(output_pdf, output_prefix)
    except Exception as e:
        print(f'Error in main: {str(e)}')
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
