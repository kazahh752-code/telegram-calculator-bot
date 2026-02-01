"""
Telegram-бот Калькулятор для Render.com
Версия для облачного хостинга
"""

import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем токен из переменной окружения (для безопасности)
TOKEN = os.environ.get('BOT_TOKEN', 'ВАШ_ТОКЕН_ЗДЕСЬ')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие при /start"""
    user_name = update.effective_user.first_name
    
    welcome_text = f"""
👋 Привет, {user_name}!

Я бот-калькулятор! 🧮

📌 Что я умею:
• Сложение: 5 + 3
• Вычитание: 10 - 4
• Умножение: 6 * 7
• Деление: 20 / 4

📝 Как пользоваться:
Просто напишите пример:
→ 25 + 17

Команды:
/help - помощь
/temp - конвертер температуры
"""
    
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка"""
    help_text = """
📚 ИНСТРУКЦИЯ:

🧮 Калькулятор:
Напишите пример:
• 15 + 8
• 100 - 35
• 12 * 5
• 50 / 2

🌡️ Конвертер температуры:
• 25C (→ Фаренгейт)
• 77F (→ Цельсий)

Команды:
/start - начало
/temp - температура
"""
    await update.message.reply_text(help_text)


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Калькулятор"""
    try:
        text = update.message.text.strip()
        
        # Проверяем наличие операторов
        if any(op in text for op in ['+', '-', '*', '/', 'х', '×', '÷']):
            # Нормализуем символы
            text = text.replace('х', '*').replace('×', '*')
            text = text.replace('÷', '/').replace(',', '.')
            
            # Безопасное вычисление
            allowed = set('0123456789+-*/(). ')
            if all(c in allowed for c in text):
                result = eval(text)
                await update.message.reply_text(
                    f"✅ Результат:\n\n{text} = {result}"
                )
            else:
                await update.message.reply_text(
                    "❌ Используйте только: + - * /"
                )
        
        # Проверяем температуру
        elif any(unit in text.upper() for unit in ['C', 'F', 'С']):
            await handle_temperature(update, context)
        
        else:
            await update.message.reply_text(
                "🤔 Напишите пример:\n"
                "Например: 25 + 17\n"
                "Или: 25C"
            )
    
    except ZeroDivisionError:
        await update.message.reply_text("❌ Нельзя делить на ноль!")
    except:
        await update.message.reply_text(
            "❌ Ошибка в вычислении\n"
            "Пример: 15 + 8"
        )


async def temp_converter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню температуры"""
    keyboard = [
        ["25°C → F", "50°C → F"],
        ["77°F → C", "100°F → C"]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=True
    )
    
    text = """
🌡️ КОНВЕРТЕР ТЕМПЕРАТУРЫ

Отправьте температуру:
• 25C (Цельсий → Фаренгейт)
• 77F (Фаренгейт → Цельсий)

Или выберите пример:
"""
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Конвертация температуры"""
    text = update.message.text.strip().upper()
    text = text.replace('°', '').replace(' ', '')
    
    try:
        if 'C' in text or 'С' in text:
            # Цельсий → Фаренгейт
            temp_str = text.replace('C', '').replace('С', '')
            temp_str = temp_str.replace('→', '').replace('F', '').strip()
            celsius = float(temp_str)
            fahrenheit = (celsius * 9/5) + 32
            
            await update.message.reply_text(
                f"🌡️ Конвертация:\n\n"
                f"{celsius}°C = {fahrenheit:.1f}°F"
            )
        
        elif 'F' in text:
            # Фаренгейт → Цельсий
            temp_str = text.replace('F', '').replace('→', '')
            temp_str = temp_str.replace('C', '').replace('С', '').strip()
            fahrenheit = float(temp_str)
            celsius = (fahrenheit - 32) * 5/9
            
            await update.message.reply_text(
                f"🌡️ Конвертация:\n\n"
                f"{fahrenheit}°F = {celsius:.1f}°C"
            )
    except:
        await update.message.reply_text(
            "❌ Неверный формат!\n\n"
            "Примеры: 25C или 77F"
        )


def main():
    """Запуск бота"""
    print("🤖 Запуск Telegram-бота...")
    print(f"📡 Токен: {TOKEN[:10]}...")
    
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("temp", temp_converter))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, calculate)
    )
    
    print("✅ Бот запущен и готов к работе!")
    print("⏳ Ожидание сообщений...")
    
    # Запускаем бота
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    main()
