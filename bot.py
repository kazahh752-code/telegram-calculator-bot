"""
Telegram-бот Калькулятор для Render.com
Исправленная версия с гарантированным порядком запуска
"""

import os
import time
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Настройки окружения
TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 10000))

# 2. Настройка Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is ACTIVE and Web Server is running!"

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

# 3. Функции бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Привет, {user_name}! Я бот-калькулятор. Пришли пример, например: 2+2")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Инструкция:\nСложение: 5+3\nВычитание: 10-4\nУмножение: 6*7\nДеление: 20/4")

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip().replace('х', '*').replace('×', '*').replace('÷', '/').replace(',', '.')
        allowed = set('0123456789+-*/(). ')
        if all(c in allowed for c in text):
            result = eval(text)
            await update.message.reply_text(f"✅ Результат: {result}")
        else:
            await update.message.reply_text("❌ Используйте только цифры и знаки + - * /")
    except ZeroDivisionError:
        await update.message.reply_text("❌ Деление на ноль невозможно")
    except Exception:
        await update.message.reply_text("❌ Ошибка в примере")

# 4. Логика запуска
def run_bot():
    """Функция для запуска бота в отдельном потоке"""
    try:
        print("🤖 Инициализация Telegram-бота...")
        if not TOKEN:
            print("❌ ОШИБКА: Переменная BOT_TOKEN не найдена!")
            return

        application = Application.builder().token(TOKEN).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))
        
        print("✅ Бот запущен и начинает опрос (polling)...")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА БОТА: {e}")

def run_web_server():
    """Запуск веб-сервера (блокирует основной поток)"""
    print(f"🌐 Запуск веб-сервера на порту {PORT}...")
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    print("🚀 СТАРТ ПРИЛОЖЕНИЯ")
    
    # Сначала запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Небольшая пауза, чтобы логи бота не перемешались с логами сервера
    time.sleep(2)
    
    # Запускаем Flask в основном потоке (удерживает сервис Render живым)
    run_web_server()
    
