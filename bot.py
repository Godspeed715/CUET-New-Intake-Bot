from flask import Flask
import threading
from typing import Final
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)



# Environment variables
TOKEN = os.environ.get("TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourBot")
CUET_REGISTRATION_FORM = os.environ.get("CUET_REGISTRATION_FORM", "https://example.com/form")
CUET_GC_LINK = os.environ.get("CUET_GC_LINK", "https://t.me/example")
CUET_BFC_GC_LINK = os.environ.get("CUET_BFC_GC_LINK")
CUET_DATABASE_GC_LINK = os.environ.get("CUET_DATABASE_GC_LINK")
CUET_EPISTLES_GC_LINK = os.environ.get("CUET_EPISTLES_GC_LINK")
CUET_FOLLOWUP_GC_LINK = os.environ.get("CUET_FOLLOWUP_GC_LINK")
CUET_MEDIA_GC_LINK = os.environ.get("CUET_MEDIA_GC_LINK")
CUET_WELFARE_GC_LINK = os.environ.get("CUET_WELFARE_GC_LINK")
CUET_WORSHIPPERS_GC_LINK = os.environ.get("CUET_WORSHIPPERS_GC_LINK")

# Group links
GC_LINKS = {
    "bfc": CUET_BFC_GC_LINK,
    "media": CUET_MEDIA_GC_LINK,
    "living_epistles": CUET_EPISTLES_GC_LINK,
    "true_worshippers": CUET_WORSHIPPERS_GC_LINK,
    "welfare": CUET_WELFARE_GC_LINK,
    "database": CUET_DATABASE_GC_LINK,
    "follow_up": CUET_FOLLOWUP_GC_LINK,
}
# Constants
STEP1, STEP2, STEP3 = range(3)
DELETE_TIMER = 5  # seconds after last chat to delete all messages

# Store messages per chat
chat_messages = {}  # {chat_id: [message_id, ...]}


def track_message(chat_id, message_id):
    if chat_id not in chat_messages:
        chat_messages[chat_id] = []
    chat_messages[chat_id].append(message_id)


async def delete_all_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int, delay: int = DELETE_TIMER):
    """Deletes all tracked messages in a chat after a delay."""
    await asyncio.sleep(delay)
    for msg_id in chat_messages.get(chat_id, []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            # This handles cases where a message has already been deleted,
            # or the bot doesn't have permissions to delete it.
            print(f"Failed to delete message {msg_id} in chat {chat_id}: {e}")
    # Clear the list of messages for this chat after trying to delete them all
    chat_messages.pop(chat_id, None)


# Step 1: /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg1 = await update.message.reply_text(
        "Hello there😊! You must be aspiring to join CUET (Covenant University Evangelical Team)😁."
    )
    track_message(update.effective_chat.id, msg1.message_id)

    keyboard = [[InlineKeyboardButton("CUET Registration Form", url=CUET_REGISTRATION_FORM)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg2 = await update.message.reply_text("Please fill out this form to continue 😉", reply_markup=reply_markup)
    track_message(update.effective_chat.id, msg2.message_id)

    keyboard_done = [[InlineKeyboardButton("Yes ✅", callback_data="yes"),
                      InlineKeyboardButton("No ❌", callback_data="no")]]
    reply_markup_done = InlineKeyboardMarkup(keyboard_done)
    msg3 = await update.message.reply_text("Have you completed the form?", reply_markup=reply_markup_done)
    track_message(update.effective_chat.id, msg3.message_id)

    return STEP2


# Step 2: Handle Yes/No
async def step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        msg = await query.edit_message_text("Great! Now choose your service unit 👇")
        track_message(query.message.chat_id, query.message.message_id)
    
        keyboard_units = [
            [InlineKeyboardButton("BFC⛪", callback_data="bfc"), InlineKeyboardButton("Media📸", callback_data="media")],
            [InlineKeyboardButton("Living Epistles📜", callback_data="living_epistles"),
                InlineKeyboardButton("True Worshippers🎵", callback_data="true_worshippers")],
            [InlineKeyboardButton("Welfare💖", callback_data="welfare"), InlineKeyboardButton("Database 📝", callback_data="database")],
            [InlineKeyboardButton("Follow Up🤗", callback_data="follow_up"), InlineKeyboardButton("Not sure yet", callback_data="not_sure")]
        ]
        reply_markup_units = InlineKeyboardMarkup(keyboard_units)
        msg2 = await query.message.reply_text("Select your service unit from below:", reply_markup=reply_markup_units)
        track_message(query.message.chat_id, msg2.message_id)

        return STEP3
            # msg = await query.edit_message_text("Please complete the form first before proceeding.")
        # track_message(query.message.chat_id, query.message.message_id)
        # asyncio.create_task(delete_all_messages(context, query.message.chat_id))
        # return ConversationHandler.END
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
    msg = await query.edit_message_text(f"So you want to join {chosen_unit} ✅")
    track_message(query.message.chat_id, query.message.message_id)

    # Send CUET group link as final message, if a link exists
    group_link = GC_LINKS.get(query.data)
    if group_link:  # Only send if the link is not None
        keyboard_group = [[InlineKeyboardButton(f"Join {chosen_unit} Group 👥", url=group_link)]]
        reply_markup_group = InlineKeyboardMarkup(keyboard_group)
        msg_group = await query.message.reply_text(
            f"Finally, join {chosen_unit} group to stay updated:\nPs: This link chat will delete in 2mins.",
            reply_markup=reply_markup_group
        )
        track_message(query.message.chat_id, msg_group.message_id)
    else:
        msg_group = await query.message.reply_text(
            f"Next time pick a sub unit.\nPs: This link chat will delete in 2mins.")
        track_message(query.message.chat_id, msg_group.message_id)

    asyncio.create_task(delete_all_messages(context, query.message.chat_id))

    return ConversationHandler.END




# --- In cancel function ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Conversation cancelled ❌")
    track_message(update.effective_chat.id, msg.message_id)
    asyncio.create_task(delete_all_messages(context, update.effective_chat.id)) # Corrected
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





# --- Run Telegram bot ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot_app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            STEP2: [CallbackQueryHandler(step2)],
            STEP3: [CallbackQueryHandler(step3)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True
    )

    bot_app.add_handler(conv_handler)
    bot_app.add_error_handler(error)
    bot_app.run_polling()
