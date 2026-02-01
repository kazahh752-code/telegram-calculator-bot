"""
Telegram-бот Калькулятор для Render (упрощённая стабильная версия)
"""

import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен и порт
TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 10000))

if not TOKEN:
    logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Telegram Bot</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🤖 Calculator Bot</h1>
        <p style="color: green; font-size: 20px;">✅ Running!</p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return {'status': 'ok'}, 200


# Функции бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_name = update.effective_user.first_name
    text = f"""👋 Привет, {user_name}!

Я бот-калькулятор! 🧮

Просто напиши пример:
→ 25 + 17
→ 100 - 45
→ 12 * 8
→ 144 / 12

Команды:
/help - помощь"""
    
    await update.message.reply_text(text)
    logger.info(f"Пользователь {user_name} запустил бота")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = """📚 Инструкция:

Напишите математический пример:
• 15 + 8
• 100 - 35  
• 12 * 5
• 50 / 2

Команды:
/start - начало
/help - помощь"""
    
    await update.message.reply_text(text)


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений"""
    try:
        text = update.message.text.strip()
        
        # Проверяем наличие операторов
        if any(op in text for op in ['+', '-', '*', '/']):
            # Нормализуем
            text = text.replace('х', '*').replace('×', '*').replace('÷', '/')
            text = text.replace(',', '.')
            
            # Безопасное вычисление
            allowed = set('0123456789+-*/(). ')
            if all(c in allowed for c in text):
                result = eval(text)
                await update.message.reply_text(f"✅ {text} = {result}")
                logger.info(f"Вычислено: {text} = {result}")
            else:
                await update.message.reply_text("❌ Используйте только: + - * /")
        else:
            await update.message.reply_text(
                "🤔 Напишите пример:\nНапример: 25 + 17"
            )
    
    except ZeroDivisionError:
        await update.message.reply_text("❌ Нельзя делить на ноль!")
    except Exception as e:
        logger.error(f"Ошибка вычисления: {e}")
        await update.message.reply_text("❌ Ошибка. Пример: 15 + 8")


def run_bot():
    """Запуск бота"""
    try:
        logger.info("=" * 50)
        logger.info("🤖 Запуск Telegram-бота...")
        logger.info(f"📡 Токен: {TOKEN[:20]}...")
        
        # Создаём приложение
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))
        
        logger.info("✅ Бот запущен!")
        logger.info("⏳ Ожидание сообщений...")
        
        # Запускаем polling
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        logger.exception(e)


def run_web():
    """Запуск веб-сервера"""
    logger.info(f"🌐 Запуск веб-сервера на порту {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 СТАРТ СЕРВИСА")
    logger.info("=" * 50)
    
    # Бот в отдельном потоке
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Веб-сервер в основном потоке
    run_web()
    
