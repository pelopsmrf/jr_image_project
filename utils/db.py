import os

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "images_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
    )


def execute(query, params=(), fetch=False):
    """Выполняет SQL-запрос. Если fetch=True, возвращает список строк-словарей."""
    conn = get_connection()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
    finally:
        conn.close()


def init_db():
    execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            size INTEGER NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_type TEXT NOT NULL
        )
    """)


def save_metadata(filename, original_name, size, file_type):
    execute(
        "INSERT INTO images (filename, original_name, size, file_type) VALUES (%s, %s, %s, %s)",
        (filename, original_name, size, file_type),
    )


def get_images(limit, offset):
    return execute(
        "SELECT * FROM images ORDER BY upload_time DESC LIMIT %s OFFSET %s",
        (limit, offset),
        fetch=True,
    )


def count_images():
    return execute("SELECT COUNT(*) AS total FROM images", fetch=True)[0]["total"]


def delete_image(image_id):
    """Удаляет запись и возвращает имя файла, или None, если записи нет."""
    rows = execute("DELETE FROM images WHERE id = %s RETURNING filename", (image_id,), fetch=True)
    return rows[0]["filename"] if rows else None
