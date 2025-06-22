# reminders.py

import datetime
from sheets_manager import conectar_sheets
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from dateutil import parser
import schedule
import time
import asyncio

TOKEN = "7863830955:AAF-7wjYMnUP9JT2RsNxCaTIDTG_6hgMvzA"

# Función para enviar recordatorio 1 día antes con botones

def enviar_recordatorios():
    client = conectar_sheets()
    sheet = client.open("CitasReservadas").sheet1
    filas = sheet.get_all_records()

    hoy = datetime.date.today()
    bot = Bot(token=TOKEN)

    for i, fila in enumerate(filas, start=2):
        fecha_str = fila["Fecha"]
        confirmado = fila["Confirmado"]
        recordado = fila["EnviadoRecordatorio"]

        try:
            fecha_cita = parser.parse(fecha_str, dayfirst=True).date()
        except:
            continue

        diferencia = int((fecha_cita - hoy).days)

        if diferencia == 1 and confirmado != "✅" and recordado != "✅":
            chat_id = fila.get("ChatId")
            if int(chat_id):
                mensaje = (
                    f"Hola {fila['Nombre']}, tienes una cita mañana a las {fila['Hora']}.")
                botones = [
                    [
                        InlineKeyboardButton("✅ Confirmar", callback_data=f"confirmar_{i}"),
                        InlineKeyboardButton("❌ Cancelar", callback_data=f"cancelar_{i}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(botones)
                try:
                    async def _send(chat_id, mensaje, markup):
                        await bot.send_message(chat_id=chat_id, text=mensaje, reply_markup=markup)
                        # … dentro del for:
                    asyncio.run(_send(int(chat_id), mensaje, reply_markup))

                    print(f"✅ Recordatorio enviado a {fila['Nombre']}")
                    sheet.update_cell(i, 7, "✅")
                except Exception as e:
                    print(f"❌ Error al enviar mensaje: {e}")
            else:
                print(f"⚠️ No se encontró chat_id para {fila['Nombre']}")


def enviar_recordatorios_30min():
    client = conectar_sheets()
    sheet = client.open("CitasReservadas").sheet1
    filas = sheet.get_all_records()
    ahora = datetime.datetime.now()
    bot = Bot(token=TOKEN)

    for i, fila in enumerate(filas, start=2):

        fecha_str = fila["Fecha"]
        hora_str = fila["Hora"]
        confirmado = fila["Confirmado"]
        recordado_30 = fila.get("Recordatorio30Min", "")

        try:
            fecha_hora_cita = parser.parse(f"{fecha_str} {hora_str}", dayfirst=True)
        except:
            continue

        diferencia = int((fecha_hora_cita - ahora).total_seconds() / 60)
        if 29 <= diferencia <= 31 and confirmado == "✅" and recordado_30 != "✅":
            
            chat_id = fila.get("ChatId")
            if int(chat_id):
                mensaje = (
                    f"¡Hola {fila['Nombre']}! Tu cita es en 30 minutos (a las {hora_str}).\n¡Te esperamos!")
                try:
                    async def enviar_recordatorio():
                        await bot.send_message(chat_id=int(chat_id), text=mensaje)
                    asyncio.run(enviar_recordatorio())
                    print(f"✅ Recordatorio 30 min enviado a {fila['Nombre']}")
                    sheet.update_cell(i, 8, "✅")
                except Exception as e:
                    print(f"❌ Error enviando a {fila['Nombre']}: {e}")
            else:
                print(f"⚠️ Sin chat_id para {fila['Nombre']}")



def tarea_completa():
    enviar_recordatorios()
    enviar_recordatorios_30min()

if __name__ == "__main__":
    print("🕒 Iniciando sistema de recordatorios automáticos...")
    schedule.every(1).minutes.do(tarea_completa)

    while True:
        schedule.run_pending()
        time.sleep(1)

