import asyncio
import aiohttp
import os
import runpod
from runpod import AsyncioEndpoint, AsyncioJob

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # For Windows users.


runpod.api_key = os.getenv("RUNPOD_API_KEY")


async def main(input):
    async with aiohttp.ClientSession() as session:
        endpoint = AsyncioEndpoint("YOUR_ENDPOINT_ID", session)
        job: AsyncioJob = await endpoint.run(input)

        # Polling job status
        while True:
            status = await job.status()
            print(f"Current job status: {status}")
            if status == "COMPLETED":
                output = await job.output()
                # convert from base64 encoded DataURL to image binary and save png
                #
                # TODO
                

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
        "prompt": "a beautiful young blonde woman",
        "num_inference_steps": 25,
        "refiner_inference_steps": 50,
        "width": 1024,
        "height": 1024,
        "guidance_scale": 7.5,
        "strength": 0.3,
        "seed": null,
        "num_images": 1
    }                                           } 
    asyncio.run(main(input))

