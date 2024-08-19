import asyncio
import os
import fal_client
import aiohttp
from nanoid import generate
from ..registry import *
from ..services import service
from ..commands import command
from ..hooks import hook
from PIL import Image
import io
from .imagesize import get_closest_image_size

# Set up Flux API key if needed
# fal_client.api_key = os.getenv("FLUX_API_KEY")

def random_img_fname():
    return generate() + ".png"

async def generate_image(prompt, w=1024, h=1024, steps=20, cfg=8):
    try:
        image_size = get_closest_image_size(w, h)
        handler = fal_client.submit(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": image_size,
                "num_inference_steps": steps,
                "guidance_scale": cfg,
                "num_images": 1,
                #"enable_safety_checker": False,
                "safety_tolerance": "6"
            },
        )
        print(f"Sending request to Flux AI with image size: {image_size}")
        result = await asyncio.to_thread(handler.get)
        return result
    except Exception as e:
        print(f"Error in generate_image: {e}")
        return None

@service()
async def select_image_model(context=None, model_id=None, local=False, uncensored=False):
    # Hardcoded model selection
    #return {
    #    'id': 'flux-dev',
    #    'name': 'Flux Dev',
    #    'provider': 'Flux AI',
    #    'endpoint_id': 'fal-ai/flux/dev'
    #}
    return {
        'id': 'flux-pro',
        'name': 'Flux Pro',
        'provider': 'Flux AI',
        'endpoint_id':  "fal-ai/flux-pro",
    }

@service()
async def text_to_image(prompt, model_id=None, from_huggingface=None,
                        count=1, context=None, save_to="imgs/" + random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    print("text_to_image: Generating image with Flux AI")
    try:
        model = await select_image_model(context)
        print(f"Using model: {model['name']}")
        
        for n in range(1, count+1):
            result = await generate_image(prompt, w, h, steps, cfg)
            if result and 'images' in result and result['images']:
                image_url = result['images'][0]['url']
                # Download and save the image
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            image = Image.open(io.BytesIO(image_data))
                            fname = f"imgs/{random_img_fname()}"
                            image.save(fname)
                            print(f"Image saved to {fname}")
                            return fname
            else:
                print("No image generated or error in result")
        return None
    except Exception as e:
        print(f"Error in text_to_image: {e}")
        return None

@command()
async def image(description="", context=None, w=1024, h=1024, steps=20, cfg=8):
    """image: Generate an image from a prompt

    # Example:

    [
      { "image": {"description": "A cute tabby cat in the forest"} },
      { "image": {"description": "A happy golden retriever in the park", "w": 800, "h": 600} }
    ]

    # Example:

    [
      { "image": {"description": "A christmas gift wrapped in a red bow.", "steps": 30, "cfg": 7.5} }
    ]

    """
    prompt = description
    print(f"Generating image for prompt: {prompt}")
    fname = await text_to_image(prompt, context=context, w=w, h=h, steps=steps, cfg=cfg)
    if fname:
        print(f"Image output to file: {fname}")
        await context.insert_image("/" + fname)
    else:
        print("Failed to generate image")

if __name__ == "__main__":
    print("Testing image generation")
    asyncio.run(text_to_image("A cute tabby cat in the forest", count=1))
    print("Done testing image generation")
