import os
import sys
import qasync
import asyncio
import traceback
import recurso.twitch_zk.utils as utils
from dotenv import load_dotenv
from clases.gui import MainWindow
from PyQt5.QtWidgets import QApplication

load_dotenv()
file_path_userbots_twitch = os.path.join(os.path.dirname(__file__), 'recurso/twitch_zk/data', 'userbots.txt')
with open(file_path_userbots_twitch, 'r') as file:
    userbots = [line.strip() for line in file]

file_path_user_data_twitch = os.path.join(os.path.dirname(__file__), 'recurso/twitch_zk/data', 'user_data_twitch.json')
user_data_twitch = utils.load_user_data_twitch(file_path_user_data_twitch)

# Para depuración
def excepthook(exc_type, exc_value, exc_traceback):
    print(f"Excepción no manejada: {exc_value}")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = excepthook

async def main():
    try:
        # Crear la ventana principal
        window = MainWindow(userbots, user_data_twitch)
        window.show()
        
        # Este bucle mantiene viva la coroutine de main()
        while True:
            await asyncio.sleep(0.1)  # Espera sin bloquear
    except Exception as e:
        print(f"ERROR en main(): {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        # Crear la aplicación Qt
        app = QApplication(sys.argv)
        
        # Configurar el bucle de eventos con qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # El método recomendado para iniciar aplicaciones con qasync
        with loop:
            loop.create_task(main())
            loop.run_forever()
            
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        traceback.print_exc()