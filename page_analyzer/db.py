import psycopg2 as pg
from psycopg2 import sql
from psycopg2.extras import DictCursor
from datetime import datetime
from flask import flash
import os


def get_db_connection():
    return pg.connect(os.getenv("DATABASE_URL"), cursor_factory=DictCursor)


def get_all_urls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT urls.id, urls.name, urls.created_at, checks.status_code
        FROM urls
        LEFT JOIN checks ON urls.id = checks.url_id
        ORDER BY urls.created_at DESC
        """
        )
    urls = cur.fetchall()
    cur.close()
    conn.close()
    return urls


def get_url_by_id(url_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name,"
                "created_at FROM urls WHERE id = %s", [url_id])
    url = cur.fetchone()
    cur.close()
    conn.close()
    return url


def get_checks_by_url_id(url_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, status_code, h1, title, description,
        created_at FROM checks WHERE url_id = %s
        ORDER BY created_at DESC
        """,
        [url_id],
    )
    checks = cur.fetchall()
    cur.close()
    conn.close()
    return checks


def insert_url(normalized_url):
    conn = get_db_connection()
    url_id = None
    try:
        cur = conn.cursor()
        cur.execute(
            sql.SQL(
                "INSERT INTO urls (name, created_at)"
                "VALUES (%s, %s) RETURNING id"
            ),
            (normalized_url, datetime.now().strftime("%Y-%m-%d")),
        )
        url_id = cur.fetchone()["id"]
        conn.commit()
        flash("Страница успешно добавлена", "success")
    except pg.IntegrityError:
        conn.rollback()
        flash("URL уже существует в базе данных", "error")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка добавления страницы: {e}", "error")
    finally:
        cur.close()
        conn.close()
    return url_id


def get_url_by_name(normalized_url):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM urls WHERE name = %s", [normalized_url])
    url = cur.fetchone()
    cur.close()
    conn.close()
    return url


def insert_check(url_id, status_code, h1_content, title_content, meta_desc):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            sql.SQL(
                "INSERT INTO checks (url_id, status_code, h1,"
                "title, description, created_at) "
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
        conn.commit()
        flash("Страница успешно проверена", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка проверки страницы: {e}", "error")
    finally:
        cur.close()
        conn.close()
