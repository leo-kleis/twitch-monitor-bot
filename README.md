Bot para Twitch

![Twitch Status](https://img.shields.io/twitch/status/:kleisarc)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-orange.svg)](https://pypi.org/project/PyQt5/)

Un bot para Twitch desarrollado en Python que combina monitoreo de chat, gestión de seguidores, interfaz gráfica y respuestas de IA con Google Gemini.

## Características

### Monitoreo
- Chat en tiempo real con seguimiento de usuarios
- Gestión de seguidores con comparación automática
- Eventos de moderación (bans, timeouts, mensajes eliminados)
- Análisis de actividad de usuarios (JOIN/PART)

### Inteligencia Artificial
- Google Gemini AI integrado para respuestas contextuales
- Límites configurables de mensajes por sesión
- Historial de conversaciones guardado automáticamente
- Activación/desactivación dinámica desde la GUI

### Interfaces
- Modo CLI para servidores y uso automatizado
- Modo GUI con interfaz PyQt5
- Tema oscuro personalizado
- Visualización en tiempo real de chat y estadísticas

### Análisis de Seguidores
- Exportación automática a CSV con timestamp
- Comparación inteligente entre archivos de seguidores
- Detección de nuevos seguidores y unfollows
- Historial completo con fecha de follow

## Instalación

### Requisitos
- Python 3.13+
- Pipenv (recomendado)
- Credenciales de Twitch Developer Console
- Clave API de Google Gemini

### Pasos

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/zkleisbotv.git
cd zkleisbotv
```

2. Instalar dependencias:
```bash
pipenv install
pipenv shell
```

3. Configurar variables de entorno:
Crear archivo `.env` en la raíz del proyecto:
```env
# Twitch App Credentials (desde dev.twitch.tv/console)
CLIENT_ID_APP=tu_client_id
CLIENT_SECRET_APP=tu_client_secret

# Bot Account
BOT=tu_bot_username
BOT_ID=tu_bot_user_id

# Twitch Token Generator
TTG_BOT_CLIENT_ID=ttg_client_id
TTG_BOT_TOKEN=ttg_access_token

# Canal Objetivo
BROADCASTER=canal_objetivo
BROADCASTER_ID=id_del_canal

# Google Gemini AI
IA_API=tu_gemini_api_key
```

4. Ejecutar la aplicación:
```bash
# Modo GUI (Recomendado)
python gui_main.py

# Modo CLI
python main.py
```

## Uso

### Interfaz Gráfica
1. Ejecutar `python gui_main.py`
2. Monitorear chat en tiempo real en el panel izquierdo
3. Ver actividad de usuarios en el panel derecho
4. Activar Gemini con el botón "Iniciar Gemi"
5. Gestionar usuarios con "Ver Usuarios"

### Comandos CLI
Durante la ejecución en modo CLI:
```bash
listar                    # Listar todos los usuarios
buscar nombre_usuario     # Buscar usuario específico
info nombre_usuario       # Ver información detallada
nick usuario nuevo_apodo  # Asignar nickname
guardar                   # Guardar cambios
salir                     # Salir del bot
```

### Comandos de Chat de Twitch
En el chat de Twitch (prefijo `?`):
- `?comando` - Lista comandos disponibles
- `?info usuario` - Información del usuario

## Arquitectura

### Flujo de Datos
1. Conexión Dual: EventSub (oficial) + WebSocket IRC (personalizado)
2. Procesamiento: Análisis de eventos y mensajes
3. Almacenamiento: SQLite para persistencia
4. Interfaz: Actualización en tiempo real
5. IA: Respuestas contextuales opcionales

## Desarrollo

### Verificación de Código
```bash
# Type checking con pyrefly (ignora falsos positivos)
pyrefly check --ignore missing-attribute --ignore bad-argument-type

# Formato compacto
pyrefly check --ignore missing-attribute --ignore bad-argument-type --output-format min-text
```

### Estructura de Datos
```python
user_data_twitch = {
    "username": {
        "id": "user_id",
        "follow_date": "dd/mm/yy|New|Visita|Renegado",
        "color": "ansi_color_code", 
        "nickname": "custom_nickname"
    }
}
```

## Características Avanzadas

### Análisis de Seguidores
- Comparación automática al cerrar la aplicación
- Detección inteligente de archivos del mismo día
- Reporte detallado de cambios:
  ```
  === ANÁLISIS DE SEGUIDORES ===
  Archivo anterior: [25-07-22] Followers.csv
  Archivo actual: [25-07-23] Followers.csv
  
  --- RESUMEN ---
  Seguidores anteriores: 411
  Seguidores actuales: 413
  Cambio neto: +2
  
  + NUEVOS SEGUIDORES (2):
    #413 - usuario1 (ID: 123456) - 22/07/25
    #412 - usuario2 (ID: 789012) - 22/07/25
  ```

### Integración IA
- Contexto de canal automático (título, categoría)
- Límites configurables de mensajes
- Historial persistente en JSON
- Control dinámico desde GUI

## Seguridad

- Variables de entorno para credenciales sensibles
- Archivo .env incluido en .gitignore
- Tokens OAuth almacenados localmente en SQLite
- Sin hardcoding de credenciales en código fuente
- Gestión segura de tokens de Twitch API

## Dependencias Principales

- TwitchIO 3.0.0b3 - API de Twitch (Es la versión Beta)
- PyQt5 - Interfaz gráfica
- Google Generative AI - Integración con Gemini
- asqlite 2.0.0 - Base de datos async SQLite
- qasync - Bridge entre PyQt5 y asyncio
- python-dotenv - Gestión de variables de entorno

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.
