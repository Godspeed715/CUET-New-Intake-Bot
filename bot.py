from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN: Final = "8175830217:AAGLvST7qsqZXXfaoiq0oGZ5aTJFyglHfC4"
BOT_USERNAME: Final = "@CUET_NEW_INTAKE_BOT"

form_message  = ()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello there😊! You must be aspiring to join "
                                    "CUET (Covenant University Evangelical Team)😁.")
    await update.message.chat.send_message("Please do me a favour and fill the form below😉."
                                            "Also at the end of the form you'll see the link"
                                           "to our telegram GC.")
    await update.message.chat.send_message("")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text()

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text()