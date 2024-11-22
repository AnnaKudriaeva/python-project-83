from flask import Flask, request, redirect, url_for, render_template, flash
from bs4 import BeautifulSoup
import requests
import psycopg2 as pg
from psycopg2 import sql
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlparse
import os
import validators

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


def get_db_connection():
    return pg.connect(os.getenv("DATABASE_URL"), cursor_factory=DictCursor)


def fetch_seo_data(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            flash("Произошла ошибка при проверке", "error")
            return None, "", "", ""

    soup = BeautifulSoup(response.text, "html.parser")
    h1_tag = soup.find("h1")
    h1_content = h1_tag.get_text(strip=True) if h1_tag else None

    title_tag = soup.find("title")
    title_content = title_tag.get_text(strip=True) if title_tag else None
    meta_desc = (
        soup.find("meta", attrs={"name": "description"})["content"]
        if soup.find("meta", attrs={"name": "description"})
        else None
    )

    return response.status_code, h1_content, title_content, meta_desc
#    except Exception:
#        flash("Произошла ошибка при проверке", "error")
#        return None, None, None, None


@app.route("/")
def index():
    return render_template("index.html")


def normalize_url(url):
    parsed_url = urlparse(url.lower())
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}".rstrip("/")
    return normalized_url


@app.route("/urls", methods=["GET"])
def get_urls():
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
    return render_template("urls.html", urls=urls)


@app.post("/urls")
def post_url():
    url = request.form.get("url")
    normalized_url = normalize_url(url)

    if not validators.url(normalized_url):
        flash("Некорректный URL", "error")
        return render_template("index.html"), 422

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        created_at = datetime.now().strftime("%Y-%m-%d")

        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()

        if existing_url:
            flash("Страница уже существует", "error")
            return redirect(url_for("get_url", id=existing_url["id"]))

        cur.execute(
            sql.SQL(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id"
            ),
            (normalized_url, created_at),
        )
        url_id = cur.fetchone()["id"]
        conn.commit()
        flash("Страница успешно добавлена", "success")
    except pg.IntegrityError:
        conn.rollback()
        flash("URL уже существует в базе данных", "error")
        return render_template("index.html"), 422
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка добавления страницы: {e}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("get_url", id=url_id))


@app.get("/urls/<int:id>")
def get_url(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", [id])
    url = cur.fetchone()

    if not url:
        flash("Ошибка при получении URL", "error")
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    cur.execute(
        "SELECT id, status_code, h1, title, description, created_at FROM checks "
        "WHERE url_id = %s ORDER BY created_at DESC",
        [id],
    )
    checks = cur.fetchall()
    cur.close()
    conn.close()

    numbered_checks = [(i + 1, check) for i, check in enumerate(checks)]
    return render_template("url.html", url=url, checks=numbered_checks)


@app.post("/urls/<int:id>/check")
def post_check_url(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM urls WHERE id = %s", [id])
    url = cur.fetchone()

    if not url:
        flash("Ошибка при проверке URL", "error")
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    status_code, h1_content, title_content, meta_desc = fetch_seo_data(url["name"])
    if status_code is None:
        cur.close()
        conn.close()
        return redirect(url_for("get_url", id=id))

    try:
        cur.execute(
            sql.SQL(
                "INSERT INTO checks (url_id, status_code, h1, title, description, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            ),
            [id, status_code, h1_content, title_content, meta_desc, datetime.now()],
        )
        conn.commit()
        flash("Страница успешно проверена", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка проверки страницы: {e}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("get_url", id=id))


if __name__ == "__main__":
    app.run(debug=True)
