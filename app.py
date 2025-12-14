import logging
import os
import io
from typing import cast

from dotenv import load_dotenv, dotenv_values
from datetime import datetime,timedelta
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler,
    CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters,
    InvalidCallbackData,PicklePersistence
)
from gemini import chat_gemini,create_new_gemini_chat,analyze_image_gemini
from gpt import chat_gpt

MAX_GEMINI_USES = 5          
COOLDOWN_MINUTES = 2        
COOLDOWN_KEY = 'gemini_cooldown'
USE_COUNT_KEY = 'gemini_use_count'


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
    
    context.user_data.setdefault(USE_COUNT_KEY, 0)  # <-- NEW
    context.user_data.setdefault(COOLDOWN_KEY, None) # <-- NEW
    
    if 'gemini_chat_session' not in context.user_data:
        context.user_data['gemini_chat_session'] = create_new_gemini_chat()

    user = update.effective_user
    await update.message.reply_html(
        rf"👋 Hi {user.mention_html()}!Welcome to Ai Models👾",
        reply_markup=ForceReply(selective=True),
    )
    choice_list: list[str] = ["😎 Gemini", "👽 ChatGPT", "☠ Grok", "👾 Claude.ai", "🤖 DeepSeek"]
    await update.message.reply_text("💬 Please choose:", reply_markup=build_keyboard(choice_list))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(
        "✊ Use /start to test this bot. "
        "💫 Use /reset to reset all bot. Conversation history cleared! "
        "🎬 Use /clear to clear the stored data so that you can see "
        
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the callback data cache"""
    context.bot.callback_data_cache.clear_callback_data()
    context.bot.callback_data_cache.clear_callback_queries()
    await update.effective_message.reply_text("🚫All clear!")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['gemini_chat_session'] = create_new_gemini_chat()
    context.user_data['menu_selection'] = None
    
    await update.effective_message.reply_text(
        "✅ Conversation history cleared! You must now select an AI model "
        "again to start a new topic (or use /start)."
    )

AI_CHOICES = ["Gemini", "ChatGPT", "Grok", "Claude.ai", "DeepSeek"]

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

def cleanup_user_data(user_data):
    """
    Cleans up unpicklable objects (like the Gemini chat session) 
    from a single user's data dictionary.
    """
    if 'gemini_chat_session' in user_data:
        # Delete the problematic, unpicklable object
        del user_data['gemini_chat_session']
    return user_data

class CustomApplication(Application):
    async def update_persistence(self) -> None:
        """
        Overrides the standard update_persistence to first clean the user_data 
        before persistence is executed.
        """
        # --- PRE-PERSISTENCE CLEANUP ---
        # Apply the cleanup function to all users' data dictionaries
        for user_id in self.user_data:
            self.user_data[user_id] = cleanup_user_data(self.user_data[user_id])
        
        # Now call the original persistence update method
        await super().update_persistence()


def check_gemini_limit(user_data: dict) -> tuple[bool, str]:
    """
    Checks if the user has hit the Gemini usage limit.
    Returns (True, message) if limited, or (False, None) if usage is allowed.
    """
    now = datetime.now()
    cooldown_until = user_data.get(COOLDOWN_KEY)
    use_count = user_data.get(USE_COUNT_KEY, 0)

    # 1. Check if the user is in an active cooldown period
    if cooldown_until and now < cooldown_until:
        remaining_time = cooldown_until - now
        minutes = int(remaining_time.total_seconds() // 60)
        seconds = int(remaining_time.total_seconds() % 60)
        return True, (
            f"⛔ Limit Reached! ⛔\n"
            f"You have used your limit of {MAX_GEMINI_USES} Gemini features.\n"
            f"Please wait {minutes} minutes and {seconds} seconds "
            f"or switch to another AI model."
        )

    # 2. Check if the counter needs a reset (i.e., cooldown is over, but counter wasn't cleared)
    if cooldown_until and now >= cooldown_until:
        user_data[USE_COUNT_KEY] = 0
        user_data[COOLDOWN_KEY] = None
        use_count = 0

    # 3. Check for the hard usage limit
    if use_count >= MAX_GEMINI_USES:
        # Start the cooldown period
        user_data[COOLDOWN_KEY] = now + timedelta(minutes=COOLDOWN_MINUTES)
        return True, (
            f"🛑 Limit Exceeded! 🛑\n"
            f"You hit the limit of {MAX_GEMINI_USES} uses. "
            f"The cooldown is active for {COOLDOWN_MINUTES} minutes.\n"
            f"Please use one of the other available models (like ChatGPT)."
        )

    
    return False, None


async def image_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages containing a photo for Gemini analysis."""
    
    selected_llm = context.user_data.get('menu_selection')
    
    if selected_llm != "gemini":
        await update.message.reply_text(
            f"Please select 'Gemini' first to use image analysis. You currently have '{selected_llm}' selected."
        )
        return

    # --- NEW: Limit Check for Image ---
    is_limited, limit_message = check_gemini_limit(context.user_data)
    if is_limited:
        await update.message.reply_text(limit_message, parse_mode='Markdown')
        return

    # 1. Prepare message feedback
    caption = update.message.caption if update.message.caption else "Describe this image."
    sent_message = await update.message.reply_text(
        f"🖼️ Analyzing image with prompt: '{caption}'..."
    )

    try:
        # 2. Download the image
        file_id = update.message.photo[-1].file_id # Get the highest resolution photo
        new_file = await context.bot.get_file(file_id)
        
        # Download the file content into memory (bytes)
        image_bytes = io.BytesIO()
        await new_file.download_to_memory(image_bytes)
        image_bytes.seek(0)
        
        # 3. Analyze the image
        gemini_response = analyze_image_gemini(image_bytes.read(), caption)
        
        # 4. Use is allowed, increment the counter
        context.user_data[USE_COUNT_KEY] += 1 # <-- INCREMENT COUNTER

        # 5. Send the result
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text=gemini_response
        )

    except Exception as e:
        logger.error(f"Error in image analysis: {e}")
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text="An error occurred during image processing. Make sure the file is valid."
        )


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
    selected_llm = context.user_data.get('menu_selection')
    user_message = update.message.text.strip()
    
    
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

    # --- NEW: Check for Bot's Capabilities Question ---
    if selected_llm == "gemini" and user_message.lower() in ["what can you do", "what are your capabilities", "help"]:
        capabilities_text = (
            "🧠 I am the Gemini Bot! I can do the following:\n\n"
            "🌐 - Smart Chat: Remember our conversation history and hold a continuous,🌟 witty discussion. Use /reset to clear my memory.\n"
            "🏞️ - Image Understanding (Vision): Send me a 🌅 photo with a caption and I will analyze the image and answer your question about it.\n"
            "💡 - Reasoning: I use advanced thinking to provide detailed and accurate answers.\n"
            f"🚨- Current Limit: You are allowed {MAX_GEMINI_USES} uses (chat/vision) before a {COOLDOWN_MINUTES} minute cooldown.🚫 Your current count is {context.user_data.get(USE_COUNT_KEY, 0)}."
        )
        await update.message.reply_text(capabilities_text, parse_mode='Markdown')
        return

    # --- NEW: Limit Check ---
    if selected_llm == "gemini":
        is_limited, limit_message = check_gemini_limit(context.user_data)
        if is_limited:
            await update.message.reply_text(limit_message, parse_mode='Markdown')
            return

    logger.info(f"Routing message to: {selected_llm}")
    sent_message = await update.message.reply_text("🤖 Generating response...")

    try:
        response = "" 
        if selected_llm == "gemini":
            chat_session = context.user_data.get('gemini_chat_session')
            if not chat_session:
                 chat_session = create_new_gemini_chat()
                 context.user_data['gemini_chat_session'] = chat_session
            
            # Use is allowed, increment the counter
            context.user_data[USE_COUNT_KEY] += 1 # <-- INCREMENT COUNTER

            response = chat_gemini(chat_session, user_message)
            
        elif selected_llm == "chatgpt":
            response = chat_gpt(user_message)
        else:
            response = f"🗣️ Sorry, the {selected_llm.capitalize()} integration is not yet available."

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
        CustomApplication.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(
        CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(list_button))
    
    # --- FIX 3: Register the chat handler ---
    # This handler catches all text messages that are not commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat)) 
    application.add_handler(MessageHandler(filters.PHOTO, image_message))
    # Run the bot until the user presses Ctrl-C
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    main()