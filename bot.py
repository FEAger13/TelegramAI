from flask import Flask
import os
import threading
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from groq import Groq

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Создаем Flask app (обязательно для Render Web Service)
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Telegram Bot is Running!"

@app.route('/ping')
def ping():
    return "pong"

# Инициализируем Telegram бота
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
client = Groq(api_key=GROQ_API_KEY)
user_sessions = {}

# Обработчик сообщений Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "Ты полезный AI ассистент."}
        ]

    user_sessions[user_id].append({"role": "user", "content": user_message})
    await update.message.chat.send_action(action="typing")

    try:
        chat_completion = client.chat.completions.create(
            messages=user_sessions[user_id],
            model="llama-3.1-8b-instant",
        )
        ai_response = chat_completion.choices[0].message.content
        user_sessions[user_id].append({"role": "assistant", "content": ai_response})
        await update.message.reply_text(ai_response)
    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text("Извините, произошла ошибка.")

# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я твой AI ассистент. Просто напиши мне сообщение!")

def run_bot():
    """Запускает Telegram бота"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask в основном потоке (на порту 5000)
    print("🌐 Веб-сервер запускается на порту 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
