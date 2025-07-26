import asyncio
import shlex
import recurso.twitch_zk.utils as utils
from clases.twitch_zk import save_active_chat_history

# Funcion para procesar comandos asíncronamente
async def command_processor(shutdown_event, file_path_user_data_twitch, user_data_twitch):
    print("\n=== Sistema de Administracion de Usuarios ===")
    print("Escribe 'ayuda' para ver los comandos disponibles.")
    
    while True:
        try:
            # Utilizamos asyncio.to_thread para manejar la entrada sin bloquear
            command = await asyncio.to_thread(input, "\nComando > ")
            args = shlex.split(command.lower())
            
            if not args:
                continue
                
            cmd = args[0]
            
            if cmd == "salir" or cmd == "exit":
                print("Cerrando el programa...")
                shutdown_event.set()  # Señalamos que el programa debe cerrarse
                return  # Salimos de la funcion
                
            elif cmd == "ayuda" or cmd == "help":
                print("\nComandos disponibles:")
                print("  listar                       - Muestra todos los usuarios")
                print("  buscar <termino>             - Busca usuarios por ID o nickname")
                print("  info <usuario>               - Muestra informacion detallada de un usuario")
                print("  nick <usuario> <nuevo>       - Cambia el nickname de un usuario")
                print("  guardar                      - Guarda los cambios inmediatamente")
                print("  salir                        - Cierra el sistema de comandos")
                
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