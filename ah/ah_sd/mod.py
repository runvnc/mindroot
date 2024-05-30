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



def get_pipeline_embeds(pipeline, prompt, negative_prompt, device):
    """ Get pipeline embeds for prompts bigger than the maxlength of the pipe
    :param pipeline:
    :param prompt:
    :param negative_prompt:
    :param device:
    :return:
    """
    max_length = pipeline.tokenizer.model_max_length

    # simple way to determine length of tokens
    count_prompt = len(prompt.split(" "))
    count_negative_prompt = len(negative_prompt.split(" "))

    # create the tensor based on which prompt is longer
    if count_prompt >= count_negative_prompt:
        input_ids = pipeline.tokenizer(prompt, return_tensors="pt", truncation=False).input_ids.to(device)
        shape_max_length = input_ids.shape[-1]
        negative_ids = pipeline.tokenizer(negative_prompt, truncation=False, padding="max_length",
                                          max_length=shape_max_length, return_tensors="pt").input_ids.to(device)

    else:
        negative_ids = pipeline.tokenizer(negative_prompt, return_tensors="pt", truncation=False).input_ids.to(device)
        shape_max_length = negative_ids.shape[-1]
        input_ids = pipeline.tokenizer(prompt, return_tensors="pt", truncation=False, padding="max_length",
                                       max_length=shape_max_length).input_ids.to(device)

    concat_embeds = []
    neg_embeds = []
    for i in range(0, shape_max_length, max_length):
        concat_embeds.append(pipeline.text_encoder(input_ids[:, i: i + max_length])[0])
        neg_embeds.append(pipeline.text_encoder(negative_ids[:, i: i + max_length])[0])

    return torch.cat(concat_embeds, dim=1), torch.cat(neg_embeds, dim=1)

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

        prompt_embeds, negative_prompt_embeds = get_pipeline_embeds(pipeline, prompt, negative_prompt, "cuda")

        image = pipeline(prompt_embeds=prompt_embeds, negative_prompt_embeds=negative_prompt_embeds,
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



