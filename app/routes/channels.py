from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from app.database.connection import create_connection
from app.database.queries import list_channels

router = APIRouter(
    tags=["Channels"]
)

# Modelo de criação
class ChannelCreate(BaseModel):
    link: str
    country_id: int

# Modelo de resposta para listagem
class ChannelListResponse(BaseModel):
    id: int
    link: str

@router.get("/channels", response_model=List[ChannelListResponse])
def get_channels():
    return list_channels()

@router.post("/channels")
def create_channel(channel: ChannelCreate):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO channels (link, country_id) VALUES (?, ?);", (channel.link, channel.country_id))
        conn.commit()
        return {"id": cursor.lastrowid, "link": channel.link, "country_id": channel.country_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Canal já existe ou país não encontrado.")
    finally:
        conn.close()
