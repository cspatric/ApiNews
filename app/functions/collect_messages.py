import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, ElementHandle

from app.database.connection import initialize_database
from app.database.queries import save_messages, list_channels


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


async def fetch_recent_messages_from_channel(page: Page, url: str, hours: int) -> List[Dict[str, Any]]:
    await page.goto(url, wait_until='domcontentloaded')
    message_blocks = await get_message_blocks(page)

    now = datetime.now()
    cutoff = now - timedelta(hours=hours)
    messages = []

    for block in reversed(message_blocks):
        result = await parse_message(block)
        if not result:
            continue

        message_time, message_text = result
        if message_time >= cutoff:
            links = extract_links(message_text)
            messages.append({
                "channel": url,
                "timestamp": message_time.strftime("%Y-%m-%d %H:%M:%S"),
                "text": message_text,
                "links": links,
            })

    return messages

async def collect_messages(hours: int, channel_ids: List[int]) -> List[Dict[str, Any]]:
    initialize_database()

    browser, playwright = await start_browser()
    page = await browser.new_page()

    all_channels = list_channels()
    selected_channels = [c["link"] for c in all_channels if c["id"] in channel_ids]

    all_messages = []

    for url in selected_channels:
        print(f"🔍 Coletando mensagens de {url}...")
        messages = await fetch_recent_messages_from_channel(page, url, hours)
        all_messages.extend(messages)

    await browser.close()
    await playwright.stop()

    save_messages(all_messages)

    return all_messages

if __name__ == "__main__":
    asyncio.run(collect_messages(hours=3, channel_ids=[1, 2, 3]))
