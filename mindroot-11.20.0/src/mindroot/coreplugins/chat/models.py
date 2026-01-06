from typing import Union, List, Literal
from pydantic import BaseModel

class TextMessagePart(BaseModel):
    type: Literal["text"]
    text: str

class ImageMessagePart(BaseModel):
    type: Literal["image"]
    data: str  # Use 'data' here to store your data URL string

# we need to be able to serialize this data to JSON
# so we can send
# it over the network
# implementaion for ImageMessagePart json serialization:
# https://pydantic-docs.helpmanual.io/usage/exporting_models/#json-serialisation
# https://pydantic-docs.helpmanual.io/usage/exporting_models/#json-serialisation




# Use Union to create a discriminated union type
MessageParts = Union[TextMessagePart, ImageMessagePart]
