import fal_client
import sys
import os
from time import sleep

# read prompt from first command line argument (if provided)
# or use default prompt
prompt = sys.argv[1] if len(sys.argv) > 1 else "A portrait of a person with a face that looks like a painting."
count = int(sys.argv[2]) if len(sys.argv) > 2 else 1

# if no seed, use random
seed = sys.argv[3] if len(sys.argv) > 3 else None


print(f"Prompt: {prompt}")
print(f"Seed: {seed}")
print(f"Count: {count}")

def generate_image(prompt):
    handler = fal_client.submit(
        #"fal-ai/flux-pro",
        "fal-ai/flux/dev",
        #"fal-ai/flux-realism",
        arguments={
            "prompt": prompt,
            "image_size": "portrait_16_9",
            "num_inference_steps": 33,
            "guidance_scale": 3.6,
            "seed": seed,
            "num_images": 1,
            "enable_safety_checker": False,
            #"safety_tolerance": "6"
        },
    )
    print("Sending request to FAL AI...")
    result = handler.get()
    return result

for i in range(0,count):
    result = generate_image(prompt)
    os.system(f"xdg-open {result['images'][0]['url']}")
    print(result)
