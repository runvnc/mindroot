import os
import shutil
from datetime import datetime

BACKUP_DIR = '.backup'

def backup_file(file_path):
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")
    
    timestamp = datetime.now().strftime('%m_%d_%H_%M_%S')
    file_name = os.path.basename(file_path)
    backup_file_name = f"{file_name}.{timestamp}"
    backup_file_path = os.path.join(BACKUP_DIR, backup_file_name)
    
    shutil.copy2(file_path, backup_file_path)
    print(f"Backup created: {backup_file_path}")


def restore_file(file_path, timestamp):
    file_name = os.path.basename(file_path)
    backup_file_name = f"{file_name}.{timestamp}"
    backup_file_path = os.path.join(BACKUP_DIR, backup_file_name)
    
    if not os.path.isfile(backup_file_path):
        raise FileNotFoundError(f"Backup {backup_file_path} does not exist.")
    
    shutil.copy2(backup_file_path, file_path)
    print(f"File restored from backup: {backup_file_path}")

