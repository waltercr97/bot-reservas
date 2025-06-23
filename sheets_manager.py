# sheets_manager.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

def conectar_sheets():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    credentials_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
    
    return gspread.authorize(creds)

def guardar_cita(chat_id,nombre, telefono, fecha, hora):
    hoja = conectar_sheets().open("CitasReservadas").sheet1
    hoja.append_row([
        # NUEVO → ChatId
        str(chat_id),
        nombre,
        telefono,
        fecha,
        hora,
        "❌",              # Confirmado
        "❌",               # EnviadoRecordatorio
        "❌"   # Recordatorio30Min ← esta es la que falta
    ])
    print("✅ Cita guardada con chat_id.")
