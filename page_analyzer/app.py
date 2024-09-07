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

        return response.status_code, h1_content, title_content, meta_description
    except Exception as e:
        flash(f"Error parsing the page: {e}", 'error')
        return None, None, None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['GET', 'POST'])
def add_url():
    if request.method == 'POST':
        url = request.form.get('url')

        if not validators.url(url):
            flash('Invalid URL!', 'error')
            return redirect(url_for('index'))

        try:
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute(
                sql.SQL("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id"),
                [url, created_at]
            )
            url_id = cur.fetchone()['id']
            conn.commit()
            flash('URL added successfully!', 'success')
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('URL already exists!', 'error')
            return redirect(url_for('index'))

        return redirect(url_for('show_url', id=url_id))
    else:
        cur.execute("""
            SELECT urls.id, urls.name, urls.created_at, checks.status_code
            FROM urls
            LEFT JOIN checks ON urls.id = checks.url_id
            ORDER BY urls.created_at DESC
        """)
        urls = cur.fetchall()
        return render_template('urls.html', urls=urls)

@app.route('/urls/<int:id>', methods=['GET', 'POST'])
def show_url(id):
    cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", [id])
    url = cur.fetchone()

    if not url:
        flash('URL not found!', 'error')
        return redirect(url_for('index'))

    cur.execute("SELECT id, status_code, h1, title, description, created_at FROM checks WHERE url_id = %s ORDER BY created_at DESC", [id])
    checks = cur.fetchall()

    if request.method == 'POST':
        status_code, h1_content, title_content, meta_description = fetch_seo_data(url['name'])
        try:
            cur.execute(
                sql.SQL("INSERT INTO checks (url_id, status_code, h1, title, description, created_at) VALUES (%s, %s, %s, %s, %s, %s)"),
                [id, status_code, h1_content, title_content, meta_description, datetime.now()]
            )
            conn.commit()
            flash('SEO check completed successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f"Error saving check data: {e}", 'error')

        return redirect(url_for('show_url', id=id))

    return render_template('url.html', url=url, checks=checks)

if __name__ == '__main__':
    app.run(debug=True)
