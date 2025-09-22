from flask import Flask
import threading
from typing import Final
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler

# Environment variables
TOKEN: Final = os.environ['BOT_TOKEN']
BOT_USERNAME: Final = os.environ['BOT_USERNAME']
CUET_REGISTRATION_FORM = os.environ['CUET_REGISTRATION_FORM']
CUET_GC_LINK = os.environ['CUET_GC_LINK']

# Constants
STEP1, STEP2, STEP3 = range(3)
DELETE_TIMER = 5  # seconds after last chat to delete all messages

# Store messages per chat
chat_messages = {}  # {chat_id: [message_id, ...]}


def track_message(chat_id, message_id):
    if chat_id not in chat_messages:
        chat_messages[chat_id] = []
    chat_messages[chat_id].append(message_id)


async def delete_all_messages(context: ContextTypes.DEFAULT_TYPE,
                              chat_id: int,
                              delay: int = DELETE_TIMER):
    await asyncio.sleep(delay)
    for msg_id in chat_messages.get(chat_id, []):
        try:
            await context.bot.delete_message(chat_id=chat_id,
                                             message_id=msg_id)
        except:
            pass  # message might already be deleted
    chat_messages.pop(chat_id, None)  # clear after deletion


# Step 1: /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg1 = await update.message.reply_text(
        "Hello there😊! You must be aspiring to join CUET (Covenant University Evangelical Team)😁."
    )
    track_message(update.effective_chat.id, msg1.message_id)

    keyboard = [[
        InlineKeyboardButton("CUET Registration Form",
                             url=CUET_REGISTRATION_FORM)
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg2 = await update.message.reply_text(
        "Please fill out this form to continue 😉", reply_markup=reply_markup)
    track_message(update.effective_chat.id, msg2.message_id)

    keyboard_done = [[
        InlineKeyboardButton("Yes ✅", callback_data="yes"),
        InlineKeyboardButton("No ❌", callback_data="no")
    ]]
    reply_markup_done = InlineKeyboardMarkup(keyboard_done)
    msg3 = await update.message.reply_text("Have you completed the form?",
                                           reply_markup=reply_markup_done)
    track_message(update.effective_chat.id, msg3.message_id)

    return STEP2


# Step 2: Handle Yes/No
async def step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        msg = await query.edit_message_text(
            "Great! Now choose your service unit 👇")
    else:
        msg = await query.edit_message_text(
            "Please complete the form first before proceeding.")

    track_message(query.effective_chat.id, query.message.message_id)

    keyboard_units = [
        [
            InlineKeyboardButton("BFC⛪", callback_data="bfc"),
            InlineKeyboardButton("Media📸", callback_data="media")
        ],
        [
            InlineKeyboardButton("Living Epistles📜",
                                 callback_data="living_epistles"),
            InlineKeyboardButton("True Worshippers🎵",
                                 callback_data="true_worshippers")
        ],
        [
            InlineKeyboardButton("Welfare💖", callback_data="welfare"),
            InlineKeyboardButton("Database 📝", callback_data="database")
        ],
        [
            InlineKeyboardButton("Follow Up🤗", callback_data="follow_up"),
            InlineKeyboardButton("Not sure yet", callback_data="not_sure")
        ]
    ]
    reply_markup_units = InlineKeyboardMarkup(keyboard_units)
    msg2 = await query.message.reply_text(
        "Select your service unit from below:",
        reply_markup=reply_markup_units)
    track_message(query.effective_chat.id, msg2.message_id)

    return STEP3


# Step 3: Handle service unit selection
async def step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selection_map = {
        "bfc": "BFC⛪",
        "media": "Media📸",
        "living_epistles": "Living Epistles📜",
        "true_worshippers": "True Worshippers🎵",
        "welfare": "Welfare💖",
        "database": "Database 📝",
        "follow_up": "Follow Up🤗",
        "not_sure": "Not sure yet"
    }

    chosen_unit = selection_map.get(query.data, query.data)
    msg = await query.edit_message_text(
        f"So you want to join **{chosen_unit}** ✅")
    track_message(query.effective_chat.id, query.message.message_id)

    # Start the self-destruct timer for all chat messages
    asyncio.create_task(delete_all_messages(context, query.effective_chat.id))

    return ConversationHandler.END


# Fallback / cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Conversation cancelled ❌")
    track_message(update.effective_chat.id, msg.message_id)
    asyncio.create_task(delete_all_messages(context, update.effective_chat.id))
    return ConversationHandler.END


# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


# --- Keep-alive Flask server ---
flask_app = Flask('')


@flask_app.route('/')
def home():
    return "Bot is alive!"


def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)


threading.Thread(target=run_flask).start()

# --- Run Telegram bot ---
if __name__ == "__main__":
    bot_app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            STEP2: [CallbackQueryHandler(step2)],
            STEP3: [CallbackQueryHandler(step3)]
        },
        fallbacks=[CommandHandler("cancel", cancel)])

    bot_app.add_handler(conv_handler)
    bot_app.add_error_handler(error)
    bot_app.run_polling()
