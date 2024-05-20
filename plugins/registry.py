import asyncio


# models.json
[
  {
    "type": "sd",
    "subtype": "SDXL",
    "name": "mklan-x-real",
    "uncensored": true,
    "description": "SDXL-Hyper, Very NSFW, strong prompt adherance.",
  }
]

# providers.json 
[
  "name": "AH Runpod",
  "local": false,
  "plugin": "ah_runpod_sd",
  "models": [ 
      "name": "mklan-x-real",
      "meta": { "endpoint_id": "b6kn2n72y7aooe" }
    }
  ]
]

async def get_models(provider=None, local=True, uncensored=False,type=None):
    # read data/model.json and parse it
    # then read data/providers.json and parse it
    # then return the models that match the specified criteria
