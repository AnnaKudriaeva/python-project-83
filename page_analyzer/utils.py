from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import flash


def normalize_url(url):
    parsed_url = urlparse(url.lower())
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}".rstrip("/")
    return normalized_url


def fetch_seo_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "error")
        return None, None, None, None

    soup = BeautifulSoup(response.text, "html.parser")

    h1_tag = soup.find("h1")
    h1_content = h1_tag.get_text(strip=True) if h1_tag else None

    title_tag = soup.find("title")
    title_content = title_tag.get_text(strip=True) if title_tag else None

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_desc_tag["content"] if meta_desc_tag else None

    return response.status_code, h1_content, title_content, meta_desc
