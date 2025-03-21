import asqlite
import sqlite3
import twitchio
import logging

LOGGER = logging.getLogger("TokenDB")

class Toker:
    def __init__(self, pool: asqlite.Pool):
        self.token_database = pool
    
    async def add_token(self, token: str, refresh: str, bot_instance) -> twitchio.authentication.ValidateTokenPayload:
        # Llamar al método add_token de la instancia de bot para agregar los tokens internamente
        resp: twitchio.authentication.ValidateTokenPayload = await bot_instance.add_token_internal(token, refresh)

        # Almacenar los tokens en la base de datos SQLite
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.debug("Token agregado a la base de datos para el usuario: %s", resp.user_id)
        return resp

    async def load_tokens(self, bot_instance) -> None:
        # Cargar tokens desde la base de datos
        async with self.token_database.acquire() as connection:
            rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        for row in rows:
            await bot_instance.add_token_internal(row["token"], row["refresh"])

    async def setup_database(self) -> None:
        # Crear la tabla de tokens, si no existe
        query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
        async with self.token_database.acquire() as connection:
            await connection.execute(query)