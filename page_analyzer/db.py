#db.py

from psycopg2 import sql
from datetime import datetime


def get_all_urls(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT urls.id, urls.name, urls.created_at, checks.status_code
            FROM urls
            LEFT JOIN checks ON urls.id = checks.url_id
            ORDER BY urls.created_at DESC
            """
        )
        return cur.fetchall()


def get_url_by_id(conn, url_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, created_at FROM urls WHERE id = %s", [url_id]
        )
        return cur.fetchone()


def get_checks_by_url_id(conn, url_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, status_code, h1, title, description, created_at
            FROM checks
            WHERE url_id = %s
            ORDER BY created_at DESC
            """,
            [url_id],
        )
        return cur.fetchall()


def insert_url(conn, normalized_url):
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "INSERT INTO urls (name, created_at)"
                "VALUES (%s, %s) RETURNING id"
            ),
            (normalized_url, datetime.now().strftime("%Y-%m-%d")),
        )
        return cur.fetchone()["id"]


def get_url_by_name(conn, normalized_url):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM urls WHERE name = %s", [normalized_url])
        return cur.fetchone()


def insert_check(conn, url_id, status_code, h1_content, title_content, meta_desc):
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "INSERT INTO checks (url_id, status_code, h1, title, description, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            ),
            [
                url_id,
                status_code,
                h1_content,
                title_content,
                meta_desc,
                datetime.now(),
            ],
        )
