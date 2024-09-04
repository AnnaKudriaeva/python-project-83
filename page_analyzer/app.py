from flask import Flask, request, redirect, url_for, render_template, flash
from bs4 import BeautifulSoup
import requests
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from datetime import datetime
import os
import validators

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

conn = psycopg2.connect(
    os.getenv('DATABASE_URL'),
    cursor_factory=DictCursor
)
cur = conn.cursor()

def fetch_seo_data(url):
    """Fetch SEO data from the URL using BeautifulSoup."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        h1_tag = soup.find('h1')
        title_tag = soup.find('title')
        meta_description_tag = soup.find('meta', attrs={'name': 'description'})

        h1_content = h1_tag.get_text(strip=True) if h1_tag else None
        title_content = title_tag.get_text(strip=True) if title_tag else None
        meta_description = meta_description_tag['content'] if meta_description_tag else None

        return h1_content, title_content, meta_description
    except Exception as e:
        flash(f"Ошибка при парсинге страницы: {e}", 'error')
        return None, None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form.get('url')

    if not validators.url(url):
        flash('Некорректный URL!', 'error')
        return redirect(url_for('index'))

    h1_content, title_content, meta_description = fetch_seo_data(url)

    try:
        cur.execute(
            sql.SQL("INSERT INTO urls (name, created_at, h1_content, title_content, meta_description) VALUES (%s, %s, %s, %s, %s)"),
            [url, datetime.now(), h1_content, title_content, meta_description]
        )
        conn.commit()
        flash('URL и SEO данные успешно добавлены!', 'success')
    except psycopg2.IntegrityError:
        conn.rollback()
        flash('URL уже существует!', 'error')

    return redirect(url_for('index'))

@app.route('/urls')
def list_urls():
    cur.execute("SELECT id, name, created_at, h1_content, title_content, meta_description FROM urls ORDER BY created_at DESC")
    urls = cur.fetchall()
    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:id>')
def show_url(id):
    cur.execute("SELECT id, name, created_at, h1_content, title_content, meta_description FROM urls WHERE id = %s", [id])
    url = cur.fetchone()
    if not url:
        flash('URL не найден!', 'error')
        return redirect(url_for('list_urls'))
    return render_template('url.html', url=url)

if __name__ == '__main__':
    app.run(debug=True)
