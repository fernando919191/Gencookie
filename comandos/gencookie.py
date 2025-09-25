import pickle
import re
import json
import tempfile
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bs4 import BeautifulSoup
import tls_client

from config import MENSAJES, DEFAULT_LOCALE, DEFAULT_COUNTRY_CODE

logger = logging.getLogger(__name__)

class CookieGeneratorConfig:
    def __init__(self, locale='com', country_code='US'):
        self.locale = locale
        self.client_identifier = "chrome_112"
        self.country_code = country_code
        self.update_urls()

    def update_urls(self):
        self.url_amazon = f"https://www.amazon.{self.locale}/"
        self.url_glow_rendered_address_selections = f"https://www.amazon.{self.locale}/portal-migration/hz/glow/get-rendered-address-selections"
        self.url_glow_address_change = f"https://www.amazon.{self.locale}/portal-migration/hz/glow/address-change"

def send_request(url, session, method="GET", headers=None, params=None, json_data=None):
    try:
        if method == "GET":
            response = session.get(url, headers=headers, params=params)
        elif method == "POST":
            response = session.post(url, headers=headers, params=params, json=json_data)
        else:
            return None, session
            
        return response, session
    except Exception as e:
        logger.error(f"Error en send_request: {e}")
        return None, session

def extract_anti_csrf_token(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        token_element = soup.find('span', {'id': 'nav-global-location-data-modal-action'})
        
        if token_element:
            data_modal = token_element.get('data-a-modal')
            if data_modal:
                cleaned_data = data_modal.replace('&quot;', '"')
                data_modal_json = json.loads(cleaned_data)
                anti_csrf_token = data_modal_json.get('ajaxHeaders', {}).get('anti-csrftoken-a2z', '')
                if anti_csrf_token:
                    return anti_csrf_token
        
        # Buscar en scripts como fallback
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                match = re.search(r'anti-csrftoken-a2z["\']?\s*:\s*["\']([^"\']+)', script.string)
                if match:
                    return match.group(1)
                    
        return None
    except Exception as e:
        logger.error(f"Error extrayendo anti-csrf token: {e}")
        return None

def extract_csrf_token(response_text):
    try:
        patterns = [
            r'CSRF_TOKEN\s*:\s*["\']([^"\']+)',
            r'csrfToken\s*:\s*["\']([^"\']+)',
            r'"csrfToken"\s*:\s*["\']([^"\']+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Error extrayendo CSRF token: {e}")
        return None

def generar_cookie_amazon(locale="com", country_code="US"):
    """Función principal para generar cookies de Amazon"""
    try:
        logger.info("🔧 Iniciando generación de cookie...")
        
        config = CookieGeneratorConfig(locale=locale, country_code=country_code)
        
        # Configurar sesión TLS
        session = tls_client.Session(
            client_identifier="chrome_112",
            random_tls_extension_order=True
        )
        
        # Headers realistas
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Paso 1: Obtener página principal
        logger.info("🌐 Obteniendo página principal de Amazon...")
        response, session = send_request(config.url_amazon, session, "GET", headers=headers)
        
        if not response or response.status_code != 200:
            logger.error(f"❌ Error al obtener página principal: {response.status_code if response else 'No response'}")
            return None, False
            
        # Paso 2: Extraer anti-CSRF token
        logger.info("🔑 Extrayendo anti-CSRF token...")
        anti_csrf_token = extract_anti_csrf_token(response.text)
        
        if not anti_csrf_token:
            logger.warning("⚠️ No se pudo extraer anti-CSRF token, usando fallback")
            anti_csrf_token = "fallback_token"
        
        # Paso 3: Obtener rendered address selections
        logger.info("📋 Obteniendo selecciones de dirección...")
        params = {
            'deviceType': 'desktop',
            'pageType': 'Gateway',
            'storeContext': 'NoStoreName',
            'actionSource': 'desktop-modal',
        }
        
        headers['anti-csrftoken-a2z'] = anti_csrf_token
        
        response, session = send_request(
            config.url_glow_rendered_address_selections, 
            session, "GET", headers=headers, params=params
        )
        
        if not response or response.status_code != 200:
            logger.error(f"❌ Error en rendered address: {response.status_code if response else 'No response'}")
            return None, False
        
        # Paso 4: Extraer CSRF token
        logger.info("🔑 Extrayendo CSRF token...")
        csrf_token = extract_csrf_token(response.text)
        
        if not csrf_token:
            logger.warning("⚠️ No se pudo extraer CSRF token, usando anti-CSRF")
            csrf_token = anti_csrf_token
        
        # Paso 5: Cambiar dirección
        logger.info("🌍 Cambiando ubicación...")
        headers['anti-csrftoken-a2z'] = csrf_token
        
        json_data = {
            'locationType': 'COUNTRY',
            'district': country_code,
            'countryCode': country_code,
            'deviceType': 'web',
            'storeContext': 'generic',
            'pageType': 'Gateway',
            'actionSource': 'glow',
        }
        
        response, session = send_request(
            config.url_glow_address_change,
            session, "POST", headers=headers, params={'actionSource': 'glow'}, json_data=json_data
        )
        
        # Verificar respuesta
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                if response_data.get("isAddressUpdated") == 1:
                    logger.info("✅ Dirección actualizada exitosamente")
                else:
                    logger.warning("⚠️ Dirección no actualizada, pero continuando...")
            except:
                logger.warning("⚠️ No se pudo parsear respuesta JSON, pero continuando...")
        
        # Paso 6: Guardar cookies
        logger.info("💾 Guardando cookies...")
        
        if not session.cookies:
            logger.error("❌ No se generaron cookies")
            return None, False
            
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
            pickle.dump(dict(session.cookies), temp_file)
            temp_path = temp_file.name
            
        logger.info(f"✅ Cookies guardadas en: {temp_path}")
        return temp_path, True
        
    except Exception as e:
        logger.error(f"❌ Error en generar_cookie_amazon: {e}")
        return None, False

async def generar_cookie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /gencookie"""
    mensaje = None
    try:
        # Enviar mensaje de "generando..."
        mensaje = await update.message.reply_text(
            "🔄 *Generando cookie de Amazon US...*\n\n⏳ Esto puede tomar unos segundos...",
            parse_mode='Markdown'
        )

        # Generar la cookie
        cookie_path, success = generar_cookie_amazon(DEFAULT_LOCALE, DEFAULT_COUNTRY_CODE)

        if success and cookie_path:
            # Editar el mensaje original
            await mensaje.edit_text(
                "✅ **¡Cookie generada exitosamente!**\n\n"
                "🌎 *País:* Amazon US\n"
                "📊 *Estado:* Lista para descargar\n"
                "⬇️ *Enviando archivo...*"
            )
            
            # Enviar el archivo
            with open(cookie_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename="amazon_us_cookies.pkl",
                    caption="🍪 **Cookie de Amazon US generada**\n\n✅ *Lista para usar en tus proyectos*"
                )
            
            # Limpiar archivo temporal
            os.unlink(cookie_path)
            
        else:
            await mensaje.edit_text(
                "❌ **Error al generar la cookie**\n\n"
                "⚠️ *Por favor, intenta nuevamente en unos minutos.*"
            )

    except Exception as e:
        error_msg = "❌ **Error inesperado**\n\n🔄 *Por favor, intenta más tarde.*"
        logger.error(f"❌ Error en generar_cookie_handler: {e}")
        
        if mensaje:
            await mensaje.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg, parse_mode='Markdown')
