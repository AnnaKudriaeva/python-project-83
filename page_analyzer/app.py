#app.py

from flask import Flask, request, redirect, url_for, render_template, flash
from dotenv import load_dotenv
from page_analyzer.db import (
    get_all_urls,
    get_url_by_id,
    get_checks_by_url_id,
    insert_url,
    get_url_by_name,
    insert_check,
)
from page_analyzer.utils import fetch_seo_data, normalize_url
import os
import psycopg2 as pg
from psycopg2.extras import DictCursor
import validators

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


def get_db_connection():
    return pg.connect(os.getenv("DATABASE_URL"), cursor_factory=DictCursor)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET"])
def get_urls():
    try:
        conn = get_db_connection()
        urls = get_all_urls(conn)
        return render_template("urls.html", urls=urls)
    finally:
        conn.close()


@app.post("/urls")
def post_url():
    url = request.form.get("url")
    normalized_url = normalize_url(url)

    if not validators.url(normalized_url):
        flash("Некорректный URL", "error")
        return render_template("index.html"), 422

    try:
        conn = get_db_connection()
        existing_url = get_url_by_name(conn, normalized_url)

        if existing_url:
            flash("Страница уже существует", "error")
            return redirect(url_for("get_url", id=existing_url["id"]))

        url_id = insert_url(conn, normalized_url)
        conn.commit()

        flash("Страница успешно добавлена", "success")
        return redirect(url_for("get_url", id=url_id))

    except Exception as e:
        flash(f"Ошибка добавления страницы: {e}", "error")
        conn.rollback()
        return render_template("index.html"), 422
    finally:
        conn.close()


@app.get("/urls/<int:id>")
def get_url(id):
    try:
        conn = get_db_connection()
        url = get_url_by_id(conn, id)
        if not url:
            flash("Ошибка при получении URL", "error")
            return redirect(url_for("index"))

        checks = get_checks_by_url_id(conn, id)
        numbered_checks = [(i + 1, check) for i, check in enumerate(checks)]
        return render_template("url.html", url=url, checks=numbered_checks)
    finally:
        conn.close()


@app.post("/urls/<int:id>/check")
def post_check_url(id):
    try:
        conn = get_db_connection()
        url = get_url_by_id(conn, id)
        if not url:
            flash("Ошибка при проверке URL", "error")
            return redirect(url_for("index"))

        status_code, h1_content, title_content, meta_desc = fetch_seo_data(url["name"])
        if status_code is None:
            return redirect(url_for("get_url", id=id))

        insert_check(conn, id, status_code, h1_content, title_content, meta_desc)
        conn.commit()
        flash("Страница успешно проверена", "success")
        return redirect(url_for("get_url", id=id))

    except Exception as e:
        flash(f"Ошибка проверки страницы: {e}", "error")
        conn.rollback()
        return redirect(url_for("get_url", id=id))
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
