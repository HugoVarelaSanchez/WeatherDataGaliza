import logging
import os
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from google import genai
from google.genai import types

# Cargar variables de entorno
load_dotenv()

# 1. CONFIGURACIÓN
TELEGRAM_TOKEN = os.getenv('API_Telegram')
GEMINI_API_KEY = 'AIzaSyAfgwY_spl3aUgLcR2maT6DoPpTSuIMQN0'
ID_USUARIO_AUTORIZADO = 7040335230

client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# --- LÓGICA DE PROCESAMIENTO ---

async def procesar_archivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_USUARIO_AUTORIZADO:
        await update.message.reply_text("Lo siento, no tienes permiso para usar este bot.")
        return

    mensaje_espera = await update.message.reply_text("⏳ Recibido. Procesando archivo multimodal...")
    
    nombre_archivo = None
    try:
        # Prompt base con la restricción de palabras clave
        instruccion_base = (
            "\n\nFinalmente, genera una lista de entre 5 y 50 palabras clave relevantes "
            "basadas en el contenido anterior, separadas por comas."
        )

        # 1. Identificar el tipo de archivo y asignar Prompt específico
        if update.message.photo:
            archivo = await update.message.photo[-1].get_file()
            extension = ".jpg"
            prompt = "Analiza esta imagen y describe su contenido detalladamente." + instruccion_base
        
        elif update.message.voice or update.message.audio:
            target = update.message.voice or update.message.audio
            archivo = await target.get_file()
            extension = ".ogg"
            prompt = "Transcribe este audio íntegramente y resume los puntos principales." + instruccion_base
        
        elif update.message.video:
            archivo = await update.message.video.get_file()
            extension = ".mp4"
            prompt = "Describe qué sucede en este video y resume las escenas clave." + instruccion_base
            
        elif update.message.document:
            mime = update.message.document.mime_type
            archivo = await update.message.document.get_file()
            extension = os.path.splitext(update.message.document.file_name)[1]
            
            if mime == 'application/pdf':
                prompt = "Actúa como un analista de documentos. Lee este PDF y haz un resumen ejecutivo de su contenido." + instruccion_base
            elif mime.startswith('video/'):
                prompt = "Analiza este video enviado como documento y resume lo que ocurre." + instruccion_base
            else:
                await mensaje_espera.edit_text("Formato de documento no soportado (solo PDFs o Videos).")
                return
        else:
            return

        # 2. Descargar localmente
        nombre_archivo = f"temp_{update.message.message_id}{extension}"
        await archivo.download_to_drive(nombre_archivo)

        # 3. Subir a Gemini
        file_upload = client.files.upload(file=nombre_archivo)
        
        # Espera activa para archivos que requieren procesamiento (Videos/PDFs largos)
        intentos = 0
        while file_upload.state.name == "PROCESSING":
            await mensaje_espera.edit_text(f"⏳ Google está analizando el archivo... ({intentos*3}s)")
            time.sleep(3)
            file_upload = client.files.get(name=file_upload.name)
            intentos += 1
            if intentos > 60: raise Exception("Tiempo de espera agotado.")

        if file_upload.state.name == "FAILED":
            raise Exception("El procesamiento del archivo falló en los servidores de Google.")

        # 4. Generar contenido
        await mensaje_espera.edit_text("🧠 Generando informe y palabras clave...")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[file_upload, prompt],
            config=types.GenerateContentConfig(temperature=0.7)
        )

        # 5. Enviar respuesta
        await mensaje_espera.edit_text(response.text)

    except Exception as e:
        logging.error(f"Error: {e}")
        await mensaje_espera.edit_text(f"❌ Error técnico: {str(e)}")
    
    finally:
        if nombre_archivo and os.path.exists(nombre_archivo):
            os.remove(nombre_archivo)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot Multimodal listo. Envíame Fotos, Audios, Vídeos o PDFs.")

if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # Filtros actualizados para incluir documentos (PDFs)
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VOICE | filters.AUDIO | filters.VIDEO | filters.Document.ALL, 
        procesar_archivo
    ))
    
    print("Bot en marcha con soporte PDF y Keywords...")
    application.run_polling()