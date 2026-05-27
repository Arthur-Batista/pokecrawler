import asyncio
import httpx
import logging
from settings import (
    BASE_URL, POKEDEX_URL, HEADERS,
    MAX_CONCURRENT, REQUEST_TIMEOUT
)
from fetcher import get_soup, get_pokemon_links
from parser import get_name, scrap_pokemon_info
from storage import get_uploaded_names, save_sqlite


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("crawler.log", encoding="utf-8"), 
        logging.StreamHandler() 
    ]
)

logging.getLogger("httpx").setLevel(logging.WARNING)

async def scrape_pokemon(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    db_lock: asyncio.Lock,
    href: str,
    uploaded_names: set
) -> None:

    url = BASE_URL + href

    async with semaphore:
        try:
            soup = await get_soup(client, url)
        except Exception as e:
            logging.error(f"Erro de rede ao acessar {href}: {e}")
            return

    name = get_name(soup)

    if not name:
        return

    if name in uploaded_names:
        return


    pokemon_data = await scrap_pokemon_info(client, soup)

    if not pokemon_data:
        return

    async with db_lock:
        save_sqlite([pokemon_data])
        print(f"[CAPTURADO] {name}")
        logging.info(f"Capturado com sucesso: {name}")


async def main():

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    db_lock = asyncio.Lock()

    uploaded_names = get_uploaded_names()

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT
    ) as client:

        pokedex_soup = await get_soup(client, POKEDEX_URL)
        pokemon_links = get_pokemon_links(pokedex_soup)


        tasks = [
            scrape_pokemon(client, semaphore, db_lock, href, uploaded_names)
            for href in pokemon_links
        ]

        logging.info(f"Iniciando scraping.")
        await asyncio.gather(*tasks)

    logging.info("Pipeline concluído com sucesso.")


if __name__ == "__main__":
    asyncio.run(main())