# 🤖 zkleisbotv - Bot Avanzado para Twitch

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-orange.svg)](https://pypi.org/project/PyQt5/)
[![Twitch](https://img.shields.io/badge/Platform-Twitch-purple.svg)](https://twitch.tv)
[![AI](https://img.shields.io/badge/AI-Google%20Gemini-red.svg)](https://ai.google.dev/)

Un bot avanzado para Twitch desarrollado en Python que combina monitoreo de chat, gestión de seguidores, interfaz gráfica moderna y respuestas inteligentes impulsadas por Google Gemini AI.

## ✨ Características Principales

### 🎯 Monitoreo Completo
- **Chat en tiempo real** con seguimiento de usuarios
- **Gestión de seguidores** con comparación automática
- **Eventos de moderación** (bans, timeouts, mensajes eliminados)
- **Análisis de actividad** de usuarios (JOIN/PART)

### 🤖 Inteligencia Artificial
- **Google Gemini AI** integrado para respuestas contextuales
- **Límites configurables** de mensajes por sesión
- **Historial de conversaciones** guardado automáticamente
- **Activación/desactivación** dinámica desde la GUI

### 🖥️ Interfaces Duales
- **Modo CLI** para servidores y uso automatizado
- **Modo GUI** con interfaz moderna PyQt5
- **Tema oscuro** personalizado
- **Visualización en tiempo real** de chat y estadísticas

### 📊 Análisis de Seguidores
- **Exportación automática** a CSV con timestamp
- **Comparación inteligente** entre archivos de seguidores
- **Detección de nuevos seguidores** y unfollows
- **Historial completo** con fecha de follow

## 🚀 Instalación Rápida

### Requisitos Previos
- Python 3.13+
- Pipenv (recomendado)
- Credenciales de Twitch Developer Console
- Clave API de Google Gemini

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/zkleisbotv.git
cd zkleisbotv
```

### 2. Instalar Dependencias
```bash
pipenv install
pipenv shell
```

### 3. Configurar Variables de Entorno
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

### 4. Ejecutar la Aplicación
```bash
# Modo GUI (Recomendado)
python gui_main.py

# Modo CLI
python main.py
```

## 🎮 Uso

### Interfaz Gráfica
1. **Ejecutar** `python gui_main.py`
2. **Monitorear** chat en tiempo real en el panel izquierdo
3. **Ver actividad** de usuarios en el panel derecho
4. **Activar Gemini** con el botón "Iniciar Gemi"
5. **Gestionar usuarios** con "Ver Usuarios"

### Comandos CLI
Durante la ejecución en modo CLI, acceder al sistema de comandos:
```bash
# Listar todos los usuarios
listar

# Buscar usuario específico
buscar nombre_usuario

# Ver información detallada
info nombre_usuario

# Asignar nickname
nick nombre_usuario nuevo_apodo

# Guardar cambios
guardar

# Salir del bot
salir
```

### Comandos de Chat de Twitch
En el chat de Twitch (prefijo `?`):
- `?comando` - Lista comandos disponibles
- `?info usuario` - Información del usuario
- Y más comandos personalizables...

## 🏗️ Arquitectura

### Componentes Principales
```
zkleisbotv/
├── clases/
│   ├── gui/           # Interfaz PyQt5
│   └── twitch_zk/     # Lógica del bot
├── recurso/
│   ├── gui/           # Recursos gráficos
│   └── twitch_zk/     # Utilidades y scripts
├── bd/                # Base de datos SQLite
└── main.py           # Punto de entrada CLI
```

### Flujo de Datos
1. **Conexión Dual**: EventSub (oficial) + WebSocket IRC (personalizado)
2. **Procesamiento**: Análisis de eventos y mensajes
3. **Almacenamiento**: SQLite para persistencia
4. **Interfaz**: Actualización en tiempo real
5. **IA**: Respuestas contextuales opcionales

## 🔧 Desarrollo

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

## 📈 Características Avanzadas

### 🔍 Análisis de Seguidores
- **Comparación automática** al cerrar la aplicación
- **Detección inteligente** de archivos del mismo día
- **Reporte detallado** de cambios:
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

### 🤖 Integración IA
- **Contexto de canal** automático (título, categoría)
- **Límites configurables** de mensajes
- **Historial persistente** en JSON
- **Control dinámico** desde GUI

## 🔒 Seguridad

### ✅ Aspectos Seguros
- **Variables de entorno** para credenciales sensibles
- **Archivo .env incluido en .gitignore**
- **Tokens OAuth** almacenados localmente en SQLite
- **Sin hardcoding** de credenciales en código fuente
- **Gestión segura** de tokens de Twitch API

### ⚠️ RIESGO DE SEGURIDAD IDENTIFICADO
**CRÍTICO**: El archivo `.env` contiene credenciales reales y está siendo rastreado por Git.

**Acción requerida inmediatamente**:
```bash
# 1. Remover .env del repositorio
git rm --cached .env

# 2. Crear .env.example con valores de ejemplo
cp .env .env.example
# Editar .env.example y reemplazar valores reales con placeholders

# 3. Verificar que .gitignore incluye .env (ya está incluido)

# 4. Regenerar todas las credenciales expuestas
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abrir Pull Request

## 📋 Dependencias Principales

- **TwitchIO** 3.0.0b3 - Cliente oficial de Twitch
- **PyQt5** - Interfaz gráfica moderna
- **Google Generative AI** - Integración con Gemini
- **asqlite** 2.0.0 - Base de datos async SQLite
- **qasync** - Bridge entre PyQt5 y asyncio
- **python-dotenv** - Gestión de variables de entorno

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Reconocimientos

- **Twitch** por su API y plataforma
- **Google** por Gemini AI
- **Comunidad Python** por las librerías utilizadas
- **Qt Project** por PyQt5

---

<div align="center">
  <strong>Desarrollado con ❤️ para la comunidad de Twitch</strong>
</div>