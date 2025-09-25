import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, BOT_PREFIX, MENSAJES
from comandos.gencookie import generar_cookie_handler

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Función principal para iniciar el bot"""
    # Crear la aplicación
    application = Application.builder().token(BOT_TOKEN).build()

    # Añadir handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gencookie", generar_cookie_handler))

    # Iniciar el bot
    print("🤖 Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
