"""
Telegram Bot Calculator - Fixed Event Loop Version
"""

import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройки
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 10000))

if not TOKEN:
    logger.error("ERROR: BOT_TOKEN not found!")
    exit(1)

# Flask
app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Bot Running!</h1><p>Status: OK</p>'

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

# Bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    msg = f"Hi {user}!\n\nI'm a calculator bot.\n\nTry: 25 + 17"
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Send me:\n\n15 + 8\n100 - 35\n12 * 5\n50 / 2"
    await update.message.reply_text(msg)

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        
        if any(op in text for op in ['+', '-', '*', '/']):
            text = text.replace('x', '*').replace(',', '.')
            allowed = set('0123456789+-*/(). ')
            
            if all(c in allowed for c in text):
                result = eval(text)
                await update.message.reply_text(f"= {result}")
            else:
                await update.message.reply_text("Use: + - * /")
        else:
            await update.message.reply_text("Example: 25 + 17")
    
    except ZeroDivisionError:
        await update.message.reply_text("Error: Division by zero")
    except:
        await update.message.reply_text("Calculation error")

# Bot runner with event loop
def run_bot():
    """Run bot with proper event loop"""
    try:
        logger.info("="*50)
        logger.info("Starting Telegram Bot...")
        logger.info(f"Token: {TOKEN[:15]}...")
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Build application
        app_bot = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app_bot.add_handler(CommandHandler("start", start))
        app_bot.add_handler(CommandHandler("help", help_cmd))
        app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))
        
        logger.info("Bot handlers registered!")
        logger.info("Starting polling...")
        
        # Run polling
        app_bot.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        logger.exception(e)

# Web server
def run_web():
    logger.info(f"Starting web server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# Main
if __name__ == '__main__':
    logger.info("="*50)
    logger.info("SERVICE STARTING")
    logger.info("="*50)
    
    # Start bot thread
    bot_thread = Thread(target=run_bot, daemon=True, name="BotThread")
    bot_thread.start()
    
    logger.info("Bot thread started!")
    
    # Start web server
    run_web()
    
