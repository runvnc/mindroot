import asyncio
import aiohttp
import os
import sys
import runpod
from runpod import AsyncioEndpoint, AsyncioJob
from nanoid import generate
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


async def select_image_model(context=None, model_id=None, local=False, uncensored=False):
    models = await select_models(service_or_command='image', provider='AH Runpod', local=False, model_id=model_id, uncensored=context.uncensored)
    return models[0]

async def text_to_image(prompt, negative_prompt='', model_id=None, from_huggingface=None,
                        count=1, context=None, save_to="imgs/" + random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    endpoint_id = '2g6ce3653k22ek'
    
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

    for n in range(1, count+1):
        print(input)
        image = await send_job(input, endpoint_id)
        fname = "imgs/"+random_img_fname()
        image.save(fname)
        print(fname)


if __name__ == "__main__":
    print("Testing image generation")
    prompt = sys.argv[1] if len(sys.argv) > 1 else "A cute tabby cat in the forest"
    negative_prompt = sys.argv[2] if len(sys.argv) > 2 else "scary"
    asyncio.run(text_to_image(prompt, negative_prompt=negative_prompt, cfg=13.5, steps=30, count=8))


    print("Done testing image generation")
