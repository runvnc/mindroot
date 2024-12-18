import base64
from io import BytesIO
from PIL import Image

def dataurl_to_pil(data_url):
    # Strip the data URL prefix if present
    if data_url.startswith('data:image'):
        # Get the base64 data after the comma
        base64_data = data_url.split(',')[1]
    else:
        base64_data = data_url
        
    # Decode base64 to bytes
    image_bytes = base64.b64decode(base64_data)
    
    # Create PIL Image from bytes
    image = Image.open(BytesIO(image_bytes))
    return image
