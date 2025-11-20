import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

# --- КОНФИГУРАЦИЯ ---
# Получите токен бота от @BotFather в Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Ваш API-ключ от Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Инициализируем клиенты
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
client = Groq(api_key=GROQ_API_KEY)

# Для простоты храним историю диалогов в оперативной памяти (при перезапуске бота очистится)
user_sessions = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Получаем или создаем историю диалога для пользователя
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "Ты полезный и дружелюбный AI-ассистент в Telegram."}
        ]

    # Добавляем сообщение пользователя в историю
    user_sessions[user_id].append({"role": "user", "content": user_message})

    # Показываем в чате, что бот печатает
    await update.message.chat.send_action(action="typing")

    try:
        # Отправляем запрос в Groq API
        chat_completion = client.chat.completions.create(
            messages=user_sessions[user_id],
            model="llama-3.1-8b-instant",  # Можно заменить на "mixtral-8x7b-32768"
        )

        # Получаем ответ от ИИ
        ai_response = chat_completion.choices[0].message.content

        # Добавляем ответ ассистента в историю и отправляем пользователю
        user_sessions[user_id].append({"role": "assistant", "content": ai_response})
        await update.message.reply_text(ai_response)

    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text("Извините, произошла ошибка.")

# Регистрируем обработчик сообщений
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Запускаем бота
if __name__ == "__main__":
    print("Бот запущен...")
    app.run_polling()
