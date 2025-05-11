import os
import json
import logging
import asyncio
import datetime

LOGGER: logging.Logger = logging.getLogger("BOT")
LOGGER.setLevel(logging.INFO)

############## Usando Chat Grupal ##############

class Gemi:
    def __init__(self, model, max_messages=20, bot=None):
        """
        Inicializa el chat grupal con Gemini.
        
        Args:
            model: El modelo de Gemini configurado
            max_messages: Número máximo de mensajes antes de desactivarse (default: 20)
            bot: Referencia al bot de Twitch para ejecutar comandos
        """
        self.model = model
        self.chat = model.start_chat(history=[])
        self.participants = set()
        self.max_messages = max_messages
        self.active = True
        self.message_count = 0
        self.bot = bot
    
    def send_message(self, usuario, message, ctx=None):
        """Envía un mensaje de un usuario específico al chat grupal"""
        # Si superó el límite, no procesar más mensajes
        if not self.active:
            return "Gemi ha alcanzado el límite de mensajes."
        
        self.participants.add(usuario)
        
        # Formatea el mensaje con el nombre del usuario
        formatted_message = f"{usuario}: {message}"
        
        # Envía el mensaje al chat
        response = self.chat.send_message(formatted_message)
        # Variable para almacenar el texto de respuesta
        response_text = None
        function_called = False
        
        # Procesar la respuesta
        try:
            # Primero intentamos procesar la respuesta directamente como texto
            if hasattr(response, 'text'):
                response_text = response.text
            # Si no tiene el atributo text, buscamos en los candidatos
            elif hasattr(response, 'candidates'):
                for candidate in response.candidates:
                    if hasattr(candidate, 'content'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                function_called = True
                                result = self._handle_function_call(part.function_call, ctx)
                                response_text = result
                            if hasattr(part, 'text'):
                                if not function_called:
                                    response_text = part.text
                                elif function_called and part.text != "":
                                    response_text = response_text + " | " + part.text
        except Exception as e:
            LOGGER.info(f"Error al procesar respuesta: {str(e)}")
            response_text = "Lo siento, ocurrió un error al procesar tu mensaje."
        
        # Si no se pudo extraer ningún texto, asignar un valor predeterminado
        if response_text is None:
            response_text = "Lo siento, no pude procesar tu solicitud correctamente."
        
        # Incrementar contador después de procesar el mensaje
        self.message_count += 1
        
        maximo = self.max_messages
        limite = maximo - 3
        if self.message_count >= limite and self.message_count < maximo:
            aviso = maximo - self.message_count
            asyncio.create_task(ctx.send(f"Solo quedan {aviso} mensajes para que Gemi se desactive."))
        
        # Verificar si llegamos al límite después de esta respuesta
        if self.message_count >= self.max_messages:
            self.active = False
            self.terminate(True)
        
        return response_text
    
    def _handle_function_call(self, function_call, ctx):
        """Maneja las llamadas a funciones del modelo"""
        if not ctx:
            return "No puedo ejecutar comandos administrativos en este contexto."
        
        function_name = function_call.name
        args = function_call.args
        
        if function_name == "change_title" and "title" in args:
            # Usar el comando del bot para cambiar el título
            asyncio.create_task(ctx.channel.modify_channel(title=args["title"]))
            return f"He cambiado el título del stream a: {args['title']}"
        
        return "No pude ejecutar el comando solicitado."
    
    def get_history(self):
        """Obtiene el historial completo del chat"""
        return self.chat.history
    
    def get_message_count(self):
        """Obtiene el número de mensajes intercambiados"""
        return self.message_count
    
    def get_participants(self):
        """Obtiene la lista de participantes del chat"""
        return list(self.participants)
    
    def is_active(self):
        """Verifica si Gemi sigue activo o ya alcanzó el límite"""
        return self.active
    
    def terminate(self, suceso):
        """Finaliza la instancia de Gemi y libera recursos y guarda el historial"""
        self.active = False
        if suceso == True:
            LOGGER.info(f"Gemi ha alcanzado el límite de {self.max_messages} mensajes y se desactivará.")
        else:
            LOGGER.info(f"Gemi ha sido desactivado manualmente.")
        
        # Guardar el historial de la conversación
        self._save_chat_history()
    
    def _save_chat_history(self):
        """Guarda el historial de chat en un archivo JSON"""
        # No guardar si no hay mensajes
        if self.message_count == 0:
            LOGGER.info("No hay mensajes para guardar en el historial.")
            return
            
        # Crear la carpeta si no existe
        chat_dir = os.path.join("recurso/twitch_zk", "chat_gemi")
        os.makedirs(chat_dir, exist_ok=True)
        
        # Generar nombre de archivo con fecha y hora
        now = datetime.datetime.now()
        filename = f"chat_{now.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(chat_dir, filename)
        
        # Resto del código igual...
        
        # Preparar el historial para guardar
        history_data = {
            "timestamp": now.isoformat(),
            "participants": list(self.participants),
            "message_count": self.message_count,
            "messages": []
        }
        
        # Convertir el historial a un formato legible
        for message in self.chat.history:
            role = message.role
            if hasattr(message, 'parts') and message.parts:
                # Obtener el texto del mensaje de los parts
                content = [part.text for part in message.parts if hasattr(part, 'text')]
                content_text = " ".join(content) if content else ""
                
                # Para mensajes de usuario, extraer el nombre si está en formato "nombre: mensaje"
                user_name = None
                if role == "user" and ":" in content_text:
                    parts = content_text.split(":", 1)
                    if len(parts) == 2:
                        user_name = parts[0].strip()
                
                history_data["messages"].append({
                    "role": role,
                    "user_name": user_name if role == "user" else None,
                    "content": content_text
                })
        
        # Guardar en archivo JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        LOGGER.info(f"Historial de chat guardado en: {filepath}")