import os
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

# Загрузка переменных окружения
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Определение стадий разговора
BASE, TARGET, AMOUNT = range(3)

# Клавиатура для отмены
cancel_kb = ReplyKeyboardMarkup([['/cancel']], resize_keyboard=True)


# Начало работы с ботом
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-конвертер валют. Используй /convert чтобы начать.\n"
        "Для отмены в любой момент используй /cancel",
        reply_markup=ReplyKeyboardRemove()
    )


# Запуск процесса конвертации
async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите код исходной валюты (например: USD):",
        reply_markup=cancel_kb
    )
    return BASE


# Обработка исходной валюты
async def base_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['base'] = update.message.text.upper()
    await update.message.reply_text("Введите код целевой валюты (например: EUR):")
    return TARGET


# Обработка целевой валюты
async def target_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target'] = update.message.text.upper()
    await update.message.reply_text("Введите сумму для конвертации:")
    return AMOUNT


# Получение суммы и выполнение конвертации
async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Ошибка! Введите число:")
        return AMOUNT

    base = context.user_data['base']
    target = context.user_data['target']

    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{base}"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data["result"] == "success":
            if target in data["conversion_rates"]:
                rate = data["conversion_rates"][target]
                converted_amount = amount * rate
                await update.message.reply_text(
                    f"Результат: {amount} {base} = {converted_amount:.2f} {target}",
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await update.message.reply_text("Ошибка: Валюта не найдена")
        else:
            await update.message.reply_text("Ошибка API. Проверьте коды валют.")

    except Exception as e:
        await update.message.reply_text(f"Ошибка соединения: {str(e)}")

    return ConversationHandler.END


# Отмена операции
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Операция отменена",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# Основная функция
def main():
    if not API_KEY:
        print("Ошибка: API-ключ не найден!")
        return

    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('convert', convert)],
        states={
            BASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_currency)],
            TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_currency)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()