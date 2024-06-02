from ..services import service
from ..commands import command
import os
import json

@hook()
async def add_instructions(context=None):
    # read in tag list from data/img_tags.txt
    with open(os.path.join(os.path.dirname(__file__), 'data/img_tags.txt')) as f:
        img_tags = f.read().splitlines()
    # convert to comma separated string
    img_tags = ', '.join(img_tags)

    return f"## Tags for Image Descriptions\n\nWhen describing an image, select from the following tags:\n\n{img_tags}.\n\nIf you need to describe something not found in the tag list, you can just use common phrases."

