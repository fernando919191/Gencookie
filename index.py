import asyncio
import logging
import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, MENSAJES, DEBUG, save_user_credentials, get_user_credentials
from comandos.gencookie import generar_cookie_handler

# Configurar logging para DisCloud
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not DEBUG else logging.DEBUG
)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    await update.message.reply_text(
        MENSAJES["inicio"],
        parse_mode='Markdown'
    )

async def acc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /acc para configurar credenciales"""
    try:
        user_id = update.message.from_user.id
        args = context.args
        
        if len(args) < 2:
            await update.message.reply_text(
                MENSAJES["error_formato"],
                parse_mode='Markdown'
            )
            return
        
        email = args[0]
        password = " ".join(args[1:])  # La contraseña puede tener espacios
        
        # Validar formato de email básico
        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                "❌ **Email inválido**\n\nPor favor ingresa un email válido",
                parse_mode='Markdown'
            )
            return
        
        # Guardar credenciales
        success = save_user_credentials(user_id, email, password)
        
        if success:
            # Mostrar confirmación (ocultando contraseña)
            password_display = password[0] + '*' * (len(password) - 2) + password[-1] if len(password) > 2 else '***'
            await update.message.reply_text(
                f"✅ **Cuenta configurada exitosamente!**\n\n"
                f"📧 *Email:* {email}\n"
                f"🔑 *Contraseña:* {password_display}\n\n"
                f"Ahora usa /gencookie para generar tus cookies",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ **Error al guardar credenciales**\n\nIntenta nuevamente",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error en acc_command: {e}")
        await update.message.reply_text(
            "❌ **Error al procesar comando**\n\nIntenta nuevamente",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /help"""
    help_text = """
🤖 *Comandos disponibles:*

/acc correo@ejemplo.com contraseña - Configurar tu cuenta Amazon
/gencookie - Generar cookies con tu cuenta
/help - Muestra esta ayuda
/start - Inicia el bot
/status - Estado del bot
/micuenta - Ver tu cuenta configurada
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /status"""
    status_text = """
✅ *Bot funcionando correctamente*

🌎 *Amazon Cookie Generator*
🔐 *Autenticación:* Por usuario
📊 *Estado:* Activo
    """
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def micuenta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /micuenta"""
    try:
        user_id = update.message.from_user.id
        credentials = get_user_credentials(user_id)
        
        if credentials:
            email = credentials['email']
            password_display = credentials['password'][0] + '*' * (len(credentials['password']) - 2) + credentials['password'][-1] if len(credentials['password']) > 2 else '***'
            
            await update.message.reply_text(
                f"📋 **Tu cuenta configurada:**\n\n"
                f"👤 *Usuario:* {update.message.from_user.first_name}\n"
                f"📧 *Email:* {email}\n"
                f"🔑 *Contraseña:* {password_display}\n\n"
                f"Última actualización: <code>{time.ctime(credentials['timestamp'])}</code>",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                MENSAJES["credenciales_faltantes"],
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error en micuenta_command: {e}")
        await update.message.reply_text(
            "❌ **Error al obtener información de la cuenta**",
            parse_mode='Markdown'
        )

def main():
    """Función principal para iniciar el bot en DisCloud"""
    try:
        # Verificar que el token esté configurado
        if BOT_TOKEN == "TU_TOKEN_AQUI":
            logger.error("❌ ERROR: Configura BOT_TOKEN en las variables de entorno de DisCloud")
            print("❌ ERROR: Configura BOT_TOKEN en las variables de entorno de DisCloud")
            return
        
        # Crear la aplicación
        application = Application.builder().token(BOT_TOKEN).build()

        # Añadir handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("acc", acc_command))
        application.add_handler(CommandHandler("gencookie", generar_cookie_handler))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("micuenta", micuenta_command))

        # Iniciar el bot
        logger.info("🤖 Bot iniciado en DisCloud...")
        print("🚀 Amazon Cookie Bot (con login por usuario) está funcionando!")
        application.run_polling()

    except Exception as e:
        logger.error(f"❌ Error al iniciar el bot: {e}")
        print(f"❌ Error al iniciar el bot: {e}")

if __name__ == "__main__":
    main()
