import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from config import TELEGRAM_TOKEN
from core.trading_logic import trade_logic, stop_trading, is_running

# ✅ Логирование (пишем ошибки в `bot_log.txt`)
logging.basicConfig(filename="bot_log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def start(update: Update, context: CallbackContext):
    """Запуск бота"""
    if is_running.is_set():
        await update.message.reply_text("⚠ Бот уже работает!")
        return

    is_running.set()  # ✅ Фикс бага: Теперь можно перезапускать бот после stop
    asyncio.create_task(trade_logic())
    await update.message.reply_text("🚀 Бот запущен. Начинаю отслеживать рынок!")

async def stop(update: Update, context: CallbackContext):
    """Остановка бота"""
    if not is_running.is_set():
        await update.message.reply_text("⚠ Бот уже остановлен!")
        return

    is_running.clear()
    await update.message.reply_text("❌ Бот остановлен! (Завершаю сделки...)")
    await stop_trading()

def main():
    """Главная функция запуска бота"""
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('stop', stop))
        logging.info("✅ Бот успешно запущен!")
        application.run_polling()
    except Exception as e:
        logging.error(f"❌ Критическая ошибка в боте: {e}")

if __name__ == '__main__':
    main()