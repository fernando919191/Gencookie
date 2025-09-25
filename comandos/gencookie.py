import re
import json
import logging
import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from bs4 import BeautifulSoup
import tls_client

from config import get_user_credentials

logger = logging.getLogger(__name__)

class AmazonBot:
    def __init__(self, locale='com'):
        self.locale = locale
        self.session = None
        self.urls = {
            'login': f'https://www.amazon.{locale}/ap/signin',
            'home': f'https://www.amazon.{locale}',
            'address': f'https://www.amazon.{locale}/a/addresses',
            'add_address': f'https://www.amazon.{locale}/a/addresses/add',
            'payment': f'https://www.amazon.{locale}/gp/cba/payment'
        }
    
    def get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def init_session(self):
        """Inicializa la sesión TLS"""
        try:
            self.session = tls_client.Session(
                client_identifier="chrome_112",
                random_tls_extension_order=True
            )
            return True
        except Exception as e:
            logger.error(f"Error iniciando sesión: {e}")
            return False
    
    def extract_csrf_token(self, html):
        """Extrae token CSRF de la página"""
        try:
            patterns = [
                r'csrfToken["\']?\s*:\s*["\']([^"\']+)',
                r'CSRF_TOKEN["\']?\s*:\s*["\']([^"\']+)',
                r'name="csrfToken"\s+value="([^"]+)"'
            ]
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    return match.group(1)
            return None
        except Exception as e:
            logger.error(f"Error extrayendo CSRF: {e}")
            return None
    
    def login(self, email, password):
        """Realiza login en Amazon"""
        try:
            logger.info("🔐 Iniciando login...")
            
            # Obtener página de login
            response = self.session.get(self.urls['login'], headers=self.get_headers())
            if response.status_code != 200:
                return False
            
            # Extraer CSRF token
            csrf_token = self.extract_csrf_token(response.text)
            
            # Preparar datos de login
            login_data = {
                'email': email,
                'password': password,
                'rememberMe': 'true'
            }
            
            if csrf_token:
                login_data['csrfToken'] = csrf_token
            
            # Headers para login
            login_headers = self.get_headers()
            login_headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': f'https://www.amazon.{self.locale}',
                'Referer': self.urls['login'],
            })
            
            # Enviar login
            time.sleep(2)
            response = self.session.post(self.urls['login'], data=login_data, headers=login_headers)
            
            # Verificar si el login fue exitoso
            if response.status_code == 200:
                if 'signin' not in response.url:
                    logger.info("✅ Login exitoso")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return False
    
    def visit_address_page(self):
        """Visita la página de direcciones"""
        try:
            logger.info("🏠 Visitando página de direcciones...")
            response = self.session.get(self.urls['address'], headers=self.get_headers())
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error visitando direcciones: {e}")
            return False
    
    def visit_payment_page(self):
        """Visita la página de pagos"""
        try:
            logger.info("💳 Visitando página de pagos...")
            response = self.session.get(self.urls['payment'], headers=self.get_headers())
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Error visitando pagos: {e}")
            return False
    
    def get_cookies(self):
        """Obtiene las cookies de la sesión"""
        try:
            if not self.session or not self.session.cookies:
                return None
            
            cookies_dict = {}
            for cookie in self.session.cookies:
                cookies_dict[cookie.name] = cookie.value
            
            return cookies_dict
        except Exception as e:
            logger.error(f"Error obteniendo cookies: {e}")
            return None

def format_cookies_amz(cookies_dict):
    """Formatea las cookies en formato .amz"""
    if not cookies_dict:
        return ""
    
    cookies_list = []
    for key, value in cookies_dict.items():
        cookies_list.append(f"{key}={value}")
    
    return "; ".join(cookies_list)

def generar_cookie_completa(user_id, locale="com", country_code="US"):
    """Función principal para generar cookies"""
    try:
        logger.info(f"🔧 Iniciando generación para usuario {user_id}")
        
        # Obtener credenciales
        credentials = get_user_credentials(user_id)
        if not credentials:
            logger.error("❌ No hay credenciales")
            return None, False
        
        email = credentials['email']
        password = credentials['password']
        
        # Crear bot de Amazon
        bot = AmazonBot(locale=locale)
        
        # Inicializar sesión
        if not bot.init_session():
            return None, False
        
        # Paso 1: Login
        if not bot.login(email, password):
            logger.error("❌ Falló el login")
            return None, False
        
        time.sleep(3)
        
        # Paso 2: Visitar página de direcciones
        if not bot.visit_address_page():
            logger.warning("⚠️ No se pudo visitar direcciones")
        
        time.sleep(2)
        
        # Paso 3: Visitar página de pagos
        if not bot.visit_payment_page():
            logger.warning("⚠️ No se pudo visitar pagos")
        
        time.sleep(2)
        
        # Paso 4: Obtener cookies finales
        cookies_dict = bot.get_cookies()
        
        if not cookies_dict:
            logger.error("❌ No se obtuvieron cookies")
            return None, False
        
        # Verificar cookies esenciales
        essential_cookies = ['session-id', 'session-token', 'ubid-main']
        essential_found = [cookie for cookie in essential_cookies if cookie in cookies_dict]
        
        logger.info(f"✅ {len(cookies_dict)} cookies obtenidas")
        logger.info(f"🔑 Cookies esenciales encontradas: {len(essential_found)}/{len(essential_cookies)}")
        
        return cookies_dict, True
        
    except Exception as e:
        logger.error(f"❌ Error en generación completa: {e}")
        return None, False

async def generar_cookie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /gencookie"""
    mensaje = None
    try:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
        
        # Verificar credenciales
        credentials = get_user_credentials(user_id)
        if not credentials:
            await update.message.reply_text(
                "❌ **Primero configura tu cuenta**\nUsa: /acc email contraseña",
                parse_mode='Markdown'
            )
            return
        
        # Mensaje de inicio
        mensaje = await update.message.reply_text(
            f"🔐 **Generando cookies para {user_name}**\n\n"
            f"📧 **Cuenta:** {credentials['email']}\n"
            "🔄 **Procesando... (15-20 segundos)**\n"
            "⏳ *Por favor espera...*",
            parse_mode='Markdown'
        )
        
        # Generar cookies
        cookies_dict, success = generar_cookie_completa(user_id)
        
        if success and cookies_dict:
            cookies_text = format_cookies_amz(cookies_dict)
            
            # Contar cookies esenciales
            essential = ['session-id', 'session-token', 'ubid-main']
            essential_count = sum(1 for cookie in essential if cookie in cookies_dict)
            
            success_message = (
                f"✅ **¡COOKIES GENERADAS EXITOSAMENTE!** ✅\n\n"
                f"👤 **Usuario:** {user_name}\n"
                f"🍪 **Total cookies:** {len(cookies_dict)}\n"
                f"🔑 **Esenciales:** {essential_count}/3\n\n"
                "**TUS COOKIES:**\n\n"
                f"`{cookies_text}`\n\n"
                "📋 **Copia el texto de arriba**\n"
                "💳 **Listas para usar**"
            )
            
            await mensaje.edit_text(success_message, parse_mode='Markdown')
            
        else:
            error_message = (
                "❌ **Error al generar cookies**\n\n"
                "**Causas posibles:**\n"
                "• Credenciales incorrectas\n"
                "• Cuenta bloqueada temporalmente\n"
                "• CAPTCHA requerido\n"
                "• Problemas de conexión\n\n"
                "**Solución:**\n"
                "1. Verifica tu cuenta con `/micuenta`\n"
                "2. Espera 10 minutos e intenta nuevamente\n"
                "3. Si persiste, usa una cuenta diferente"
            )
            
            await mensaje.edit_text(error_message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"❌ Error en handler: {e}")
        error_msg = "❌ **Error inesperado**\nIntenta más tarde."
        
        if mensaje:
            await mensaje.edit_text(error_msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(error_msg, parse_mode='Markdown')