from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
from flask import flash

def normalize_url(url):
    """
    Нормализует URL, приводя его к стандартному виду.
    Убирает лишние символы и преобразует в нижний регистр.
    """
    parsed_url = urlparse(url.lower())
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}".rstrip("/")
    return normalized_url


def fetch_seo_data(url):
    """
    Извлекает SEO-данные с указанного URL.
    Возвращает код статуса, содержимое <h1>, <title> и <meta name="description">.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "error")
        return None, None, None, None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Извлекаем данные
    h1_tag = soup.find("h1")
    h1_content = h1_tag.get_text(strip=True) if h1_tag else None

    title_tag = soup.find("title")
    title_content = title_tag.get_text(strip=True) if title_tag else None

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_desc_tag["content"] if meta_desc_tag else None

    return response.status_code, h1_content, title_content, meta_desc
