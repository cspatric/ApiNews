from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from app.database.connection import create_connection
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query

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

@router.get("/get/filter", response_model=List[MessageResponse])
def filter_messages(
    country_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    priority_id: Optional[int] = Query(None)
):
    conn = create_connection()
    cursor = conn.cursor()

    limit_timestamp = (datetime.utcnow() - timedelta(minutes=30)).isoformat()

    try:
        query = """
            SELECT m.id, m.channel_id, m.timestamp, m.text, m.links, m.images, m.video
            FROM messages m
            JOIN channels c ON m.channel_id = c.id
        """
        filters = ["m.timestamp >= ?"]
        params = [limit_timestamp]

        if country_id:
            filters.append("c.country_id = ?")
            params.append(country_id)

        if category_id or priority_id:
            query += """
                JOIN alerts a ON instr(a.message_ids, CAST(m.id AS TEXT)) > 0
            """
            if category_id:
                query += " JOIN alert_categories ac ON a.priority_id = ac.id "
                filters.append("ac.id = ?")
                params.append(category_id)
            if priority_id:
                filters.append("a.priority_id = ?")
                params.append(priority_id)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, params)
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
            }
            for row in rows
        ]
    finally:
        conn.close()
