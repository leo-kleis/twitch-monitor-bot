import logging
import websockets
import recurso.twitch_zk.utils as utils
import recurso.gui.utils_gui as utils_gui

class WebSocketClient:
    def __init__(self, oauth_token, username, channel, userbots, user_data_twitch, msg_type, message_callback=None):
        self.oauth_token = oauth_token
        self.username = username
        self.channel = channel
        self.uri = "wss://irc-ws.chat.twitch.tv:443"
        self.websocket = None
        self.joined_users = set()  # Almacena usuarios conectados
        self.running = False
        self.userbots = userbots
        self.user_data_twitch = user_data_twitch
        self.message_callback = message_callback
        self.msg_type = msg_type
        self.LOGGER = logging.getLogger("WSC")
        self.LOGGER.setLevel(logging.INFO)

    async def connect(self):
        """Conectar al websocket de Twitch IRC"""
        try:
            self.websocket = await websockets.connect(self.uri)
            
            # Autenticacion con el servidor de IRC
            await self.websocket.send(f"PASS oauth:{self.oauth_token}")
            await self.websocket.send(f"NICK {self.username}")
            await self.websocket.send("CAP REQ :twitch.tv/membership")  # Habilita eventos JOIN/PART
            await self.websocket.send("CAP REQ :twitch.tv/commands")    # Habilita eventos como CLEARCHAT
            await self.websocket.send("CAP REQ :twitch.tv/tags")        # Habilita etiquetas de mensajes           
            await self.websocket.send(f"JOIN #{self.channel}")
            
            utils_gui.log_and_callback(self, f"\033[1m\033[42m\033[30m   WebSocket Conectado          \033[0m", self.msg_type)
            self.running = True
            return True
        except Exception as e:
            self.LOGGER.error(f"Error al conectar: {e}")
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
                self.LOGGER.error(f"Error al parsear etiquetas: {e}")
        return tags_dict

    async def listen(self):
        """Escuchar mensajes del websocket"""
        if not self.websocket:
            self.LOGGER.error("No hay conexion websocket establecida")
            return
    
        try:
            while self.running:
                message = await self.websocket.recv()
    
                # Manejo de PING/PONG
                if str(message).startswith("PING"):
                    await self.websocket.send(f"PONG {str(message).split()[1]}")
                    continue
    
                # Manejo de CLEARCHAT (ban, timeout, clear)
                if "CLEARCHAT" in str(message):
                    if "#" + self.channel in str(message):
                        tags_dict = self._parse_tags(str(message))
                        
                        # Determinar si es para un usuario especifico o limpieza general
                        is_user_targeted = ":" in str(message).split("#" + self.channel + " :")
                        
                        if is_user_targeted:
                            # Ban o timeout a un usuario especifico
                            user = str(message).split("#" + self.channel + " :")[1].strip()
                            
                            # Extraer informacion de moderacion
                            ban_duration = tags_dict.get("ban-duration", None)
                            ban_reason = tags_dict.get("ban-reason", "").replace("\\s", " ")
                            
                            if ban_duration:
                                action_type = f"timeout por {ban_duration} segundos"
                                if ban_reason:
                                    action_type += f" - Razon: {ban_reason}"
                            else:
                                action_type = "ban permanente"
                                if ban_reason:
                                    action_type += f" - Razon: {ban_reason}"
                                    
                            utils_gui.log_and_callback(self, f"\033[1m\033[43m\033[30m Usuario {user} recibio {action_type} \033[0m", self.msg_type)
                        else:
                            # Limpieza completa del chat (/clear)
                            utils_gui.log_and_callback(self, f"\033[1m\033[43m\033[30m Chat limpiado completamente \033[0m", self.msg_type)

                # Manejo de CLEARMSG (eliminacion de mensaje individual)
                elif "CLEARMSG" in str(message):
                    if "#" + self.channel in str(message):
                        tags_dict = self._parse_tags(str(message))
                        
                        # Extraer informacion del mensaje eliminado
                        login = tags_dict.get("login", "desconocido")
                        target_msg_id = tags_dict.get("target-msg-id", "")
                        
                        # Extraer el contenido del mensaje eliminado si esta disponible
                        msg_content = ""
                        if ":" in str(message).split("#" + self.channel + " :"):
                            msg_content = str(message).split("#" + self.channel + " :")[1].strip()
                            msg_content = f" - Mensaje: '{msg_content}'"

                        utils_gui.log_and_callback(self, f"\033[1m\033[43m\033[30m Mensaje de {login} eliminado{msg_content} \033[0m", self.msg_type)

                # Manejo de multiples eventos JOIN/PART
                for line in str(message).split("\r\n"):
                    if "JOIN" in line:
                        try:
                            user = line.split("!")[0][1:]  # Extrae el usuario
                            if user not in self.userbots:
                                self.joined_users.add(user)
                                user_id = utils.buscar_id_usuario(user)
                                follow_first_time = utils.verificar_follow_fecha(user_id) #? Entrega fecha o None
                                
                                if user in self.user_data_twitch:
                                    follow_status = self.user_data_twitch[user]["follow_date"] #? Entrega fecha o Visita o New o Renegado
                                    
                                    if follow_first_time == None and follow_status != "Visita" and follow_status != "New" and follow_status != "Renegado":
                                        follow_status = "Renegado"
                                        self.user_data_twitch[user]["follow_date"] = follow_status
                                else:
                                    if follow_first_time != None:
                                        follow_status = follow_first_time
                                    else:
                                        follow_status = "New"
                                        
                                    self.user_data_twitch[user] = {
                                        "id": user_id,
                                        "follow_date": follow_status,
                                        "color": utils.assign_random_color(),
                                        "nickname": ""
                                    }
                                user_color = self.user_data_twitch[user]["color"]
                                nickuser = self.user_data_twitch[user]["nickname"]
                                formatted_nick = f"[{nickuser}] " if nickuser else ""
                                utils_gui.log_and_callback(self, f"{user_color}{user}\033[0m {formatted_nick}({follow_status}) \033[32mse unio al canal\033[0m", self.msg_type)
                        except IndexError:
                            pass

                    elif "PART" in line:
                        try:
                            user = line.split("!")[0][1:]
                            if user in self.joined_users:
                                self.joined_users.remove(user)
                                user_id = self.user_data_twitch[user]["id"]
                                
                                if user_id != None and user_id != "":
                                    follow_last_time = utils.verificar_follow_fecha(user_id) #? Entrega fecha o None
                                    follow_status = self.user_data_twitch[user]["follow_date"] #? Entrega fecha o Visita o New o Renegado
                                    
                                    if follow_last_time == None and follow_status != "Visita" and follow_status != "New" and follow_status != "Renegado":
                                        follow_status = "Renegado"
                                        self.user_data_twitch[user]["follow_date"] = follow_status
                                else:
                                    print(f"ID de usuario no encontrado para {user}")
                                    follow_status = self.user_data_twitch[user]["follow_date"]
                                    
                                user_color = self.user_data_twitch[user]["color"]
                                nickuser = self.user_data_twitch[user]["nickname"]
                                formatted_nick = f"[{nickuser}] " if nickuser else ""
                                utils_gui.log_and_callback(self, f"{user_color}{user}\033[0m {formatted_nick}({follow_status}) \033[31msalio del canal\033[0m", self.msg_type)
                        except IndexError:
                            pass
        except websockets.exceptions.ConnectionClosed:
            self.LOGGER.warning("Conexion websocket cerrada")
        except Exception as e:
            self.LOGGER.error(f"Error en el websocket: {e}")
        finally:
            self.running = False
            self.websocket = None

    async def disconnect(self):
        """Desconectar del websocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            utils_gui.log_and_callback(self, "Desconectado del websocket", self.msg_type)

    def get_connected_users(self):
        """Obtener la lista de usuarios conectados"""
        return list(self.joined_users)