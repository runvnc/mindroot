import requests
import zipfile
import tarfile
import io
import os

def download_and_extract(url, extract_dir):
    # Download the file
    response = requests.get(url)

    # Get the file extension from the URL
    file_extension = os.path.splitext(url)[1].lower()

    # Create the directory if it doesn't exist
    os.makedirs(extract_dir, exist_ok=True)

    if file_extension == '.zip':
        # Create a BytesIO object from the response content
        zip_data = io.BytesIO(response.content)

        # Open the ZIP file
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            # Extract all the contents of the ZIP file to the specified directory
            zip_ref.extractall(extract_dir)

        print(f"ZIP file downloaded from {url} and extracted to {extract_dir} successfully.")
    elif file_extension in ['.tar', '.gz', '.tgz']:
        # Create a BytesIO object from the response content
        tar_data = io.BytesIO(response.content)

        # Open the TAR file
        with tarfile.open(fileobj=tar_data, mode='r:*') as tar_ref:
            # Extract all the contents of the TAR file to the specified directory
            tar_ref.extractall(extract_dir)

        print(f"TAR file downloaded from {url} and extracted to {extract_dir} successfully.")
    else:
        # Save the file to the specified directory
        file_name = os.path.join(extract_dir, os.path.basename(url))
        with open(file_name, 'wb') as file:
            file.write(response.content)

        print(f"File downloaded from {url} and saved to {file_name} successfully.")

# Example usage
file_url = 'https://example.com/file.zip'
extract_directory = 'path/to/extract/directory'
download_and_extract(file_url, extract_directory)
