from flask import Flask
import os
import threading
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from groq import Groq

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Создаем Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI Telegram Bot is Running!"

@app.route('/ping')
def ping():
    return "pong"

# Инициализируем компоненты
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
client = Groq(api_key=GROQ_API_KEY)
user_sessions = {}

# Обработчик сообщений Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_message = update.message.text
        
        logger.info(f"📨 Получено сообщение от {user_id}: {user_message}")

        if user_id not in user_sessions:
            user_sessions[user_id] = [
                {"role": "system", "content": "Ты полезный AI ассистент. Отвечай подробно и помогай пользователю."}
            ]

        user_sessions[user_id].append({"role": "user", "content": user_message})
        await update.message.chat.send_action(action="typing")

        logger.info("🔄 Отправляем запрос в Groq API...")
        
        # Пробуем разные модели если одна не работает
        try:
            chat_completion = client.chat.completions.create(
                messages=user_sessions[user_id],
                model="llama-3.1-70b-versatile",
            )
        except Exception as model_error:
            logger.warning(f"Модель 70b не работает, пробуем 8b: {model_error}")
            chat_completion = client.chat.completions.create(
                messages=user_sessions[user_id],
                model="llama-3.1-8b-instant",
            )
        
        ai_response = chat_completion.choices[0].message.content
        logger.info(f"🤖 Получен ответ от ИИ: {ai_response[:100]}...")
        
        user_sessions[user_id].append({"role": "assistant", "content": ai_response})
        await update.message.reply_text(ai_response)
        
        logger.info("✅ Сообщение отправлено пользователю")
        
    except Exception as e:
        logger.error(f"🚨 Ошибка в handle_message: {e}")
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте еще раз.")

# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Привет! Я твой AI-ассистент!\n"
        "Задавай любой вопрос - я постараюсь помочь!"
    )

def run_web():
    """Запускает веб-сервер в отдельном потоке"""
    logger.info("🌐 Веб-сервер запускается на порту 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_bot():
    """Запускает Telegram бота в основном потоке"""
    try:
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("🤖 Telegram бот запускается...")
        
        # Запускаем с обработкой конфликтов
        application.run_polling(
            drop_pending_updates=True,  # Важно! Игнорируем старые сообщения
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.error(f"🚨 Критическая ошибка бота: {e}")

if __name__ == "__main__":
    logger.info("🚀 Запуск приложения...")
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Запускаем бота в основном потоке
    run_bot()
