import torch
import sys
import asyncio
from diffusers import StableDiffusionXLPipeline, StableDiffusionPipeline
from nanoid import generate
import os

from ..commands import command
from ..services import service
from ..hooks import hook

pipeline = None

if os.environ.get('AH_DEFAULT_SD_MODEL'):
    current_model = 'models/' + os.environ.get('AH_DEFAULT_SD_MODEL')
    local_model = True
    use_sdxl = True
    from_huggingface = False
else:
    current_model = 'manpreets7/dreamshaper-3.2'
    local_model = False
    use_sdxl = False
    from_huggingface = True

if os.environ.get('AH_USE_SDXL') == 'True':
    use_sdxl = True
else:
    use_sdxl = False

def random_img_fname():
    return generate() + ".png"

def use_model(model_id, local=True):
    global current_model
    global local_model
    current_model = model_id
    local_model = local

@hook()
async def warmup(context=None):
    global from_huggingface
    global current_model
    global pipeline
    global local_model
    global use_sdxl
    model_id = current_model
 
    if from_huggingface is None:
        from_huggingface = not local_model

    if use_sdxl:
        print("Initializing stable diffusion XL pipeline...")

        if not from_huggingface:
            pipeline = StableDiffusionXLPipeline.from_single_file(model_id, torch_dtype=torch.float16)
        else:
            pipeline = StableDiffusionXLPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    else:
        print("Initializing stable diffusion pipeline...")

        if not from_huggingface:
            pipeline = StableDiffusionPipeline.from_single_file(model_id, torch_dtype=torch.float16)
        else:
            pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)

    pipeline = pipeline.to("cuda")
    if not local_model:
        pipeline.safety_checker = lambda images, **kwargs: (images, [False])


@service(is_local=True)
async def text_to_image(prompt, negative_prompt='', model_id=None, from_huggingface=None,
                        count=1, context=None, save_to="imgs/" + random_img_fname(), w=1024, h=1024, steps=20, cfg=8):
    if pipeline is None:
        await warmup()

    if model_id is not None and  model_id != current_model:
        use_model(model_id, from_huggingface is None)
        await warmup()

    for n in range(1, count+1):
        image = pipeline(prompt=prompt, negative_prompt=negative_prompt,
                         num_inference_steps=steps, guidance_scale=cfg).images[0]
        fname = "imgs/"+random_img_fname()
        image.save(fname)
        return fname


@command(is_local=True)
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



