from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the router from chat.py
from plugins.ah_chat.chat import router as chat_router
app.include_router(chat_router)

# Other server setup code can go here
