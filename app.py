import logging
from typing import cast
import os
from dotenv import load_dotenv, dotenv_values

from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler,
    CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters,
    InvalidCallbackData,PicklePersistence
)
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
        rf"Hi {user.mention_html()}!Welcome to Ai Models",
        reply_markup=ForceReply(selective=True),
    )
    choice_list: list[str] = ["Gemini", "ChatGPT", "Grok", "Claude.ai", "Nova.ai"]
    await update.message.reply_text("Please choose:", reply_markup=build_keyboard(choice_list))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(
        "Use /start to test this bot. Use /clear to clear the stored data so that you can see "
        "what happens, if the button data is not available. "
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the callback data cache"""
    context.bot.callback_data_cache.clear_callback_data()
    context.bot.callback_data_cache.clear_callback_queries()
    await update.effective_message.reply_text("All clear!")

AI_CHOICES = ["Gemini", "ChatGPT", "Grok", "Claude.ai", "Nova.ai"]

def build_keyboard(choices: list[str]) -> InlineKeyboardMarkup:
    """
    Helper function to build the inline keyboard.
    
    The button text is the AI name (from the 'choices' list).
    The callback data is a tuple: (index, the full list of choices).
    """
    buttons = []
    # Loop through the list of choices
    for index, choice_name in enumerate(choices):
        # The button text is the AI name (choice_name).
        # The callback data contains: (index + 1, the full choices list).
        # We use (index + 1) because buttons are naturally numbered starting at 1.
        callback_data = (index + 1, choices)
        
        button = InlineKeyboardButton(choice_name, callback_data=callback_data)
        buttons.append(button)
        
    return InlineKeyboardMarkup.from_column(buttons)


async def list_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Parses the CallbackQuery, stores the selected model, and prompts the user to start chatting.
    """
    query = update.callback_query
    await query.answer()
    
    button_index, choices = cast("tuple[int, list[str]]", query.data)
    selected_choice = choices[button_index - 1]
    
    # --- FIX 1: Store the selected model in user_data ---
    # Convert the selected model name to lowercase for easy comparison in the chat handler
    context.user_data['menu_selection'] = selected_choice.lower()
    
    await query.edit_message_text(
        text=f"✅ Model selected: {selected_choice}\n\n"
             f"You can now send me your questions, and I will forward them to {selected_choice}.",
        reply_markup=None, # Remove the keyboard after selection
    )

    context.drop_callback_data(query)


async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informs the user that the button is no longer available."""
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "Sorry, I could not process this button click 😕 Please send /start to get a new keyboard."
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Retrieve the model selection from user_data
    selected_llm = context.user_data.get('menu_selection')
    user_message = update.message.text
    
    if selected_llm is None:
        # If no model is selected, prompt the user to choose one.
        await update.message.reply_text("Please select an AI model using the buttons below first.")
        # Re-display the menu
        choice_list: list[str] = ["Gemini", "ChatGPT", "Grok", "Claude.ai", "Nova.ai"]
        await update.message.reply_text("Choose a model:", reply_markup=build_keyboard(choice_list))
        return
    
    if user_message is None:
        # Handle non-text messages if necessary (e.g., photos)
        await update.message.reply_text("Please send a text message.")
        return

    logger.info(f"Routing message to: {selected_llm}")
    
    # Provide visual feedback while waiting for the API
    sent_message = await update.message.reply_text("🤖 Generating response...")

    try:
        if selected_llm == "gemini":
            response = chat_gemini(user_message)
        elif selected_llm == "chatgpt":
            response = chat_gpt(user_message)
        else:
            # Handle models you haven't implemented yet (Grok, Claude.ai, etc.)
            response = f"Sorry, the {selected_llm.capitalize()} integration is not yet available."

        # Edit the temporary message with the final response
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text=response
        )
        
    except Exception as e:
        logger.error(f"Error in {selected_llm} API call: {e}")
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text=f"An error occurred while talking to {selected_llm.capitalize()}. Please try again later."
        )


# ... (rest of main) ...

def main() -> None:
    """Run the bot."""
    persistence = PicklePersistence(filepath="arbitrarycallbackdatabot")
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(
        CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(list_button))
    
    # --- FIX 3: Register the chat handler ---
    # This handler catches all text messages that are not commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat)) 

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()