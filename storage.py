import json
import sqlite3
from settings import DB_FILE


def get_uploaded_names(filename: str = DB_FILE) -> set:
    try:
        with sqlite3.connect(filename) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM pokemons")
            return {row[0] for row in cursor.fetchall()}
    except:
        return set()


def save_sqlite(
    pokemons: list[dict],
    filename: str = DB_FILE
):

    with sqlite3.connect(filename) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pokemons (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                pokedex_number     INTEGER,
                name               TEXT NOT NULL,
                category           TEXT,
                types              TEXT,
                previous_evolution TEXT,
                next_evolution     TEXT,
                abilities          TEXT,
                hp                 INTEGER,
                attack             INTEGER,
                defense            INTEGER,
                sp_atk             INTEGER,
                sp_def             INTEGER,
                speed              INTEGER,
                image_path         TEXT
            )
        """)

        for pokemon in pokemons:

            pokedex_number = pokemon.get("pokedex_number")

            evolution = pokemon.get("evolution", {})
            next_evolutions = evolution.get("next", [])
            stats = pokemon.get("stats", {})

            conn.execute("""
                INSERT INTO pokemons (
                    pokedex_number, name, category, types,
                    previous_evolution, next_evolution, abilities,
                    hp, attack, defense, sp_atk, sp_def, speed, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pokedex_number,
                pokemon.get("name"),
                pokemon.get("category"),
                ", ".join(pokemon.get("types", [])),
                evolution.get("previous"),
                ", ".join(next_evolutions) if next_evolutions else None,
                json.dumps(pokemon.get("abilities", []), ensure_ascii=False),
                stats.get("HP"),
                stats.get("Attack"),
                stats.get("Defense"),
                stats.get("Sp. Atk"),
                stats.get("Sp. Def"),
                stats.get("Speed"),
                pokemon.get("image_path")
            ))

        conn.commit()