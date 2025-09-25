import os
import json
import time

def load_user_credentials():
    """Carga las credenciales de usuarios desde archivo"""
    try:
        if os.path.exists("user_credentials.json"):
            with open("user_credentials.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def get_user_credentials(user_id):
    """Obtiene las credenciales de un usuario"""
    credentials = load_user_credentials()
    return credentials.get(str(user_id))