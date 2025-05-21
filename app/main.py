from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from app.database.connection import initialize_database
from app.database.queries import create_channel, list_channels
from app.functions.collect_messages import collect_messages  # ⬅️ Importando a função de coleta

app = FastAPI(
    title="News API",
    version="1.0.0"
)

initialize_database()

# 📥 Modelo de entrada para /channels
class ChannelCreateRequest(BaseModel):
    link: str

# 📤 Modelo de resposta para criação
class ChannelResponse(BaseModel):
    id: int
    link: str
    status: str

# 📤 Modelo de resposta para listagem
class ChannelListResponse(BaseModel):
    id: int
    link: str

# 📥 Modelo de entrada para /collect
class CollectRequest(BaseModel):
    hours: int
    channel_ids: List[int]

# 📤 Modelo de resposta de mensagens coletadas
class MessageResponse(BaseModel):
    channel: str
    timestamp: str
    text: str
    links: List[str]


@app.post("/channels", response_model=ChannelResponse)
def register_channel(request: ChannelCreateRequest):
    return create_channel(request.link)


@app.get("/channels", response_model=List[ChannelListResponse])
def get_channels():
    return list_channels()


@app.post("/collect", response_model=List[MessageResponse])
async def collect_messages_endpoint(request: CollectRequest):
    return await collect_messages(request.hours, request.channel_ids)
