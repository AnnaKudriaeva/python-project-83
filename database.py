import psycopg2
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение URL базы данных из переменной окружения
DATABASE_URL = os.getenv('DATABASE_URL')

# Подключение к базе данных
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
