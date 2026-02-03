"""
Crypto & Currency Tracker Bot
Бот для отслеживания курсов криптовалют и валют
"""

import os
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')

if not TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

# API для получения данных
CRYPTO_API = "https://api.coingecko.com/api/v3/simple/price"
CURRENCY_API = "https://api.exchangerate-api.com/v4/latest/USD"


# === ФУНКЦИИ ПОЛУЧЕНИЯ ДАННЫХ ===

def get_crypto_prices():
    """Получить цены криптовалют"""
    try:
        params = {
            'ids': 'bitcoin,ethereum,tether,binancecoin,solana,ripple,cardano,dogecoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        response = requests.get(CRYPTO_API, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting crypto prices: {e}")
        return None


def get_currency_rates():
    """Получить курсы валют"""
    try:
        response = requests.get(CURRENCY_API, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('rates', {})
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting currency rates: {e}")
        return None


def format_price(price):
    """Форматирование цены"""
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    else:
        return f"${price:.6f}"


def format_change(change):
    """Форматирование изменения за 24ч"""
    if change > 0:
        return f"🟢 +{change:.2f}%"
    else:
        return f"🔴 {change:.2f}%"


# === ОБРАБОТЧИКИ КОМАНД ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user.first_name
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Криптовалюты", callback_data='crypto'),
            InlineKeyboardButton("💵 Валюты", callback_data='currency')
        ],
        [
            InlineKeyboardButton("📊 Всё сразу", callback_data='all'),
            InlineKeyboardButton("❓ Помощь", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""👋 Привет, {user}!

Я бот для отслеживания курсов! 📊

💰 Криптовалюты:
Bitcoin, Ethereum, Solana и др.

💵 Валюты:
USD, EUR, GBP, CNY и др.

Выбери что показать:"""
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    logger.info(f"👤 Пользователь {user} запустил бота")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    message = """📚 Инструкция:

🔹 Команды:
/start - главное меню
/crypto - курсы криптовалют
/currency - курсы валют
/btc - только Bitcoin
/eth - только Ethereum
/usd - доллар к рублю
/help - эта справка

🔹 Криптовалюты:
• Bitcoin (BTC)
• Ethereum (ETH)
• Solana (SOL)
• Ripple (XRP)
• И другие...

🔹 Валюты:
• USD, EUR, GBP
• RUB, CNY, JPY
• И многие другие

Данные обновляются в реальном времени! 🔄"""
    
    await update.message.reply_text(message)


async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /crypto - показать криптовалюты"""
    await update.message.reply_text("⏳ Получаю данные...")
    
    prices = get_crypto_prices()
    
    if not prices:
        await update.message.reply_text("❌ Ошибка при получении данных. Попробуйте позже.")
        return
    
    # Формируем сообщение
    message = "💰 <b>КРИПТОВАЛЮТЫ</b>\n\n"
    
    crypto_names = {
        'bitcoin': '₿ Bitcoin (BTC)',
        'ethereum': 'Ξ Ethereum (ETH)',
        'tether': '₮ Tether (USDT)',
        'binancecoin': '🔶 BNB',
        'solana': '◎ Solana (SOL)',
        'ripple': '✕ Ripple (XRP)',
        'cardano': '₳ Cardano (ADA)',
        'dogecoin': 'Ð Dogecoin (DOGE)'
    }
    
    for crypto_id, name in crypto_names.items():
        if crypto_id in prices:
            price = prices[crypto_id].get('usd', 0)
            change = prices[crypto_id].get('usd_24h_change', 0)
            
            message += f"{name}\n"
            message += f"💵 {format_price(price)}\n"
            message += f"📊 24ч: {format_change(change)}\n\n"
    
    # Добавляем время обновления
    now = datetime.now().strftime("%H:%M:%S")
    message += f"🕐 Обновлено: {now}"
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='crypto')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)


async def currency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /currency - показать валюты"""
    await update.message.reply_text("⏳ Получаю курсы валют...")
    
    rates = get_currency_rates()
    
    if not rates:
        await update.message.reply_text("❌ Ошибка при получении данных. Попробуйте позже.")
        return
    
    # USD = 1, пересчитываем
    message = "💵 <b>КУРСЫ ВАЛЮТ</b>\n\n"
    message += "Относительно 1 USD:\n\n"
    
    currencies = {
        'RUB': '🇷🇺 Российский рубль',
        'EUR': '🇪🇺 Евро',
        'GBP': '🇬🇧 Фунт стерлингов',
        'JPY': '🇯🇵 Японская йена',
        'CNY': '🇨🇳 Китайский юань',
        'TRY': '🇹🇷 Турецкая лира',
        'UAH': '🇺🇦 Украинская гривна',
        'KZT': '🇰🇿 Казахский тенге'
    }
    
    for code, name in currencies.items():
        if code in rates:
            rate = rates[code]
            message += f"{name}\n"
            message += f"💰 {rate:.2f} {code}\n\n"
    
    # Также покажем обратные курсы (к рублю)
    if 'RUB' in rates:
        rub_rate = rates['RUB']
        message += "━━━━━━━━━━━━━━━\n"
        message += f"<b>1 USD = {rub_rate:.2f} RUB</b>\n"
        
        if 'EUR' in rates:
            eur_to_rub = rates['RUB'] / rates['EUR']
            message += f"<b>1 EUR = {eur_to_rub:.2f} RUB</b>\n"
    
    now = datetime.now().strftime("%H:%M:%S")
    message += f"\n🕐 Обновлено: {now}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='currency')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)


async def btc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /btc - только Bitcoin"""
    await update.message.reply_text("⏳ Получаю курс Bitcoin...")
    
    try:
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'usd,rub',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }
        response = requests.get(CRYPTO_API, params=params, timeout=10)
        data = response.json()
        
        if 'bitcoin' in data:
            btc = data['bitcoin']
            
            message = "₿ <b>BITCOIN (BTC)</b>\n\n"
            message += f"💵 USD: {format_price(btc['usd'])}\n"
            
            if 'rub' in btc:
                message += f"🇷🇺 RUB: {btc['rub']:,.0f} ₽\n"
            
            message += f"\n📊 Изменение 24ч:\n"
            message += f"{format_change(btc.get('usd_24h_change', 0))}\n"
            
            if 'usd_market_cap' in btc:
                mcap = btc['usd_market_cap'] / 1_000_000_000
                message += f"\n💎 Капитализация:\n${mcap:,.0f}B"
            
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Ошибка получения данных")
    
    except Exception as e:
        logger.error(f"BTC command error: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных")


async def eth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /eth - только Ethereum"""
    await update.message.reply_text("⏳ Получаю курс Ethereum...")
    
    try:
        params = {
            'ids': 'ethereum',
            'vs_currencies': 'usd,rub',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }
        response = requests.get(CRYPTO_API, params=params, timeout=10)
        data = response.json()
        
        if 'ethereum' in data:
            eth = data['ethereum']
            
            message = "Ξ <b>ETHEREUM (ETH)</b>\n\n"
            message += f"💵 USD: {format_price(eth['usd'])}\n"
            
            if 'rub' in eth:
                message += f"🇷🇺 RUB: {eth['rub']:,.0f} ₽\n"
            
            message += f"\n📊 Изменение 24ч:\n"
            message += f"{format_change(eth.get('usd_24h_change', 0))}\n"
            
            if 'usd_market_cap' in eth:
                mcap = eth['usd_market_cap'] / 1_000_000_000
                message += f"\n💎 Капитализация:\n${mcap:,.0f}B"
            
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Ошибка получения данных")
    
    except Exception as e:
        logger.error(f"ETH command error: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных")


async def usd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /usd - курс доллара"""
    await update.message.reply_text("⏳ Получаю курс USD...")
    
    rates = get_currency_rates()
    
    if rates and 'RUB' in rates:
        rub_rate = rates['RUB']
        
        message = "💵 <b>ДОЛЛАР США</b>\n\n"
        message += f"1 USD = {rub_rate:.2f} RUB\n"
        message += f"1 RUB = {1/rub_rate:.4f} USD\n\n"
        message += f"100 USD = {rub_rate*100:,.2f} RUB\n"
        message += f"1000 USD = {rub_rate*1000:,.2f} RUB"
        
        await update.message.reply_text(message, parse_mode='HTML')
    else:
        await update.message.reply_text("❌ Ошибка получения данных")


# === ОБРАБОТЧИК КНОПОК ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'crypto':
        # Отправляем данные о крипте
        prices = get_crypto_prices()
        
        if not prices:
            await query.edit_message_text("❌ Ошибка при получении данных")
            return
        
        message = "💰 <b>КРИПТОВАЛЮТЫ</b>\n\n"
        
        crypto_names = {
            'bitcoin': '₿ Bitcoin (BTC)',
            'ethereum': 'Ξ Ethereum (ETH)',
            'tether': '₮ Tether (USDT)',
            'binancecoin': '🔶 BNB',
            'solana': '◎ Solana (SOL)',
            'ripple': '✕ Ripple (XRP)',
            'cardano': '₳ Cardano (ADA)',
            'dogecoin': 'Ð Dogecoin (DOGE)'
        }
        
        for crypto_id, name in crypto_names.items():
            if crypto_id in prices:
                price = prices[crypto_id].get('usd', 0)
                change = prices[crypto_id].get('usd_24h_change', 0)
                
                message += f"{name}\n"
                message += f"💵 {format_price(price)}\n"
                message += f"📊 24ч: {format_change(change)}\n\n"
        
        now = datetime.now().strftime("%H:%M:%S")
        message += f"🕐 Обновлено: {now}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='crypto')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    
    elif query.data == 'currency':
        # Отправляем курсы валют
        rates = get_currency_rates()
        
        if not rates:
            await query.edit_message_text("❌ Ошибка при получении данных")
            return
        
        message = "💵 <b>КУРСЫ ВАЛЮТ</b>\n\n"
        message += "Относительно 1 USD:\n\n"
        
        currencies = {
            'RUB': '🇷🇺 Российский рубль',
            'EUR': '🇪🇺 Евро',
            'GBP': '🇬🇧 Фунт стерлингов',
            'JPY': '🇯🇵 Японская йена',
            'CNY': '🇨🇳 Китайский юань',
            'TRY': '🇹🇷 Турецкая лира'
        }
        
        for code, name in currencies.items():
            if code in rates:
                rate = rates[code]
                message += f"{name}\n💰 {rate:.2f} {code}\n\n"
        
        if 'RUB' in rates:
            rub_rate = rates['RUB']
            message += "━━━━━━━━━━━━━━━\n"
            message += f"<b>1 USD = {rub_rate:.2f} RUB</b>\n"
        
        now = datetime.now().strftime("%H:%M:%S")
        message += f"\n🕐 Обновлено: {now}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='currency')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    
    elif query.data == 'all':
        await query.edit_message_text("⏳ Загружаю все данные...")
        # Можно добавить показ всего сразу
        await query.edit_message_text("Используй команды:\n/crypto - криптовалюты\n/currency - валюты")
    
    elif query.data == 'help':
        message = """📚 Инструкция:

🔹 Команды:
/start - главное меню
/crypto - криптовалюты
/currency - валюты
/btc - Bitcoin
/eth - Ethereum
/usd - доллар

Данные в реальном времени! 🔄"""
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif query.data == 'back':
        # Возврат в главное меню
        keyboard = [
            [
                InlineKeyboardButton("💰 Криптовалюты", callback_data='crypto'),
                InlineKeyboardButton("💵 Валюты", callback_data='currency')
            ],
            [
                InlineKeyboardButton("📊 Всё сразу", callback_data='all'),
                InlineKeyboardButton("❓ Помощь", callback_data='help')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """📊 Главное меню

Выбери что показать:"""
        
        await query.edit_message_text(message, reply_markup=reply_markup)


# === ГЛАВНАЯ ФУНКЦИЯ ===

def main():
    """Запуск бота"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК CRYPTO TRACKER BOT")
    logger.info("=" * 60)
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Команды
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("crypto", crypto_command))
        application.add_handler(CommandHandler("currency", currency_command))
        application.add_handler(CommandHandler("btc", btc_command))
        application.add_handler(CommandHandler("eth", eth_command))
        application.add_handler(CommandHandler("usd", usd_command))
        
        # Кнопки
        application.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("✅ Обработчики зарегистрированы")
        logger.info("⏳ Запуск polling...")
        
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
    
