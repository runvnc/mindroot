import asyncio
import aiohttp
import os
import runpod
from runpod import AsyncioEndpoint, AsyncioJob
from nanoid import generate
import ..registry 

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # For Windows users.

runpod.api_key = os.getenv("RUNPOD_API_KEY")

def random_img_fname():
    return generate() + ".png"

def get_endpoint(model_id):
    models = registry.get_models(provider='ah', type='sd')
    return models[model_id]['meta']['endpoint_id']


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

@service(is_local=False)
async def text_to_image(prompt, negative_prompt='', model_id=None, from_huggingface=None,
                        count=1, context=None, save_to="imgs/" + random_img_fname(), w=896, h=1152, steps=20, cfg=8):
    uncensored = False
    if context is not None and 'uncensored' in context:
        uncensored = context['uncensored']

    models = registry.get_models(type='sd', provider='AH Runpod', model_id=model_id, uncensored=uncensored)
    model = models[0]

    endpoint_id = model['meta']['endpoint_id']

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

    async for n in range(1, count+1):
        image = send_job(input, endpoint_id)
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
    fname = await context.text_to_image(prompt)
    print("image output to file", fname)
    print("context = ", context)
    await context.insert_image(fname)


