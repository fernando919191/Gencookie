import pickle
import re
import json
import tempfile
import os
from telegram import Update
from telegram.ext import ContextTypes
from bs4 import BeautifulSoup
import tls_client

from config import MENSAJES, DEFAULT_LOCALE, DEFAULT_COUNTRY_CODE

class CookieGeneratorConfig:
    def __init__(self, locale='com', country_code='US'):
        self.locale = locale
        self.client_identifier = "chrome_112"
        self.zip_code = 10115
        self.country_code = country_code
        self.update_urls()

    def update_urls(self):
        self.url_amazon = f"https://www.amazon.{self.locale}/"
        self.url_glow_rendered_address_selections = f"https://www.amazon.{self.locale}/portal-migration/hz/glow/get-rendered-address-selections"
        self.url_glow_address_change = f"https://www.amazon.{self.locale}/portal-migration/hz/glow/address-change"

class InvalidRequestMethodException(Exception):
    pass

class RequestErrorException(Exception):
    pass

class TokenElementNotFoundException(Exception):
    pass

class DataModalNotFoundException(Exception):
    pass

class AntiCsrfTokenNotFoundException(Exception):
    pass

class CsrfTokenNotFoundException(Exception):
    pass

def aligned_print(label, value, width=20):
    print(f"{label + ':':<{width}}{value}")

def send_request(url, session, method="GET", headers=None, params=None, json=None):
    if method == "GET":
        response = session.get(url, headers=headers, params=params, json=json)
    elif method == "POST":
        response = session.post(url, headers=headers, params=params, json=json)
    else:
        raise InvalidRequestMethodException

    if response.status_code == 200:
        return response, session
    else:
        raise RequestErrorException(f"Error retrieving the webpage: Status code {response.status_code}")

def extract_anti_csrf_token(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    token_element = soup.find('span', {'id': 'nav-global-location-data-modal-action'})
    if token_element:
        data_modal = token_element.get('data-a-modal')
        if data_modal:
            data_modal_json = json.loads(data_modal.replace('&quot;', '"'))
            anti_csrf_token = data_modal_json.get('ajaxHeaders', {}).get('anti-csrftoken-a2z', '')
            if anti_csrf_token:
                return anti_csrf_token
            else:
                raise AntiCsrfTokenNotFoundException
        else:
            raise DataModalNotFoundException
    else:
        raise TokenElementNotFoundException

def extract_csrf_token(response_text):
    match = re.search(r'CSRF_TOKEN : "(.+?)"', response_text)
    if match:
        return match.group(1)
    else:
        raise CsrfTokenNotFoundException

def generar_cookie_amazon(locale="com", country_code="US"):
    """Función principal para generar cookies de Amazon"""
    try:
        config = CookieGeneratorConfig(locale=locale, country_code=country_code)

        url_amazon = config.url_amazon
        url_glow_rendered_address_selections = config.url_glow_rendered_address_selections
        url_glow_address_change = config.url_glow_address_change
        client_identifier = config.client_identifier
        country_code = config.country_code

        session = tls_client.Session(client_identifier=client_identifier, random_tls_extension_order=True)
        amazon_base_response, session = send_request(url_amazon, session, "GET")
        html_content = amazon_base_response.text

        anti_csrf_token = extract_anti_csrf_token(html_content)
        aligned_print("Anti-CSRF-Token", anti_csrf_token)

        headers = {'anti-csrftoken-a2z': anti_csrf_token}
        params = {
            'deviceType': 'desktop',
            'pageType': 'Gateway',
            'storeContext': 'NoStoreName',
            'actionSource': 'desktop-modal',
        }

        rendered_address_selection_response, session = send_request(
            url_glow_rendered_address_selections, session, "GET", params=params, headers=headers
        )

        csrf_token = extract_csrf_token(rendered_address_selection_response.text)
        aligned_print("CSRF-TOKEN", csrf_token)

        headers['anti-csrftoken-a2z'] = csrf_token
        params = {'actionSource': 'glow'}

        json_data = {
            'locationType': 'COUNTRY',
            'district': country_code,
            'countryCode': country_code,
            'deviceType': 'web',
            'storeContext': 'generic',
            'pageType': 'Gateway',
            'actionSource': 'glow',
        }

        glow_address_change_response, session = send_request(
            url_glow_address_change, session, "POST", headers=headers, params=params, json=json_data
        )

        aligned_print('HTTP Status Code', glow_address_change_response.status_code)

        if glow_address_change_response.json().get("isAddressUpdated") == 1:
            aligned_print('Success', "True")
            
            # Guardar cookies en archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
                pickle.dump(session.cookies, temp_file)
                temp_path = temp_file.name
            
            return temp_path, True
        else:
            aligned_print('Success', "False")
            return None, False

    except Exception as e:
        aligned_print('Error', str(e))
        return None, False

async def generar_cookie_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /gencookie"""
    try:
        # Enviar mensaje de "generando..."
        mensaje = await update.message.reply_text(
            MENSAJES["generando"],
            parse_mode='Markdown'
        )

        # Generar la cookie
        cookie_path, success = generar_cookie_amazon(DEFAULT_LOCALE, DEFAULT_COUNTRY_CODE)

        if success and cookie_path:
            # Editar el mensaje original
            await mensaje.edit_text(
                f"✅ {MENSAJES['cookie_lista']}\n\n"
                f"🌎 *País:* Amazon US\n"
                f"📊 *Estado:* Generada exitosamente\n"
                f"📁 *Archivo listo para descargar*"
            )
            
            # Enviar el archivo
            with open(cookie_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename="amazon_us_cookie.pkl",
                    caption="🍪 **Cookie de Amazon US generada**"
                )
            
            # Limpiar archivo temporal
            os.unlink(cookie_path)
            
        else:
            await mensaje.edit_text(
                f"❌ *Error al generar la cookie*\n\n"
                f"Por favor, intenta nuevamente más tarde."
            )

    except Exception as e:
        error_msg = f"❌ *Error inesperado:* {str(e)}"
        if 'mensaje' in locals():
            await mensaje.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg, parse_mode='Markdown')
