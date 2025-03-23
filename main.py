import os
import asyncio
import logging
import asqlite
import twitchio # v3.0.0b3
import recurso.utils as utils
from dotenv import load_dotenv
from clases.bot_class import Bot
from clases.wss_class import WebSocketClient
from clases.component_class import save_active_chat_history

LOGGER: logging.Logger = logging.getLogger("MAIN")
LOGGER.setLevel(logging.WARNING)

file_path_userbots = os.path.join(os.path.dirname(__file__), 'recurso/data', 'userbots.txt')
with open(file_path_userbots, 'r') as file:
    userbots = [line.strip() for line in file]

file_path_user_followers = os.path.join(os.path.dirname(__file__), 'recurso/data', 'user_followers.json')
user_followers = utils.load_user_followers(file_path_user_followers)

file_path_user_colors = os.path.join(os.path.dirname(__file__), 'recurso/data', 'user_colors.json')
user_colors = utils.load_user_colors(file_path_user_colors)

def main() -> None:
    twitchio.utils.setup_logging(level=logging.WARNING)  # Nivel de registro global

    # Crear ruta para la base de datos en la carpeta bd
    db_path = os.path.join(os.path.dirname(__file__), 'bd/data', 'tokens.db')
    
    load_dotenv()
    # Configuración del websocket
    oauth_token = os.getenv("TTG_BOT_TOKEN")
    bot_name = os.getenv("BOT")
    broadcaster_name = os.getenv("BROADCASTER")
    
    async def runner() -> None:
        async with asqlite.create_pool(db_path) as tdb, Bot(token_database=tdb, userbots=userbots, user_colors=user_colors, user_followers=user_followers) as bot:  
            # Inicializar el bot y el websocket
            await bot.setup_database()
            # Inicializar el cliente websocket
            ws_client = WebSocketClient(oauth_token, bot_name, broadcaster_name, userbots, user_colors, user_followers)
            # Iniciar conexión websocket
            connection_success = await ws_client.connect()
            if connection_success:
                # Ejecutar el bot y el websocket concurrentemente
                await asyncio.gather(
                    bot.start(),
                    ws_client.listen()
                )
            else:
                # Si la conexión websocket falla, ejecutar solo el bot
                LOGGER.warning("No se pudo conectar al websocket. Ejecutando solo el bot.")
                await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Apagando debido a KeyboardInterrupt...")
        save_active_chat_history()
    finally:
        utils.save_user_followers(file_path_user_followers, user_followers)
        utils.save_user_colors(file_path_user_colors, user_colors)

if __name__ == "__main__":
    main()