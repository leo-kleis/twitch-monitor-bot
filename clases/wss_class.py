import logging
import websockets
import recurso.utils as utils

# Configuración del logger específico para WebSocketClient
LOGGER = logging.getLogger("WSC")
LOGGER.setLevel(logging.INFO)

class WebSocketClient:
    def __init__(self, oauth_token, username, channel, userbots, user_colors, user_followers):
        self.oauth_token = oauth_token
        self.username = username
        self.channel = channel
        self.uri = "wss://irc-ws.chat.twitch.tv:443"
        self.websocket = None
        self.joined_users = set()  # Almacena usuarios conectados
        self.logger = LOGGER
        self.running = False
        self.userbots = userbots
        self.user_colors = user_colors
        self.user_followers = user_followers

    async def connect(self):
        """Conectar al websocket de Twitch IRC"""
        try:
            self.websocket = await websockets.connect(self.uri)
            
            # Autenticación con el servidor de IRC
            await self.websocket.send(f"PASS oauth:{self.oauth_token}")
            await self.websocket.send(f"NICK {self.username}")
            await self.websocket.send("CAP REQ :twitch.tv/membership")  # Habilita eventos JOIN/PART
            await self.websocket.send(f"JOIN #{self.channel}")
            
            self.logger.info(f"\033[1m\033[42m\033[30m   WebSocket Conectado          \033[0m")
            self.running = True
            return True
        except Exception as e:
            self.logger.error(f"Error al conectar: {e}")
            return False

    async def listen(self):
        """Escuchar mensajes del websocket"""
        if not self.websocket:
            self.logger.error("No hay conexión websocket establecida")
            return

        try:
            while self.running:
                message = await self.websocket.recv()

                # Manejo de PING/PONG
                if message.startswith("PING"):
                    await self.websocket.send(f"PONG {message.split()[1]}")

                # Manejo de múltiples eventos JOIN/PART
                for line in message.split("\r\n"):
                    if "JOIN" in line:
                        try:
                            user = line.split("!")[0][1:]  # Extrae el usuario
                            if user not in self.userbots:
                                self.joined_users.add(user)
                                user_color = utils.get_user_color(user, self.user_colors)
                                
                                if user in self.user_followers:
                                    follow_status = self.user_followers[user]
                                else:
                                    follow_status = "New"

                                self.logger.info(f"{user_color}{user}\033[0m ({follow_status}) \033[32mse unió al canal\033[0m")
                        except IndexError:
                            pass

                    elif "PART" in line:
                        try:
                            user = line.split("!")[0][1:]
                            if user in self.joined_users:
                                self.joined_users.remove(user)
                                user_color = utils.get_user_color(user, self.user_colors)

                                if user in self.user_followers:
                                    follow_status = self.user_followers[user]
                                else:
                                    follow_status = "New"

                                self.logger.info(f"{user_color}{user}\033[0m ({follow_status}) \033[31msalió del canal\033[0m")
                        except IndexError:
                            pass
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("Conexión websocket cerrada")
        except Exception as e:
            self.logger.error(f"Error en el websocket: {e}")
        finally:
            self.running = False
            self.websocket = None

    async def disconnect(self):
        """Desconectar del websocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.logger.info("Desconectado del websocket")

    def get_connected_users(self):
        """Obtener la lista de usuarios conectados"""
        return list(self.joined_users)
