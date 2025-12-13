import logging
import os
from dotenv import load_dotenv, dotenv_values

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from gemini import chat_gemini
from gpt import chat_gpt


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Bot Token not found ...")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['menu_selection'] = None
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!Welcome to Ai Models"
        "Select a model:\n"
        "1.Gemini\n"
        "2.ChatGPT",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    selectedLLM = context.user_data['menu_selection']

    if selectedLLM is None:
        if update.message.text is None:
            await update.message.reply_text("Please select a model")
            return
        llm = update.message.text.lower()
        if llm == "gemini":
            selectedLLM = "gemini"
        elif llm == "chatgpt":
            selectedLLM = "chatgpt"

        context.user_data['menu_selection'] = selectedLLM

    logger.info(selectedLLM)
    if selectedLLM == "gemini":
        await update.message.reply_text(chat_gemini(update.message.text))
    elif selectedLLM == "chatgpt":
        await update.message.reply_text(chat_gpt(update.message.text))


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()