from ..hooks import hook
import os
import json

@hook()
async def add_instructions(context=None):
    try:
        with open('data/img_tags.txt') as f:
            img_tags = f.read().splitlines()
        # convert to comma separated string
        img_tags = ', '.join(img_tags)

        return f"## Tags for Image Descriptions\n\nWhen describing an image, select from the following tags:\n\n{img_tags}.\n\nRemember: always use underscores instead of spaces! If you need to describe something not found in the tag list, you can just use common phrases."
    except Exception as e:
        print("img_tags.txt not found in data/")
    return ""
