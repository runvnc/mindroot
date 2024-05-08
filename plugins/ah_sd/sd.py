import torch
import sys
from diffusers import StableDiffusionXLPipeline, StableDiffusionPipeline
from nanoid import generate

current_model = 'stabilityai/stable-diffusion-2-1'

def random_img_fname():
    return generate() + ".png"

def use_model(model_id):
    global current_model
    current_model = model_id

def sdxl_text_to_image(prompt, negative_prompt, model_id, from_huggingface=True, count=1, save_to="imgs/" + random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    if model_id is None:
        model_id = current_model
 
    if not from_huggingface:
        pipeline = StableDiffusionXLPipeline.from_single_file(model_id, torch_dtype=torch.float16)
    else:
        pipeline = StableDiffusionXLPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
 
    pipeline = pipeline.to("cuda")

    for n in range(1, count+1):
        image = pipeline(prompt=prompt, negative_prompt=negative_prompt, guidance_scale=cfg).images[0]
        image.save("imgs/"+random_img_fname())

def sd_text_to_image(prompt, negative_prompt, model_id, from_huggingface=True, count=1, save_to="imgs/" + random_img_fname(), w=512, h=512, steps=20, cfg=8):
    if model_id is None:
        model_id = current_model
    if not from_huggingface:
        pipeline = StableDiffusionPipeline.from_single_file(model_id, torch_dtype=torch.float16)
    else:
        pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipeline = pipeline.to("cuda")

    for n in range(1, count+1):
        image = pipeline(prompt=prompt, negative_prompt=negative_prompt, guidance_scale=cfg).images[0]
        image.save("imgs/"+random_img_fname())

i
if __name__ == "__main__":
    prompt = sys.argv[1]
    negative_prompt = sys.argv[2]
    sdxl_text_to_image("models/model.safetensors", prompt, negative_prompt, count=4, cfg=30)


