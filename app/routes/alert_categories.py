from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from app.database.connection import create_connection

router = APIRouter(
    tags=["Alert Categories"]
)

class AlertCategoryCreate(BaseModel):
    name: str

class AlertCategoryResponse(BaseModel):
    id: int
    name: str

@router.post("/alert_categories", response_model=AlertCategoryResponse)
def create_alert_category(category: AlertCategoryCreate):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO alert_categories (name) VALUES (?);",
            (category.name,)
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "name": category.name
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Categoria já cadastrada ou erro de integridade.")
    finally:
        conn.close()

@router.get("/alert_categories", response_model=List[AlertCategoryResponse])
def list_alert_categories():
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name FROM alert_categories;")
        rows = cursor.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]
    finally:
        conn.close()
