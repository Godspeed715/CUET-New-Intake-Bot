from flask import Flask
import threading
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)
import logging

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
TOKEN = os.environ.get("BOT_TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourBot")
CUET_REGISTRATION_FORM = os.environ.get("CUET_REGISTRATION_FORM", "https://example.com/form")
CUET_GC_LINK = os.environ.get("CUET_GC_LINK", "https://t.me/example")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required.")

# --- Constants ---
STEP2, STEP3 = range(2)
DELETE_TIMER = 5  # seconds
chat_messages = {}

# --- Helper Functions ---
def track_message(chat_id, message_id):
    chat_messages.setdefault(chat_id, []).append(message_id)

async def delete_all_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Deletes all tracked messages in a chat."""
    for msg_id in chat_messages.get(chat_id, []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            logger.warning(f"Failed to delete message {msg_id} in chat {chat_id}: {e}")
    chat_messages.pop(chat_id, None)

def schedule_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Schedules deletion using job_queue."""
    context.job_queue.run_once(lambda ctx: asyncio.create_task(delete_all_messages(context, chat_id)),
                               when=DELETE_TIMER)

# --- Bot Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg1 = await update.message.reply_text("Hello there😊! You must be aspiring to join CUET😁.")
    track_message(update.effective_chat.id, msg1.message_id)

    form_btn = [[InlineKeyboardButton("CUET Registration Form", url=CUET_REGISTRATION_FORM)]]
    msg2 = await update.message.reply_text("Please fill out this form to continue 😉",
                                           reply_markup=InlineKeyboardMarkup(form_btn))
    track_message(update.effective_chat.id, msg2.message_id)

    confirm_btns = [[InlineKeyboardButton("Yes ✅", callback_data="yes"),
                     InlineKeyboardButton("No ❌", callback_data="no")]]
    msg3 = await update.message.reply_text("Have you completed the form?",
                                           reply_markup=InlineKeyboardMarkup(confirm_btns))
    track_message(update.effective_chat.id, msg3.message_id)

    return STEP2

async def step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        await query.edit_message_text("Great! Now choose your service unit 👇")
    else:
        await query.edit_message_text("Please complete the form first before proceeding.")

    units = [
        [InlineKeyboardButton("BFC⛪", callback_data="bfc"), InlineKeyboardButton("Media📸", callback_data="media")],
        [InlineKeyboardButton("Living Epistles📜", callback_data="living_epistles"),
         InlineKeyboardButton("True Worshippers🎵", callback_data="true_worshippers")],
        [InlineKeyboardButton("Welfare💖", callback_data="welfare"), InlineKeyboardButton("Database 📝", callback_data="database")],
        [InlineKeyboardButton("Follow Up🤗", callback_data="follow_up"), InlineKeyboardButton("Not sure yet", callback_data="not_sure")]
    ]
    msg2 = await query.message.reply_text("Select your service unit from below:",
                                          reply_markup=InlineKeyboardMarkup(units))
    track_message(query.message.chat_id, msg2.message_id)

    return STEP3

async def step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chosen = query.data.replace("_", " ").title()
    await query.edit_message_text(f"So you want to join **{chosen}** ✅", parse_mode="Markdown")

    # Schedule deletion of all chat messages
    schedule_delete(context, query.message.chat_id)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Conversation cancelled ❌")
    track_message(update.effective_chat.id, msg.message_id)
    # Schedule deletion of all chat messages
    schedule_delete(context, update.effective_chat.id)
    return ConversationHandler.END

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Update {update} caused error {context.error}")

# --- Flask Keep-Alive ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# --- Main ---
if __name__ == "__main__":
    # Start Flask in a background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Build Telegram bot application
    bot_app = Application.builder().token(TOKEN).build()

    # Add handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={STEP2: [CallbackQueryHandler(step2)], STEP3: [CallbackQueryHandler(step3)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    bot_app.add_handler(conv_handler)
    bot_app.add_error_handler(error)

    # Start polling
    logger.info("Bot is starting polling...")
    bot_app.run_polling()
