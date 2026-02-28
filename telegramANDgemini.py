
import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from google import genai
from google.genai import types

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# 1. CONFIGURACIÓN DE LLAVES
TELEGRAM_TOKEN = os.getenv('API_Telegram')
GEMINI_API_KEY = os.getenv('API_Gemini')
ID_USUARIO_AUTORIZADO = 7040335230 # Tu ID verificado

# Inicializar cliente de Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# --- LÓGICA DE PROCESAMIENTO ---

async def procesar_archivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificación de seguridad
    if update.effective_user.id != ID_USUARIO_AUTORIZADO:
        await update.message.reply_text("Lo siento, no tienes permiso para usar este bot.")
        return

    # Mensaje de feedback inicial
    mensaje_espera = await update.message.reply_text("⏳ Procesando con Gemini 1.5 Flash... espera un momento.")
    
    nombre_archivo = None
    try:
        # 1. Identificar el tipo de archivo
        if update.message.photo:
            archivo = await update.message.photo[-1].get_file()
            extension = ".jpg"
            prompt = "Analiza esta imagen, extrae sus características y haz un resumen detallado del contenido y texto visible."
        elif update.message.voice or update.message.audio:
            target = update.message.voice or update.message.audio
            archivo = await target.get_file()
            extension = ".ogg"
            prompt = "Transcribe este audio íntegramente y luego resume los puntos principales de forma estructurada."
        else:
            await mensaje_espera.edit_text("Por favor, envía una imagen, nota de voz o archivo de audio.")
            return

        # 2. Descargar el archivo localmente
        # Usamos el ID del mensaje para evitar conflictos si envías varios archivos rápido
        nombre_archivo = f"temp_{update.message.message_id}{extension}"
        await archivo.download_to_drive(nombre_archivo)

        # 3. Subir a Gemini y generar contenido
        # Subimos el archivo al File Service de Google para mejor soporte multimodal
        file_upload = client.files.upload(file=nombre_archivo)
        
# Busca la parte de la generación de contenido y cámbiala por esta:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[file_upload, prompt],
            config=types.GenerateContentConfig(
                # Forzamos una configuración básica que evita el chequeo v1beta estricto
                candidate_count=1,
                temperature=0.7
            )
        )
        # 4. Enviar respuesta al usuario
        # Si la respuesta es muy larga, Telegram podría dar error, pero para resúmenes va perfecto
        await mensaje_espera.edit_text(response.text)

    except Exception as e:
        logging.error(f"Error en procesar_archivo: {e}")
        await mensaje_espera.edit_text(f"❌ Error técnico: {str(e)}")
    
    finally:
        # 5. Limpieza: borrar el archivo temporal siempre, incluso si hay error
        if nombre_archivo and os.path.exists(nombre_archivo):
            try:
                os.remove(nombre_archivo)
            except Exception as e:
                logging.warning(f"No se pudo borrar el archivo temporal: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ ¡Bot listo!\n\nEnvíame una imagen para analizarla o un audio para transcribirlo. "
        "Solo responderé a mensajes del usuario autorizado."
    )

if __name__ == "__main__":
    # Verificar que los tokens existan
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Error: Falta API_Telegram o API_Gemini en el archivo .env")
        exit()

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VOICE | filters.AUDIO, 
        procesar_archivo
    ))
    
    print("🚀 Bot encendido correctamente.")
    print(f"📡 Escuchando solo al ID: {ID_USUARIO_AUTORIZADO}")
    application.run_polling()