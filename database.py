import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from travel_utils import normalize_trip_data

DB_PATH = Path(__file__).resolve().parent / "travel_planner.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_name TEXT NOT NULL,
                destination TEXT NOT NULL,
                trip_data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_trip(
    trip_name: str,
    destination: str,
    trip_data: dict[str, Any]
) -> int:

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO trips
            (trip_name, destination, trip_data, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                trip_name,
                destination,
                json.dumps(trip_data, ensure_ascii=False),
                created_at,
            ),
        )

        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_trips():
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, trip_name, destination, created_at
            FROM trips
            ORDER BY id DESC
            """
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "trip_name": row[1],
            "destination": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


def get_trip(trip_id: int):
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, trip_name, destination,
                   trip_data, created_at
            FROM trips
            WHERE id = ?
            """,
            (trip_id,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return None

    trip_data = json.loads(row[3])

    return {
        "id": row[0],
        "trip_name": row[1],
        "destination": row[2],
        "trip_data": normalize_trip_data(trip_data),
        "created_at": row[4],
    }


def delete_trip(trip_id: int):
    conn = _connect()
    try:
        conn.execute(
            "DELETE FROM trips WHERE id = ?",
            (trip_id,),
        )
        conn.commit()
    finally:
        conn.close()