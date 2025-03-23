import os
import logging
import twitchio # v3.0.0b3
import recurso.utils as utils
from clases.gemi_class import Gemi
from twitchio.ext import commands
from dotenv import load_dotenv

LOGGER: logging.Logger = logging.getLogger("COMPONENT")
LOGGER.setLevel(logging.INFO)

load_dotenv()
BROADCASTER_NAME = os.getenv("BROADCASTER")
BOT_NAME = os.getenv("BOT")
charla = None

# Al final del archivo
def save_active_chat_history():
    """Guarda el historial del chat activo si existe y tiene mensajes"""
    global charla
    if charla is not None and hasattr(charla, 'get_message_count'):
        if charla.get_message_count() > 0:
            LOGGER.info("Guardando historial de chat activo...")
            charla.terminate(False)
    return

class MyComponent(commands.Component):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        usuario = payload.chatter
        if usuario.name == BOT_NAME:
            LOGGER.info(f"\033[95m{usuario.name}\033[0m (BOTME): {payload.text}")
        elif usuario.name == BROADCASTER_NAME:
            user_color = utils.get_user_color(usuario.name, self.bot.user_colors)
            LOGGER.info(f"{user_color}{usuario.name}\033[0m (BROADCASTER): {payload.text}")
        elif usuario.name in self.bot.userbots:
            LOGGER.info(f"\033[93m{usuario.name} (BOT): {payload.text}")
        else:
            user_color = utils.get_user_color(usuario.name, self.bot.user_colors)
            follow = await usuario.follow_info()

            if follow is None:
                follow_status = "Visita"
                self.bot.user_followers[usuario.name] = follow_status
            else:
                follow_status = f"{follow.followed_at.strftime('%d-%m-%Y')}"
                self.bot.user_followers[usuario.name] = follow_status
            
            roles = utils.rol_user(usuario)
            LOGGER.info(f"{roles}{user_color}{usuario.name}\033[0m ({follow_status}): {payload.text}")


    @commands.Component.listener()
    async def event_follow(self, payload: twitchio.ChannelFollow) -> None:
        # Evento enviado cuando alguien sigue al canal...
        usuario = payload.user.name
        fecha_creacion = payload.followed_at.strftime('%d-%m-%Y')
        self.bot.user_followers[usuario] = fecha_creacion
        LOGGER.info(f"\033[1m\033[30m{usuario}\033[0m\033[1m ha seguido al canal!\033[0m")
    
    
    @commands.Component.listener()
    async def event_custom_redemption_add(self, payload: twitchio.ChannelPointsRedemptionAdd) -> None:
        user_color = utils.get_user_color(payload.user.name, self.bot.user_colors)
        # Evento enviado cuando alguien canjea un punto de canal...
        LOGGER.info(f"{user_color}\033[1m{payload.user.name}\033[0m\033[1m ha canjeado \033[1m\033[30m{payload.reward.title}\033[0m\033[1m | \033[1m\033[30m{payload.reward.cost}\033[0m\033[1m Puntos\033[0m")


    @commands.Component.listener()
    async def event_raid(self, payload: twitchio.ChannelRaid) -> None:
        # Evento enviado cuando alguien canjea un punto de canal...
        LOGGER.info(f"\033[1m\033[30m{payload.from_broadcaster}\033[0m\033[1m ha hecho un raid con {payload.viewer_count} viewers\033[0m")
    
    
    @commands.Component.listener()
    async def event_mod_action(self, payload: twitchio.ChannelModerate) -> None:
        # Evento enviado cuando alguien modera el canal...
        if payload.action == "delete":
            LOGGER.info(f"\033[1m\033[30m{payload.moderator}\033[0m\033[1m ha eliminado el mensaje \033[1m\033[31m\"{payload.delete.text}\"\033[0m\033[1m de \033[1m\033[30m{payload.delete.user}\033[0m")
        elif payload.action == "raid":
            LOGGER.info(f"\033[1m\033[30m{payload.moderator}\033[0m\033[1m ha hecho un raid con {payload.raid.viewer_count} viewers\033[0m")
        
        
    @commands.Component.listener()
    async def event_channel_update(self, payload: twitchio.ChannelUpdate) -> None:
        # Evento enviado cuando alguien modera el canal...
        LOGGER.info(f"\033[1m{payload.title} - {payload.category_name}\033[0m")


    @commands.command(aliases=["Hola", "Holiwi", "hey"])
    async def hi(self, ctx: commands.Context) -> None:
        """Comando simple que dice hola!

        !hi, !Hola, !Holiwi, !hey
        """
        await ctx.reply(f"¡Hola {ctx.chatter.mention}!")


    @commands.command(aliases=["corte"])
    async def clip(self, ctx: commands.Context) -> None:
        """Comando que crea un clip para luego ser editado y sin no es el caso
        crea un clip de los ultimos 30 segundos.
    
        !clip, !corte
        """
        try:
            corte = await ctx.chatter.create_clip(has_delay=False, token_for=self.bot.user)

            edit_url = corte.edit_url  # URL para editar el clip
            
            await ctx.send(f"¡Clip creado! Editar: {edit_url}")
        except Exception as e:
            LOGGER.error(f"Error al crear clip: {str(e)}")


    @commands.command(aliases=["ds"])
    async def discord(self, ctx: commands.Context) -> None:
        """Comando que envía la invitación de discord.

        !discord, !ds
        """
        await ctx.send("Link de discord: discord.gg/UwbUxbj - Igualmente también pueden copiar el código: UwbUxbj")


    @commands.group(invoke_fallback=True, aliases=["social", "rrss"])
    async def socials(self, ctx: commands.Context) -> None:
        """Comando de grupo para nuestros enlaces sociales.

        !socials
        """
        await ctx.send("discord.gg/UwbUxbj, tiktok.com/@kleis.arc, facebook.com/TioArcW")

    @socials.command(name="discord", aliases=["ds"])
    async def socials_discord(self, ctx: commands.Context) -> None:
        """Subcomando de socials que envía solo nuestra invitación de discord.

        !socials discord
        """
        await ctx.send("Link de discord: discord.gg/UwbUxbj - Igualmente también pueden copiar el código: UwbUxbj")
        
    @socials.command(name="tiktok", aliases=["tt"])
    async def socials_tiktok(self, ctx: commands.Context) -> None:
        """Subcomando de socials que envía solo nuestro enlace de tiktok.

        !socials tiktok
        """
        await ctx.send("Link de tiktok: tiktok.com/@kleis.arc")
        
    @socials.command(name="facebook", aliases=["fb"])
    async def socials_facebook(self, ctx: commands.Context) -> None:
        """Subcomando de socials que envía solo nuestro enlace de facebook.

        !socials facebook
        """
        await ctx.send("Link de facebook: facebook.com/TioArcW")


    #example commands.guard
    @commands.command(aliases=["repeat"])
    @commands.is_moderator() #? Solo para moderadores
    async def say(self, ctx: commands.Context, *, content: str) -> None:
        """Comando solo para moderadores, que repite lo que dices.

        !say hello world, !repeat I am cool LUL
        """
        await ctx.send(content)
        
        
    @commands.command(aliases=["settitle"])
    @commands.is_moderator()  #? Solo para moderadores
    async def title(self, ctx: commands.Context, *, tittle: str) -> None:
        """Comando solo para moderadores, que cambia el titulo del stream.

        !title Nuevo titulo del stream
        """
        await ctx.channel.modify_channel(title=tittle)
        await ctx.send(f"Titulo cambiado a: {tittle}")
        
        
    @commands.command(aliases=["setgame"])
    @commands.is_moderator()  #? Solo para moderadores
    async def game(self, ctx: commands.Context, *, game: str) -> None:
        """Comando solo para moderadores, que cambia el juego del stream.

        !game Nuevo juego del stream
        """
        game_id = utils.name_game(game)
        if game_id is not None:
            await ctx.channel.modify_channel(game_id=game_id)
            await ctx.send(f"Juego cambiado a: {game}")
        else:
            await ctx.send(f"Juego no encontrado: {game} - Revisa la lista de juegos disponibles con ?getgame o ?games.")
    
    
    @commands.command(aliases=["getgame"])
    @commands.is_moderator()  #? Solo para moderadores
    async def games(self, ctx: commands.Context) -> None:
        """Comando que envía la lista de juegos disponibles.

        !getgame, !games
        """
        games = utils.get_games()
        await ctx.send(f"Lista de categorias disponibles para cambiar con ?setgame o ?game: {', '.join(games)}")
        await ctx.send("No importa si esta en mayusculas o minusculas, solo importa que sea el nombre correcto.")
    
    @commands.command(aliases=["activar", "on"])
    @commands.is_broadcaster()
    async def activate(self, ctx: commands.Context, maximo: int = 20) -> None:
        """Comando solo para el broadcaster, que activa Gemi IA con límite configurable (mínimo 5)."""
        global charla
        
        # Verificar si ya existe una instancia activa
        if charla is not None:
            if charla.is_active():
                await ctx.reply("Gemi ya está activa. Desactívala primero con ?off antes de iniciar una nueva instancia.")
                return
            else:
                # Si existe pero no está activa, la terminamos correctamente
                charla.terminate(False)
                charla = None
        
        # Verificar el valor mínimo
        if maximo < 5:
            await ctx.reply("Error: El límite de mensajes debe ser al menos 5.")
            return
        
        model = await utils.iniciar_gemi(self, ctx)
        
        charla = Gemi(model, max_messages=maximo, bot=self.bot)
        await ctx.reply(f"Gemi ON con límite de {maximo} mensajes.")
        
    @commands.command(aliases=["desactivar", "off"])
    @commands.is_broadcaster()  #! Solo para moderadores
    async def deactivate(self, ctx: commands.Context) -> None:
        """Comando solo para el broadcaster, que desactiva Gemi IA.

        !deactivate, !desactivar
        """
        global charla
        charla.terminate(False)
        charla = None
        await ctx.reply("Gemi OFF.")
    
    @commands.command(aliases=["ai", "resp"])
    @commands.is_elevated()
    async def ia(self, ctx: commands.Context, *, message: str) -> None:
        """Comando para interactuar con la IA."""
        global charla
        if charla is not None:
            if not charla.is_active():
                await ctx.send("Gemi ha alcanzado el límite de mensajes.")
                charla = None
                return
            usuario = ctx.chatter.name
            # Pasar el contexto para que el modelo pueda ejecutar comandos
            response = charla.send_message(usuario, message, ctx=ctx)
            
            if not charla.is_active():
                await ctx.send(response)
                await ctx.send("Gemi ha alcanzado el límite de mensajes y se ha desactivado.")
                charla = None
                return
                
            await ctx.send(response)
        else:
            await ctx.send("Gemi no esta activada.")