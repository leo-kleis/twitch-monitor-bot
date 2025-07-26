import os
import sys
import asyncio
import logging
import asqlite
import twitchio # v3.0.0b3
import subprocess
import recurso.twitch_zk.utils as utils
from dotenv import load_dotenv
from clases.twitch_zk import Bot
from clases.twitch_zk import WebSocketClient
from recurso.com_pross import command_processor
from clases.twitch_zk import save_active_chat_history

LOGGER: logging.Logger = logging.getLogger("MAIN")
LOGGER.setLevel(logging.WARNING)

file_path_userbots_twitch = os.path.join(os.path.dirname(__file__), 'recurso/twitch_zk/data', 'userbots.txt')
with open(file_path_userbots_twitch, 'r') as file:
    userbots = [line.strip() for line in file]

file_path_user_data_twitch = os.path.join(os.path.dirname(__file__), 'bd/data', 'zkleisbotv_twitch.db')
user_data_twitch = utils.load_user_data_twitch(file_path_user_data_twitch)

def main() -> None:
    twitchio.utils.setup_logging(level=logging.WARNING)  # Nivel de registro global

    # Crear ruta para la base de datos en la carpeta bd
    db_path_twitch = os.path.join(os.path.dirname(__file__), 'bd/data', 'tokens_twitch.db')
    
    load_dotenv()
    #* Configuracion del websocket usando "Twitch Token Generator"
    oauth_token = os.getenv("TTG_BOT_TOKEN")
    bot_name = os.getenv("BOT")
    broadcaster_name = os.getenv("BROADCASTER")
    
    async def runner() -> None:
        # Crear un evento para señalar la terminacion del programa
        shutdown_event = asyncio.Event()
        
        async with asqlite.create_pool(db_path_twitch) as tdb:
            bot = Bot(
                token_database=tdb,
                userbots=userbots,
                user_data_twitch=user_data_twitch,
                msg_type=None,
                message_callback=None
            )
            
            # Inicializar el bot y el websocket
            await bot.setup_database()
            
            # Inicializar el cliente websocket
            ws_client = WebSocketClient(
                oauth_token,
                bot_name,
                broadcaster_name,
                userbots,
                user_data_twitch,
                msg_type=None,
                message_callback=None
            )
            
            # Iniciar conexion websocket
            connection_success = await ws_client.connect()
            
            # Crear las tareas
            tasks = []
            tasks.append(asyncio.create_task(command_processor(shutdown_event, file_path_user_data_twitch, user_data_twitch)))
            tasks.append(asyncio.create_task(bot.start()))
            
            if connection_success:
                tasks.append(asyncio.create_task(ws_client.listen()))
            else:
                LOGGER.warning("No se pudo conectar al websocket. Ejecutando solo el bot.")
            
            # Esperar a que se active el evento de cierre o a que se completen las tareas
            await shutdown_event.wait()
            
            # Cancelar todas las tareas que aún estén en ejecucion
            for task in tasks:
                task.cancel()
            # Esperar a que se completen todas las cancelaciones
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Apagando debido a KeyboardInterrupt...")    
    finally:
        save_active_chat_history()
        utils.save_user_data_twitch(file_path_user_data_twitch, user_data_twitch)
        try:
            subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(__file__), 'recurso', 'twitch_zk', 'follow', 'listadofollow.py')],
                check=True
            )
            print("Listado generado correctamente.")
        except Exception as e:
            print(f"Error al ejecutar listadofollow.py: {e}")
            print("Programa finalizado correctamente.")
        
if __name__ == "__main__":
    main()