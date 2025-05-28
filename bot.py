import logging
import asyncio
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from telethon_manager import login_account, broadcast_message, MAX_ACCOUNTS

# States for login flow
API_ID, API_HASH, PHONE, OTP = range(4)

# Per-user temporary data for login
user_login_data = {}
user_messages = {}

# Set up logging
logging.basicConfig(level=logging.INFO)

# Replace with your bot token
BOT_TOKEN = "YOUR_BOT_TOKEN"

# ------------------- Handlers ----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to the Multi-Account Broadcast Bot!\nPlease enter your *API ID* to begin login for Account #1:", parse_mode="Markdown")
    user_login_data[update.effective_user.id] = {"account_index": 0}
    return API_ID

async def get_api_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = user_login_data[update.effective_user.id]
    user_data["api_id"] = int(update.message.text)
    await update.message.reply_text("✅ Got API ID. Now enter your *API Hash*:", parse_mode="Markdown")
    return API_HASH

async def get_api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = user_login_data[update.effective_user.id]
    user_data["api_hash"] = update.message.text.strip()
    await update.message.reply_text("📱 Now enter your *phone number* (with country code):", parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = user_login_data[update.effective_user.id]
    user_data["phone"] = update.message.text.strip()

    async def send_code():
        await update.message.reply_text("📨 OTP code sent. Please enter the code:")

    async def get_otp():
        context.user_data["awaiting_otp"] = True
        while "otp" not in context.user_data:
            await asyncio.sleep(1)
        return context.user_data.pop("otp")

    bot_user_id = update.effective_user.id
    account_index = user_data["account_index"]
    api_id = user_data["api_id"]
    api_hash = user_data["api_hash"]
    phone = user_data["phone"]

    success, msg = await login_account(
        bot_user_id, account_index, api_id, api_hash, phone,
        send_code=lambda: send_code(),
        get_otp=lambda: get_otp()
    )

    await update.message.reply_text(msg)
    if success:
        if account_index + 1 >= MAX_ACCOUNTS:
            await update.message.reply_text("🛑 Max 10 accounts added.")
            return ConversationHandler.END
        await update.message.reply_text("Add another account? Send /yes to add or /done to finish.")
        return PHONE  # Reuse this state to allow decision
    else:
        return ConversationHandler.END

async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_otp"):
        context.user_data["otp"] = update.message.text.strip()
        await update.message.reply_text("✅ OTP received. Logging in...")
        return ConversationHandler.END

async def add_another(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_login_data[user_id]["account_index"] += 1
    await update.message.reply_text(f"Let's log in Account #{user_login_data[user_id]['account_index'] + 1}. Please enter *API ID*:", parse_mode="Markdown")
    return API_ID

async def finish_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Setup complete. Send any message, then type /broadcast to send it from all your accounts.")
    return ConversationHandler.END

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_messages[user_id] = update.message.text
    await update.message.reply_text("💬 Message saved. Now type /broadcast to send it.")

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_messages:
        await update.message.reply_text("❌ You haven't sent a message yet. Send your message first.")
        return

    message = user_messages[user_id]
    await update.message.reply_text("🚀 Starting broadcast...")

    start_time = time.time()
    success, result = await broadcast_message(user_id, message)
    elapsed = round(time.time() - start_time, 2)

    if success:
        await update.message.reply_text(f"{result}\n⏱ Time taken: {elapsed} seconds\n✅ Thank you!")
    else:
        await update.message.reply_text(f"❌ Broadcast failed: {result}")

# ------------------ Main Bot Setup ------------------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    login_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            API_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_id)],
            API_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_hash)],
            PHONE: [
                CommandHandler("yes", add_another),
                CommandHandler("done", finish_add),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp)],
        },
        fallbacks=[],
    )

    app.add_handler(login_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_message))
    app.add_handler(CommandHandler("broadcast", do_broadcast))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()