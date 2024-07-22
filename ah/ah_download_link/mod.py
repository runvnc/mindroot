from ..services import service
from ..commands import command
import os
import uuid
import json
from datetime import datetime, timedelta

@command()
async def create_download_link(filename, expiration_time=None, context=None):
    """Create a download link for a file and send it to the chat.

    Parameters:
    filename (str): The name of the file to create a download link for.
    expiration_time (int, optional): The number of minutes until the link expires.
    context (object): The context object for the current session.

    Returns:
    str: A message indicating success or failure.
    """
    # Verify file exists
    if not os.path.exists(filename):
        return f"Error: File '{filename}' not found."

    # Generate a unique identifier for the download
    download_id = str(uuid.uuid4())

    # Create a relative URL
    download_url = f"/download/{download_id}"

    # Set expiration time
    if expiration_time:
        expiry = datetime.now() + timedelta(minutes=int(expiration_time))
        expiry_str = expiry.strftime("%Y-%m-%d %H:%M:%S")
    else:
        expiry_str = "No expiration"

    # Prepare download information
    download_info = {
        "id": download_id,
        "filename": os.path.abspath(filename),
        "expiry": expiry_str
    }

    # Ensure the directory exists
    os.makedirs(f"data/dl_links/{context.user}", exist_ok=True)

    # Store download information
    with open(f"data/dl_links/{context.user}/{download_id}", 'w') as f:
        json.dump(download_info, f)

    # Create the message with the download link
    filename_only = os.path.basename(filename)
    message = f"Download link: [**{filename_only}**]({download_url})\nExpires: {expiry_str}"

    # Send the message to the chat
    await context.agent_output("new_message", {
        "content": message,
        "agent": context.agent['name']
    })

    return "Download link created and sent to chat."
