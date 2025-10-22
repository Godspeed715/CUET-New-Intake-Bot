from flask import Flask, request
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

# --- Environment variables ---
TOKEN = os.environ['BOT_TOKEN']
BOT_USERNAME = os.environ['BOT_USERNAME']
CUET_REGISTRATION_FORM = os.environ['CUET_REGISTRATION_FORM']
CUET_GC_LINK = os.environ['CUET_GC_LINK']

STEP2, STEP3 = range(2)
DELETE_TIMER = 5
chat_messages = {}

# --- Helper functions ---
def track_message(chat_id, message_id):
    chat_messages.setdefault(chat_id, []).append(message_id)

async def delete_all_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int, delay: int = DELETE_TIMER):
    await asyncio.sleep(delay)
    for msg_id in chat_messages.get(chat_id, []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    chat_messages.pop(chat_id, None)

# --- Bot logic ---
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
    track_message(query.effective_chat.id, query.message.message_id)

    units = [
        [InlineKeyboardButton("BFC⛪", callback_data="bfc"), InlineKeyboardButton("Media📸", callback_data="media")],
        [InlineKeyboardButton("Living Epistles📜", callback_data="living_epistles"),
         InlineKeyboardButton("True Worshippers🎵", callback_data="true_worshippers")],
        [InlineKeyboardButton("Welfare💖", callback_data="welfare"), InlineKeyboardButton("Database 📝", callback_data="database")],
        [InlineKeyboardButton("Follow Up🤗", callback_data="follow_up"), InlineKeyboardButton("Not sure yet", callback_data="not_sure")]
    ]
    msg2 = await query.message.reply_text("Select your service unit from below:",
                                          reply_markup=InlineKeyboardMarkup(units))
    track_message(query.effective_chat.id, msg2.message_id)
    return STEP3


async def step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chosen = query.data.replace("_", " ").title()
    await query.edit_message_text(f"So you want to join **{chosen}** ✅", parse_mode="Markdown")
    track_message(query.effective_chat.id, query.message.message_id)
    asyncio.create_task(delete_all_messages(context, query.effective_chat.id))
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Conversation cancelled ❌")
    track_message(update.effective_chat.id, msg.message_id)
    asyncio.create_task(delete_all_messages(context, update.effective_chat.id))
    return ConversationHandler.END


# --- Flask setup for webhook ---
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={STEP2: [CallbackQueryHandler(step2)], STEP3: [CallbackQueryHandler(step3)]},
    fallbacks=[CommandHandler("cancel", cancel)]
)
telegram_app.add_handler(conv_handler)

@app.route("/")
def home():
    return "Bot is running!", 200

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok", 200


if __name__ == "__main__":
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_URL', 'your-app.onrender.com')}/{TOKEN}"
    )
