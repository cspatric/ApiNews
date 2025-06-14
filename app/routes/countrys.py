from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from app.database.connection import create_connection

router = APIRouter(
    prefix="/countrys",
    tags=["Countrys"]
)

class CountryCreate(BaseModel):
    name: str

class CountryResponse(BaseModel):
    id: int
    name: str

@router.get("/get", response_model=List[CountryResponse])
def list_countrys():
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name FROM countrys;")
        results = cursor.fetchall()
        return [{"id": row[0], "name": row[1]} for row in results]
    finally:
        conn.close()


@router.post("/create", response_model=CountryResponse)
def create_country(country: CountryCreate):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO countrys (name) VALUES (?);", (country.name,))
        conn.commit()
        return {"id": cursor.lastrowid, "name": country.name}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="País já cadastrado ou erro de integridade.")
    finally:
        conn.close()

