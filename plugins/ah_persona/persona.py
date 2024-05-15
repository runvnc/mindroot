from ..commands import command

async def get_persona_data(persona_name):
    import os
    import json
    import sys

    print("persona name is", persona_name, file=sys.stderr)

    persona_path = os.path.join('personas', 'local', persona_name)
    if not os.path.exists(persona_path):
        persona_path = os.path.join('personas', 'shared', persona_name)
        if not os.path.exists(persona_path):
            return {}
    # read the persona data
    persona_file = os.path.join(persona_path, 'persona.json')
    if not os.path.exists(persona_file):
        return {}
    with open(persona_file, 'r') as f:
        persona_data = json.load(f)

    persona_data['avatar_image_path'] = os.path.join(persona_path, 'avatar.png')
    persona_data['face_ref_image_path'] = os.path.join(persona_path, 'faceref.png')

    # if faceref image does not exist, use the avatar image
    if not os.path.exists(persona_data['face_ref_image_path']):
        persona_data['face_ref_image_path'] = persona_data['avatar_image_path']

    return persona_data


@command()
async def pic_of_me(prompt, context=None):
    """pic_of_me(prompt)

    Generate a picture of the persona given a detailed description of what they are doing.
    Always use this instead of 'image' when creating an image of the persona!

    Example:

    { "pic_of_me": "wearing a blue hat and a red shirt, playing guitar." }

    """
    persona = context.persona
    print("persona:", persona)
    img = await context.image(prompt + ',' + persona['appearance'])
    swapped = await context.face_swap(img, persona['face_ref_image_path'])
    await context.insert_image(swapped)


