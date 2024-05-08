import torch
import sys
import asyncio
from diffusers import StableDiffusionXLPipeline, StableDiffusionPipeline
from nanoid import generate
import os

if os.environ.get('AH_DEFAULT_SD_MODEL'):
    current_model = os.environ.get('AH_DEFAULT_SD_MODEL')
    local_model = True
else:
    current_model = 'manpreets7/dreamshaper-3.2'
    local_model = False

def random_img_fname():
    return generate() + ".png"

def use_model(model_id, local=True):
    global current_model
    global local_model
    current_model = model_id
    local_model = local

async def sdxl_text_to_image(prompt, negative_prompt='', model_id=None, from_huggingface=None,
                             count=1, save_to="imgs/" + random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    if model_id is None:
        model_id = current_model
 
    if from_huggingface is None:
        from_huggingface = local_model

    if not from_huggingface:
        pipeline = StableDiffusionXLPipeline.from_single_file(model_id, torch_dtype=torch.float16)
    else:
        pipeline = StableDiffusionXLPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
 
    pipeline = pipeline.to("cuda")
    pipeline.safety_checker = lambda images, **kwargs: (images, [False])

    for n in range(1, count+1):
        image = pipeline(prompt=prompt, negative_prompt=negative_prompt,
                         num_inference_steps=steps, guidance_scale=cfg).images[0]
        fname = "imgs/"+random_img_fname()
        image.save(fname)
        return fname

async def sd_text_to_image(prompt, negative_prompt='', model_id=None, from_huggingface=None, count=1,
                           save_to="imgs/" + random_img_fname(), w=512, h=512, steps=20, cfg=8):
    if model_id is None:
        model_id = current_model

    if from_huggingface is None:
        from_huggingface = local_model


    if not from_huggingface:
        pipeline = StableDiffusionPipeline.from_single_file(model_id, torch_dtype=torch.float16)
    else:
        pipeline = StableDiffusionPipeline.from_pretrained(model_id,torch_dtype=torch.float16 )
    pipeline = pipeline.to("cuda")
    pipeline.safety_checker = lambda images, **kwargs: (images, [False])

    for n in range(1, count+1):
        image = pipeline(prompt=prompt, negative_prompt=negative_prompt, 
                         num_inference_steps=steps, guidance_scale=cfg).images[0]
        fname = "imgs/"+random_img_fname() 
        image.save(fname)
        return fname

async def simple_image(prompt):
    fname = await sd_text_to_image(prompt)
    return f"""<img src="{fname}" />"""

if __name__ == "__main__":
    prompt = sys.argv[1]
    negative_prompt = sys.argv[2]
    sdxl_text_to_image("models/model.safetensors", prompt, negative_prompt, count=4, cfg=30)
    asyncio.run(sd_text_to_image(prompt, negative_prompt, count=1, cfg=30))



