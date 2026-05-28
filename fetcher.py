import asyncio
import aiofiles
import os
import logging
import httpx
from bs4 import BeautifulSoup
from settings import BASE_URL, HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, IMAGES_DIR


async def get_soup(
    client: httpx.AsyncClient,
    url: str,
    max_retries: int = 3
) -> BeautifulSoup:

    for attempt in range(max_retries):
        try:
            response = await client.get(url)
            response.raise_for_status() 
            await asyncio.sleep(REQUEST_DELAY)
            
            return BeautifulSoup(response.text, "html.parser")
            
        except httpx.HTTPError as e:
            
            if attempt == max_retries - 1:
                logging.error(f"Falha ao acessar {url} após {max_retries} tentativas: {e}")
                raise e
            
            tempo_espera = 2 ** attempt
            await asyncio.sleep(tempo_espera)


def get_pokemon_links(
    soup: BeautifulSoup,
) -> list[str]:

    tables = soup.find_all("table", class_="roundy")

    if not tables:
        return []

    pokemon_links = []

    for table in tables:
        for link in table.find_all("a"):
            href = link.get("href")

            if not href:
                continue
            if "Pok" not in href:
                continue
            if href in pokemon_links:
                continue

            pokemon_links.append(href)

    return pokemon_links



async def download_image(
    client: httpx.AsyncClient, 
    url: str, 
    name: str
) -> str | None:

    os.makedirs(IMAGES_DIR, exist_ok=True)

    ext = url.rsplit(".", 1)[-1]
    path = f"{IMAGES_DIR}/{name}.{ext}"

    try:
        response = await client.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        async with aiofiles.open(path, "wb") as f:
            await f.write(response.content)

        return path

    except Exception as e:
        logging.error(f"Erro ao baixar imagem de {name}: {e}")
        return None


def get_image_url(soup: BeautifulSoup) -> str | None:

    info_card = soup.select_one("table.roundy.infobox")

    if not info_card:
        return None

    img = info_card.select_one("img")

    if not img:
        return None

    src = img.get("src", "")

    if "/thumb/" in src:
        src = src.replace("/thumb/", "/")
        src = src.rsplit("/", 1)[0]

    if src.startswith("//"):
        src = "https:" + src

    return src
