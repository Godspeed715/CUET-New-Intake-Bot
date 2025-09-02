from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN: Final = "8175830217:AAGLvST7qsqZXXfaoiq0oGZ5aTJFyglHfC4"
BOT_USERNAME: Final = "@CUET_NEW_INTAKE_BOT"


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello there😊! You must be aspiring to join "
                                    "CUET (Covenant University Evangelical Team)😁.")
    await update.message.chat.send_message("Please do me a favour and fill the form below😉."
                                            "Also at the end of the form you'll see the link"
                                           "to our telegram GC.")
    await update.message.chat.send_message("")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This is a bot to join CUET (Covenant University Evangelical Team).")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(" ")

# Responses



# error
async def error(update: Update, context:ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('start', reset_command))


    # error handler
    app.add_error_handler(error)

    # Polls bot
    print('Polling...')
    app.run_polling(poll_interval=3)