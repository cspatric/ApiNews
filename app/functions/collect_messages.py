import asyncio
import re
import json
import argparse
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any

import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser, ElementHandle

from app.database.connection import initialize_database
from app.database.queries import list_channels

# 🔧 Carrega variáveis do .env
load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/messages/create")
DEFAULT_CAPTURE_MINUTES = int(os.getenv("TIME_MESSAGE_CAPTURE", "10"))


async def start_browser() -> Tuple[Browser, Any]:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    return browser, playwright


async def get_message_blocks(page: Page) -> List[ElementHandle]:
    await page.wait_for_selector('div.tgme_widget_message_wrap', timeout=10000)
    return await page.query_selector_all('div.tgme_widget_message_wrap')


async def parse_message(block: ElementHandle) -> Optional[Tuple[datetime, str]]:
    time_element = await block.query_selector('time')
    text_element = await block.query_selector('div.tgme_widget_message_text')

    if not time_element or not text_element:
        return None

    datetime_str = await time_element.get_attribute('datetime')
    if not datetime_str:
        return None

    try:
        message_time = datetime.fromisoformat(datetime_str).replace(tzinfo=None)
        message_text = await text_element.inner_text()
        return message_time, message_text.strip()
    except Exception:
        return None


def extract_links(text: str) -> List[str]:
    return re.findall(r'https?://\S+', text)


async def fetch_recent_messages_from_channel(page: Page, url: str, minutes: int) -> List[Dict[str, Any]]:
    await page.goto(url, wait_until='domcontentloaded')
    message_blocks = await get_message_blocks(page)

    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)
    messages = []

    for block in reversed(message_blocks):
        result = await parse_message(block)
        if not result:
            continue

        message_time, message_text = result
        if message_time >= cutoff:
            links = extract_links(message_text)
            messages.append({
                "timestamp": message_time.strftime("%Y-%m-%d %H:%M:%S"),
                "text": message_text,
                "links": json.dumps(links),
            })

    return messages


async def collect_messages(minutes: int, channel_ids: List[int]):
    initialize_database()

    browser, playwright = await start_browser()
    page = await browser.new_page()

    all_channels = list_channels()
    selected = [(c["id"], c["link"]) for c in all_channels if c["id"] in channel_ids]

    for channel_id, url in selected:
        print(f"🔍 Coletando mensagens de {url}...")
        messages = await fetch_recent_messages_from_channel(page, url, minutes)

        for msg in messages:
            payload = {
                "channel_id": channel_id,
                "timestamp": msg["timestamp"],
                "text": msg["text"],
                "links": msg["links"],
                "images": None,
                "video": None
            }
            try:
                res = requests.post(API_URL, json=payload)
                print(f"✅ Enviado: {res.status_code} {res.json()}")
            except Exception as e:
                print(f"❌ Erro ao enviar mensagem: {e}")

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta mensagens do Telegram e envia para API.")
    parser.add_argument("--minutes", type=int, help="Minutos anteriores para buscar (prioriza .env se ausente)")
    parser.add_argument("--country", type=int, required=True, help="ID do país para coletar os canais")
    args = parser.parse_args()

    from dotenv import load_dotenv
    import os
    load_dotenv()

    minutes = args.minutes or int(os.getenv("TIME_MESSAGE_CAPTURE", 10))
    country_id = args.country

    # Filtra canais automaticamente pelo país
    all_channels = list_channels()
    selected_channel_ids = [c["id"] for c in all_channels if c["country_id"] == country_id]

    if not selected_channel_ids:
        print(f"⚠️ Nenhum canal encontrado com country_id = {country_id}")
    else:
        asyncio.run(collect_messages(minutes / 60, selected_channel_ids))
