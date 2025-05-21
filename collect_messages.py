import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, ElementHandle
from database import initialize_database, save_messages

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


async def main(channels: List[str], hours: int = 1):
    initialize_database()

    browser, playwright = await start_browser()
    page = await browser.new_page()

    all_messages = []

    for url in channels:
        print(f"🔍 Coletando mensagens de {url}...")
        messages = await fetch_recent_messages_from_channel(page, url, hours)
        all_messages.extend(messages)

    await browser.close()
    await playwright.stop()

    # Salvar no banco
    save_messages(all_messages)

    # (Opcional) também salvar em JSON
    with open("telegram_messages.json", "w", encoding="utf-8") as f:
        json.dump(all_messages, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {len(all_messages)} mensagens salvas no banco de dados SQLite.")


if __name__ == "__main__":
    # Coloque aqui os canais que você deseja monitorar
    channels_to_check = [
        "https://t.me/s/TCH_channel",
        "https://t.me/s/ukrpravda_news",
        # Adicione mais canais públicos aqui
    ]
    asyncio.run(main(channels=channels_to_check, hours=3))

