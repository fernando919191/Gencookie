import os
import json
import time

# Configuración del bot de Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "8321777390:AAEbxf7tpdxu-bec0jLL1u6WCT4P1ouNgj8")

# Configuración de Amazon
DEFAULT_LOCALE = "com"
DEFAULT_COUNTRY_CODE = "US"

# Archivo para almacenar credenciales de usuarios
CREDENTIALS_FILE = "user_credentials.json"

# Mensajes del bot
MENSAJES = {
    "inicio": "🤖 *Bot de Cookies Amazon (Flujo Completo)*\n\nComandos:\n/acc correo contraseña - Configurar cuenta\n/gencookie - Flujo completo con dirección EE.UU.",
}

# Debug
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def load_user_credentials():
    """Carga las credenciales de usuarios desde archivo"""
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_user_credentials(user_id, email, password):
    """Guarda las credenciales de un usuario"""
    try:
        credentials = load_user_credentials()
        credentials[str(user_id)] = {
            'email': email,
            'password': password,
            'timestamp': time.time()
        }
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f, indent=2)
        return True
    except:
        return False

def get_user_credentials(user_id):
    """Obtiene las credenciales de un usuario"""
    credentials = load_user_credentials()
    return credentials.get(str(user_id))
