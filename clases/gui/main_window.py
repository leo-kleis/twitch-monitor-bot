from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                            QTextEdit, QLabel, QSplitter, QHBoxLayout, QSizePolicy, QFrame,
                            QDialog, QDialogButtonBox, QListWidget, QLineEdit)
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QCloseEvent
import asyncio
import asqlite
import os
from typing import Optional
from dotenv import load_dotenv
from clases.twitch_zk import Bot
from clases.twitch_zk import Gemi
from recurso.twitch_zk import utils
from clases.twitch_zk import WebSocketClient
from twitchio import PartialUser
from recurso.gui.style_manager import StyleManager


class BotController(QObject):
    """Clase intermedia que maneja la comunicacion entre la GUI y el bot"""
    message_received = pyqtSignal(str, str)  # Señal para nuevos mensajes (mensaje, tipo)
    bot_started = pyqtSignal()
    bot_stopped = pyqtSignal()
    
    def __init__(self, userbots, user_data_twitch):
        super().__init__()
        self.userbots = userbots
        self.user_data_twitch = user_data_twitch
        self.bot: Optional[Bot] = None
        self.ws_client: Optional[WebSocketClient] = None
        self.tdb: Optional[asqlite.Pool] = None
        self.running = False
        
        # Configuracion desde el .env
        load_dotenv()
        self.oauth_token = os.getenv("TTG_BOT_TOKEN")
        self.bot_name = os.getenv("BOT")
        self.broadcaster_name = os.getenv("BROADCASTER")
        
    async def start_bot(self):
        if self.running:
            return
            
        # Logica similar a tu main.py para iniciar el bot
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
        
        # Iniciar la conexion
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
        # Logica para detener correctamente el bot
        self.bot_stopped.emit()
        
    async def cleanup_resources(self, file_path_user_data_twitch):
        """Guardar datos y limpiar recursos antes de cerrar la aplicacion"""
        from clases.twitch_zk import save_active_chat_history
        import recurso.twitch_zk.utils as utils
        
        # Guardar historial de chat
        save_active_chat_history()
        
        # Guardar datos de usuario
        utils.save_user_data_twitch(file_path_user_data_twitch, self.user_data_twitch)

        # Si hay alguna otra limpieza necesaria para el bot o websocket
        if self.bot is not None:
            # Limpiar recursos del bot si es necesario
            pass

class MainWindow(QMainWindow):
    def __init__(self, userbots, user_data_twitch, file_path_user_data_twitch):
        """Constructor de la ventana principal"""
        super().__init__()
        self.file_path_user_data_twitch = file_path_user_data_twitch
        self.setWindowTitle("Twitch Bot Manager")
        self.setGeometry(100, 100, 1000, 600)
        
        # Inicializar atributos de UI
        self.canal_label: QLabel
        self.title_label: QLabel
        self.category_label: QLabel
        self.viewers_label: QLabel
        self.chat_area: QTextEdit
        self.users_area: QTextEdit
        self.start_button_gemi: QPushButton
        self.stop_button_gemi: QPushButton
        self.view_users_button: QPushButton
        # Atributos adicionales para métodos async
        self.BROADCASTER_ID: Optional[str] = None
        self.BOT_ID: Optional[str] = None
        self.usuario_canal: Optional[PartialUser] = None
        self.charla: Optional[Gemi] = None
        
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
        self.canal_label.setTextFormat(Qt.RichText)
        if self.bot_controller.broadcaster_name == "kleisarc":
            canal_name = "KleisArc"
        else:
            canal_name = self.bot_controller.broadcaster_name
        self.canal_label.setText(StyleManager.format_label_value("Canal", canal_name, 'white', 'blue'))
        info_layout.addWidget(self.canal_label)

        # Espaciador
        info_layout.addSpacing(15)

        # Titulo del stream
        self.title_label = QLabel()
        self.title_label.setTextFormat(Qt.RichText)
        self.title_label.setText(StyleManager.format_label_value("Titulo", "-", 'white', 'green'))
        info_layout.addWidget(self.title_label)

        # Espaciador
        info_layout.addSpacing(15)
        
        # Categoria del stream
        self.category_label = QLabel()
        self.category_label.setTextFormat(Qt.RichText)
        self.category_label.setText(StyleManager.format_label_value("Categoria", "-", 'white', 'green'))
        info_layout.addWidget(self.category_label)
        
        # Espacio flexible para empujar el contador de espectadores a la derecha
        info_layout.addStretch(1)
        
        # Contador de espectadores
        self.viewers_label = QLabel()
        self.viewers_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.viewers_label.setTextFormat(Qt.RichText)
        self.viewers_label.setText(StyleManager.format_label_value("Espectadores", "-", 'white', 'red'))
        info_layout.addWidget(self.viewers_label)
        
        # Añadir la barra de informacion al layout principal
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
        self.start_button_gemi.setMaximumHeight(40)  # Altura maxima en pixeles
        self.start_button_gemi.clicked.connect(self.start_gemi)
        buttons_layout.addWidget(self.start_button_gemi)
        
        self.stop_button_gemi = QPushButton("Detener Gemi")
        self.stop_button_gemi.setMaximumHeight(40)   # Altura maxima en pixeles
        self.stop_button_gemi.clicked.connect(self.stop_gemi)
        self.stop_button_gemi.setEnabled(False)
        buttons_layout.addWidget(self.stop_button_gemi)
        
        buttons_layout.addStretch()
        
        # Boton para ver usuarios - en el extremo derecho
        self.view_users_button = QPushButton("Ver Usuarios")
        self.view_users_button.setMaximumHeight(40)
        self.view_users_button.clicked.connect(self.show_users)
        buttons_layout.addWidget(self.view_users_button)
        
        main_layout.addLayout(buttons_layout)

        # Hacer que el splitter ocupe todo el espacio disponible
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Configurar tamaño minimo para los cuadros de texto
        self.chat_area.setMinimumHeight(300)  # Altura minima en pixeles
        self.users_area.setMinimumHeight(300)  # Altura minima en pixeles
        
    @pyqtSlot()
    def start_bot(self):
        asyncio.create_task(self.bot_controller.start_bot())
        
    @pyqtSlot()
    def stop_bot(self):
        asyncio.create_task(self.bot_controller.stop_bot())

    @pyqtSlot()
    def start_gemi(self):
        """Inicia el bot de Gemini"""
        # Desactivar el boton de inicio y activar el boton de detencion
        self.start_button_gemi.setEnabled(False)
        self.stop_button_gemi.setEnabled(True)
        
        # Crear una tarea asincrona para iniciar Gemini
        asyncio.create_task(self._start_gemi_async())
        
    async def _start_gemi_async(self):
        """Implementacion asincrona para iniciar Gemini"""
        try:
            # Verificar que el bot este disponible
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
                        message = "Gemi ya esta activado.",
                        token_for = self.bot_controller.oauth_token
                    )
                    
                    formatted_message = '<div style="font-family: Kanit, sans-serif; font-size: 14px; margin: 3px 0; display: block;"><span style="color:#4aff4a; text-decoration: underline; font-weight: bold;">Gemi ya esta activado.</span><br></div>'
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
            # Iniciar Gemini con la informacion del canal
            model = await utils.iniciar_gemi(channel_info[0])

            self.charla = Gemi(model, max_messages=20, bot=self.bot_controller.bot)

            setattr(sys.modules['clases.twitch_zk.component_class'], 'charla', self.charla)
            
            await self.usuario_canal.send_message(
                sender = str(self.BOT_ID),
                message = "Gemi iniciado con limite de 20 mensajes.",
                token_for = self.bot_controller.oauth_token
            )
            
            # Informar que se inicio correctamente
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
        
        # Resetear la variable en el modulo component_class
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
            
            # Activar interpretacion de HTML
            self.viewers_label.setTextFormat(Qt.RichText)
            
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
        """Actualiza la informacion del stream en la interfaz"""
        # Usar el nuevo metodo del StyleManager
        title_html = StyleManager.format_label_value("Titulo", title, 'white', 'green')
        category_html = StyleManager.format_label_value("Categoria", category, 'white', 'green')
        
        # Activar interpretacion de HTML en los labels
        self.title_label.setTextFormat(Qt.RichText)
        self.category_label.setTextFormat(Qt.RichText)
        
        # Asignar el texto HTML
        self.title_label.setText(title_html)
        self.category_label.setText(category_html)  
    
    @pyqtSlot()
    def show_users(self):
        """Muestra un dialogo con la lista de usuarios en user_data_twitch con filtro por nombre"""
        # Crear dialogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Usuarios")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)
        
        # Aplicar estilos desde StyleManager
        dialog.setStyleSheet(StyleManager.get_dialog_stylesheet())
        
        layout = QVBoxLayout(dialog)
        
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Buscar:")
        filter_label.setStyleSheet(f"color: {StyleManager.COLORS['blue']};")
        filter_layout.addWidget(filter_label)
    
        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Escriba para buscar por nombre...")
        filter_layout.addWidget(filter_input)
        layout.addLayout(filter_layout)
        
        # Lista de usuarios
        user_list = QListWidget()
        layout.addWidget(user_list)
        
        # Almacenar todos los usuarios para poder filtrarlos
        all_users = []
        # Lista para mantener referencia a los usuarios filtrados actualmente mostrados
        filtered_users = []
        
        # Rellenar la lista con los usuarios
        if self.bot_controller.user_data_twitch:
            for user_name, user_data in self.bot_controller.user_data_twitch.items():
                # user_data es un diccionario con la informacion del usuario {id, follow_date, color, nickname}
                follow_date = user_data['follow_date']
                nickname = user_data['nickname']
                
                if nickname != "":
                    nickname = f"({nickname}) "
                
                display_text = f"{nickname}{user_name} [{follow_date}]"
                all_users.append((display_text, user_name))
                user_list.addItem(display_text)
            
            # Inicializar filtered_users con todos los usuarios
            filtered_users = all_users.copy()
        else:
            user_list.addItem("No hay usuarios registrados.")
        
        # Funcion para filtrar la lista
        def filter_users():
            filter_text = filter_input.text().lower()
            user_list.clear()
            filtered_users.clear()  # Limpiar la lista de usuarios filtrados
            
            for display_text, name in all_users:
                # Obtener el nickname del usuario actual
                user_data = self.bot_controller.user_data_twitch.get(name)
                nickname = user_data.get('nickname', '').lower()
                
                # Buscar en nombre y nickname
                if filter_text in name.lower() or filter_text in nickname:
                    user_list.addItem(display_text)
                    filtered_users.append((display_text, name))  # Añadir a la lista filtrada
            
            if user_list.count() == 0:
                user_list.addItem("No se encontraron coincidencias.")
        
        # Conectar el evento de cambio de texto
        filter_input.textChanged.connect(filter_users)
        
        # Conectar el evento de doble clic para editar el nickname
        # Ahora usamos filtered_users en lugar de all_users
        user_list.itemDoubleClicked.connect(lambda item: self.edit_user_nickname(dialog, filtered_users, user_list.currentRow()))
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        # Mostrar dialogo
        dialog.exec_()
    
    def edit_user_nickname(self, parent_dialog, all_users, current_row):
        """Abre un dialogo para editar el nickname del usuario seleccionado"""
        if current_row < 0 or current_row >= len(all_users):
            return
        
        # Obtener el nombre de usuario seleccionado
        _, user_name = all_users[current_row]
        
        # Obtener datos actuales del usuario
        user_data = self.bot_controller.user_data_twitch.get(user_name)
        if not user_data:
            return
        
        current_nickname = user_data.get('nickname', '')
        
        # Crear dialogo de edicion
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
        
        edit_dialog = QDialog(parent_dialog)
        edit_dialog.setWindowTitle(f"Editar Nickname - {user_name}")
        edit_dialog.setMinimumWidth(300)
        edit_dialog.setStyleSheet(StyleManager.get_dialog_stylesheet())
        
        layout = QVBoxLayout(edit_dialog)
        
        # Informacion del usuario
        info_label = QLabel(f"Usuario: {user_name}")
        info_label.setStyleSheet(f"color: {StyleManager.COLORS['blue']};")
        layout.addWidget(info_label)
        
        # Campo para editar el nickname
        nickname_label = QLabel("Nickname:")
        layout.addWidget(nickname_label)
        
        nickname_input = QLineEdit()
        nickname_input.setText(current_nickname)
        nickname_input.selectAll()  # Seleccionar todo el texto para facilitar la edicion
        layout.addWidget(nickname_input)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(edit_dialog.accept)
        buttons.rejected.connect(edit_dialog.reject)
        layout.addWidget(buttons)
        
        # Mostrar dialogo y procesar resultado
        if edit_dialog.exec_() == QDialog.Accepted:
            new_nickname = nickname_input.text().strip()
            
            # Actualizar el nickname en el diccionario
            self.bot_controller.user_data_twitch[user_name]['nickname'] = new_nickname
            
            # Actualizar la lista en el dialogo principal
            parent_dialog.accept()  # Cerrar el dialogo actual
            self.show_users()  # Volver a abrir con la informacion actualizada
    
    def closeEvent(self, event: Optional[QCloseEvent]):  # type: ignore
        async def shutdown_sequence():
            if self.bot_controller.running:
                await self.bot_controller.stop_bot()
            await self.bot_controller.cleanup_resources(self.file_path_user_data_twitch)
        
        # Crear la tarea y programarla en el bucle existente
        # No usamos run_until_complete porque el bucle ya esta corriendo
        future = asyncio.ensure_future(shutdown_sequence())
        
        # No esperamos a que termine para aceptar el evento de cierre
        # Ya que estamos en la interfaz grafica
        event.accept()