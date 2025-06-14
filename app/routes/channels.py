from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from app.database.connection import create_connection
from app.database.queries import list_channels

router = APIRouter(
    tags=["Channels"]
)

# 📥 Modelo de entrada
class ChannelCreate(BaseModel):
    link: str
    country_id: int

# 📤 Modelo de saída
class ChannelListResponse(BaseModel):
    id: int
    link: str
    country_id: int

@router.get("/channels", response_model=List[ChannelListResponse])
def get_channels():
    return list_channels()

@router.post("/channels", response_model=ChannelListResponse)
def create_channel(channel: ChannelCreate):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO channels (link, country_id) VALUES (?, ?);",
            (channel.link, channel.country_id)
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "link": channel.link,
            "country_id": channel.country_id
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Canal já existe ou país não encontrado.")
    finally:
        conn.close()

@router.get("/channels/filter", response_model=List[ChannelListResponse])
def filter_channels(country_id: Optional[int] = Query(None, description="Filtrar por ID do país")):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        if country_id is not None:
            cursor.execute("SELECT id, link, country_id FROM channels WHERE country_id = ?", (country_id,))
        else:
            cursor.execute("SELECT id, link, country_id FROM channels")
        rows = cursor.fetchall()
        return [
            {"id": row[0], "link": row[1], "country_id": row[2]}
            for row in rows
        ]
    finally:
        conn.close()
