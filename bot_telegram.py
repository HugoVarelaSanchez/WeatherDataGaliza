from dotenv import load_dotenv
import os
import telebot
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

TELEGRAM_TOKEN = os.getenv("API_TG")
ARCHIVO_CSV = "sample_data.csv"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def obtener_datos_hora_actual():
    """Lee el CSV y busca solo la fila de la hora actual"""
    try:
        # 1. Leer el archivo CSV
        df = pd.read_csv(ARCHIVO_CSV)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 2. Obtener la hora actual y redondearla (ej: 08:35:19 -> 08:00:00)
        ahora = datetime.now()
        hora_en_punto = ahora.replace(minute=0, second=0, microsecond=0)
        
        # 3. Filtrar: Buscar exactamente esa hora en el CSV
        datos_hora = df[df['timestamp'] == hora_en_punto]
        
        if datos_hora.empty:
            return f"No tengo datos guardados para esta hora exacta ({hora_en_punto.strftime('%H:%M')}) en el archivo."

        # 4. Extraer los datos de esa única fila (iloc[0] coge la primera coincidencia)
        fila = datos_hora.iloc[0]
        
        hora_str = fila['timestamp'].strftime('%H:%M')
        
        # EL SALVAVIDAS: Quitamos los guiones bajos y ponemos formato Título
        estado_cielo = str(fila['sky_state']).replace('_', ' ').title() 
        
        temp = fila['temperature']
        viento = fila['wind']
        precip = fila['precipitation_amount']
        
        # 5. Construir el mensaje súper limpio
        mensaje = (
            f"📍 *El tiempo ahora mismo ({hora_str})*\n\n"
            f"☁️ *Cielo:* {estado_cielo}\n"
            f"🌡️ *Temperatura:* {temp}°C\n"
            f"💨 *Viento:* {viento} m/s\n"
            f"💧 *Lluvia:* {precip} mm"
        )
        return mensaje

    except Exception as e:
        error_limpio = str(e).replace('_', ' ').replace('*', ' ').replace("'", "")
        return f"Ups, error leyendo el CSV: {error_limpio}"

# --- INTERACCIÓN CON EL USUARIO ---

@bot.message_handler(commands=['start', 'tiempo', 'ahora'])
def enviar_prediccion(message):
    """Se ejecuta cuando el usuario envía /start"""
    
    # Mensaje rápido de carga
    mensaje_espera = bot.reply_to(message, "⏳ Consultando la estación meteorológica...")
    
    # Llamamos a nuestra función
    respuesta_final = obtener_datos_hora_actual()
    
    # Editamos el mensaje con el resultado final
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=mensaje_espera.message_id,
        text=respuesta_final,
        parse_mode="Markdown"
    )

# --- INICIO DEL BOT ---
if __name__ == "__main__":
    print("Bot listo. Esperando a que un usuario diga /start en Telegram...")
    bot.infinity_polling()