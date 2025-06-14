from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime, timedelta
from app.database.connection import create_connection

router = APIRouter(tags=["Alertas"])

# 📥 Modelo de entrada
class AlertCreate(BaseModel):
    message_ids: List[int]
    priority_id: Optional[int] = None
    country_id: Optional[int] = None
    title: str
    short_description: Optional[str] = None
    alert_body: Optional[dict] = None
    images: Optional[str] = None
    video: Optional[str] = None
    coordinates: Optional[str] = None

# 📤 Modelo de resposta
class AlertResponse(BaseModel):
    id: int
    message_ids: List[int]
    priority_id: Optional[int]
    country_id: Optional[int]
    title: str
    short_description: Optional[str]
    alert_body: Optional[dict]
    images: Optional[str]
    video: Optional[str]
    timestamp: str
    coordinates: Optional[str]

class MessageResponse(BaseModel):
    id: int
    channel_id: int
    timestamp: str
    text: Optional[str]
    links: Optional[str]
    images: Optional[str]
    video: Optional[str]

@router.post("/alerts", response_model=AlertResponse)
def create_alert(alert: AlertCreate):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO alerts (
                message_ids, priority_id, country_id, title, short_description,
                alert_body, images, video, timestamp, coordinates
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            json.dumps(alert.message_ids),
            alert.priority_id,
            alert.country_id,
            alert.title,
            alert.short_description,
            json.dumps(alert.alert_body) if alert.alert_body else None,
            alert.images,
            alert.video,
            now,
            alert.coordinates
        ))
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "message_ids": alert.message_ids,
            "priority_id": alert.priority_id,
            "country_id": alert.country_id,
            "title": alert.title,
            "short_description": alert.short_description,
            "alert_body": alert.alert_body,
            "images": alert.images,
            "video": alert.video,
            "timestamp": now,
            "coordinates": alert.coordinates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, message_ids, priority_id, country_id, title,
                   short_description, alert_body, images, video,
                   timestamp, coordinates
            FROM alerts
        """)
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "message_ids": json.loads(row[1]),
                "priority_id": row[2],
                "country_id": row[3],
                "title": row[4],
                "short_description": row[5],
                "alert_body": json.loads(row[6]) if row[6] else None,
                "images": row[7],
                "video": row[8],
                "timestamp": row[9],
                "coordinates": row[10],
            }
            for row in rows
        ]
    finally:
        conn.close()


@router.get("/alerts/filter", response_model=List[MessageResponse])
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
