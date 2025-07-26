# CLAUDE.md

Este archivo proporciona orientación a Claude Code (claude.ai/code) al trabajar con código en este repositorio.

## Descripción del Proyecto

zkleisbotv es una aplicación de bot para chat de Twitch construida en Python que se integra con Twitch IRC/EventSub, Google Gemini AI, e incluye interfaces CLI y GUI. El bot monitorea el chat de Twitch, gestiona seguidores, maneja interacciones de usuarios y proporciona respuestas de chat impulsadas por IA.

## Ejecutar la Aplicación

**Modo CLI (Sin GUI):**
```bash
python main.py
```

**Modo GUI:**
```bash
python gui_main.py
```

## Comandos de Desarrollo

**Instalar Dependencias:**
```bash
pipenv install
```

**Activar Entorno Virtual:**
```bash
pipenv shell
```

**Configuración del Entorno:**
- Copiar archivo `.env` con credenciales y tokens requeridos de la API de Twitch
- Variables de entorno requeridas:
  - `CLIENT_ID_APP`, `CLIENT_SECRET_APP` (credenciales de la app de Twitch)
  - `BOT`, `BOT_ID` (detalles de la cuenta del bot)
  - `TTG_BOT_TOKEN` (token del bot de Twitch Token Generator)
  - `BROADCASTER`, `BROADCASTER_ID` (canal objetivo)
  - `IA_API` (clave API de Google Gemini)

## Resumen de Arquitectura

### Componentes Principales

**Puntos de Entrada:**
- `main.py` - versión CLI con bucle de eventos asyncio
- `gui_main.py` - versión GUI usando PyQt5 con integración qasync

**Clases del Bot (`clases/twitch_zk/`):**
- `Bot` - Bot principal de TwitchIO con suscripciones EventSub
- `WebSocketClient` - Cliente WebSocket IRC personalizado para eventos JOIN/PART
- `Gemi` - Integración de chat IA Google Gemini
- `MyComponent` - Comandos del bot y manejadores de eventos

**Componentes GUI (`clases/gui/`):**
- `MainWindow` - Interfaz principal PyQt5 con visualización de chat y controles
- `BotController` - Puente asíncrono entre GUI y lógica del bot

**Utilidades:**
- `recurso/twitch_zk/utils.py` - Gestión de datos de usuario, seguimiento de seguidores
- `recurso/gui/style_manager.py` - Estilos GUI y formato de mensajes
- `bd/db_token.py` - Gestión de tokens y operaciones de base de datos

### Flujo de Datos

1. **Inicialización del Bot**: Carga datos de usuario desde SQLite, se conecta a la API de Twitch
2. **Conexión Dual**: EventSub para eventos oficiales + WebSocket IRC para JOIN/PART de usuarios
3. **Seguimiento de Usuarios**: Mantiene estado de seguidores, apodos y colores en `user_data_twitch`
4. **Integración IA**: Gemini procesa mensajes de chat con contexto del canal
5. **Actualizaciones GUI**: Visualización de chat en tiempo real con mensajes de usuario coloreados

### Estructura de Base de Datos

**Bases de Datos SQLite:**
- `bd/data/tokens_twitch.db` - Almacenamiento de tokens OAuth
- `bd/data/zkleisbotv_twitch.db` - Datos de usuario e historial de seguidores

**Formato de Datos de Usuario:**
```python
user_data_twitch = {
    "username": {
        "id": "user_id",
        "follow_date": "date|New|Visita|Renegado", 
        "color": "ansi_color_code",
        "nickname": "custom_nickname"
    }
}
```

### Sistema de Comandos

**Comandos CLI** (vía `recurso/com_pross.py`):
- `listar` - Listar todos los usuarios
- `buscar <término>` - Buscar usuarios por nombre/apodo
- `info <usuario>` - Mostrar detalles del usuario
- `nick <usuario> <apodo>` - Establecer apodo de usuario
- `guardar` - Guardar cambios en base de datos
- `salir` - Salir de la aplicación

**Comandos de Chat de Twitch** (prefijo: `?`):
- Definidos en `clases/twitch_zk/component_class.py`
- Incluye gestión de seguidores, toggle de chat IA, información de usuario

## Puntos de Integración Clave

**Suscripciones Twitch EventSub:**
- Mensajes de chat, follows, canjes de puntos de canal, raids, eventos de moderación

**Arquitectura Asíncrona:**
- El bucle de eventos principal gestiona Bot, WebSocket y GUI simultáneamente
- qasync conecta eventos PyQt5 con asyncio para modo GUI

**Integración Chat IA:**
- El modelo Gemini recibe contexto del canal (título, categoría)
- Mantiene historial de conversación con límites de mensajes configurables
- Responde a mensajes de chat que mencionan al bot

## Organización de Archivos

- `clases/` - Clases principales del bot y GUI
- `recurso/` - Funciones utilitarias y recursos GUI
- `bd/` - Archivos de base de datos y gestión de tokens
- `pruebas/` - Archivos de prueba y ejemplos
- `recurso/twitch_zk/follow/` - Seguimiento de seguidores y exportación CSV
- `recurso/twitch_zk/chat_gemi/` - Logs de conversaciones de chat IA

## Notas de Desarrollo

- Usa Python 3.13 con pipenv para gestión de dependencias
- PyQt5 para GUI con estilo de tema oscuro personalizado
- Diseño asíncrono en todo - evitar operaciones bloqueantes
- Datos de usuario persisten entre sesiones vía SQLite
- Seguimiento de estado de seguidores se integra con llamadas a la API de Twitch
- Salida de consola con códigos de color para diferentes tipos de mensajes