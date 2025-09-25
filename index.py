import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, MENSAJES, DEBUG
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /help"""
    help_text = """
🤖 *Comandos disponibles:*

/gencookie - Genera cookies para Amazon US
/help - Muestra esta ayuda
/start - Inicia el bot
/status - Estado del bot
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /status"""
    status_text = """
✅ *Bot funcionando correctamente*

🌎 *Amazon US Cookie Generator*
📊 *Estado:* Activo
🕒 *Servicio:* DisCloud
    """
    await update.message.reply_text(status_text, parse_mode='Markdown')

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
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("gencookie", generar_cookie_handler))

        # Iniciar el bot
        logger.info("🤖 Bot iniciado en DisCloud...")
        print("🚀 Amazon Cookie Bot está funcionando!")
        application.run_polling()

    except Exception as e:
        logger.error(f"❌ Error al iniciar el bot: {e}")
        print(f"❌ Error al iniciar el bot: {e}")

if __name__ == "__main__":
    main()
