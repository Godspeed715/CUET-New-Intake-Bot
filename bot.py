from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler

TOKEN: Final = "8175830217:AAGLvST7qsqZXXfaoiq0oGZ5aTJFyglHfC4"
BOT_USERNAME: Final = "@CUET_NEW_INTAKE_BOT"
CUET_REGISTRATION_FORM = "https://forms.gle/d7CdSUdVdwYwJB397"
CUET_GC_LINK = "https://t.me/+Nx2jAnLnH40wNzdk"



# Constants
STEP1, STEP2, STEP3 = range(3)


# Step 1: /start command sends form
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello there😊! You must be aspiring to join CUET (Covenant University Evangelical Team)😁."
    )

    keyboard = [[InlineKeyboardButton("CUET Registration Form", url=CUET_REGISTRATION_FORM)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Please fill out this form to continue 😉",
        reply_markup=reply_markup
    )

    # Ask if user completed the form
    keyboard_done = [
        [InlineKeyboardButton("Yes ✅", callback_data="yes"),
         InlineKeyboardButton("No ❌", callback_data="no")]
    ]
    reply_markup_done = InlineKeyboardMarkup(keyboard_done)
    await update.message.reply_text(
        "Have you completed the form?",
        reply_markup=reply_markup_done
    )

    return STEP2  # move to step 2

# Step 2: Handle Yes/No
async def step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        await query.edit_message_text("Great! Now choose your service unit 👇")
    else:
        await query.edit_message_text("Please complete the form first before proceeding.")

    # Show service unit buttons
    keyboard_units = [
        [InlineKeyboardButton("BFC⛪", callback_data="bfc"), InlineKeyboardButton("Media📸", callback_data="media")],
        [InlineKeyboardButton("Living Epistles📜", callback_data="living_epistles"), InlineKeyboardButton("True Worshippers🎵", callback_data="true_worshippers")],
        [InlineKeyboardButton("Welfare💖", callback_data="welfare"), InlineKeyboardButton("Database 📝", callback_data="database")],
        [InlineKeyboardButton("Follow Up🤗", callback_data="follow_up"), InlineKeyboardButton("Not sure yet", callback_data="not_sure")]
    ]
    reply_markup_units = InlineKeyboardMarkup(keyboard_units)
    await query.message.reply_text("Select your service unit from below:", reply_markup=reply_markup_units)

    return STEP3  # move to step 3

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
    await query.edit_message_text(f"So you want to join **{chosen_unit}** ✅")
    return ConversationHandler.END

# Fallback / cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Conversation cancelled ❌")
    return ConversationHandler.END

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

# Run bot
if __name__ == "__main__":
    # TOKEN = "YOUR_BOT_TOKEN_HERE"  # replace with your new token
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            STEP2: [CallbackQueryHandler(step2)],
            STEP3: [CallbackQueryHandler(step3)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error)
    app.run_polling()

