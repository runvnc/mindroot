import subprocess
import os

def recalculate_excel(file_path):
    libreoffice_path = '/usr/bin/libreoffice'  # Adjust this path if necessary
    temp_dir = '/tmp/libreoffice_convert'  # Temporary directory for LibreOffice
    
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    cmd = [
        libreoffice_path,
        '--headless',
        '--convert-to', 'xlsx',
        '--outdir', temp_dir,
        file_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"File recalculated: {file_path}")
        
        # Move the recalculated file back to the original location
        recalculated_file = os.path.join(temp_dir, os.path.basename(file_path))
        os.replace(recalculated_file, file_path)
    except subprocess.CalledProcessError as e:
        print(f"Error recalculating file: {e}")

# Usage example (commented out)
# recalculate_excel('path/to/your/excel_file.xlsx')
