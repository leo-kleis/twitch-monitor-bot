import os
import asyncio
import logging
import asqlite
import twitchio # v3.0.0b3
import recurso.twitch_zk.utils as utils
from dotenv import load_dotenv
from clases.twitch_zk.bot_class import Bot
from clases.twitch_zk.wss_class import WebSocketClient
from clases.twitch_zk.component_class import save_active_chat_history

LOGGER: logging.Logger = logging.getLogger("MAIN")
LOGGER.setLevel(logging.WARNING)

file_path_userbots_twitch = os.path.join(os.path.dirname(__file__), 'recurso/twitch_zk/data', 'userbots.txt')
with open(file_path_userbots_twitch, 'r') as file:
    userbots = [line.strip() for line in file]

file_path_user_followers_twitch = os.path.join(os.path.dirname(__file__), 'recurso/twitch_zk/data', 'user_followers.json')
user_followers = utils.load_user_followers(file_path_user_followers_twitch)

file_path_user_colors_twitch = os.path.join(os.path.dirname(__file__), 'recurso/twitch_zk/data', 'user_colors.json')
user_colors_twitch = utils.load_user_colors(file_path_user_colors_twitch)

def main() -> None:
    twitchio.utils.setup_logging(level=logging.WARNING)  # Nivel de registro global

    # Crear ruta para la base de datos en la carpeta bd
    db_path_twitch = os.path.join(os.path.dirname(__file__), 'bd/data', 'tokens_twitch.db')
    
    load_dotenv()
    #* Configuración del websocket usando "Twitch Token Generator"
    oauth_token = os.getenv("TTG_BOT_TOKEN")
    bot_name = os.getenv("BOT")
    broadcaster_name = os.getenv("BROADCASTER")
    
    async def runner() -> None:
        async with asqlite.create_pool(db_path_twitch) as tdb:
            bot = Bot(
                token_database=tdb,
                userbots=userbots,
                user_colors=user_colors_twitch,
                user_followers=user_followers
            )
            
            # Inicializar el bot y el websocket
            await bot.setup_database()
            # Inicializar el cliente websocket
            ws_client = WebSocketClient(oauth_token, bot_name, broadcaster_name, userbots, user_colors_twitch, user_followers)
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
        utils.save_user_followers(file_path_user_followers_twitch, user_followers)
        utils.save_user_colors(file_path_user_colors_twitch, user_colors_twitch)

if __name__ == "__main__":
    main()