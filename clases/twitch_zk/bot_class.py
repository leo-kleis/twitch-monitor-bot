import os
import asyncio
import logging
import twitchio
from twitchio import eventsub
from bd.db_token import Toker
from twitchio.ext import commands
from dotenv import load_dotenv

LOGGER: logging.Logger = logging.getLogger("BOT")
LOGGER.setLevel(logging.INFO)

load_dotenv()
CLIENT_ID_APP = os.getenv("CLIENT_ID_APP")
CLIENT_SECRET_APP = os.getenv("CLIENT_SECRET_APP")
BOT_ID = os.getenv("BOT_ID")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")

class Bot(commands.Bot):
    def __init__(self, *, token_database, userbots, user_colors, user_followers) -> None:
        self.token_manager = Toker(token_database)
        super().__init__(
            client_id=CLIENT_ID_APP,
            client_secret=CLIENT_SECRET_APP,
            bot_id=BOT_ID,
            BROADCASTER_ID=BROADCASTER_ID,
            prefix="?",
        )
        self.userbots = userbots
        self.user_colors = user_colors
        self.user_followers = user_followers

    async def setup_hook(self) -> None:
        # Importación local para evitar referencias circulares
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

    # Método auxiliar para la funcionalidad original de add_token
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

    async def get_viewer_count(self) -> int:
        last_viewer_count = None
        same_count_counter = 0
        while True:
            try:
                stream = await self.fetch_streams(user_ids=[BROADCASTER_ID])
                if stream == []:
                    LOGGER.info("\033[1m\033[41mStream offline\033[0m")
                else:
                    viewer_count = stream[0].viewer_count
                    if viewer_count == last_viewer_count:
                        same_count_counter += 1
                    else:
                        same_count_counter = 0
                        last_viewer_count = viewer_count
                    
                    if same_count_counter < 3:
                        LOGGER.info(f"\033[1mNúmero de espectadores actuales: \033[31m{viewer_count}\033[0m", )
            except Exception as e:
                LOGGER.warning("Error al obtener el número de espectadores: %s", e)
            
            await asyncio.sleep(180)
    
    async def event_ready(self) -> None:
        LOGGER.info(f"\033[1m\033[42m\033[30m   BOT Conectado exitosamente   \033[0m")
        channel_info = await self.fetch_channels([BROADCASTER_ID])
        LOGGER.info(f"\033[32m{channel_info[0].title}\033[0m | \033[32m{channel_info[0].game_name}\033[0m")
        
        asyncio.create_task(self.get_viewer_count())
        
    async def event_command_error(context: commands.Context, error: Exception):
        return
