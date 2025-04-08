from lib.providers.services import service
from lib.providers.commands import command
import os
import json
import sys
from pathlib import Path
from PIL import Image

from .init_persona import *


@service()
async def get_persona_data(persona_name, context=None):
    print("persona name is", persona_name, file=sys.stderr)
    # use pwd as base dir
    # current working dir of process 
    pwd = os.getcwd()
    persona_path = os.path.join(pwd, 'personas', 'local', persona_name)
    if not os.path.exists(persona_path):
        persona_path = os.path.join(pwd, 'personas', 'shared', persona_name)
        if not os.path.exists(persona_path):
            # need to raise an error here
            raise Exception(f"Persona {persona_name} not found in {persona_path}")

    # read the persona data
    # use blue background and yellow text
    print("\033[44m\033[33m", file=sys.stderr)
    print(f"Reading persona data from {persona_path}", file=sys.stderr)


    persona_file = os.path.join(persona_path, 'persona.json')
    if not os.path.exists(persona_file):
        return {}
    with open(persona_file, 'r') as f:
        persona_data = json.load(f)

    persona_data['avatar_image_path'] = os.path.join(persona_path, 'avatar.png')
    persona_data['face_ref_image_path'] = os.path.join(persona_path, 'faceref.png')

    if not os.path.exists(persona_data['face_ref_image_path']):
        persona_data['face_ref_image_path'] = persona_data['avatar_image_path']

    persona_data['voice_samples'] = []
    for file in os.listdir(persona_path):
        if file.endswith(".wav"):
            persona_data['voice_samples'].append(os.path.join(persona_path, file))

    print("persona data is", persona_data, file=sys.stderr)
    print("\033[0m", file=sys.stderr)
    return persona_data

@command()
async def pic_of_me(prompt="", context=None):
    """pic_of_me

    Generate a picture of the persona given a detailed description of what they
    they look like and what are doing, where they are, etc.. You will (usually) want to include
    the full text from the Appearance section of the Persona.

    The description should be very detailed and specific, and should include
    the persona's appearance such as what they are wearing, their expression, what they are doing.
    Also include details about the background or scene where they are as well as the pose they are in.
    Always use this instead of 'image' when creating an image of the persona!

    CRITICAL: include details about the image composition such as front-view, side-view, focus,
    camera settings, lighting, etc.
    CRITICAL: put the most relevant and distinguishing aspects such as pose or anything unique about this
    image up front in the description.

    Example:

    { 
    "pic_of_me": { "prompt": 
        "(in third person: image composition, taken from angle, where they are, what they are doing, details of appearance, details of scene, camera settings, etc. etc.)" } }

    """
    persona = context.agent['persona']
    print("persona:", persona)
    negative_appearance = 'split-view, diptych, side-by-side, 2girl, 2boy'
    if 'negative_appearance' in persona:
        negative_appearance = persona['negative_appearance']

    img = await context.text_to_image(f"({prompt}:1.25), " + persona['appearance'], negative_appearance, cfg=12)
    print("img = ", img)
    img_dir = os.path.dirname(persona['face_ref_image_path'])
    try:
        swapped = await context.swap_face(img_dir, img)
    except Exception as e:
        print("Error swapping face:", e)
        swapped = img
    #await context.insert_image("/"+swapped)
    print("swapped:", swapped)
    obj = { "markdown": f"![pic_of_me](/{swapped})" }
    #await context.partial_command('json_encoded_md', obj)
    await context.run_command('json_encoded_md', obj)

@command()
async def video_of_me(prompt="", context=None):
    """video_of_me
    
    Generate a video of the persona based on a detailed description. 
    This command first creates an image of the persona using the provided prompt
    and their appearance details, then converts that image into a video animation.
    
    The description should be very detailed and specific, and should include
    the persona's appearance such as what they are wearing, their expression, what they are doing.
    Also include details about the background or scene where they are as well as the pose they are in.
    Always use this instead of 'image' when creating a video of the persona!
    
    CRITICAL: include details about the image composition such as front-view, side-view, focus,
    camera settings, lighting, etc.
    CRITICAL: put the most relevant and distinguishing aspects such as pose or anything unique about this
    image up front in the description.
    CRITICAL: include movement details in the prompt to guide the video generation.
    
    Example:
    
    { 
    "video_of_me": { "prompt": 
        "(in third person: image composition, taken from angle, where they are, what they are doing, details of appearance, details of scene, camera settings, movement details, etc.)" } }
    
    """
    persona = context.agent['persona']
    print("persona:", persona)
    negative_appearance = 'split-view, diptych, side-by-side, 2girl, 2boy'
    if 'negative_appearance' in persona:
        negative_appearance = persona['negative_appearance']

    # Generate the initial image
    img = await context.text_to_image(f"({prompt}:1.25), " + persona['appearance'], negative_appearance, cfg=12)
    print("img = ", img)
    
    # Face swapping process
    img_dir = os.path.dirname(persona['face_ref_image_path'])
    try:
        swapped = await context.swap_face(img_dir, img)
    except Exception as e:
        print("Error swapping face:", e)
        swapped = img
    
    print("swapped:", swapped)
    
    # Convert image to video using the image_to_video service
    try:
        # Get the absolute path of the swapped image
        cwd = os.getcwd()
        swapped_abs_path = os.path.join(cwd, swapped)
        print("swapped_abs_path:", swapped_abs_path)
        
        # Load the image with PIL
        pil_image = Image.open(swapped_abs_path)
        print("loaded image with PIL")
        # Use the image_to_video service with the PIL image
        video = await context.image_to_video(pil_image, prompt)
        print("video:", video)
        
        # Return the video in markdown format for display
        obj = {"markdown": f"<video width='100%' controls><source src='/{video}' type='video/mp4'></video>"}
        await context.run_command('markdown_await_user', obj)
    except Exception as e:
        print("Error creating video:", e)
        # Fallback to displaying the image if video creation fails
        obj = {"markdown": f"![pic_of_me](/{swapped}) (Video generation failed)"}
        await context.run_command('markdown_await_user', obj)
