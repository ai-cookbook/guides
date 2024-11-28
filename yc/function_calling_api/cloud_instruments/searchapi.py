import os
import requests
import dotenv
from loguru import logger
from yandex_cloud_ml_sdk import YCloudML

# Загрузка переменных окружения
dotenv.load_dotenv()

# Получение идентификаторов папки и API ключа
FOLDER_ID = os.getenv('FOLDER_ID')
API_KEY = os.getenv('YANDEX_API_KEY')

# URL для генеративного поиска
SEARCH_API_GENERATIVE = f"https://ya.ru/search/xml/generative?folderid={FOLDER_ID}"
SERP_SITE = os.getenv('SERP_SITE', None)
SERP_HOST = os.getenv('SERP_HOST', None)
SERP_URL = os.getenv('SERP_URL', None)

# Инициализация SDK Yandex Cloud
sdk = YCloudML(folder_id=FOLDER_ID, auth=API_KEY)

def process_response(response):
    """Обрабатывает ответ от API и возвращает комбинированный контент."""
    content = ""
    sources = []

    # Проверяем тип контента в ответе
    if "application/json" in response.headers.get("Content-Type", ""):
        content = response.json().get("message", {}).get("content", "")
        sources = response.json().get("links", [])
    elif "text/xml" in response.headers.get("Content-Type", ""):
        pass  # Ошибка не логируется
    else:
        pass  # Неожиданный тип контента не логируется

    # Формируем комбинированный контент для ответа
    combined_content = f"Ответ SearchAPI:\n{content}\n\nИсточники:\n" + "\n".join(sources)
    return combined_content

def search_api_generative(message: str) -> str:
    """Выполняет генеративный поиск без контекста треда."""
    headers = {"Authorization": f"Api-Key {API_KEY}"}
    data = {
        "messages": [{"content": message, "role": "user"}],
        "site": SERP_SITE,
        "host": SERP_HOST,
        "url": SERP_URL
    }

    # Отправляем запрос к API
    response = requests.post(SEARCH_API_GENERATIVE, headers=headers, json=data)
    combined_content = process_response(response)
    
    return combined_content