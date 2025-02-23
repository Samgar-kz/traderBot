import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from config import TELEGRAM_TOKEN
from trading_logic import trade_logic, is_running

async def start(update: Update, context: CallbackContext):
    """Запуск бота"""
    global is_running
    if is_running:
        await update.message.reply_text("⚠ Бот уже работает!")
        return

    is_running = True
    asyncio.create_task(trade_logic())  # Запускаем торговлю в фоне
    await update.message.reply_text("🚀 Бот запущен. Начинаю отслеживать рынок!")

async def stop(update: Update, context: CallbackContext):
    """Остановка бота"""
    global is_running
    is_running = False
    await update.message.reply_text("❌ Бот остановлен!")

def main():
    """Главная функция запуска бота"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.run_polling()

if __name__ == '__main__':
    main()