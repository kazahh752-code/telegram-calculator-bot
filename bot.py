"""
Telegram Bot Calculator for Railway
Простой бот без веб-сервера
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен
TOKEN = os.environ.get('BOT_TOKEN')

if not TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

logger.info(f"✅ Token found: {TOKEN[:15]}...")


# === ОБРАБОТЧИКИ КОМАНД ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user.first_name
    
    message = f"""👋 Привет, {user}!

Я бот-калькулятор! 🧮

Просто напиши математический пример:
→ 25 + 17
→ 100 - 45
→ 12 * 8
→ 144 / 12

Команды:
/start - начало
/help - помощь"""
    
    await update.message.reply_text(message)
    logger.info(f"👤 Пользователь {user} запустил бота")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    message = """📚 Инструкция:

Напиши математический пример:
• 15 + 8
• 100 - 35
• 12 * 5
• 50 / 2

Можно использовать скобки:
• (10 + 5) * 2
• 100 / (25 - 5)

Команды:
/start - начало
/help - эта справка"""
    
    await update.message.reply_text(message)


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка математических выражений"""
    try:
        text = update.message.text.strip()
        
        # Проверяем наличие математических операторов
        if any(op in text for op in ['+', '-', '*', '/']):
            
            # Заменяем возможные варианты символов
            text = text.replace('х', '*')
            text = text.replace('×', '*')
            text = text.replace('÷', '/')
            text = text.replace(',', '.')
            
            # Проверка безопасности - только цифры и операторы
            allowed_chars = set('0123456789+-*/(). ')
            if all(c in allowed_chars for c in text):
                
                # Вычисляем
                result = eval(text)
                
                # Отправляем результат
                await update.message.reply_text(f"✅ Результат:\n\n{text} = {result}")
                
                logger.info(f"🧮 Вычислено: {text} = {result}")
            else:
                await update.message.reply_text("❌ Используй только цифры и операторы: + - * / ( )")
        
        else:
            await update.message.reply_text(
                "🤔 Не вижу математики!\n\n"
                "Попробуй так: 25 + 17"
            )
    
    except ZeroDivisionError:
        await update.message.reply_text("❌ Ошибка: нельзя делить на ноль!")
        logger.warning("⚠️ Попытка деления на ноль")
    
    except Exception as e:
        await update.message.reply_text(
            "❌ Ошибка в вычислении\n\n"
            "Проверь правильность примера.\n"
            "Пример: 15 + 8"
        )
        logger.error(f"❌ Ошибка вычисления: {e}")


# === ГЛАВНАЯ ФУНКЦИЯ ===

def main():
    """Запуск бота"""
    
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК TELEGRAM-БОТА")
    logger.info("=" * 60)
    
    try:
        # Создаём приложение
        application = Application.builder().token(TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))
        
        logger.info("✅ Обработчики зарегистрированы")
        logger.info("⏳ Запуск polling...")
        
        # Запускаем бота
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.exception(e)
        exit(1)


if __name__ == '__main__':
    main()
