from flask import Flask, request, jsonify # Added request and jsonify for webhook handling
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

# Set up logging (Good practice for debugging on Render)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables & Configuration ---
# Your bot token is used as the secret path for the webhook URL
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")

BOT_USERNAME = os.environ.get('BOT_USERNAME', 'YourBot')
CUET_REGISTRATION_FORM = os.environ.get('CUET_REGISTRATION_FORM', 'https://example.com/form')
CUET_GC_LINK = os.environ.get('CUET_GC_LINK', 'https://t.me/example')

# --- Constants ---
STEP2, STEP3 = range(2)
DELETE_TIMER = 5
chat_messages = {}
WEBHOOK_PATH = f'/{TOKEN}' # We will use the token as a secure webhook path

# --- Global Telegram Application (Initialised later) ---
bot_app: Application = None

# --- Helper Functions ---
def track_message(chat_id, message_id):
    chat_messages.setdefault(chat_id, []).append(message_id)

async def delete_all_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int, delay: int = DELETE_TIMER):
    await asyncio.sleep(delay)
    for msg_id in chat_messages.get(chat_id, []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            logger.warning(f"Could not delete message {msg_id} in chat {chat_id}: {e}")
    chat_messages.pop(chat_id, None)

# --- Bot Handlers (Same as before) ---
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
        # User pressed 'No', but we still want to move the conversation forward state-wise 
        # to allow them to correct it or try again.
        await query.edit_message_text("Please complete the form first before proceeding. If you'd like to try again, select 'Yes'.")
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
    track_message(update.effective_chat.id, msg2.message_id)
    return STEP3

async def step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chosen = query.data.replace("_", " ").title()
    await query.edit_message_text(f"So you want to join **{chosen}** ✅", parse_mode="Markdown")
    
    # Start the delete timer for all messages
    asyncio.create_task(delete_all_messages(context, query.effective_chat.id))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Conversation cancelled ❌")
    track_message(update.effective_chat.id, msg.message_id)
    asyncio.create_task(delete_all_messages(context, update.effective_chat.id))
    return ConversationHandler.END

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Update {update} caused error {context.error}")

# --- Flask Keep-Alive and Webhook Setup ---
flask_app = Flask(__name__)

# 1. Health Check Route (for Render to ping and keep the service awake)
@flask_app.route('/')
def home():
    return "Bot is alive!", 200

# 2. Webhook Route (receives updates from Telegram)
@flask_app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    if request.method == "POST":
        # Get the JSON data from Telegram
        json_data = request.get_json(force=True)
        # Convert the JSON data into a Telegram Update object and process it
        update = Update.de_json(json_data, bot_app.bot)
        
        # Process the update asynchronously
        await bot_app.process_update(update)
        
    # Telegram expects a 200 OK response quickly
    return "ok", 200

# --- Run bot and Flask ---
if __name__ == "__main__":
    # 1. Build the Telegram Application
    bot_app = Application.builder().token(TOKEN).build()

    # 2. Add Handlers (Same as your original code)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={STEP2: [CallbackQueryHandler(step2)], STEP3: [CallbackQueryHandler(step3)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True
    )

    bot_app.add_handler(conv_handler)
    bot_app.add_error_handler(error)

    # 3. Webhook Setup (Required when using webhooks instead of polling)
    # The WEBHOOK_URL_BASE must be set in your Render environment variables 
    # (e.g., https://your-render-service.onrender.com)
    WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE")
    
    if WEBHOOK_URL_BASE:
        # Setting the webhook tells Telegram where to send updates
        webhook_url = f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}"
        try:
            # Must run this inside the asyncio loop
            async def set_hook():
                await bot_app.bot.set_webhook(url=webhook_url)
                logger.info(f"Webhook successfully set to: {webhook_url}")
            
            # Since we are outside the bot_app.run_webhook() context, 
            # we need to manually run the asyncio task for set_webhook.
            # We must use a dedicated event loop for this sync-to-async operation.
            loop = asyncio.new_event_loop()
            loop.run_until_complete(set_hook())
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            
    # 4. Run Flask Application (Replaces threading and polling)
    port = int(os.environ.get("PORT", 8080)) # Default to 8080 as a common web service port
    logger.info(f"Starting Flask server on port {port}...")
    # Flask will now listen for incoming HTTP requests (health checks and Telegram webhooks)
    flask_app.run(host="0.0.0.0", port=port)
