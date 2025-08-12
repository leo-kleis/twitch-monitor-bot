import logging
import asyncio
import socket
import ssl
from typing import Optional, Set, Any, Dict
import recurso.twitch_zk.utils as utils
import recurso.gui.utils_gui as utils_gui

class TwitchIRCClient:
    def __init__(self, oauth_token, username, channel, userbots, user_data_twitch, msg_type, message_callback=None):
        self.oauth_token = oauth_token
        self.username = username
        self.channel = channel
        self.host = "irc.chat.twitch.tv"
        self.port = 6697  # Puerto SSL para IRC
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.joined_users: Set[str] = set()
        self.running = False
        self.userbots = userbots
        self.user_data_twitch = user_data_twitch
        self.message_callback = message_callback
        self.msg_type = msg_type
        self.LOGGER = logging.getLogger("IRC")
        self.LOGGER.setLevel(logging.INFO)
        
        # Buffer para mensajes incompletos
        self.buffer = ""
        
        # Configuración de reconexión
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # segundos

    async def connect(self):
        """Conectar al servidor IRC de Twitch"""
        try:
            # Crear contexto SSL
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Establecer conexión TCP con SSL
            self.reader, self.writer = await asyncio.open_connection(
                self.host, 
                self.port, 
                ssl=ssl_context
            )
            
            # Autenticación IRC
            await self._send_raw(f"PASS oauth:{self.oauth_token}")
            await self._send_raw(f"NICK {self.username}")
            
            # Habilitar capacidades de Twitch
            await self._send_raw("CAP REQ :twitch.tv/membership")  # JOIN/PART events
            await self._send_raw("CAP REQ :twitch.tv/commands")    # CLEARCHAT, etc.
            await self._send_raw("CAP REQ :twitch.tv/tags")        # Message tags
            
            # Unirse al canal
            await self._send_raw(f"JOIN #{self.channel}")
            
            utils_gui.log_and_callback(self, f"\033[1m\033[42m\033[30m   IRC Conectado                \033[0m", self.msg_type)
            self.running = True
            self.reconnect_attempts = 0
            return True
            
        except Exception as e:
            self.LOGGER.error(f"Error al conectar a IRC: {e}")
            return False

    async def _send_raw(self, message):
        """Enviar mensaje raw al servidor IRC"""
        if self.writer:
            try:
                self.writer.write(f"{message}\r\n".encode('utf-8'))
                await self.writer.drain()
                self.LOGGER.debug(f"Enviado: {message}")
            except Exception as e:
                self.LOGGER.error(f"Error enviando mensaje: {e}")
                raise

    async def _read_line(self):
        """Leer una línea completa del servidor IRC"""
        if not self.reader:
            return None
            
        try:
            data = await self.reader.read(4096)
            if not data:
                return None
                
            self.buffer += data.decode('utf-8', errors='ignore')
            
            lines = []
            while '\r\n' in self.buffer:
                line, self.buffer = self.buffer.split('\r\n', 1)
                if line.strip():
                    lines.append(line.strip())
                    
            return lines
            
        except Exception as e:
            self.LOGGER.error(f"Error leyendo del servidor: {e}")
            return None

    def _parse_tags(self, message):
        """Analizar las etiquetas IRC de Twitch"""
        tags_dict = {}
        if message.startswith("@"):
            try:
                tags_part, message_part = message.split(" ", 1)
                tags_part = tags_part[1:]  # Quitar @
                
                for tag in tags_part.split(";"):
                    if "=" in tag:
                        key, value = tag.split("=", 1)
                        tags_dict[key] = value if value else None
                        
            except Exception as e:
                self.LOGGER.error(f"Error parseando tags: {e}")
                
        return tags_dict

    async def listen(self):
        """Escuchar mensajes del servidor IRC"""
        if not self.reader:
            self.LOGGER.error("No hay conexión IRC establecida")
            return
            
        try:
            while self.running:
                lines = await self._read_line()
                if not lines:
                    # Conexión perdida
                    self.LOGGER.warning("Conexión IRC perdida")
                    if await self._reconnect():
                        continue
                    else:
                        break
                
                for line in lines:
                    await self._process_message(line)
                    
        except Exception as e:
            self.LOGGER.error(f"Error en el loop de escucha: {e}")
        finally:
            self.running = False
            await self._cleanup()

    async def _process_message(self, message):
        """Procesar un mensaje IRC individual"""
        try:
            self.LOGGER.debug(f"Recibido: {message}")
            
            # Manejo de PING
            if message.startswith("PING"):
                pong_target = message.split(":", 1)[1] if ":" in message else "tmi.twitch.tv"
                await self._send_raw(f"PONG :{pong_target}")
                return
            
            # Manejo de CLEARCHAT (bans, timeouts, clear)
            if "CLEARCHAT" in message:
                await self._handle_clearchat(message)
                return
                
            # Manejo de CLEARMSG (eliminación de mensaje específico)
            if "CLEARMSG" in message:
                await self._handle_clearmsg(message)
                return
            
            # Manejo de JOIN
            if " JOIN " in message:
                await self._handle_join(message)
                return
                
            # Manejo de PART
            if " PART " in message:
                await self._handle_part(message)
                return
                
        except Exception as e:
            self.LOGGER.error(f"Error procesando mensaje '{message}': {e}")

    async def _handle_clearchat(self, message):
        """Manejar eventos CLEARCHAT"""
        try:
            if f"#{self.channel}" not in message:
                return
                
            tags_dict = self._parse_tags(message)
            
            # Verificar si es para usuario específico o limpieza general
            if f"#{self.channel} :" in message:
                # Ban/timeout a usuario específico
                user = message.split(f"#{self.channel} :")[1].strip()
                
                ban_duration = tags_dict.get("ban-duration")
                ban_reason = tags_dict.get("ban-reason", "").replace("\\s", " ")
                
                if ban_duration:
                    action_type = f"timeout por {ban_duration} segundos"
                    if ban_reason:
                        action_type += f" - Razón: {ban_reason}"
                else:
                    action_type = "ban permanente"
                    if ban_reason:
                        action_type += f" - Razón: {ban_reason}"
                        
                utils_gui.log_and_callback(self, f"\033[1m\033[43m\033[30m Usuario {user} recibió {action_type} \033[0m", self.msg_type)
            else:
                # Limpieza completa del chat
                utils_gui.log_and_callback(self, f"\033[1m\033[43m\033[30m Chat limpiado completamente \033[0m", self.msg_type)
                
        except Exception as e:
            self.LOGGER.error(f"Error en _handle_clearchat: {e}")

    async def _handle_clearmsg(self, message):
        """Manejar eventos CLEARMSG"""
        try:
            if f"#{self.channel}" not in message:
                return
                
            tags_dict = self._parse_tags(message)
            login = tags_dict.get("login", "desconocido")
            
            # Extraer contenido del mensaje eliminado si está disponible
            msg_content = ""
            if f"#{self.channel} :" in message:
                msg_content = message.split(f"#{self.channel} :")[1].strip()
                msg_content = f" - Mensaje: '{msg_content}'"
                
            utils_gui.log_and_callback(self, f"\033[1m\033[43m\033[30m Mensaje de {login} eliminado{msg_content} \033[0m", self.msg_type)
            
        except Exception as e:
            self.LOGGER.error(f"Error en _handle_clearmsg: {e}")

    async def _handle_join(self, message):
        """Manejar eventos JOIN"""
        try:
            # Formato: :usuario!usuario@usuario.tmi.twitch.tv JOIN #canal
            if "!" in message and f"#{self.channel}" in message:
                user = message.split("!")[0][1:]  # Quitar el :
                
                if user not in self.userbots:
                    self.joined_users.add(user)
                    await self._process_user_join(user)
                    
        except Exception as e:
            self.LOGGER.error(f"Error en _handle_join: {e}")

    async def _handle_part(self, message):
        """Manejar eventos PART"""
        try:
            # Formato: :usuario!usuario@usuario.tmi.twitch.tv PART #canal
            if "!" in message and f"#{self.channel}" in message:
                user = message.split("!")[0][1:]  # Quitar el :
                
                if user in self.joined_users:
                    self.joined_users.remove(user)
                    await self._process_user_part(user)
                    
        except Exception as e:
            self.LOGGER.error(f"Error en _handle_part: {e}")

    async def _process_user_join(self, user):
        """Procesar cuando un usuario se une al canal"""
        try:
            user_id = utils.buscar_id_usuario(user)
            follow_first_time = utils.verificar_follow_fecha(user_id)
            
            if user in self.user_data_twitch:
                follow_status = self.user_data_twitch[user]["follow_date"]
                
                if follow_first_time is None and follow_status not in ["Visita", "New", "Renegado"]:
                    follow_status = "Renegado"
                    self.user_data_twitch[user]["follow_date"] = follow_status
            else:
                follow_status = follow_first_time if follow_first_time is not None else "New"
                
                self.user_data_twitch[user] = {
                    "id": user_id,
                    "follow_date": follow_status,
                    "color": utils.assign_random_color(),
                    "nickname": ""
                }
            
            user_color = self.user_data_twitch[user]["color"]
            nickuser = self.user_data_twitch[user]["nickname"]
            formatted_nick = f"[{nickuser}] " if nickuser else ""
            
            utils_gui.log_and_callback(self, f"{user_color}{user}\033[0m {formatted_nick}({follow_status}) \033[32mse unió al canal\033[0m", self.msg_type)
            
        except Exception as e:
            self.LOGGER.error(f"Error procesando JOIN de {user}: {e}")

    async def _process_user_part(self, user):
        """Procesar cuando un usuario sale del canal"""
        try:
            if user not in self.user_data_twitch:
                return
                
            user_id = self.user_data_twitch[user]["id"]
            
            if user_id:
                follow_last_time = utils.verificar_follow_fecha(user_id)
                follow_status = self.user_data_twitch[user]["follow_date"]
                
                if follow_last_time is None and follow_status not in ["Visita", "New", "Renegado"]:
                    follow_status = "Renegado"
                    self.user_data_twitch[user]["follow_date"] = follow_status
            else:
                follow_status = self.user_data_twitch[user]["follow_date"]
            
            user_color = self.user_data_twitch[user]["color"]
            nickuser = self.user_data_twitch[user]["nickname"]
            formatted_nick = f"[{nickuser}] " if nickuser else ""
            
            utils_gui.log_and_callback(self, f"{user_color}{user}\033[0m {formatted_nick}({follow_status}) \033[31msalió del canal\033[0m", self.msg_type)
            
        except Exception as e:
            self.LOGGER.error(f"Error procesando PART de {user}: {e}")

    async def _reconnect(self):
        """Intentar reconectar al servidor IRC"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.LOGGER.error("Máximo número de reintentos de reconexión alcanzado")
            return False
            
        self.reconnect_attempts += 1
        self.LOGGER.info(f"Intentando reconectar ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        await self._cleanup()
        await asyncio.sleep(self.reconnect_delay)
        
        success = await self.connect()
        if success:
            self.LOGGER.info("Reconexión exitosa")
            return True
        else:
            self.LOGGER.warning(f"Fallo en intento de reconexión {self.reconnect_attempts}")
            return False

    async def _cleanup(self):
        """Limpiar recursos de conexión"""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
            
        self.writer = None
        self.reader = None
        self.buffer = ""

    async def disconnect(self):
        """Desconectar del servidor IRC"""
        self.running = False
        
        if self.writer:
            try:
                await self._send_raw(f"PART #{self.channel}")
                await self._send_raw("QUIT")
            except:
                pass
                
        await self._cleanup()
        utils_gui.log_and_callback(self, "Desconectado del IRC", self.msg_type)

    def get_connected_users(self):
        """Obtener la lista de usuarios conectados"""
        return list(self.joined_users)
