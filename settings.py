BASE_URL = "https://bulbapedia.bulbagarden.net"

POKEDEX_URL = (
    f"{BASE_URL}/wiki/"
    "List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"
)

HEADERS = {"User-Agent": "Mozilla/5.0"}

DB_FILE = "pokemons.db"
IMAGES_DIR = "images"

MAX_CONCURRENT = 20
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 0.3
