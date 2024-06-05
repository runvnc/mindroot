import asyncio
import aiohttp
import os
import runpod
from runpod import AsyncioEndpoint, AsyncioJob
from nanoid import generate
from ..registry import *
from ..services import service
from ..commands import command
from ..hooks import hook

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # For Windows users.

runpod.api_key = os.getenv("RUNPOD_API_KEY")

def random_img_fname():
    return generate() + ".png"


async def send_job(input, endpoint_id):
    async with aiohttp.ClientSession() as session:
        endpoint = AsyncioEndpoint(endpoint_id, session)
        job: AsyncioJob = await endpoint.run(input)

        while True:
            status = await job.status()
            print(f"Current job status: {status}")
            if status == "COMPLETED":
                output = await job.output()
                import base64
                from PIL import Image
                import io

                image_data = output['image_url']
                if image_data.startswith('data:image/png;base64,'):
                    image_data = image_data[len('data:image/png;base64,'):]
                elif image_data.startswith('data:image/jpeg;base64,'):
                    image_data = image_data[len('data:image/jpeg;base64,'):]

                image_bytes = base64.b64decode(image_data)

                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                return image
                
                break
            elif status in ["FAILED"]:
                print("Job failed or encountered an error.")

                break
            else:
                print("Job in queue or processing..")
                await asyncio.sleep(1)


#@hook()
#async def add_instructions(context=None):
#    return ''
#    model = await context.select_image_model()
#    if 'tips' in model:
#        return model['tips']

@service(is_local=False)
async def select_image_model(context=None, model_id=None, local=False, uncensored=False):
    models = await select_models(service_or_command='image', provider='AH Runpod', local=False, model_id=model_id, uncensored=context.uncensored)
    return models[0]

@service(is_local=False)
async def text_to_image(prompt, negative_prompt='', model_id=None, from_huggingface=None,
                        count=1, context=None, save_to="imgs/" + random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    print("text_to_image. trying to get model")
    models = await select_models(service_or_command='text_to_image', provider='AH Runpod', local=False, model_id=model_id, uncensored=context.uncensored)
    model = models[0]
    print("model is", model)
    endpoint_id = model['endpoint_id']
    
    input = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_inference_steps": steps,
        "refiner_inference_steps": 0,
        "width": w,
        "height": h,
        "guidance_scale": cfg,
        "strength": 0.3,
        "seed": None,
        "num_images": 1
    }
    # anything defined under model['defaults'] is applied to input
    if 'defaults' in model:
        # convert property names: steps -> num_inference_steps, cfg->guidance_scale
        if 'steps' in model['defaults']:
            input['num_inference_steps'] = model['defaults']['steps']
        if 'cfg' in model['defaults']:
            input['guidance_scale'] = model['defaults']['cfg']

        if 'seed' in model['defaults']:
            input['seed'] = model['defaults']['seed']
        if 'prompt' in model['defaults']:
            input['prompt'] += ',' + model['defaults']['prompt']
        if 'negative_prompt' in model['defaults']:
            input['negative_prompt'] += ',' + model['defaults']['negative_prompt']
        if 'width' in model['defaults']:
            input['width'] = model['defaults']['width']
        if 'height' in model['defaults']:
            input['height'] = model['defaults']['height']

    for n in range(1, count+1):
        print(input)
        image = await send_job(input, endpoint_id)
        fname = "imgs/"+random_img_fname()
        image.save(fname)
        return fname


@command(is_local=False)
async def image(prompt, context=None):
    """image: Generate an image from a prompt

    # Example:

    [
      { "image": "A cute tabby cat in the forest"},
      { "image": "A happy golden retriever in the park"}
    ]

    # Example:

    [
      { "image": "A christmas gift wrapped in a red bow."}
    ]

    """
    print(prompt)
    fname = await context.text_to_image(prompt)
    print("image output to file", fname)
    print("context = ", context)
    await context.insert_image(fname)

if __name__ == "__main__":
    print("Testing image generation")
    asyncio.run(text_to_image("A cute tabby cat in the forest", count=1))
    print("Done testing image generation")
