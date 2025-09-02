from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN: Final = "8175830217:AAGLvST7qsqZXXfaoiq0oGZ5aTJFyglHfC4"
BOT_USERNAME: Final = "@CUET_NEW_INTAKE_BOT"
CUET_REGISTRATION_FORM = "https://forms.gle/d7CdSUdVdwYwJB397"
CUET_GC_LINK = "https://t.me/+Nx2jAnLnH40wNzdk"

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard_1 = [[InlineKeyboardButton("CUET Registration Form", url=CUET_REGISTRATION_FORM)]]
    keyboard_2 = [
        [InlineKeyboardButton("Yes", callback_data="yes"), InlineKeyboardButton("No", callback_data="no")]
    ]
    reply_markup_1 = InlineKeyboardMarkup(keyboard_1)
    reply_markup_2 = InlineKeyboardMarkup(keyboard_2)


    await update.message.reply_text("Hello there😊! You must be aspiring to join "
                                    "CUET (Covenant University Evangelical Team)😁.")
    await update.message.chat.send_message("Please do me a favour and fill the form below😉."
                                            "Also at the end of the form you'll see the link"
                                           "to our telegram GC.", reply_markup=reply_markup_1)
    await update.message.chat.send_message("Are you done with filling the form?", reply_markup=reply_markup_2)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This is a bot to join CUET (Covenant University Evangelical Team).")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(" ")

async def button_handler_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge button press

    if query.data == "yes":
        await query.edit_message_text("So now onto the next Question 👇")

# Responses



# self commands
# async def service_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):


# error
async def error(update: Update, context:ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CallbackQueryHandler(button_handler_1))


    # error handler
    app.add_error_handler(error)

    # Polls bot
    print('Polling...')
    app.run_polling(poll_interval=3)