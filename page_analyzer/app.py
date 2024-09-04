import os
from flask import Flask, request, redirect, url_for, render_template, flash
import psycopg2
import validators
from psycopg2 import sql
from dotenv import load_dotenv
from datetime import datetime
from psycopg2.extras import DictCursor

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    cursor_factory=DictCursor
)

cur = conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form.get('url')

    if not validators.url(url):
        flash('Некорректный URL!', 'error')
        return redirect(url_for('index'))

    try:
        # Добавление URL в базу данных
        cur.execute(
            sql.SQL("INSERT INTO urls (name, created_at) VALUES (%s, %s)"),
            [url, datetime.now()]
        )
        conn.commit()
        flash('URL успешно добавлен!', 'success')
    except psycopg2.IntegrityError:
        conn.rollback()
        flash('URL уже существует!', 'error')

    return redirect(url_for('index'))

@app.route('/urls')
def list_urls():
    # Fetch all URLs from the database
    cur.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC")
    urls = cur.fetchall()  # `urls` will be a list of dictionaries
    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:id>')
def show_url(id):
    # Fetch a specific URL by ID
    cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", [id])
    url = cur.fetchone()  # `url` will be a dictionary
    if not url:
        flash('URL не найден!', 'error')
        return redirect(url_for('list_urls'))
    return render_template('url.html', url=url)

if __name__ == '__main__':
    app.run(debug=True)
