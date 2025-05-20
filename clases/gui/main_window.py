from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                            QTextEdit, QLabel, QSplitter, QHBoxLayout, QSizePolicy, QFrame)
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
import asyncio
import asqlite
import os
from dotenv import load_dotenv
from clases.twitch_zk import Bot
from clases.twitch_zk import Gemi
from recurso.twitch_zk import utils
from clases.twitch_zk import WebSocketClient
from recurso.gui.style_manager import StyleManager, MessageType


class BotController(QObject):
    """Clase intermedia que maneja la comunicación entre la GUI y el bot"""
    message_received = pyqtSignal(str, str)  # Señal para nuevos mensajes (mensaje, tipo)
    bot_started = pyqtSignal()
    bot_stopped = pyqtSignal()
    
    def __init__(self, userbots, user_data_twitch):
        super().__init__()
        self.userbots = userbots
        self.user_data_twitch = user_data_twitch
        self.bot = None
        self.ws_client = None
        self.running = False
        
        # Configuración desde el .env
        load_dotenv()
        self.oauth_token = os.getenv("TTG_BOT_TOKEN")
        self.bot_name = os.getenv("BOT")
        self.broadcaster_name = os.getenv("BROADCASTER")
        
    async def start_bot(self):
        if self.running:
            return
            
        # Lógica similar a tu main.py para iniciar el bot
        db_path_twitch = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'bd/data', 'tokens_twitch.db')
        
        self.tdb = await asqlite.create_pool(db_path_twitch)
        self.bot = Bot(
            token_database=self.tdb,
            userbots=self.userbots,
            user_data_twitch=self.user_data_twitch,
            msg_type="chat",
            message_callback=lambda msg, msg_type="websocket": self.message_received.emit(msg, msg_type)
        )
        
        # Inicializar el bot
        await self.bot.setup_database()
        
        # Inicializar el WebSocket
        self.ws_client = WebSocketClient(
            self.oauth_token,
            self.bot_name,
            self.broadcaster_name,
            self.userbots,
            self.user_data_twitch,
            msg_type="websocket",
            message_callback=lambda msg, msg_type="websocket": self.message_received.emit(msg, msg_type)
        )
        
        # Iniciar la conexión
        connection_success = await self.ws_client.connect()
        
        # Iniciar el bot en segundo plano
        self.running = True
        self.bot_started.emit()
        
        # Iniciar tareas en background
        if connection_success:
            asyncio.create_task(self.bot.start())
            asyncio.create_task(self.ws_client.listen())
        else:
            asyncio.create_task(self.bot.start())
    
    async def stop_bot(self):
        if not self.running:
            return
            
        # Detener el bot y limpiar recursos
        self.running = False
        # Lógica para detener correctamente el bot
        self.bot_stopped.emit()
        
    async def cleanup_resources(self):
        """Guardar datos y limpiar recursos antes de cerrar la aplicación"""
        from clases.twitch_zk import save_active_chat_history
        import recurso.twitch_zk.utils as utils
        
        # Guardar historial de chat
        save_active_chat_history()
        
        # Guardar datos de usuario
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'recurso/twitch_zk/data', 'user_data_twitch.json')
        utils.save_user_data_twitch(file_path, self.user_data_twitch)
        
        # Si hay alguna otra limpieza necesaria para el bot o websocket
        if self.bot is not None:
            # Limpiar recursos del bot si es necesario
            pass

class MainWindow(QMainWindow):
    def __init__(self, userbots, user_data_twitch):
        super().__init__()
        self.setWindowTitle("Twitch Bot Manager")
        self.setGeometry(100, 100, 1000, 600)
        
        # Aplicar estilo oscuro global
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                font-family: 'Kanit', sans-serif;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-family: 'Kanit', sans-serif;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
                selection-background-color: #0078d7;
                font-family: 'Kanit', sans-serif;
                font-size: 13px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 8px;
                border-radius: 4px;
                border: none;
                font-family: 'Kanit', sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0086f0;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
        """)
        
        # Crear el controlador del bot
        self.bot_controller = BotController(userbots, user_data_twitch)
        self.bot_controller.message_received.connect(self.on_message_received)
        
        # Configurar la interfaz
        self.setup_ui()
        
        asyncio.create_task(self.bot_controller.start_bot())
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal (vertical)
        main_layout = QVBoxLayout(central_widget)

        info_layout = QHBoxLayout()
        
        # Canal del stream
        self.canal_label = QLabel()
        self.canal_label.setTextFormat(Qt.TextFormat.RichText)
        if self.bot_controller.broadcaster_name == "kleisarc":
            canal_name = "KleisArc"
        else:
            canal_name = self.bot_controller.broadcaster_name
        self.canal_label.setText(StyleManager.format_label_value("Canal", canal_name, 'white', 'blue'))
        info_layout.addWidget(self.canal_label)

        # Espaciador
        info_layout.addSpacing(15)

        # Título del stream
        self.title_label = QLabel()
        self.title_label.setTextFormat(Qt.TextFormat.RichText)
        self.title_label.setText(StyleManager.format_label_value("Título", "-", 'white', 'green'))
        info_layout.addWidget(self.title_label)

        # Espaciador
        info_layout.addSpacing(15)
        
        # Categoría del stream
        self.category_label = QLabel()
        self.category_label.setTextFormat(Qt.TextFormat.RichText)
        self.category_label.setText(StyleManager.format_label_value("Categoría", "-", 'white', 'green'))
        info_layout.addWidget(self.category_label)
        
        # Espacio flexible para empujar el contador de espectadores a la derecha
        info_layout.addStretch(1)
        
        # Contador de espectadores
        self.viewers_label = QLabel()
        self.viewers_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.viewers_label.setTextFormat(Qt.TextFormat.RichText)
        self.viewers_label.setText(StyleManager.format_label_value("Espectadores", "-", 'white', 'red'))
        info_layout.addWidget(self.viewers_label)
        
        # Añadir la barra de información al layout principal
        main_layout.addLayout(info_layout)
        
        # Añadir un separador visual (opcional)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #555555;")
        separator.setMaximumHeight(1)
        main_layout.addWidget(separator)
        main_layout.addSpacing(5)

        # Crear un splitter horizontal para dividir la ventana
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panel izquierdo - Chat
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        chat_label = QLabel("Chat de Twitch")
        chat_layout.addWidget(chat_label)
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            span { display: inline; }
            h3 { color: #00aeff; font-size: 16px; }
            body { font-family: 'Kanit', sans-serif; font-size: 13px; }
        """)
        self.chat_area.setAcceptRichText(True)
        chat_layout.addWidget(self.chat_area)
        
        splitter.addWidget(chat_widget)
        
        # Panel derecho - Usuarios y comandos
        users_widget = QWidget()
        users_layout = QVBoxLayout(users_widget)
        
        users_label = QLabel("Usuarios y Comandos")
        users_layout.addWidget(users_label)
                
        self.users_area = QTextEdit()
        self.users_area.setReadOnly(True)
        self.users_area.setStyleSheet("""
            span { display: inline; }
            h3 { color: #00aeff; font-size: 16px; }
            body { font-family: 'Kanit', sans-serif; font-size: 13px; }
        """)
        self.users_area.setAcceptRichText(True)
        users_layout.addWidget(self.users_area)
        
        splitter.addWidget(users_widget)
        
        # Establecer proporciones iniciales (60% izquierda, 40% derecha)
        splitter.setSizes([600, 400])
        
        # Botones de control (mantener en el layout principal)
        buttons_layout = QHBoxLayout()
        
        self.start_button_gemi = QPushButton("Iniciar Gemi")
        self.start_button_gemi.setMaximumHeight(40)  # Altura máxima en píxeles
        self.start_button_gemi.clicked.connect(self.start_gemi)
        buttons_layout.addWidget(self.start_button_gemi)
        
        self.stop_button_gemi = QPushButton("Detener Gemi")
        self.stop_button_gemi.setMaximumHeight(40)   # Altura máxima en píxeles
        self.stop_button_gemi.clicked.connect(self.stop_gemi)
        self.stop_button_gemi.setEnabled(False)
        buttons_layout.addWidget(self.stop_button_gemi)
        
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)

        # Hacer que el splitter ocupe todo el espacio disponible
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Configurar tamaño mínimo para los cuadros de texto
        self.chat_area.setMinimumHeight(300)  # Altura mínima en píxeles
        self.users_area.setMinimumHeight(300)  # Altura mínima en píxeles
        
    @pyqtSlot()
    def start_bot(self):
        asyncio.create_task(self.bot_controller.start_bot())
        
    @pyqtSlot()
    def stop_bot(self):
        asyncio.create_task(self.bot_controller.stop_bot())

    @pyqtSlot()
    def start_gemi(self):
        """Inicia el bot de Gemini"""
        # Desactivar el botón de inicio y activar el botón de detención
        self.start_button_gemi.setEnabled(False)
        self.stop_button_gemi.setEnabled(True)
        
        # Crear una tarea asíncrona para iniciar Gemini
        asyncio.create_task(self._start_gemi_async())
        
    async def _start_gemi_async(self):
        """Implementación asíncrona para iniciar Gemini"""
        try:
            # Verificar que el bot esté disponible
            if not self.bot_controller.bot:
                formatted_message = '<div style="font-family: Kanit, sans-serif; font-size: 14px; margin: 3px 0; display: block;"><span style="color:red;">Error: Bot no inicializado</span><br></div>'
                cursor = self.users_area.textCursor()
                cursor.movePosition(cursor.End)
                cursor.insertHtml(formatted_message)
                self.users_area.setTextCursor(cursor)
                self.users_area.ensureCursorVisible()
                return

            import sys
            from clases.twitch_zk.component_class import charla
            
            self.BROADCASTER_ID = os.getenv("BROADCASTER_ID")
            self.BOT_ID = os.getenv("BOT_ID")

            self.usuario_canal = self.bot_controller.bot.create_partialuser(user_id=str(self.BROADCASTER_ID))

            if charla is not None:
                if charla.is_active():
                    await self.usuario_canal.send_message(
                        sender = str(self.BOT_ID),
                        message = "Gemi ya está activado.",
                        token_for = self.bot_controller.oauth_token
                    )
                    
                    formatted_message = '<div style="font-family: Kanit, sans-serif; font-size: 14px; margin: 3px 0; display: block;"><span style="color:#4aff4a; text-decoration: underline; font-weight: bold;">Gemi ya está activado.</span><br></div>'
                    cursor = self.users_area.textCursor()
                    cursor.movePosition(cursor.End)
                    cursor.insertHtml(formatted_message)
                    self.users_area.setTextCursor(cursor)
                    self.users_area.ensureCursorVisible()
                    return
                else:
                    charla.terminate(False)
                    setattr(sys.modules['clases.twitch_zk.component_class'], 'charla', None)

            # Usar el bot desde bot_controller
            channel_info = await self.bot_controller.bot.fetch_channels([str(self.BROADCASTER_ID)])
            # Iniciar Gemini con la información del canal
            model = await utils.iniciar_gemi(channel_info[0])

            self.charla = Gemi(model, max_messages=20, bot=self.bot_controller.bot)

            setattr(sys.modules['clases.twitch_zk.component_class'], 'charla', self.charla)
            
            await self.usuario_canal.send_message(
                sender = str(self.BOT_ID),
                message = "Gemi iniciado con límite de 20 mensajes.",
                token_for = self.bot_controller.oauth_token
            )
            
            # Informar que se inició correctamente
            formatted_message = '<div style="font-family: Kanit, sans-serif; font-size: 14px; margin: 3px 0; display: block;"><span style="color:#4aff4a; text-decoration: underline; font-weight: bold;">Gemi iniciado</span><br></div>'
            cursor = self.users_area.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertHtml(formatted_message)
            self.users_area.setTextCursor(cursor)
            self.users_area.ensureCursorVisible()
            
        except Exception as e:
            await self.usuario_canal.send_message(
                sender = str(self.BOT_ID),
                message = "Gemi con problemas.",
                token_for = self.bot_controller.oauth_token
            )
            
            # Manejar errores
            error_message = f'<div style="font-family: Kanit, sans-serif; font-size: 14px; margin: 3px 0; display: block;"><span style="color:red;">Error al iniciar Gemi: {str(e)}</span><br></div>'
            cursor = self.users_area.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertHtml(error_message)
            self.users_area.setTextCursor(cursor)
            self.users_area.ensureCursorVisible()
            
            # Restaurar estado de los botones
            self.start_button_gemi.setEnabled(True)
            self.stop_button_gemi.setEnabled(False)

    @pyqtSlot()
    def stop_gemi(self):
        """Detiene el bot de Gemini"""
        self.start_button_gemi.setEnabled(True)
        self.stop_button_gemi.setEnabled(False)
        
        asyncio.create_task(self._stop_gemi_async())
        
        # Añadir mensaje al panel de comandos
        formatted_message = '<div style="font-family: Kanit, sans-serif; font-size: 14px; margin: 3px 0; display: block;"><span style="color:#ff6a6a; text-decoration: underline; font-weight: bold;">Gemi detenido</span><br></div>'
        
        cursor = self.users_area.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(formatted_message)
        
        self.users_area.setTextCursor(cursor)
        self.users_area.ensureCursorVisible()
        
        from clases.twitch_zk.component_class import charla
        
        if charla is not None:
            charla.terminate(False)
        
        # Resetear la variable en el módulo component_class
        import sys
        setattr(sys.modules['clases.twitch_zk.component_class'], 'charla', None)
        
        # Limpiar la referencia local
        if hasattr(self, 'charla'):
            self.charla = None

    async def _stop_gemi_async(self):
        await self.usuario_canal.send_message(
            sender = str(self.BOT_ID),
            message = "Gemi desactivado.",
            token_for = self.bot_controller.oauth_token
        )

    @pyqtSlot(str, str)
    def on_message_received(self, message, msg_type="chat"):
        """Procesa mensajes recibidos y los muestra en el panel correspondiente"""
        
        if msg_type == "viewer_count":
            # Actualizar el label dedicado con formato de color
            viewers_html = StyleManager.format_label_value("Espectadores", message, 'white', 'red')
            
            # Activar interpretación de HTML
            self.viewers_label.setTextFormat(Qt.TextFormat.RichText)
            
            # Aplicar el texto formateado
            self.viewers_label.setText(viewers_html)
            return
        elif msg_type == "stream_info":
            # Formato esperado: title|category
            if "|" in message:
                title, category = message.split("|", 1)
                self.update_stream_info(title, category)
            return
        
        # Usar el StyleManager para formatear mensajes
        formatted_message = StyleManager.format_message(message, msg_type)
        
        if msg_type in ["websocket", "system", "error", "warning", "command"]:
            # Mensajes del sistema, errores, comandos, etc
            cursor = self.users_area.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertHtml(formatted_message)
            
            self.users_area.setTextCursor(cursor)
            self.users_area.ensureCursorVisible()
        elif msg_type in ["chat", "bot"]:
            # Mensajes de chat y del bot
            cursor = self.chat_area.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertHtml(formatted_message)
            
            self.chat_area.setTextCursor(cursor)
            self.chat_area.ensureCursorVisible()
            
    def update_stream_info(self, title, category):
        """Actualiza la información del stream en la interfaz"""
        # Usar el nuevo método del StyleManager
        title_html = StyleManager.format_label_value("Título", title, 'white', 'green')
        category_html = StyleManager.format_label_value("Categoría", category, 'white', 'green')
        
        # Activar interpretación de HTML en los labels
        self.title_label.setTextFormat(Qt.TextFormat.RichText)
        self.category_label.setTextFormat(Qt.TextFormat.RichText)
        
        # Asignar el texto HTML
        self.title_label.setText(title_html)
        self.category_label.setText(category_html)  
    
    def closeEvent(self, event):
        async def shutdown_sequence():
            if self.bot_controller.running:
                await self.bot_controller.stop_bot()
            await self.bot_controller.cleanup_resources()
        
        # Crear la tarea y programarla en el bucle existente
        # No usamos run_until_complete porque el bucle ya está corriendo
        future = asyncio.ensure_future(shutdown_sequence())
        
        # No esperamos a que termine para aceptar el evento de cierre
        # Ya que estamos en la interfaz gráfica
        event.accept()