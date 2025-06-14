from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from app.database.connection import create_connection
from datetime import datetime

router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)

class MessageCreate(BaseModel):
    channel_id: int
    text: Optional[str] = None
    links: Optional[str] = None
    images: Optional[str] = None
    video: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    channel_id: int
    timestamp: str
    text: Optional[str]
    links: Optional[str]
    images: Optional[str]
    video: Optional[str]

@router.get("/get", response_model=List[MessageResponse])
def list_messages():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, channel_id, timestamp, text, links, images, video FROM messages")
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "channel_id": row[1],
                "timestamp": row[2],
                "text": row[3],
                "links": row[4],
                "images": row[5],
                "video": row[6],
            } for row in rows
        ]
    finally:
        conn.close()

@router.post("/create", response_model=MessageResponse)
def create_message(message: MessageCreate):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        current_timestamp = datetime.now().isoformat() 

        cursor.execute("""
            INSERT INTO messages (channel_id, timestamp, text, links, images, video)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ( 
            message.channel_id,
            current_timestamp,
            message.text,
            message.links,
            message.images,
            message.video
        ))
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "channel_id": message.channel_id,
            "timestamp": current_timestamp,
            "text": message.text,
            "links": message.links,
            "images": message.images,
            "video": message.video,
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Erro ao inserir mensagem. Verifique o canal.")
    finally:
        conn.close()

    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO messages (channel_id, timestamp, text, links, images, video)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message.channel_id,
            message.timestamp,
            message.text,
            message.links,
            message.images,
            message.video
        ))
        conn.commit()
        return {
            "id": cursor.lastrowid,
            **message.dict()
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Erro ao inserir mensagem. Verifique o canal.")
    finally:
        conn.close()

