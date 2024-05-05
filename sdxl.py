import torch
from diffusers import StableDiffusionXLPipeline
from nanoid import generate

def random_img_fname():
    return generate() + ".png"

def sdxl_text_to_image(prompt, model_id, count=1, save_to="imgs/" + random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    pipeline = StableDiffusionXLPipeline.from_single_file(model_id, torch_dtype=torch.float16)
    pipeline = pipeline.to("cuda")

    for n in range(1, count+1):
        image = pipeline(prompt).images[0]
        image.save("imgs/"+random_img_fname())

if __name__ == "__main__":
    prompt = "a beach at sunset"
    sdxl_text_to_image(prompt,"models/model.safetensors", count=2)


