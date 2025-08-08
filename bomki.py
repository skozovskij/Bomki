import json
import os
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from apscheduler.schedulers.background import BackgroundScheduler

DATA_FILE = "users.json"

HELP_TEXT = (
    "  Доступні команди:\n"
    "/start — зареєструватися в системі\n"
    "/zdaty — позначити, що ви здали за поточний місяць\n"
    "/status — переглянути, за які місяці вже здано\n"
    "/help — показати цей список команд\n"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not os.path.exists(DATA_FILE):
        users = {}
    else:
        with open(DATA_FILE, "r") as f:
            users = json.load(f)

    if user_id not in users:
        users[user_id] = {"submitted_months": []}
        with open(DATA_FILE, "w") as f:
            json.dump(users, f)
        await update.message.reply_text("Ти зареєстрований!")
    else:
        await update.message.reply_text("Ти вже зареєстрований.")

    await update.message.reply_text(HELP_TEXT)

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    current_month = datetime.today().strftime("%Y-%m")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            users = json.load(f)

        if user_id in users:
            if current_month not in users[user_id]["submitted_months"]:
                users[user_id]["submitted_months"].append(current_month)
                with open(DATA_FILE, "w") as f:
                    json.dump(users, f)
                await update.message.reply_text(f"Ти здав за {current_month}. Дякую!")
            else:
                await update.message.reply_text("Ти вже здав за цей місяць.")
        else:
            await update.message.reply_text("Ти ще не зареєстрований. Використай /start.")
    else:
        await update.message.reply_text("Дані не знайдено. Використай /start.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    current_month = datetime.today().strftime("%Y-%m")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            users = json.load(f)

        if user_id in users:
            submitted = users[user_id].get("submitted_months", [])
            submitted_str = "\n".join(f"{m}" for m in sorted(submitted)) if submitted else "— нічого не здано —"

            if current_month in submitted:
                current_status = f" За {current_month} вже здано."
            else:
                current_status = f"За {current_month} ще не здано."

            await update.message.reply_text(
                f"Твій статус:\n\n{submitted_str}\n\n{current_status}"
            )
        else:
            await update.message.reply_text("Ти ще не зареєстрований. Використай /start.")
    else:
        await update.message.reply_text("Дані не знайдено. Використай /start.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text
    await update.message.reply_text(
        f"Команда `{command}` не розпізнана.\nСпробуй /help, щоб побачити доступні команди."
    )

def monthly_check(bot: Bot):
    today = datetime.today()
    current_month = today.strftime("%Y-%m")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            users = json.load(f)

        for user_id, data in users.items():
            if current_month not in data.get("submitted_months", []):
                bot.send_message(chat_id=user_id, text=f"Ти ще не здав за {current_month}. Будь ласка, зроби це якнайшвидше!")

def weekly_reminder(bot: Bot):
    today = datetime.today()
    current_month = today.strftime("%Y-%m")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            users = json.load(f)

        for user_id, data in users.items():
            if current_month not in data.get("submitted_months", []):
                bot.send_message(chat_id=user_id, text=f"Нагадування: Ти ще не здав за {current_month}. Не забудь!")

async def main():
    bot_token = "7503125819:AAHNfAUw4Z5JieHb6_wvZwXcl0nuCgzvNAs"
    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("zdaty", submit))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))  # Обробка невідомих команд

    bot = Bot(token=bot_token)

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: monthly_check(bot), 'cron', day=1, hour=9)
    scheduler.add_job(lambda: weekly_reminder(bot), 'cron', day_of_week='mon', hour=9)
    scheduler.start()

    print("active")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main())
