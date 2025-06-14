import asyncio
import os
import re
import json
import random
import argparse
import sys
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any

import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser, ElementHandle
from dateutil import parser

# Configurações iniciais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from app.database.connection import initialize_database
from app.database.queries import list_channels

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/messages/create")
DEFAULT_CAPTURE_MINUTES = int(os.getenv("TIME_MESSAGE_CAPTURE", "10"))
MEDIA_IMAGE_PATH = "app/media/image"
MEDIA_VIDEO_PATH = "app/media/video"

# Utilitários
def extract_links(text: str) -> List[str]:
    return re.findall(r'https?://\S+', text)


def ensure_media_dirs():
    os.makedirs(MEDIA_IMAGE_PATH, exist_ok=True)
    os.makedirs(MEDIA_VIDEO_PATH, exist_ok=True)


# Navegador
async def start_browser() -> Tuple[Browser, Any]:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=50)
    return browser, playwright


# Processamento de mensagens
async def get_message_blocks(page: Page) -> List[ElementHandle]:
    try:
        await page.wait_for_selector('div.tgme_widget_message_wrap', timeout=10000)
        return await page.query_selector_all('div.tgme_widget_message_wrap')
    except Exception as e:
        print(f"⚠️ Erro ao buscar blocos de mensagem: {e}")
        return []


async def parse_message(block: ElementHandle) -> Optional[Tuple[datetime, str]]:
    try:
        # Busca o elemento time dentro do link de data
        time_el = await block.query_selector('a.tgme_widget_message_date time')
        text_el = await block.query_selector('div.tgme_widget_message_text')

        print(f"⏱️ time_el encontrado? {'✅' if time_el else '❌'}")
        print(f"📝 text_el encontrado? {'✅' if text_el else '❌'}")

        if not time_el:
            time_el = await block.query_selector('time')  # fallback

        timestamp_str = await time_el.get_attribute('datetime') if time_el else None
        text = await text_el.inner_text() if text_el else ""

        print(f"📅 datetime bruto: {timestamp_str}")
        print(f"🧾 texto extraído: {text.strip()[:100]}...")

        if timestamp_str:
            timestamp = parser.isoparse(timestamp_str).replace(tzinfo=None)
            return timestamp, text.strip()
        else:
            print("⚠️ Timestamp ausente.")
    except Exception as e:
        print(f"⚠️ Erro ao processar mensagem: {e}")
    return None
async def download_media(page: Page, src: str, folder: str, prefix: str, timestamp: datetime, msg_id: int) -> str:
    ext = "jpg" if prefix == "image" else "mp4"
    filename = f"{prefix}-{timestamp.strftime('%Y%m%d%H%M%S')}-{msg_id}-{random.randint(1000,9999)}.{ext}"
    path = os.path.join(folder, filename)

    # Se for imagem, tenta o método tradicional
    if prefix == "image":
        try:
            response = await page.context.request.get(src)
            if response.ok:
                content = await response.body()
                with open(path, "wb") as f:
                    f.write(content)
                print(f"✅ Imagem salva: {path}")
                return filename
            else:
                print(f"❌ Falha ao baixar imagem: {response.status}")
        except Exception as e:
            print(f"❌ Erro ao baixar imagem: {e}")
        return ""

    # Se for vídeo, faz download via browser com fetch e blob
    try:
        print(f"📥 Iniciando download via navegador: {src}")
        await page.evaluate(f"""
            (async () => {{
                const response = await fetch("{src}");
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = "{filename}";
                document.body.appendChild(a);
                a.click();
                a.remove();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            }})()
        """)
        print(f"✅ Vídeo enviado para download (navegador): {filename}")
        return filename
    except Exception as e:
        print(f"❌ Erro no download de vídeo via navegador: {e}")
        return ""

def baixar_video_direct(src: str, path: str):
    headers = {
        "Referer": "https://t.me/",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(src, headers=headers, stream=True)
        if r.ok:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Download concluído: {path}")
        else:
            print(f"❌ Erro {r.status_code} ao baixar vídeo")
    except Exception as e:
        print(f"❌ Erro ao baixar vídeo via requests: {e}")


async def fetch_messages(page: Page, url: str, minutes: int, msg_id_start=1) -> List[Dict[str, Any]]:
    await page.goto(url, wait_until='domcontentloaded')
    blocks = await get_message_blocks(page)
    print(f"📦 {len(blocks)} mensagens encontradas em {url}")

    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)
    messages = []
    msg_id = msg_id_start

    for block in reversed(blocks):
        parsed = await parse_message(block)
        if not parsed:
            continue

        msg_time, msg_text = parsed
        if msg_time < cutoff:
            continue

        links = extract_links(msg_text)
        images, videos = [], []

        # 🔧 Corrigido: busca por imagens (src ou background-image)
        photo_links = await block.query_selector_all('a.tgme_widget_message_photo_wrap')
        img_els = []

        for link in photo_links:
            # Primeiro tenta pegar <img src>
            img_tag = await link.query_selector('img')
            if img_tag:
                src = await img_tag.get_attribute("src")
                if src:
                    img_els.append(src)
            else:
                # Tenta extrair de style="background-image: url(...)"
                style = await link.get_attribute("style")
                if style and "background-image" in style:
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                    if match:
                        img_els.append(match.group(1))

        for src in img_els:
            if src:
                images.append(await download_media(page, src, MEDIA_IMAGE_PATH, "image", msg_time, msg_id))

        # 🔄 GIFs e vídeos (suporte a src e poster)
        vid_els = await block.query_selector_all('video')
        for vid in vid_els:
            src = await vid.get_attribute("src")
            poster = await vid.get_attribute("poster")

            print(f"🎥 VIDEO SRC: {src}")
            print(f"🖼️ POSTER: {poster}")
            # GIFs ou vídeos (formato mp4)
            if src and ".mp4" in src:
                filename = f"video-{msg_time.strftime('%Y%m%d%H%M%S')}-{msg_id}-{random.randint(1000,9999)}.mp4"
                path = os.path.join(MEDIA_VIDEO_PATH, filename)
                baixar_video_direct(src, path)
                videos.append(filename)

            # Poster (thumb de vídeo) como imagem
            if poster and ".jpg" in poster:
                images.append(await download_media(page, poster, MEDIA_IMAGE_PATH, "image", msg_time, msg_id))


        messages.append({
            "timestamp": msg_time.strftime("%Y-%m-%d %H:%M:%S"),
            "text": msg_text,
            "links": json.dumps(links),
            "images": images,
            "videos": videos
        })
        msg_id += 1

    return messages

# Principal
async def collect_messages(minutes: int, country_id: int):
    initialize_database()
    ensure_media_dirs()

    browser, playwright = await start_browser()
    page = await browser.new_page()

    all_channels = list_channels()
    selected = [(c["id"], c["link"]) for c in all_channels if int(c["country_id"]) == int(country_id)]
    print(f"🔎 {len(selected)} canais com country_id={country_id}: {[id for id, _ in selected]}")

    if not selected:
        print("⚠️ Nenhum canal encontrado.")
    else:
        for channel_id, url in selected:
            print(f"🔍 Lendo mensagens de {url}")
            try:
                messages = await fetch_messages(page, url, minutes)
            except Exception as e:
                print(f"❌ Erro ao buscar mensagens do canal {url}: {e}")
                continue

            for msg in messages:
                payload = {
                    "channel_id": channel_id,
                    "timestamp": msg["timestamp"],
                    "text": msg["text"],
                    "links": msg["links"],
                    "images": json.dumps(msg["images"]),
                    "video": json.dumps(msg["videos"])
                }
                try:
                    res = requests.post(API_URL, json=payload)
                    print(f"✅ Enviado: {res.status_code} {res.json()}")
                except Exception as e:
                    print(f"❌ Falha ao enviar mensagem do canal {channel_id}: {e}")

    await browser.close()
    await playwright.stop()


# CLI
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Coleta mensagens do Telegram e envia para API.")
    arg_parser.add_argument("--minutes", type=int, help="Minutos anteriores para buscar")
    arg_parser.add_argument("--country", type=int, required=True, help="ID do país para filtrar canais")
    args = arg_parser.parse_args()

    asyncio.run(collect_messages(args.minutes or DEFAULT_CAPTURE_MINUTES, args.country))

