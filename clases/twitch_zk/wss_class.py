import logging
import websockets
import recurso.twitch_zk.utils as utils

# Configuración del logger específico para WebSocketClient
LOGGER = logging.getLogger("WSC")
LOGGER.setLevel(logging.INFO)

class WebSocketClient:
    def __init__(self, oauth_token, username, channel, userbots, user_data_twitch):
        self.oauth_token = oauth_token
        self.username = username
        self.channel = channel
        self.uri = "wss://irc-ws.chat.twitch.tv:443"
        self.websocket = None
        self.joined_users = set()  # Almacena usuarios conectados
        self.running = False
        self.userbots = userbots
        self.user_data_twitch= user_data_twitch

    async def connect(self):
        """Conectar al websocket de Twitch IRC"""
        try:
            self.websocket = await websockets.connect(self.uri)
            
            # Autenticación con el servidor de IRC
            await self.websocket.send(f"PASS oauth:{self.oauth_token}")
            await self.websocket.send(f"NICK {self.username}")
            await self.websocket.send("CAP REQ :twitch.tv/membership")  # Habilita eventos JOIN/PART
            await self.websocket.send("CAP REQ :twitch.tv/commands")    # Habilita eventos como CLEARCHAT
            await self.websocket.send("CAP REQ :twitch.tv/tags")        # Habilita etiquetas de mensajes           
            await self.websocket.send(f"JOIN #{self.channel}")
            
            LOGGER.info(f"\033[1m\033[42m\033[30m   WebSocket Conectado          \033[0m")
            self.running = True
            return True
        except Exception as e:
            LOGGER.error(f"Error al conectar: {e}")
            return False

    def _parse_tags(self, message):
        """Analiza las etiquetas IRC y las devuelve como diccionario"""
        tags_dict = {}
        if "@" in message:
            try:
                tags_part = message.split(" ", 1)[0]
                if tags_part.startswith("@"):
                    tags_part = tags_part[1:]  # Quitar @ inicial
                    
                # Separa las etiquetas y crea un diccionario
                for tag in tags_part.split(";"):
                    if "=" in tag:
                        key, value = tag.split("=", 1)
                        tags_dict[key] = value
            except Exception as e:
                LOGGER.error(f"Error al parsear etiquetas: {e}")
        return tags_dict

    async def listen(self):
        """Escuchar mensajes del websocket"""
        if not self.websocket:
            LOGGER.error("No hay conexión websocket establecida")
            return
    
        try:
            while self.running:
                message = await self.websocket.recv()
    
                # Manejo de PING/PONG
                if message.startswith("PING"):
                    await self.websocket.send(f"PONG {message.split()[1]}")
                    continue
    
                # Manejo de CLEARCHAT (ban, timeout, clear)
                if "CLEARCHAT" in message:
                    if "#" + self.channel in message:
                        tags_dict = self._parse_tags(message)
                        
                        # Determinar si es para un usuario específico o limpieza general
                        is_user_targeted = ":" in message.split("#" + self.channel + " :")
                        
                        if is_user_targeted:
                            # Ban o timeout a un usuario específico
                            user = message.split("#" + self.channel + " :")[1].strip()
                            
                            # Extraer información de moderación
                            ban_duration = tags_dict.get("ban-duration", None)
                            ban_reason = tags_dict.get("ban-reason", "").replace("\\s", " ")
                            
                            if ban_duration:
                                action_type = f"timeout por {ban_duration} segundos"
                                if ban_reason:
                                    action_type += f" - Razón: {ban_reason}"
                            else:
                                action_type = "ban permanente"
                                if ban_reason:
                                    action_type += f" - Razón: {ban_reason}"
                                    
                            LOGGER.info(f"\033[1m\033[43m\033[30m Usuario {user} recibió {action_type} \033[0m")
                        else:
                            # Limpieza completa del chat (/clear)
                            LOGGER.info(f"\033[1m\033[43m\033[30m Chat limpiado completamente \033[0m")
                
                # Manejo de CLEARMSG (eliminación de mensaje individual)
                elif "CLEARMSG" in message:
                    if "#" + self.channel in message:
                        tags_dict = self._parse_tags(message)
                        
                        # Extraer información del mensaje eliminado
                        login = tags_dict.get("login", "desconocido")
                        target_msg_id = tags_dict.get("target-msg-id", "")
                        
                        # Extraer el contenido del mensaje eliminado si está disponible
                        msg_content = ""
                        if ":" in message.split("#" + self.channel + " :"):
                            msg_content = message.split("#" + self.channel + " :")[1].strip()
                            msg_content = f" - Mensaje: '{msg_content}'"
                        
                        LOGGER.info(f"\033[1m\033[43m\033[30m Mensaje de {login} eliminado{msg_content} \033[0m")
                    
                # Manejo de múltiples eventos JOIN/PART
                for line in message.split("\r\n"):
                    if "JOIN" in line:
                        try:
                            user = line.split("!")[0][1:]  # Extrae el usuario
                            if user not in self.userbots:
                                self.joined_users.add(user)
                                if user in self.user_data_twitch:
                                    follow_status = self.user_data_twitch[user]["follow_date"]
                                else:
                                    follow_status = "New"
                                    self.user_data_twitch[user] = {
                                        "follow_date": follow_status,
                                        "color": utils.assign_random_color(),
                                        "nickname": ""
                                    }
                                user_color = self.user_data_twitch[user]["color"]
                                nickuser = self.user_data_twitch[user]["nickname"]
                                formatted_nick = f"[{nickuser}] " if nickuser else ""
                                LOGGER.info(f"{user_color}{user}\033[0m {formatted_nick}({follow_status}) \033[32mse unió al canal\033[0m")
                        except IndexError:
                            pass

                    elif "PART" in line:
                        try:
                            user = line.split("!")[0][1:]
                            if user in self.joined_users:
                                self.joined_users.remove(user)
                                if user in self.user_data_twitch:
                                    follow_status = self.user_data_twitch[user]["follow_date"]
                                else:
                                    follow_status = "New"
                                    self.user_data_twitch[user] = {
                                        "follow_date": follow_status,
                                        "color": utils.assign_random_color(),
                                        "nickname": ""
                                    }
                                user_color = self.user_data_twitch[user]["color"]
                                nickuser = self.user_data_twitch[user]["nickname"]
                                formatted_nick = f"[{nickuser}] " if nickuser else ""
                                LOGGER.info(f"{user_color}{user}\033[0m {formatted_nick}({follow_status}) \033[31msalió del canal\033[0m")
                        except IndexError:
                            pass
        except websockets.exceptions.ConnectionClosed:
            LOGGER.warning("Conexión websocket cerrada")
        except Exception as e:
            LOGGER.error(f"Error en el websocket: {e}")
        finally:
            self.running = False
            self.websocket = None

    async def disconnect(self):
        """Desconectar del websocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            LOGGER.info("Desconectado del websocket")

    def get_connected_users(self):
        """Obtener la lista de usuarios conectados"""
        return list(self.joined_users)