import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from config import TELEGRAM_TOKEN
from trading_logic import trade_logic, stop_trading, is_running

async def start(update: Update, context: CallbackContext):
    """Запуск бота"""
    if is_running.is_set():
        await update.message.reply_text("⚠ Бот уже работает!")
        return

    asyncio.create_task(trade_logic())
    await update.message.reply_text("🚀 Бот запущен. Начинаю отслеживать рынок!")

async def stop(update: Update, context: CallbackContext):
    """Остановка бота"""
    if not is_running.is_set():
        await update.message.reply_text("⚠ Бот уже остановлен!")
        return

    await update.message.reply_text("❌ Бот остановлен! (Завершение сделок...)")
    await stop_trading()

def main():
    """Главная функция запуска бота"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.run_polling()

if __name__ == '__main__':
    main()
