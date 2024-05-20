import asyncio
import aiohttp
import os
import runpod
from runpod import AsyncioEndpoint, AsyncioJob

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # For Windows users.


runpod.api_key = os.getenv("RUNPOD_API_KEY")


async def main(input, endpoint_id):
    async with aiohttp.ClientSession() as session:
        endpoint = AsyncioEndpoint(endpoint_id, session)
        job: AsyncioJob = await endpoint.run(input)

        # Polling job status
        while True:
            status = await job.status()
            print(f"Current job status: {status}")
            if status == "COMPLETED":
                output = await job.output()
                # Convert from base64 encoded DataURL to image binary and save png
                import base64
                from PIL import Image
                import io

                image_data = output['image_url']
                if image_data.startswith('data:image/png;base64,'):
                    image_data = image_data[len('data:image/png;base64,'):]
                elif image_data.startswith('data:image/jpeg;base64,'):
                    image_data = image_data[len('data:image/jpeg;base64,'):]

                image_bytes = base64.b64decode(image_data)

                # Convert bytes to a PIL Image
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

                # Save the image to a file
                image.save('output.png', format='PNG')
                

                print("Job output:", output)
                break  # Exit the loop once the job is completed.
            elif status in ["FAILED"]:
                print("Job failed or encountered an error.")

                break
            else:
                print("Job in queue or processing. Waiting 3 seconds...")
                await asyncio.sleep(3)  # Wait for 3 seconds before polling again


if __name__ == "__main__":
    input = {
        "prompt": "a sunset",
        "negative_prompt": "weird, ugly",
        "num_inference_steps": 13,
        "refiner_inference_steps": 50,
        "width": 896,
        "height": 1152,
        "guidance_scale": 7.5,
        "strength": 0.3,
        "seed": None,
        "num_images": 1
    }
    asyncio.run(main(input, "b6kn2n72y7aooe"))
