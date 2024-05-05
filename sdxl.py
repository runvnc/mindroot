import torch
from diffusers import StableDiffusionPipeline
from nanoid import generate
#model_id = "stabilityai/stable-diffusion-xl-base-1.0"

def random_img_fname():
    return generate() + ".png"

def sdxl_text_to_image(prompt, model_id, save_to=random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipeline = pipeline.to("cuda")

    image = pipeline(prompt).images[0]

    image.save(save_to)

if __name__ == "main":
    prompt = "a beautiful sunset over a tranquil beach, vibrant colors, detailed, artstation, 4k"
    sdxl_text_to_image(prompt,stabilityai/"stable-diffusion-xl-base-1.0")


