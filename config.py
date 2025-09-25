import os

# Configuración del bot de Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "8321777390:AAEbxf7tpdxu-bec0jLL1u6WCT4P1ouNgj8")

# Configuración de Amazon
DEFAULT_LOCALE = "com"
DEFAULT_COUNTRY_CODE = "US"

# Configuración de reintentos
MAX_RETRIES = 3
RETRY_DELAY = 2

# Mensajes del bot
MENSAJES = {
    "inicio": "🤖 *Bot de Cookies Amazon*\n\nUsa /gencookie para generar cookies de Amazon US",
    "generando": "🔄 *Generando cookie...*",
    "exito": "✅ *¡Cookie generada exitosamente!*",
    "error": "❌ *Error al generar la cookie*",
    "cookie_lista": "🍪 **Aquí tienes tu cookie Amazon US**"
}

# Debug
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
