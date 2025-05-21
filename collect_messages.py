import asyncio
from playwright.async_api import async_playwright

async def coletar_mensagens_telegram():
    async with async_playwright() as p:
        navegador = await p.chromium.launch(headless=False)
        pagina = await navegador.new_page()
        await pagina.goto("https://t.me/s/TCH_channel", wait_until='domcontentloaded')

        await pagina.wait_for_selector('div.tgme_widget_message_text', timeout=10000)

        mensagens = await pagina.query_selector_all('div.tgme_widget_message_text')
        print("\n📥 Últimas mensagens:\n")
        for mensagem in mensagens[-5:]:
            texto = await mensagem.inner_text()
            print("•", texto.strip(), "\n")

        await navegador.close()

asyncio.run(coletar_mensagens_telegram())
