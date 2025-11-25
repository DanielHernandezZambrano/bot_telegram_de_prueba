from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler,  
    ContextTypes, 
    ConversationHandler, 
    CallbackQueryHandler,
    filters
)
from config import TOKEN_BOT
import json
import os

# Token:
TOKEN = TOKEN_BOT

# Los estados son como "pantallas" en las que puede estar el usuario
MENU = 0
ESPERANDO_NOTAS = 1
VIENDO_NOTAS = 2
BORRANDO_NOTAS = 3  

# Estructura: {user_id: [lista de notas]}, carga al iniciar
if os.path.exists('notas.json'):
    with open('notas.json', 'r', encoding='utf-8') as f:
        notas_usuarios = json.load(f)
    print(f"✅ Notas cargadas: {len(notas_usuarios)} usuarios")
else:
    notas_usuarios = {}
    print("📝 Archivo de notas no existe, creando uno nuevo")


def crear_menu():
    # Creamos el menu

    keyboard = [
        [InlineKeyboardButton("Agregar Nota", callback_data="agregar")],
        [InlineKeyboardButton("Ver Notas", callback_data="ver")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup

def crear_menu_ver_notas():
    """Este menu es para cuando el usuario vea las nota
    y por si quiere eliminar algunas, es diferente al orginal (boton borrar)"""

    keyboard = [
        [InlineKeyboardButton("🗑️ Borrar Nota", callback_data="borrar")],
        [InlineKeyboardButton("⬅️ Volvel al menú", callback_data="volver")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Este comando se ejecuta cuando el usuario escribe /start
    Es lo primero que ve el usuario al iniciar el bot
    """

    user_id = str(update.effective_user.id)  # Usuario de la instancia actual
    
    # Inicializar lista de notas si es un usuario nuevo:
    if user_id not in notas_usuarios:
        notas_usuarios[user_id] = []

    await update.message.reply_text(
        "¡Hola!, Ven a tu anotador!!!", 
        reply_markup=crear_menu()
        )

    return MENU


# ========== MANEJAR CLICKS EN BOTONES DEL MENÚ ==========
async def manejar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Se ejecuta cuando el usuario hace clic en un botón del menú
    """
    
    query = update.callback_query
    
    # IMPORTANTE: Siempre responder al callback
    await query.answer()

    if query.data == "agregar":
        await query.edit_message_text("📝 Envíame tu nota")

        return ESPERANDO_NOTAS
    
    elif query.data == "ver":
        await query.edit_message_text("Veamos tus notas")

        user_id = str(update.effective_user.id)
        notas = notas_usuarios.get(user_id, [])

        if not notas:
            texto = "No tenés notas guardadas todavía."

        else:
            texto = "📝 Tus notas:\n\n"
            for i, nota in enumerate(notas, 1):
                texto += f"{i}. {nota}\n"
            
        await query.edit_message_text(
            texto,
            reply_markup= crear_menu_ver_notas()
            )
    
    return VIENDO_NOTAS


async def manejar_viendo_notas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se ejecuta cuando el usuario hace clic en botones mientras ve notas"""
    
    query = update.callback_query
    await query.answer()
    
    if query.data == "volver":

        await query.edit_message_text(
            "Volvimos al menú",
            reply_markup= crear_menu()
            )
        
        return MENU
    
    elif query.data == "borrar":
        
        await query.edit_message_text("Dime el número de tu nota que quieres borrar")

        return BORRANDO_NOTAS


async def guardar_nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se ejecuta cuando el usuario envía texto en ESPERANDO_NOTAS"""
    
    user_id = str(update.effective_user.id)  # Usuario de la instancia actual
    nota = update.message.text
    
    # Inicializar si no existe (por las dudas)
    if user_id not in notas_usuarios:
        notas_usuarios[user_id] = []
    
    # Guardar la nota en memoria
    notas_usuarios[user_id].append(nota)
    
    # Guardar en archivo JSON
    with open('notas.json', 'w', encoding='utf-8') as f:
        json.dump(notas_usuarios, f, ensure_ascii=False, indent=2)
    
    await update.message.reply_text(
        f"✅ Nota guardada!\n"
        f"Total de notas: {len(notas_usuarios[user_id])}",
        reply_markup=crear_menu()
    )

    return MENU


async def borrar_nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se ejecuta cuando el usuario envía un número para borrar"""
    
    user_id = str(update.effective_user.id)
    numero_texto = update.message.text
    
    # Validar que sea un número
    if not numero_texto.isdigit():
        await update.message.reply_text("Ingresa un número entero por favor")
        
        return BORRANDO_NOTAS # Vuelve a intentar
    
    # Convertir a número
    numero = int(numero_texto) - 1
    
    # Validar que el número exista en la lista
    if 0 <= numero < len(notas_usuarios[user_id]):

        # Guardar la nota antes de borrarla
        nota_eliminada = notas_usuarios[user_id].pop(numero)

        with open('notas.json', 'w', encoding='utf-8') as f:
            json.dump(notas_usuarios, f, ensure_ascii=False, indent=2)

        # Mostrar qué nota se borró
        await update.message.reply_text(
            f"✅ Nota #{numero_texto} eliminada:\n\n"
            f"{nota_eliminada}",
            reply_markup=crear_menu())

        return MENU

    else:
        await update.message.reply_text("El número ingresado no existe en tus notas")

        return BORRANDO_NOTAS # Vuelve a intentar


async def volver_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se ejecuta con /menu"""
    await update.message.reply_text(
        "¿Qué querés hacer?",
        reply_markup=crear_menu()
    )
    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se ejecuta con /cancel"""
    await update.message.reply_text(
        "Conversación cancelada.\n"
        "Escribí /start para empezar de nuevo."
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()
    
    # ========== CREAR EL CONVERSATIONHANDLER COMPLETO ==========
    conv_handler = ConversationHandler(
        # ¿Cómo EMPIEZA la conversación?
        entry_points=[
            CommandHandler('start', start)
        ],
        
        # ¿Qué pasa en cada ESTADO?
        states={
            MENU: [
                # Manejar clicks en botones del menú
                CallbackQueryHandler(manejar_menu, pattern="^(agregar|ver)$")
            ],
            ESPERANDO_NOTAS: [
                # Recibir el texto de la nota
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_nota),
                # Permitir volver al menú con /menu
                CommandHandler('menu', volver_menu)
            ]
            # VIENDO_NOTAS no hace falta porque se maneja todo en manejar_menu
        },
        
        # ¿Cómo CANCELAR la conversación?
        fallbacks=[
            CommandHandler('cancel', cancel)
        ],
        per_message=False
    )
    
    # Agregar el handler al bot
    app.add_handler(conv_handler)
    
    print("🤖 Bot iniciado y escuchando...")
    app.run_polling()

if __name__ == "__main__":
    main()