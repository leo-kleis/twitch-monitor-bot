import asyncio
import shlex
import sys
import os
import threading
from typing import Optional
from dotenv import load_dotenv
import recurso.twitch_zk.utils as utils
from clases.twitch_zk import save_active_chat_history
from clases.twitch_zk import TwitchMarkerManager

load_dotenv()
#* Configuracion del websocket usando "Twitch Token Generator"
TOKEN_TTG = os.getenv("TTG_BOT_TOKEN")
CLIENT_ID_TTG = os.getenv("TTG_BOT_CLIENT_ID")
TTG_ID = os.getenv("BROADCASTER_ID")

# Clase para manejar el estado de F6
class F6Handler:
    def __init__(self):
        self.marker_manager: Optional[TwitchMarkerManager] = None
        self.contador = 0
        self.lock = threading.Lock()

f6_handler = F6Handler()

# Variable global para controlar el hilo de escucha de teclas
key_listener_thread = None
key_listener_active = False
global_hotkey_listener = None
marker_manager_main: Optional[TwitchMarkerManager] = None  # Para command_processor
contador_marker = 0

# Función para manejar el hotkey F6 globalmente
def on_f6_pressed():
    """Callback que se ejecuta cuando se presiona F6 globalmente"""
    global f6_handler
    
    # Prevenir múltiples ejecuciones simultáneas usando lock
    if not f6_handler.lock.acquire(blocking=False):
        print("\nF6 ya se está procesando, espera...")
        return
    
    print("\nF6 presionado globalmente - Creando marcador...")
    
    # Crear una nueva tarea asyncio para el marcador
    try:
        # Ejecutar en un hilo separado para no bloquear
        def create_marker_thread():            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Crear una nueva instancia para cada thread/loop para evitar conflictos
            temp_marker_manager = TwitchMarkerManager(
                token=TOKEN_TTG,
                client_id=CLIENT_ID_TTG,
                user_id=TTG_ID
            )
            
            try:
                f6_handler.contador += 1
                result = loop.run_until_complete(temp_marker_manager.create_stream_marker(f"Marcador creado {f6_handler.contador}"))
                if result and result.get('success'):
                    print("Marcador creado exitosamente!")
                else:
                    error = result.get('error', 'Error desconocido') if result else 'Error desconocido'
                    print(f"Error al crear marcador: {error}")
            except Exception as e:
                print(f"Error al crear marcador: {e}")
            finally:
                # Cerrar la sesión temporal
                try:
                    loop.run_until_complete(temp_marker_manager.close())
                except Exception as e:
                    print(f"Error al cerrar sesión temporal: {e}")
                loop.close()
                f6_handler.lock.release()  # Liberar el lock
            print("Comando > ", end="", flush=True)
        
        # Ejecutar en hilo separado para no bloquear el hook
        marker_thread = threading.Thread(target=create_marker_thread, daemon=True)
        marker_thread.start()
        
    except Exception as e:
        print(f"Error al procesar F6: {e}")
        f6_handler.lock.release()  # Liberar el lock en caso de error

# Función para inicializar el listener global de teclas
def setup_global_hotkey():
    """Configura el listener global para F6"""
    global global_hotkey_listener
    
    try:
        from pynput import keyboard
        
        def on_press(key):
            try:
                # Verificar si es F6
                if key == keyboard.Key.f6:
                    on_f6_pressed()
            except AttributeError:
                # Teclas especiales que no tienen atributos
                pass
        
        # Crear y iniciar el listener global
        global_hotkey_listener = keyboard.Listener(on_press=on_press)
        global_hotkey_listener.start()
        
        return True
        
    except ImportError:
        print("Warning: pynput no disponible. F6 global no funcionará.")
        return False
    except Exception as e:
        print(f"Error al configurar hotkey global: {e}")
        return False

# Función para detener el listener global
def stop_global_hotkey():
    """Detiene el listener global de teclas"""
    global global_hotkey_listener
    
    if global_hotkey_listener:
        try:
            global_hotkey_listener.stop()
            global_hotkey_listener = None
        except Exception as e:
            print(f"Error al detener hotkey global: {e}")

# Función legacy mantenida por compatibilidad (ya no se usa)
def key_listener():
    """Función legacy - ahora se usa setup_global_hotkey()"""
    pass

# Funcion para procesar comandos asíncronamente
async def command_processor(shutdown_event, file_path_user_data_twitch, user_data_twitch):
    global key_listener_thread, key_listener_active, marker_manager_main
    
    print("\n=== Sistema de Administracion de Usuarios ===")
    print("Escribe 'ayuda' para ver los comandos disponibles.")
    
    # Configurar hotkey global F6
    if setup_global_hotkey():
        print("Tecla rápida F6 GLOBAL activada para crear marcadores de stream")
    else:
        print("Advertencia: No se pudo configurar F6 global")
    
    while True:
        try:
            # Utilizamos asyncio.to_thread para manejar la entrada sin bloquear
            command = await asyncio.to_thread(input, "\nComando > ")
            args = shlex.split(command.lower())
            
            if not args:
                continue
                
            cmd = args[0]
            
            if cmd == "salir" or cmd == "exit":
                key_listener_active = False  # Detener el listener de teclas
                stop_global_hotkey()  # Detener el hotkey global
                print("Cerrando el programa...")
                shutdown_event.set()  # Señalamos que el programa debe cerrarse
                return  # Salimos de la funcion
                
            elif cmd == "ayuda" or cmd == "help":
                print("\nComandos disponibles:")
                print("  listar                       - Muestra todos los usuarios")
                print("  buscar <termino>             - Busca usuarios por ID o nickname")
                print("  info <usuario>               - Muestra informacion detallada de un usuario")
                print("  nick <usuario> <nuevo>       - Cambia el nickname de un usuario")
                print("  marcador [descripcion]       - Crea un marcador en el stream")
                print("  guardar                      - Guarda los cambios inmediatamente")
                print("  salir                        - Cierra el sistema de comandos")
                print("  F6                           - Tecla rápida GLOBAL para crear marcador")
                
            elif cmd == "marcador":
                if marker_manager_main is None:
                    marker_manager_main = TwitchMarkerManager(
                        token=TOKEN_TTG,
                        client_id=CLIENT_ID_TTG,
                        user_id=TTG_ID
                    )
                # Crear marcador con descripción opcional
                descripcion = " ".join(args[1:]) if len(args) > 1 else None
                print("Creando marcador de stream...")
                try:
                    success = await marker_manager_main.create_stream_marker(descripcion)
                    if not success.get('success', False):
                        print("Verifica que estés transmitiendo y que las variables de entorno estén configuradas correctamente.")
                except Exception as e:
                    print(f"Error al crear marcador: {e}")
                
            elif cmd == "listar":
                if user_data_twitch:
                    print("\n=== Lista de Usuarios ===")
                    for usuario, datos in user_data_twitch.items():
                        nick = datos.get('nickname', 'Sin nickname')
                        print(f"  Usuario: {usuario}, Nickname: {nick}")
                    print(f"\nTotal: {len(user_data_twitch)} usuarios")
                else:
                    print("No hay usuarios registrados.")
                    
            elif cmd == "buscar" and len(args) > 1:
                término = args[1].lower()
                resultados = []
                
                for usuario, datos in user_data_twitch.items():
                    nick = (datos.get('nickname') or '').lower()
                    if término in usuario.lower() or término in nick:
                        resultados.append((usuario, datos.get('nickname', 'Sin nickname')))
                
                if resultados:
                    print(f"\n=== Resultados de búsqueda para '{término}' ===")
                    for usuario, nick in resultados:
                        print(f"  Usuario: {usuario}, Nickname: {nick}")
                    print(f"\nTotal: {len(resultados)} coincidencias")
                else:
                    print(f"No se encontraron usuarios que coincidan con '{término}'.")
                    
            elif cmd == "info" and len(args) > 1:
                usuario = args[1]
                if usuario in user_data_twitch:
                    datos = user_data_twitch[usuario]
                    print(f"\n=== Informacion del Usuario: {usuario} ===")
                    for campo, valor in datos.items():
                        print(f"  {campo}: {valor}")
                else:
                    print(f"El usuario '{usuario}' no existe.")
                    
            elif cmd == "nick" and len(args) > 2:
                usuario = args[1]
                nuevo_nick = args[2]
                
                if usuario in user_data_twitch:
                    antiguo_nick = user_data_twitch[usuario].get('nickname', 'Sin nickname')
                    user_data_twitch[usuario]['nickname'] = nuevo_nick
                    print(f"Nickname actualizado para {usuario}: '{antiguo_nick}' → '{nuevo_nick}'")
                else:
                    print(f"El usuario '{usuario}' no existe.")
                    
            elif cmd == "guardar":
                utils.save_user_data_twitch(file_path_user_data_twitch, user_data_twitch)
                print("Datos guardados correctamente en la base de datos.")
                
            else:
                print("Comando no reconocido. Escribe 'ayuda' para ver los comandos disponibles.")
                
        except Exception as e:
            print(f"Error al procesar el comando: {e}")
    
    # Cleanup al terminar
    stop_global_hotkey()
    
    # Cerrar la sesión del marker manager principal si existe
    if marker_manager_main:
        try:
            await marker_manager_main.close()
        except Exception as e:
            print(f"Error al cerrar marker_manager_main: {e}")

# Función de cleanup para ser llamada desde main.py
def cleanup_hotkeys():
    """Función para limpiar recursos al cerrar el programa"""
    global marker_manager_main
    
    stop_global_hotkey()
    
    # Cerrar la instancia principal del marker manager si existe
    if marker_manager_main:
        try:
            # Crear un event loop temporal para cerrar las sesiones
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(marker_manager_main.close())
            loop.close()
        except Exception as e:
            print(f"Error al limpiar marker_manager_main: {e}")
        finally:
            marker_manager_main = None