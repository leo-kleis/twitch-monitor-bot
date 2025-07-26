import os
import asyncio
import logging
import twitchio
import recurso.gui.utils_gui as utils_gui
from bd import Toker
from twitchio import eventsub
from dotenv import load_dotenv
from twitchio.ext import commands

load_dotenv()
CLIENT_ID_APP = os.getenv("CLIENT_ID_APP")
CLIENT_SECRET_APP = os.getenv("CLIENT_SECRET_APP")
BOT_ID = os.getenv("BOT_ID")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")

class Bot(commands.Bot):
    def __init__(self, *, token_database, userbots, user_data_twitch, msg_type, message_callback=None) -> None:
        self.token_manager = Toker(token_database)
        super().__init__(
            client_id=str(CLIENT_ID_APP),
            client_secret=str(CLIENT_SECRET_APP),
            bot_id=str(BOT_ID),
            prefix="?"
        )
        self.userbots = userbots
        self.user_data_twitch = user_data_twitch
        self.msg_type = msg_type
        self.message_callback = message_callback
        self.LOGGER = logging.getLogger("BOT")
        self.LOGGER.setLevel(logging.INFO)

    async def setup_hook(self) -> None:
        # Importacion local para evitar referencias circulares
        from clases.twitch_zk.component_class import MyComponent
        
        # Agregar nuestro componente que contiene nuestros comandos...
        await self.add_component(MyComponent(self))

        # Suscribirse para leer el chat (event_message) de nuestro canal como el bot...
        # Esto crea y abre un websocket a Twitch EventSub...
        subscription = eventsub.ChatMessageSubscription(broadcaster_user_id=BROADCASTER_ID, user_id=BOT_ID)
        await self.subscribe_websocket(payload=subscription)

        # Suscribirse y escuchar cuando alguien sigue al canal...
        subscription = eventsub.ChannelFollowSubscription(broadcaster_user_id=BROADCASTER_ID, moderator_user_id=BOT_ID)
        await self.subscribe_websocket(payload=subscription)

        # Suscribirse y escuchar cuando alguien canjea un punto de canal...
        subscription = eventsub.ChannelPointsRedeemAddSubscription(broadcaster_user_id=BROADCASTER_ID)
        await self.subscribe_websocket(payload=subscription, as_bot=False, token_for=BROADCASTER_ID)

        # Suscribirse y escuchar cuando alguien hace un raid...
        subscription = eventsub.ChannelRaidSubscription(to_broadcaster_user_id=BROADCASTER_ID)
        await self.subscribe_websocket(payload=subscription, as_bot=False, token_for=BROADCASTER_ID)

        # Suscribirse y escuchar cuando alguien modera el canal...
        subscription = eventsub.ChannelModerateV2Subscription(broadcaster_user_id=BROADCASTER_ID, moderator_user_id=BOT_ID)
        await self.subscribe_websocket(payload=subscription)

        subscription = eventsub.ChannelUpdateSubscription(broadcaster_user_id=BROADCASTER_ID)
        await self.subscribe_websocket(payload=subscription, as_bot=False, token_for=BROADCASTER_ID)

    ######################################################################################################################

    # Metodo auxiliar para la funcionalidad original de add_token
    async def add_token_internal(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        return await super().add_token(token, refresh)

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Delegar a nuestro token_manager
        return await self.token_manager.add_token(token, refresh, self)

    async def load_tokens(self, path: str | None = None) -> None:
        # Delegar a nuestro token_manager
        await self.token_manager.load_tokens(self)

    async def setup_database(self) -> None:
        # Delegar a nuestro token_manager
        await self.token_manager.setup_database()
    
    ######################################################################################################################

    async def get_viewer_count(self) -> None:
        last_viewer_count = None
        same_count_counter = 0
        while True:
            try:
                stream = await self.fetch_streams(user_ids=[str(BROADCASTER_ID)])
                if stream == []:
                    # Modo GUI: actualizar etiqueta y enviar mensaje
                    if self.message_callback:
                        self.message_callback("Offline", "viewer_count")
                    else:
                        # Sin GUI, solo usar logger
                        self.LOGGER.info("\033[1m\033[41mStream offline\033[0m")
                else:
                    viewer_count = stream[0].viewer_count
                    if viewer_count == last_viewer_count:
                        same_count_counter += 1
                    else:
                        same_count_counter = 0
                        last_viewer_count = viewer_count
                    
                    # Siempre enviar el contador al UI si estamos en modo GUI
                    if self.message_callback:
                        self.message_callback(str(viewer_count), "viewer_count")
                    
                    # Solo mostrar en log si hay cambios o pocas repeticiones
                    if same_count_counter < 3:
                        if not self.message_callback:
                            self.LOGGER.info(f"\033[1mNumero de espectadores actuales: \033[31m{viewer_count}\033[0m")
            except Exception as e:
                self.LOGGER.warning("Error al obtener el numero de espectadores: %s", e)
            
            await asyncio.sleep(180)
    
    async def event_ready(self) -> None:
        utils_gui.log_and_callback(self, f"\033[1m\033[42m\033[30m   BOT Conectado   \033[0m", self.msg_type)
        channel_info = await self.fetch_channels([str(BROADCASTER_ID)])
        if self.message_callback:
            self.message_callback(f"{channel_info[0].title}|{channel_info[0].game_name}", "stream_info")
        else:
            self.LOGGER.info(f"\033[32m{channel_info[0].title}\033[0m | \033[32m{channel_info[0].game_name}\033[0m")

        asyncio.create_task(self.get_viewer_count())
    
    async def event_command_error(self, payload):
        """Maneja errores en la ejecucion de comandos"""
        context = payload.context
        error = payload.error
        
        # Registra el error en los logs
        self.LOGGER.error(f"Error en comando {context.command.name if context.command else 'desconocido'}: {error}")
        
        # Importar excepciones correctas
        from twitchio.ext.commands.exceptions import CommandNotFound, MissingRequiredArgument, GuardFailure
        
        if isinstance(error, CommandNotFound):
            # Ignorar silenciosamente comandos no encontrados
            return
        elif isinstance(error, MissingRequiredArgument):
            await context.send(f"@{context.author.name} Faltan argumentos para el comando.")
        elif isinstance(error, GuardFailure):
            # Se dispara cuando fallan los decoradores como @commands.is_broadcaster()
            await context.send(f"@{context.author.name} No tienes permiso para usar este comando.")
        else:
            # Otros errores inesperados
            self.LOGGER.error(f"Error no manejado: {error}")
        return
