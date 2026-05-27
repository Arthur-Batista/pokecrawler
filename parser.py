from bs4 import BeautifulSoup, Tag
from fetcher import get_image_url, download_image
import httpx
import logging


def visible(tag) -> bool:
    style = tag.get("style", "")
    return "display:none" not in style.replace(" ", "")


def get_element(
    soup: BeautifulSoup | Tag,
    selector: str,
    required: bool = False
) -> Tag | None:

    element = soup.select_one(selector)

    if required and element is None:
        raise ValueError(f"Elemento não encontrado: '{selector}'")

    return element


def get_name(soup: BeautifulSoup) -> str | None:
    tag = soup.find("big")
    return tag.text.strip() if tag else None


def get_category(soup: BeautifulSoup) -> str | None:
    tag = soup.find("span")
    return tag.text.strip() if tag else None


from bs4 import BeautifulSoup

def get_pokedex_number(soup: BeautifulSoup) -> int | None:
    tag = soup.find(title="List of Pokémon by National Pokédex number")
    
    if not tag:
        return None
        
    raw_number = tag.text.strip()
    
    if raw_number and "?" not in raw_number:
        try:
            return int(raw_number.replace("#", ""))
        except ValueError:
            return None
            
    return None


def get_types(soup: BeautifulSoup) -> list:

    elements = soup.select('[title*="type"]')
    types = []

    for element in elements:
        tipo = element.get_text(strip=True)

        if tipo == "Unknown":
            break
        if tipo in types:
            break

        types.append(tipo)

    return types


def get_skills(soup: BeautifulSoup) -> list[dict]:

    skills = []

    abilities_section = soup.find("b", string="Abilities")

    if not abilities_section:
        return skills

    abilities_td = abilities_section.find_parent("td")

    for td in abilities_td.select("td"):

        if not visible(td):
            continue

        link = td.find("a")

        if not link:
            continue

        ability = link.get_text(strip=True)
        text = td.get_text(" ", strip=True)
        hidden = "Hidden Ability" in text

        skills.append({"name": ability, "hidden": hidden})

    return skills


def get_evolution(soup: BeautifulSoup, name: str) -> dict:

    evolution_span = soup.find("span", id="Evolution")

    if not evolution_span:
        return {"previous": None, "next": []}

    all_tables = evolution_span.find_all_next("table")
    stages = {}

    for table in all_tables:

        small_tags = table.find_all("small")
        stage = None

        for small in small_tags:
            text = small.get_text(strip=True)
            if "Unevolved" in text:
                stage = 0; break
            elif "First Evolution" in text:
                stage = 1; break
            elif "Second Evolution" in text:
                stage = 2; break
            elif "Third Evolution" in text:
                stage = 3; break

        if stage is None:
            continue

        trs = table.find_all("tr")
        if not trs:
            continue

        last_tr = trs[-1]

        a_tag = last_tr.find(
            "a", href=lambda h: h and "Pok%C3%A9mon" in h
        )

        if not a_tag:
            a_tag = last_tr.find("a", class_="mw-selflink")

        if not a_tag:
            continue

        poke_name = a_tag.get_text(strip=True)
        if poke_name:
            stages[poke_name] = stage

    if not stages:
        return {"previous": None, "next": []}

    if name in stages:
        current_stage = stages[name]
    else:
        min_stage = min(stages.values())
        if min_stage == 1:
            current_stage = 0
        else:
            return {"previous": None, "next": []}

    previous_list = [n for n, s in stages.items() if s == current_stage - 1]
    next_list     = [n for n, s in stages.items() if s == current_stage + 1]

    return {
        "previous": previous_list[0] if len(previous_list) == 1 else None,
        "next": next_list
    }


def get_stats(soup: BeautifulSoup) -> dict:

    base_stats_span = soup.find("span", id="Base_stats")

    if not base_stats_span:
        return {}

    stats_table = base_stats_span.find_next("table")

    if not stats_table:
        return {}

    stats = {}
    stat_names = {
        "HP": "HP", "Attack": "Attack", "Defense": "Defense",
        "Sp. Atk": "Sp. Atk", "Sp. Def": "Sp. Def", "Speed": "Speed"
    }

    for th in stats_table.find_all("th"):
        divs = th.find_all("div", recursive=False)

        if len(divs) < 2:
            continue

        stat_label = divs[0].get_text(strip=True).rstrip(":")
        stat_value = divs[1].get_text(strip=True)

        if stat_label in stat_names and stat_value.isdigit():
            stats[stat_names[stat_label]] = int(stat_value)

    return stats


async def scrap_pokemon_info(client: httpx.AsyncClient, soup: BeautifulSoup) -> dict | None:
    try:
        info_card = get_element(soup, "table.roundy.infobox", required=True)
        name = get_name(soup)
        image_url = get_image_url(soup)

        pokemon_data = {
            "name": name,
            "category": get_category(info_card),
            "pokedex_number": get_pokedex_number(info_card),
            "types": get_types(info_card),
            "evolution": get_evolution(soup, name),
            "abilities": get_skills(info_card),
            "stats": get_stats(soup),
            "image_path": await download_image(client, image_url, name) if image_url else None
        }

        return pokemon_data

    except Exception as e:
        logging.error(f"Erro ao parsear dados: {e}")
        return None
