import asyncio
import logging
import os
import time
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurar logging para DisCloud
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Configuración
BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_TOKEN_AQUI")
CREDENTIALS_FILE = "user_credentials.json"

def load_user_credentials():
    """Carga las credenciales de usuarios desde archivo"""
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error cargando credenciales: {e}")
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
        with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(credentials, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error guardando credenciales: {e}")
        return False

def get_user_credentials(user_id):
    """Obtiene las credenciales de un usuario"""
    credentials = load_user_credentials()
    return credentials.get(str(user_id))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    welcome_text = """
🤖 **Bot de Cookies Amazon - VikingCookies** 🍪

🔐 *Autenticación personalizada por usuario*

**Comandos disponibles:**
/acc email@ejemplo.com contraseña - Configurar tu cuenta Amazon
/gencookie - Generar cookies con flujo completo
/micuenta - Ver tu cuenta configurada
/help - Mostrar ayuda
/status - Estado del bot

**Ejemplo:**
`/acc usuario@gmail.com micontraseña123`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def acc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /acc para configurar credenciales"""
    try:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
        message_text = update.message.text
        
        logger.info(f"Usuario {user_id} ({user_name}) ejecutó /acc")
        
        # Verificar si el mensaje tiene suficiente longitud
        if len(message_text.strip()) < 10:  # "/acc x@y.z p"
            await update.message.reply_text(
                "❌ **Formato incorrecto**\n\n"
                "**Uso correcto:**\n"
                "`/acc email@ejemplo.com contraseña`\n\n"
                "**Ejemplos:**\n"
                "`/acc usuario@gmail.com contraseña123`\n"
                "`/acc usuario@hotmail.com mi.contraseña`\n"
                "`/acc usuario@yahoo.com contraseña con espacios`",
                parse_mode='Markdown'
            )
            return
        
        # Dividir el mensaje en partes
        parts = message_text.split()
        
        # El formato debe ser: /acc email contraseña
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ **Faltan argumentos**\n\n"
                "Debes incluir email y contraseña.\n\n"
                "**Ejemplo:**\n"
                "`/acc tuemail@gmail.com tucontraseña`",
                parse_mode='Markdown'
            )
            return
        
        # Obtener email (segunda palabra)
        email = parts[1].strip()
        
        # Obtener contraseña (todo lo demás)
        password = ' '.join(parts[2:]).strip()
        
        # Validaciones básicas
        if not email or not password:
            await update.message.reply_text(
                "❌ **Email o contraseña vacíos**",
                parse_mode='Markdown'
            )
            return
        
        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                "❌ **Email inválido**\n\nPor favor ingresa un email válido",
                parse_mode='Markdown'
            )
            return
        
        if len(password) < 4:
            await update.message.reply_text(
                "❌ **Contraseña muy corta**\n\nLa contraseña debe tener al menos 4 caracteres",
                parse_mode='Markdown'
            )
            return
        
        # Guardar credenciales
        success = save_user_credentials(user_id, email, password)
        
        if success:
            # Mostrar contraseña oculta
            if len(password) > 3:
                password_display = password[0] + '•' * (len(password) - 2) + password[-1]
            else:
                password_display = '•' * len(password)
            
            confirmation_text = (
                f"✅ **¡Cuenta configurada exitosamente, {user_name}!** ✅\n\n"
                f"📧 **Email:** `{email}`\n"
                f"🔑 **Contraseña:** `{password_display}`\n"
                f"🆔 **Tu ID:** `{user_id}`\n\n"
                f"**Próximo paso:** Usa `/gencookie` para generar tus cookies de Amazon"
            )
            
            await update.message.reply_text(confirmation_text, parse_mode='Markdown')
            logger.info(f"Credenciales guardadas para usuario {user_id}")
            
        else:
            await update.message.reply_text(
                "❌ **Error al guardar credenciales**\n\nPor favor, intenta nuevamente",
                parse_mode='Markdown'
            )
            logger.error(f"Error guardando credenciales para usuario {user_id}")
            
    except Exception as e:
        logger.error(f"Error en acc_command: {e}")
        error_text = (
            "❌ **Error al procesar el comando**\n\n"
            "**Por favor, usa este formato:**\n"
            "`/acc email@ejemplo.com contraseña`\n\n"
            "**Ejemplo concreto:**\n"
            "`/acc miemail@gmail.com MiContraseña.123`\n\n"
            "Si el problema persiste, contacta al administrador."
        )
        await update.message.reply_text(error_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /help"""
    help_text = """
🆘 **AYUDA - VikingCookies Bot** 🍪

**📋 COMANDOS DISPONIBLES:**

`/start` - Mensaje de bienvenida
`/acc email contraseña` - Configurar cuenta Amazon
`/gencookie` - Generar cookies (flujo completo)
`/micuenta` - Ver tu cuenta configurada
`/status` - Estado del bot
`/help` - Esta ayuda

**🔐 CONFIGURACIÓN INICIAL:**

1. **Configura tu cuenta:**