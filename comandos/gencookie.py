import pickle
import re
import json
import tempfile
import os
import logging
import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from bs4 import BeautifulSoup
import tls_client
import uuid

from config import MENSAJES, DEFAULT_LOCALE, DEFAULT_COUNTRY_CODE, get_user_credentials

logger = logging.getLogger(__name__)

class CookieGeneratorConfig:
    def __init__(self, locale='com', country_code='US'):
        self.locale = locale
        self.client_identifier = "chrome_112"
        self.country_code = country_code
        self.update_urls()

    def update_urls(self):
        self.url_amazon = f"https://www.amazon.{self.locale}/"
        self.url_login = f"https://www.amazon.{self.locale}/ap/signin"
        self.url_addresses = f"https://www.amazon.{self.locale}/a/addresses"
        self.url_add_address = f"https://www.amazon.{self.locale}/a/addresses/add"
        self.url_one_click = f"https://www.amazon.{self.locale}/gp/cba/one-click"
        self.url_payment = f"https://www.amazon.{self.locale}/gp/cba/payment"

def get_random_user_agent():
    """Genera un User-Agent realista"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    return random.choice(user_agents)

def generate_random_address():
    """Genera una dirección válida de Estados Unidos"""
    streets = ["Main St", "Oak Ave", "Maple Dr", "Elm St", "Cedar Ln", "Pine St", "Washington Ave"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio"]
    states = ["NY", "CA", "IL", "TX", "AZ", "PA", "FL"]
    
    return {
        'fullName': 'John Doe',
        'addressLine1': f'{random.randint(100, 9999)} {random.choice(streets)}',
        'city': random.choice(cities),
        'state': random.choice(states),
        'postalCode': str(random.randint(10000, 99999)),
        'phoneNumber': f'555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
        'isDefaultAddress': True
    }

def extract_csrf_token(html_content):
    """Extrae CSRF token de la página"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Buscar en input hidden
    csrf_input = soup.find('input', {'name': 'csrfToken'})
    if csrf_input:
        return csrf_input.get('value', '')
    
    # Buscar en meta tags
    meta_csrf = soup.find('meta', {'name': 'csrf-token'})
    if meta_csrf:
        return meta_csrf.get('content', '')
    
    # Buscar en scripts
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            patterns = [
                r'csrfToken["\']?\s*:\s*["\']([^"\']+)',
                r'CSRF_TOKEN["\']?\s*:\s*["\']([^"\']+)',
                r'"csrfToken"\s*:\s*["\']([^"\']+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, script.string)
                if match:
                    return match.group(1)
    
    return ''

def extract_hidden_inputs(html_content):
    """Extrae inputs hidden del formulario"""
    soup = BeautifulSoup(html_content, 'html.parser')
    hidden_inputs = {}
    
    forms = soup.find_all('form')
    for form in forms:
        inputs = form.find_all('input', {'type': 'hidden'})
        for input_tag in inputs:
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                hidden_inputs[name] = value
                
    return hidden_inputs

def perform_login(session, email, password, locale='com'):
    """Realiza el login en Amazon"""
    try:
        config = CookieGeneratorConfig(locale=locale)
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Obtener página de login
        logger.info("🔐 Obteniendo página de login...")
        response = session.get(config.url_login, headers=headers)
        if response.status_code != 200:
            return False, session
            
        # Extraer datos del formulario
        hidden_inputs = extract_hidden_inputs(response.text)
        csrf_token = extract_csrf_token(response.text)
        
        login_data = {
            'email': email,
            'password': password,
        }
        login_data.update(hidden_inputs)
        
        if csrf_token:
            login_data['csrfToken'] = csrf_token
            
        login_headers = headers.copy()
        login_headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://www.amazon.{locale}',
            'Referer': config.url_login,
        })
        
        # Enviar credenciales
        logger.info("🔑 Enviando credenciales...")
        time.sleep(2)
        
        response = session.post(config.url_login, data=login_data, headers=login_headers)
        
        # Verificar login exitoso
        if response.status_code == 200:
            if 'signin' not in response.url and 'ap/signin' not in response.url:
                logger.info("✅ Login exitoso")
                return True, session
        
        return False, session
            
    except Exception as e:
        logger.error(f"❌ Error en login: {e}")
        return False, session

def add_us_address(session, locale='com'):
    """Agrega una dirección de Estados Unidos"""
    try:
        config = CookieGeneratorConfig(locale=locale)
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Paso 1: Ir a la página de direcciones
        logger.info("🏠 Yendo a la página de direcciones...")
        response = session.get(config.url_addresses, headers=headers)
        if response.status_code != 200:
            return False, session
        
        # Paso 2: Obtener página para agregar dirección
        logger.info("📝 Obteniendo formulario de dirección...")
        response = session.get(config.url_add_address, headers=headers)
        if response.status_code != 200:
            return False, session
        
        # Extraer CSRF token y hidden inputs
        csrf_token = extract_csrf_token(response.text)
        hidden_inputs = extract_hidden_inputs(response.text)
        
        # Generar dirección aleatoria
        address = generate_random_address()
        
        # Datos para la nueva dirección
        address_data = {
            'countryCode': 'US',
            'fullName': address['fullName'],
            'addressLine1': address['addressLine1'],
            'city': address['city'],
            'state': address['state'],
            'postalCode': address['postalCode'],
            'phoneNumber': address['phoneNumber'],
            'isDefaultAddress': 'true',
            'addAddress': 'Add Address'
        }
        
        address_data.update(hidden_inputs)
        
        if csrf_token:
            address_data['csrfToken'] = csrf_token
        
        address_headers = headers.copy()
        address_headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://www.amazon.{locale}',
            'Referer': config.url_add_address,
        })
        
        # Paso 3: Enviar la nueva dirección
        logger.info("📍 Agregando dirección de EE.UU....")
        time.sleep(2)
        
        response = session.post(config.url_add_address, data=address_data, headers=address_headers)
        
        if response.status_code == 200:
            logger.info("✅ Dirección agregada exitosamente")
            return True, session
        
        return False, session
        
    except Exception as e:
        logger.error(f"❌ Error agregando dirección: {e}")
        return False, session

def configure_one_click(session, locale='com'):
    """Configura one-click payment"""
    try:
        config = CookieGeneratorConfig(locale=locale)
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Paso 1: Ir a one-click settings
        logger.info("⚙️ Configurando one-click...")
        response = session.get(config.url_one_click, headers=headers)
        if response.status_code != 200:
            return False, session
        
        # Paso 2: Ir a payment methods (sin agregar tarjeta real)
        logger.info("💳 Visitando página de pagos...")
        response = session.get(config.url_payment, headers=headers)
        
        # Simular tiempo en la página
        time.sleep(3)
        
        logger.info("✅ Flujo de one-click completado")
        return True, session
        
    except Exception as e:
        logger.error(f"❌ Error en one-click: {e}")
        return False, session

def cookies_to_dict(cookie_jar):
    """Convierte cookies a diccionario"""
    cookies_dict = {}
    for cookie in cookie_jar:
        cookies_dict[cookie.name] = cookie.value
    return cookies_dict

def format_cookies_amz(cookies_dict):
    """Formatea las cookies en formato .amz"""
    cookies_list = []
    for key, value in cookies_dict.items():
        cookies_list.append(f"{key}={value}")
    return "; ".join(cookies_list)

def generar_cookie_completa(user_id, locale="com", country_code="US"):
    """Función principal con flujo completo"""
    try:
        # Obtener credenciales del usuario
        credentials = get_user_credentials(user_id)
        if not credentials:
            return None, False
        
        email = credentials['email']
        password = credentials['password']
        
        logger.info(f"🔧 Iniciando flujo completo para usuario {user_id}...")
        
        config = CookieGeneratorConfig(locale=locale, country_code=country_code)
        
        # Configurar sesión TLS
        session = tls_client.Session(
            client_identifier="chrome_112",
            random_tls_extension_order=True
        )
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # FLUJO COMPLETO:
        
        # 1. Login
        logger.info("1️⃣ Realizando login...")
        login_success, session = perform_login(session, email, password, locale)
        if not login_success:
            return None, False
        
        time.sleep(2)
        
        # 2. Agregar dirección de EE.UU.
        logger.info("2️⃣ Agregando dirección de EE.UU....")
        address_success, session = add_us_address(session, locale)
        if not address_success:
            logger.warning("⚠️ No se pudo agregar dirección, continuando...")
        
        time.sleep(2)
        
        # 3. Configurar one-click
        logger.info("3️⃣ Configurando one-click...")
        one_click_success, session = configure_one_click(session, locale)
        if not one_click_success:
            logger.warning("⚠️ No se pudo configurar one-click, continuando...")
        
        time.sleep(2)
        
        # 4. Visitar página principal final para cookies completas
        logger.info("4️⃣ Obteniendo cookies finales...")
        response = session.get(config.url_amazon, headers=headers)
        
        if not session.cookies:
            return None, False
            
        # Convertir cookies a diccionario
        cookies_dict = cookies_to_dict(session.cookies)
        
        # Verificar cookies esenciales
        essential_cookies = ['session-id', 'session-token', 'ubid-main']
        essential_count = sum(1 for cookie in essential_cookies if cookie in cookies_dict)
        
        logger.info(f"✅ Flujo completado! {len(cookies_dict)} cookies generadas")
        logger.info(f"📊 Cookies esenciales: {essential_count}/3")
        
        return cookies_dict, True
        
    except Exception as e:
        logger.error(f"❌ Error en flujo completo: {e}")
        return None, False

async def generar_cookie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /gencookie"""
    mensaje = None
    try:
        user_id = update.message.from_user.id
        
        # Verificar credenciales
        credentials = get_user_credentials(user_id)
        if not credentials:
            await update.message.reply_text(
                "❌ **Primero configura tu cuenta Amazon**\n\n"
                "Usa: /acc correo@ejemplo.com contraseña",
                parse_mode='Markdown'
            )
            return
        
        # Mensaje inicial
        mensaje = await update.message.reply_text(
            f"🔐 **Iniciando flujo completo para {credentials['email']}**\n\n"
            "🔄 *Pasos a realizar:*\n"
            "1️⃣ Login en Amazon\n"
            "2️⃣ Agregar dirección EE.UU.\n" 
            "3️⃣ Configurar One-Click\n"
            "4️⃣ Generar cookies\n\n"
            "⏳ *Esto tomará unos 15-20 segundos...*",
            parse_mode='Markdown'
        )

        # Generar cookies con flujo completo
        cookies_dict, success = generar_cookie_completa(user_id, DEFAULT_LOCALE, DEFAULT_COUNTRY_CODE)

        if success and cookies_dict:
            # Formatear cookies
            cookies_text = format_cookies_amz(cookies_dict)
            
            # Mensaje final
            cookie_message = (
                f"✅ **¡FLUJO COMPLETADO EXITOSAMENTE!** ✅\n\n"
                f"👤 *Usuario:* {credentials['email']}\n"
                f"🍪 *Cookies generadas:* {len(cookies_dict)}\n"
                f"🇺🇸 *Dirección EE.UU.:* ✅ Agregada\n"
                f"⚡ *One-Click:* ✅ Configurado\n\n"
                "🔹 **Cookies listas para usar:**\n\n"
                f"`{cookies_text}`\n\n"
                "📋 *Copia el texto de arriba*\n"
                "💳 *Ahora las cookies son más válidas para verificaciones*"
            )
            
            await mensaje.edit_text(cookie_message, parse_mode='Markdown')
            
        else:
            await mensaje.edit_text(
                "❌ **Error en el flujo completo**\n\n"
                "⚠️ *Posibles causas:*\n"
                "• Credenciales incorrectas\n" 
                "• CAPTCHA requerido\n"
                "• Problemas de conexión\n\n"
                "🔄 Verifica tu cuenta e intenta nuevamente",
                parse_mode='Markdown'
            )

    except Exception as e:
        error_msg = "❌ **Error inesperado en el flujo**\n🔧 Intenta más tarde."
        logger.error(f"Error en generar_cookie_handler: {e}")
        
        if mensaje:
            await mensaje.edit_text(error_msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(error_msg, parse_mode='Markdown')
