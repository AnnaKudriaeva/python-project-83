from flask import Flask, request, redirect, url_for, render_template, flash
from page_analyzer.db import (get_all_urls,
                              get_url_by_id,
                              get_checks_by_url_id,
                              insert_url,
                              get_url_by_name,
                              insert_check
                              )
from page_analyzer.utils import fetch_seo_data, normalize_url
import os
import validators

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET"])
def get_urls():
    urls = get_all_urls()
    return render_template("urls.html", urls=urls)


@app.post("/urls")
def post_url():
    url = request.form.get("url")
    normalized_url = normalize_url(url)

    if not validators.url(normalized_url):
        flash("Некорректный URL", "error")
        return render_template("index.html"), 422

    existing_url = get_url_by_name(normalized_url)
    if existing_url:
        flash("Страница уже существует", "error")
        return redirect(url_for("get_url", id=existing_url["id"]))

    url_id = insert_url(normalized_url)
    if not url_id:
        return render_template("index.html"), 422

    return redirect(url_for("get_url", id=url_id))


@app.get("/urls/<int:id>")
def get_url(id):
    url = get_url_by_id(id)
    if not url:
        flash("Ошибка при получении URL", "error")
        return redirect(url_for("index"))

    checks = get_checks_by_url_id(id)
    numbered_checks = [(i + 1, check) for i, check in enumerate(checks)]
    return render_template("url.html", url=url, checks=numbered_checks)


@app.post("/urls/<int:id>/check")
def post_check_url(id):
    url = get_url_by_id(id)
    if not url:
        flash("Ошибка при проверке URL", "error")
        return redirect(url_for("index"))

    status_code, h1_content, title_content, meta_desc = fetch_seo_data(
        url["name"]
        )
    if status_code is None:
        return redirect(url_for("get_url", id=id))

    insert_check(id, status_code, h1_content, title_content, meta_desc)
    return redirect(url_for("get_url", id=id))


if __name__ == "__main__":
    app.run(debug=True)
