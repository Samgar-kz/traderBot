import asyncio
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from config import TELEGRAM_TOKEN
from trading_logic import trade_logic, stop_trading

trade_thread = None  # Переменная для потока торговли

async def start(update: Update, context: CallbackContext):
    """Запуск бота"""
    global trade_thread

    if trade_thread and trade_thread.is_alive():
        await update.message.reply_text("⚠ Бот уже работает!")
        return

    trade_thread = threading.Thread(target=lambda: asyncio.run(trade_logic()), daemon=True)
    trade_thread.start()

    await update.message.reply_text("🚀 Бот запущен. Начинаю отслеживать рынок!")

async def stop(update: Update, context: CallbackContext):
    """Остановка бота"""
    global trade_thread

    if not trade_thread or not trade_thread.is_alive():
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