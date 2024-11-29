import os

import validators
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from page_analyzer import db
from page_analyzer.utils import fetch_seo_data, normalize_url

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL")


@app.errorhandler(Exception)
def handle_exception(e):
    flash(f"Произошла ошибка: {e}", "error")
    return redirect(url_for("index")), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET"])
def get_urls():
    conn = db.get_connection(app.config["DATABASE_URL"])
    try:
        urls = db.get_all_urls(conn)
    finally:
        conn.close()
    return render_template("urls.html", urls=urls)


@app.post("/urls")
def post_url():
    url = request.form.get("url")
    normalized_url = normalize_url(url)

    if not validators.url(normalized_url):
        flash("Некорректный URL", "error")
        return render_template("index.html"), 422

    conn = db.get_connection(app.config["DATABASE_URL"])
    try:
        existing_url = db.get_url_by_name(conn, normalized_url)
        if existing_url:
            flash("Страница уже существует", "error")
            return redirect(url_for("get_url", id=existing_url["id"]))

        url_id = db.insert_url(conn, normalized_url)
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка добавления страницы: {e}", "error")
        return render_template("index.html"), 422
    finally:
        conn.close()

    flash("Страница успешно добавлена", "success")
    return redirect(url_for("get_url", id=url_id))


@app.get("/urls/<int:id>")
def get_url(id):
    conn = db.get_connection(app.config["DATABASE_URL"])
    try:
        url = db.get_url_by_id(conn, id)
        if not url:
            flash("Ошибка при получении URL", "error")
            return redirect(url_for("index"))

        checks = db.get_checks_by_url_id(conn, id)
    finally:
        conn.close()

    numbered_checks = [(i + 1, check) for i, check in enumerate(checks)]
    return render_template("url.html", url=url, checks=numbered_checks)


@app.post("/urls/<int:id>/check")
def post_check_url(id):
    conn = db.get_connection(app.config["DATABASE_URL"])
    try:
        url = db.get_url_by_id(conn, id)
        if not url:
            flash("Ошибка при проверке URL", "error")
            return redirect(url_for("index"))

        status_code, h1_content, title_content, meta_desc = fetch_seo_data(
            url["name"]
            )
        if status_code is None:
            flash("Не удалось проверить страницу", "error")
            return redirect(url_for("get_url", id=id))

        db.insert_check(
            conn, id, status_code, h1_content, title_content, meta_desc
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка проверки страницы: {e}", "error")
        return redirect(url_for("get_url", id=id))
    finally:
        conn.close()

    flash("Страница успешно проверена", "success")
    return redirect(url_for("get_url", id=id))


if __name__ == "__main__":
    app.run(debug=True)
