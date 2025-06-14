from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from app.database.connection import create_connection

router = APIRouter(
    tags=["Priorities"]
)

class PriorityCreate(BaseModel):
    name: str

class PriorityResponse(BaseModel):
    id: int
    name: str

@router.post("/priorities", response_model=PriorityResponse)
def create_priority(priority: PriorityCreate):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO priorities (name) VALUES (?);", (priority.name,))
        conn.commit()
        return {"id": cursor.lastrowid, "name": priority.name}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Prioridade já cadastrada.")
    finally:
        conn.close()

@router.get("/priorities", response_model=List[PriorityResponse])
def list_priorities():
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name FROM priorities;")
        rows = cursor.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]
    finally:
        conn.close()
