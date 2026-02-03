"""
Crypto & Currency Tracker Bot - Improved Version
Улучшенная версия с обработкой ошибок
"""

import os
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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

# API endpoints
CRYPTO_API = "https://api.coingecko.com/api/v3/simple/price"
CURRENCY_API = "https://api.exchangerate-api.com/v4/latest/USD"

# Альтернативное API для валют
CURRENCY_API_ALT = "https://open.er-api.com/v6/latest/USD"


# === ФУНКЦИИ ПОЛУЧЕНИЯ ДАННЫХ ===

def get_crypto_prices():
    """Получить цены криптовалют"""
    try:
        logger.info("Запрос к CoinGecko API...")
        params = {
            'ids': 'bitcoin,ethereum,tether,binancecoin,solana,ripple,cardano,dogecoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(CRYPTO_API, params=params, timeout=15)
        logger.info(f"CoinGecko ответ: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получено {len(data)} монет")
            return data
        else:
            logger.error(f"API error: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Timeout при запросе к CoinGecko")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def get_currency_rates():
    """Получить курсы валют с резервным API"""
    try:
        logger.info("Запрос курсов валют...")
        
        # Пробуем основное API
        try:
            response = requests.get(CURRENCY_API, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                logger.info(f"Получено {len(rates)} валют")
                return rates
        except:
            logger.warning("Основное API недоступно, пробуем альтернативное...")
        
        # Пробуем альтернативное API
        response = requests.get(CURRENCY_API_ALT, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            logger.info(f"Получено {len(rates)} валют (альтернативное API)")
            return rates
        
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
    """Форматирование изменения"""
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
            InlineKeyboardButton("₿ Bitcoin", callback_data='btc'),
            InlineKeyboardButton("Ξ Ethereum", callback_data='eth')
        ],
        [
            InlineKeyboardButton("💵 USD/RUB", callback_data='usd'),
            InlineKeyboardButton("❓ Помощь", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""👋 Привет, {user}!

Я бот для отслеживания курсов! 📊

<b>Что я показываю:</b>

💰 <b>Криптовалюты:</b>
• Bitcoin, Ethereum, Solana
• BNB, XRP, Cardano, Dogecoin

💵 <b>Валюты:</b>
• USD, EUR, GBP, RUB
• CNY, JPY, TRY и другие

📊 Данные в реальном времени!

Выбери что показать:"""
    
    await update.message.reply_text(
        message, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    message = """📚 <b>ИНСТРУКЦИЯ</b>

<b>Команды:</b>
/start - главное меню
/crypto - все криптовалюты
/currency - все валюты
/btc - детали Bitcoin
/eth - детали Ethereum
/usd - курс USD/RUB
/help - эта справка

<b>Криптовалюты:</b>
Bitcoin, Ethereum, Solana,
BNB, XRP, Cardano, Dogecoin

<b>Валюты:</b>
USD, EUR, GBP, RUB, CNY,
JPY, TRY, UAH, KZT

Данные обновляются
в реальном времени! 🔄"""
    
    await update.message.reply_text(message, parse_mode='HTML')


async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать криптовалюты"""
    msg = await update.message.reply_text("⏳ Получаю данные...",parse_mode='HTML')
    
    prices = get_crypto_prices()
    
    if not prices:
        await msg.edit_text(
            "❌ <b>Ошибка получения данных</b>\n\n"
            "Возможные причины:\n"
            "• API временно недоступен\n"
            "• Проблемы с сетью\n\n"
            "Попробуйте через минуту ⏱️",
            parse_mode='HTML'
        )
        return
    
    message = "💰 <b>КРИПТОВАЛЮТЫ</b>\n\n"
    
    crypto_names = {
        'bitcoin': '₿ Bitcoin (BTC)',
        'ethereum': 'Ξ Ethereum (ETH)',
        'solana': '◎ Solana (SOL)',
        'ripple': '✕ Ripple (XRP)',
        'cardano': '₳ Cardano (ADA)',
        'binancecoin': '🔶 BNB',
        'dogecoin': 'Ð Dogecoin (DOGE)',
        'tether': '₮ Tether (USDT)'
    }
    
    for crypto_id, name in crypto_names.items():
        if crypto_id in prices:
            price = prices[crypto_id].get('usd', 0)
            change = prices[crypto_id].get('usd_24h_change', 0)
            
            message += f"<b>{name}</b>\n"
            message += f"💵 {format_price(price)}\n"
            message += f"📊 24ч: {format_change(change)}\n\n"
    
    now = datetime.now().strftime("%H:%M")
    message += f"🕐 Обновлено: {now}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='crypto')],
        [InlineKeyboardButton("◀️ Меню", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(message, parse_mode='HTML', reply_markup=reply_markup)


async def currency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать валюты"""
    msg = await update.message.reply_text("⏳ Получаю курсы...", parse_mode='HTML')
    
    rates = get_currency_rates()
    
    if not rates:
        await msg.edit_text(
            "❌ <b>Ошибка получения данных</b>\n\n"
            "API валют недоступен.\n"
            "Попробуйте через минуту ⏱️",
            parse_mode='HTML'
        )
        return
    
    message = "💵 <b>КУРСЫ ВАЛЮТ</b>\n\n"
    message += "Относительно 1 USD:\n\n"
    
    currencies = {
        'RUB': '🇷🇺 Рубль',
        'EUR': '🇪🇺 Евро',
        'GBP': '🇬🇧 Фунт',
        'JPY': '🇯🇵 Йена',
        'CNY': '🇨🇳 Юань',
        'TRY': '🇹🇷 Лира'
    }
    
    for code, name in currencies.items():
        if code in rates:
            rate = rates[code]
            message += f"<b>{name}</b>\n"
            message += f"💰 {rate:.2f} {code}\n\n"
    
    if 'RUB' in rates and 'EUR' in rates:
        rub_rate = rates['RUB']
        eur_to_rub = rub_rate / rates['EUR']
        message += "━━━━━━━━━━━\n"
        message += f"<b>1 USD = {rub_rate:.2f} RUB</b>\n"
        message += f"<b>1 EUR = {eur_to_rub:.2f} RUB</b>\n"
    
    now = datetime.now().strftime("%H:%M")
    message += f"\n🕐 {now}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='currency')],
        [InlineKeyboardButton("◀️ Меню", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(message, parse_mode='HTML', reply_markup=reply_markup)


async def btc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали Bitcoin"""
    msg = await update.message.reply_text("⏳ Загрузка...", parse_mode='HTML')
    
    try:
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'usd,rub',
            'include_24hr_change': 'true'
        }
        response = requests.get(CRYPTO_API, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'bitcoin' in data:
                btc = data['bitcoin']
                
                message = "₿ <b>BITCOIN (BTC)</b>\n\n"
                message += f"💵 <b>USD:</b> {format_price(btc['usd'])}\n"
                
                if 'rub' in btc:
                    message += f"🇷🇺 <b>RUB:</b> {btc['rub']:,.0f} ₽\n"
                
                message += f"\n📊 <b>Изменение 24ч:</b>\n"
                message += f"{format_change(btc.get('usd_24h_change', 0))}"
                
                await msg.edit_text(message, parse_mode='HTML')
            else:
                await msg.edit_text("❌ Данные недоступны", parse_mode='HTML')
        else:
            await msg.edit_text("❌ Ошибка API", parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"BTC error: {e}")
        await msg.edit_text("❌ Ошибка получения данных", parse_mode='HTML')


async def eth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали Ethereum"""
    msg = await update.message.reply_text("⏳ Загрузка...", parse_mode='HTML')
    
    try:
        params = {
            'ids': 'ethereum',
            'vs_currencies': 'usd,rub',
            'include_24hr_change': 'true'
        }
        response = requests.get(CRYPTO_API, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'ethereum' in data:
                eth = data['ethereum']
                
                message = "Ξ <b>ETHEREUM (ETH)</b>\n\n"
                message += f"💵 <b>USD:</b> {format_price(eth['usd'])}\n"
                
                if 'rub' in eth:
                    message += f"🇷🇺 <b>RUB:</b> {eth['rub']:,.0f} ₽\n"
                
                message += f"\n📊 <b>Изменение 24ч:</b>\n"
                message += f"{format_change(eth.get('usd_24h_change', 0))}"
                
                await msg.edit_text(message, parse_mode='HTML')
            else:
                await msg.edit_text("❌ Данные недоступны", parse_mode='HTML')
        else:
            await msg.edit_text("❌ Ошибка API", parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"ETH error: {e}")
        await msg.edit_text("❌ Ошибка получения данных", parse_mode='HTML')


async def usd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Курс доллара"""
    msg = await update.message.reply_text("⏳ Загрузка...", parse_mode='HTML')
    
    rates = get_currency_rates()
    
    if rates and 'RUB' in rates:
        rub_rate = rates['RUB']
        
        message = "💵 <b>ДОЛЛАР США</b>\n\n"
        message += f"<b>1 USD = {rub_rate:.2f} RUB</b>\n\n"
        message += f"100 USD = {rub_rate*100:,.2f} RUB\n"
        message += f"1000 USD = {rub_rate*1000:,.2f} RUB"
        
        await msg.edit_text(message, parse_mode='HTML')
    else:
        await msg.edit_text("❌ Ошибка получения данных", parse_mode='HTML')


# === ОБРАБОТЧИК КНОПОК ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'crypto':
        await query.edit_message_text("⏳ Загрузка...", parse_mode='HTML')
        
        prices = get_crypto_prices()
        
        if not prices:
            await query.edit_message_text(
                "❌ Ошибка получения данных\nПопробуйте позже",
                parse_mode='HTML'
            )
            return
        
        message = "💰 <b>КРИПТОВАЛЮТЫ</b>\n\n"
        
        crypto_names = {
            'bitcoin': '₿ Bitcoin',
            'ethereum': 'Ξ Ethereum',
            'solana': '◎ Solana',
            'ripple': '✕ Ripple',
            'cardano': '₳ Cardano',
            'binancecoin': '🔶 BNB',
            'dogecoin': 'Ð Dogecoin'
        }
        
        for crypto_id, name in crypto_names.items():
            if crypto_id in prices:
                price = prices[crypto_id].get('usd', 0)
                change = prices[crypto_id].get('usd_24h_change', 0)
                
                message += f"<b>{name}</b>\n"
                message += f"{format_price(price)} {format_change(change)}\n\n"
        
        now = datetime.now().strftime("%H:%M")
        message += f"🕐 {now}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='crypto')],
            [InlineKeyboardButton("◀️ Меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    
    elif query.data == 'currency':
        await query.edit_message_text("⏳ Загрузка...", parse_mode='HTML')
        
        rates = get_currency_rates()
        
        if not rates:
            await query.edit_message_text("❌ Ошибка", parse_mode='HTML')
            return
        
        message = "💵 <b>ВАЛЮТЫ</b>\n\n"
        
        currencies = {
            'RUB': '🇷🇺 Рубль',
            'EUR': '🇪🇺 Евро',
            'GBP': '🇬🇧 Фунт',
            'CNY': '🇨🇳 Юань'
        }
        
        for code, name in currencies.items():
            if code in rates:
                message += f"<b>{name}:</b> {rates[code]:.2f}\n"
        
        if 'RUB' in rates:
            message += f"\n<b>1 USD = {rates['RUB']:.2f} RUB</b>"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='currency')],
            [InlineKeyboardButton("◀️ Меню", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    
    elif query.data in ['btc', 'eth', 'usd']:
        await query.edit_message_text(
            f"Используйте команду /{query.data}",
            parse_mode='HTML'
        )
    
    elif query.data == 'help':
        message = """📚 <b>КОМАНДЫ</b>

/start - меню
/crypto - криптовалюты
/currency - валюты
/btc - Bitcoin
/eth - Ethereum
/usd - USD/RUB

Данные в реальном времени!"""
        
        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    
    elif query.data == 'back':
        keyboard = [
            [
                InlineKeyboardButton("💰 Криптовалюты", callback_data='crypto'),
                InlineKeyboardButton("💵 Валюты", callback_data='currency')
            ],
            [
                InlineKeyboardButton("₿ Bitcoin", callback_data='btc'),
                InlineKeyboardButton("Ξ Ethereum", callback_data='eth')
            ],
            [
                InlineKeyboardButton("💵 USD/RUB", callback_data='usd'),
                InlineKeyboardButton("❓ Помощь", callback_data='help')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "📊 <b>Главное меню</b>\n\nВыбери что показать:"
        
        await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)


# === ГЛАВНАЯ ФУНКЦИЯ ===

def main():
    """Запуск бота"""
    logger.info("=" * 60)
    logger.info("🚀 CRYPTO TRACKER BOT")
    logger.info("=" * 60)
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("crypto", crypto_command))
        application.add_handler(CommandHandler("currency", currency_command))
        application.add_handler(CommandHandler("btc", btc_command))
        application.add_handler(CommandHandler("eth", eth_command))
        application.add_handler(CommandHandler("usd", usd_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("✅ Handlers registered")
        logger.info("⏳ Starting polling...")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        exit(1)


if __name__ == '__main__':
    main()
        
