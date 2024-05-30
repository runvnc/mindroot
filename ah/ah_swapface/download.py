import requests
import zipfile
import tarfile
import io
import os

def download_and_extract(url, extract_dir):
    print("Downloading from:", url, "to:", extract_dir)
    response = requests.get(url)

    file_extension = os.path.splitext(url)[1].lower()

    os.makedirs(extract_dir, exist_ok=True)

    if file_extension == '.zip':
        zip_data = io.BytesIO(response.content)

        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"ZIP file downloaded from {url} and extracted to {extract_dir} successfully.")
    elif file_extension in ['.tar', '.gz', '.tgz']:
        tar_data = io.BytesIO(response.content)

        with tarfile.open(fileobj=tar_data, mode='r:*') as tar_ref:
            tar_ref.extractall(extract_dir)

        print(f"TAR file downloaded from {url} and extracted to {extract_dir} successfully.")
    else:
        file_name = os.path.join(extract_dir, os.path.basename(url).split('?')[0])
        with open(file_name, 'wb') as file:
            file.write(response.content)

        print(f"File downloaded from {url} and saved to {file_name} successfully.")

