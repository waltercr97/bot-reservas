# main.py

from sheets_manager import conectar_sheets
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters,CallbackQueryHandler
)

# Estados del flujo
NOMBRE, FECHA, HORA, TELEFONO = range(4)
ADMIN_CHAT_ID = "1081885795"
# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Vamos a agendar tu cita. ¿Cuál es tu nombre?")
    return NOMBRE

async def pedir_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text
    await update.message.reply_text("¿Qué día deseas la cita? (formato: dd/mm/yyyy)")
    return FECHA

async def pedir_hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fecha"] = update.message.text
    await update.message.reply_text("¿A qué hora deseas la cita? (formato: hh:mm)")
    return HORA

async def pedir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hora"] = update.message.text
    await update.message.reply_text("¿Cuál es tu número de teléfono?")
    return TELEFONO

from sheets_manager import guardar_cita

# ...

async def finalizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text
    datos = context.user_data
    chat_id = update.effective_chat.id  # ← obtenemos el chat_id

    guardar_cita(
         # ← pasamos el chat_id
        chat_id,  
        datos["nombre"],
        datos["telefono"],
        datos["fecha"],
        datos["hora"]
              
    )

    await update.message.reply_text(
        f"Gracias, {datos['nombre']}! Tu cita para el {datos['fecha']} "
        f"a las {datos['hora']} ha sido registrada."
    )
     # ✅ Notificación al administrador
    admin_mensaje = (
        f"📥 *Nueva cita agendada:*\n"
        f"👤 Nombre: {datos['nombre']}\n"
        f"📞 Teléfono: {datos['telefono']}\n"
        f"📅 Fecha: {datos['fecha']}  🕐 Hora: {datos['hora']}\n"
        f"💬 Chat ID: {chat_id}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_mensaje, parse_mode="Markdown")
    
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Proceso cancelado.")
    return ConversationHandler.END

# Para saber tu chat_id
async def obtener_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Tu chat_id es: {update.effective_chat.id}")

# ------- BOTONES CONFIRMAR/CANCELAR -------
async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()                              # Telegram exige responder al callback

    print("🔔 Callback recibido:", query.data)        # Ej: "confirmar_5"

    # 1️⃣ Parsear acción y nº de fila
    try:
        accion, fila_str = query.data.split("_")      # ("confirmar", "5")
        fila = int(fila_str)
    except ValueError:
        await query.edit_message_text("⚠️ Error procesando tu respuesta.")
        return

    # 2️⃣ Abrir la hoja y marcar la columna 6 (Confirmado)
    sheet = conectar_sheets().open("CitasReservadas").sheet1

    if accion == "confirmar":
        sheet.update_cell(fila, 6, "✅")              # Columna 6 = Confirmado
        await query.edit_message_text("✅ ¡Cita confirmada! Nos vemos pronto.")
    elif accion == "cancelar":
        sheet.update_cell(fila, 6, "❌")
        await query.edit_message_text("❌ Cita cancelada. Si necesitas otra hora, vuelve a reservar.")
    else:
        await query.edit_message_text("⚠️ Acción no reconocida.")

def main():
    TOKEN = "7863830955:AAF-7wjYMnUP9JT2RsNxCaTIDTG_6hgMvzA"

    app = ApplicationBuilder().token(TOKEN).build()
    # registra el CallbackQueryHandler primero que nada
    app.add_handler(CallbackQueryHandler(manejar_botones, pattern=r"^(confirmar|cancelar)_\d+$"))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_fecha)],
            FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_hora)],
            HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_telefono)],
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, finalizar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("chatid", obtener_chat_id))
    print("🤖 Bot de reservas corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
