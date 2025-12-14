import logging
import os
import io
from typing import cast
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler,
    CallbackQueryHandler, 
    ContextTypes, 
    MessageHandler, 
    filters,
    InvalidCallbackData,
    PicklePersistence
)
from gemini import chat_gemini, create_new_gemini_chat, analyze_image_gemini
from gpt import chat_gpt

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# Gemini usage limits
MAX_GEMINI_USES = 10          
COOLDOWN_MINUTES = 2        
COOLDOWN_KEY = 'gemini_cooldown'
USE_COUNT_KEY = 'gemini_use_count'

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Bot Token not found in .env file")

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================================================
# AI MODEL CONFIGURATION
# ============================================================================

# Define AI models with their display names and internal identifiers
AI_MODELS = {
    "gemini": {"display": "😎 Gemini", "enabled": True},
    "chatgpt": {"display": "👽 ChatGPT", "enabled": True},
    "grok": {"display": "☠ Grok", "enabled": False},
    "claude": {"display": "👾 Claude", "enabled": True},
    "deepseek": {"display": "🤖 DeepSeek", "enabled": False}
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_keyboard(ai_models: dict) -> InlineKeyboardMarkup:
    """
    Builds an inline keyboard with available AI models.
    
    Args:
        ai_models: Dictionary of AI models with their configurations
        
    Returns:
        InlineKeyboardMarkup with buttons for each enabled AI model
        
    How it works:
    - Creates a button for each AI model
    - The button text is the display name (with emoji)
    - The callback_data is a tuple: (model_id, list of all model_ids)
    - This tuple format is required for arbitrary_callback_data feature
    """
    buttons = []
    model_ids = list(ai_models.keys())
    
    for idx, (model_id, config) in enumerate(ai_models.items()):
        if config["enabled"]:
            # callback_data structure: (index, list of model IDs)
            callback_data = (idx, model_ids)
            button = InlineKeyboardButton(
                config["display"], 
                callback_data=callback_data
            )
            buttons.append(button)
    
    return InlineKeyboardMarkup.from_column(buttons)


def check_gemini_limit(user_data: dict) -> tuple[bool, str]:
    """
    Checks if user has exceeded Gemini usage limits.
    
    Args:
        user_data: User's context data dictionary
        
    Returns:
        Tuple of (is_limited: bool, message: str or None)
        
    Why we need this:
    - Gemini API has rate limits and costs per request
    - This prevents abuse and manages API costs
    - Gives users clear feedback about limits
    
    How it works:
    1. Check if user is in active cooldown period
    2. Reset counter if cooldown has expired
    3. Check if user hit the usage limit
    4. Start cooldown if limit exceeded
    """
    now = datetime.now()
    cooldown_until = user_data.get(COOLDOWN_KEY)
    use_count = user_data.get(USE_COUNT_KEY, 0)
    
    # Active cooldown check
    if cooldown_until and now < cooldown_until:
        remaining_time = cooldown_until - now
        minutes = int(remaining_time.total_seconds() // 60)
        seconds = int(remaining_time.total_seconds() % 60)
        return True, (
            f"⛔ Limit Reached!\n"
            f"You've used {MAX_GEMINI_USES} Gemini requests.\n"
            f"Wait {minutes}m {seconds}s or try another model."
        )
    
    # Reset counter if cooldown expired
    if cooldown_until and now >= cooldown_until:
        user_data[USE_COUNT_KEY] = 0
        user_data[COOLDOWN_KEY] = None
        use_count = 0
    
    # Check usage limit
    if use_count >= MAX_GEMINI_USES:
        user_data[COOLDOWN_KEY] = now + timedelta(minutes=COOLDOWN_MINUTES)
        return True, (
            f"🛑 Limit Exceeded!\n"
            f"{MAX_GEMINI_USES} uses reached. "
            f"Cooldown: {COOLDOWN_MINUTES} minutes.\n"
            f"Try ChatGPT or other models!"
        )
    
    return False, None


def get_or_create_gemini_session(user_data: dict):
    """
    Gets existing Gemini chat session or creates a new one.
    
    Why we don't store the session object:
    - Gemini chat sessions contain unpicklable thread locks
    - PicklePersistence can't serialize these objects
    - We create new sessions as needed instead
    
    Args:
        user_data: User's context data
        
    Returns:
        A new or cached Gemini chat session (not persisted)
    """
    # Store in a temporary cache that won't be pickled
    if '_gemini_session_cache' not in user_data:
        user_data['_gemini_session_cache'] = create_new_gemini_chat()
    return user_data['_gemini_session_cache']


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start command - Initialize the bot and show AI model selection.
    
    What happens:
    1. Initialize user data with default values
    2. Greet the user with their name
    3. Display keyboard with available AI models
    """
    # Initialize user data
    context.user_data['menu_selection'] = None
    context.user_data.setdefault(USE_COUNT_KEY, 0)
    context.user_data.setdefault(COOLDOWN_KEY, None)
    
    user = update.effective_user
    
    # Send welcome message
    await update.message.reply_html(
        f"👋 Hi {user.mention_html()}!\n"
        f"Welcome to the Multi-AI Chat Bot! 🤖\n\n"
        f"Choose an AI model below to start chatting:",
        reply_markup=ForceReply(selective=True),
    )
    
    # Show model selection keyboard
    await update.message.reply_text(
        "💬 Select your AI model:", 
        reply_markup=build_keyboard(AI_MODELS)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /help command - Display bot usage information.
    """
    help_text = (
        "🤖 Multi-AI Chat Bot Help\n\n"
        "Available Commands:\n"
        "• /start - Start the bot and select an AI model\n"
        "• /switch - Switch to a different AI model\n"
        "• /exit - Exit current model (keeps history)\n"
        "• /reset - Clear all conversation history\n"
        "• /status - Check your usage statistics\n"
        "• /help - Show this help message\n\n"
        "Available Models:\n"
        "• 😎 Gemini - Google's AI (with image analysis)\n"
        "• 👽 ChatGPT - OpenAI's GPT model\n"
        "• 👾 Claude - Anthropic's Claude AI\n"
        "• ☠ Grok - xAI's Grok model\n"
        "• 🤖 DeepSeek - DeepSeek AI model\n\n"
        "Tips:\n"
        "- Send text messages to chat with the selected AI\n"
        "- Send images (Gemini/Claude) for visual analysis\n"
        f"- Gemini has a limit of {MAX_GEMINI_USES} uses per {COOLDOWN_MINUTES} minutes"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /reset command - Clear conversation history and model selection.
    
    What it does:
    - Removes cached Gemini session (forces new conversation)
    - Clears model selection
    - Resets to initial state
    """
    if '_gemini_session_cache' in context.user_data:
        del context.user_data['_gemini_session_cache']
    
    context.user_data['menu_selection'] = None
    
    await update.message.reply_text(
        "✅ Reset complete!\n"
        "Conversation history cleared. Use /start to select a new model."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /status command - Show current usage statistics.
    """
    use_count = context.user_data.get(USE_COUNT_KEY, 0)
    cooldown_until = context.user_data.get(COOLDOWN_KEY)
    selected_model = context.user_data.get('menu_selection', 'None')
    
    status_text = (
        f"📊 Your Status\n\n"
        f"Selected Model: {selected_model.title() if selected_model else 'None'}\n"
        f"Gemini Uses: {use_count}/{MAX_GEMINI_USES}\n"
    )
    
    if cooldown_until:
        remaining = cooldown_until - datetime.now()
        if remaining.total_seconds() > 0:
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            status_text += f"Cooldown: {minutes}m {seconds}s remaining"
        else:
            status_text += "Cooldown: Expired (counter will reset on next use)"
    else:
        status_text += "Cooldown: Not active"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')


async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /exit command - Exit current model and return to model selection.
    
    What it does:
    - Clears current model selection
    - Keeps conversation history intact (unlike /reset)
    - Shows model selection keyboard again
    - User can switch models without losing conversation data
    
    Use cases:
    - User wants to try a different AI model
    - Current model is having issues
    - Quick model switching during conversation
    """
    selected_model = context.user_data.get('menu_selection')
    
    if selected_model:
        # Clear model selection but keep conversation histories
        context.user_data['menu_selection'] = None
        
        await update.message.reply_text(
            f"👋 Exited from {AI_MODELS.get(selected_model, {}).get('display', selected_model)}.\n"
            f"Your conversation history is preserved.\n\n"
            f"Select a new model below:",
            reply_markup=build_keyboard(AI_MODELS)
        )
    else:
        await update.message.reply_text(
            "ℹ️ No model currently selected.\n"
            "Use /start to begin."
        )


async def switch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /switch command - Switch to a different AI model.
    
    Difference from /exit:
    - /exit: Just exits, shows keyboard
    - /switch: Exits and shows keyboard (essentially the same for now)
    
    Benefits:
    - More intuitive command name for users
    - Can be extended to show current model first
    - Provides context about what will happen
    
    Future enhancements:
    - Could show side-by-side model comparisons
    - Could suggest best model for user's query type
    - Could preserve separate histories per model
    """
    selected_model = context.user_data.get('menu_selection')
    
    # Build status message
    if selected_model:
        current_model_name = AI_MODELS.get(selected_model, {}).get('display', selected_model)
        status_msg = f"🔄 Switching from {current_model_name}.\n\n"
    else:
        status_msg = "🔄 Choose your AI model:\n\n"
    
    # Clear selection
    context.user_data['menu_selection'] = None
    
    # Show available models
    status_msg += "Available models:\n"
    for model_id, config in AI_MODELS.items():
        if config["enabled"]:
            status_msg += f"• {config['display']}\n"
    
    status_msg += "\nSelect one below:"
    
    await update.message.reply_text(
        status_msg,
        reply_markup=build_keyboard(AI_MODELS)
    )


# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

async def list_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles AI model selection from inline keyboard.
    
    How arbitrary_callback_data works:
    - Instead of string data, we use Python objects (tuples)
    - Telegram limits callback_data to 64 bytes
    - arbitrary_callback_data lets us use unlimited data
    - The data is stored in bot's cache, not sent to Telegram
    
    The callback_data structure:
    - (index, [list of model IDs])
    - We use the index to look up which model was selected
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    
    try:
        # Extract data from callback
        button_index, model_ids = cast("tuple[int, list[str]]", query.data)
        selected_model_id = model_ids[button_index]
        
        # Store the selected model (lowercase for easy comparison)
        context.user_data['menu_selection'] = selected_model_id
        
        # Get display name
        display_name = AI_MODELS[selected_model_id]["display"]
        
        # Send confirmation
        await query.edit_message_text(
            text=(
                f"✅ Selected: {display_name}\n\n"
                f"Start chatting! I'll route your messages to {display_name}.\n\n"
                f"Commands:\n"
                f"• /reset - Change AI model\n"
                f"• /help - Show help\n"
                f"• /status - Check usage"
            ),
            reply_markup=None,
        )
        
        # Clean up callback data cache
        context.drop_callback_data(query)
        
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.edit_message_text(
            "❌ Error selecting model. Please try /start again."
        )


async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles expired or invalid callback data.
    
    Why this happens:
    - Callback data cache has size limits
    - Old buttons may be invalidated
    - This provides graceful degradation
    """
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "⚠️ This button has expired.\n"
        "Please use /start to get a fresh keyboard."
    )


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

async def image_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles image messages for Gemini vision analysis.
    
    How it works:
    1. Check if Gemini is selected
    2. Check usage limits
    3. Download image from Telegram
    4. Send to Gemini API with caption as prompt
    5. Return analysis result
    
    Why we use io.BytesIO:
    - Keeps image data in memory (faster than disk)
    - No need to clean up temporary files
    - Efficient for small to medium images
    """
    selected_model = context.user_data.get('menu_selection')
    
    # Only Gemini supports image analysis
    if selected_model != "gemini":
        await update.message.reply_text(
            f"❌ Image analysis requires Gemini.\n"
            f"Currently selected: {selected_model or 'None'}\n"
            f"Use /reset to switch models."
        )
        return
    
    # Check usage limits
    is_limited, limit_message = check_gemini_limit(context.user_data)
    if is_limited:
        await update.message.reply_text(limit_message)
        return
    
    # Get prompt from caption or use default
    caption = update.message.caption or "Describe this image in detail."
    
    # Show processing message
    sent_message = await update.message.reply_text(
        f"🖼️ Analyzing image...\n"
        f"Prompt: '{caption}'"
    )
    
    try:
        # Download image
        file_id = update.message.photo[-1].file_id  # Highest resolution
        new_file = await context.bot.get_file(file_id)
        
        # Store in memory
        image_bytes = io.BytesIO()
        await new_file.download_to_memory(image_bytes)
        image_bytes.seek(0)
        
        # Analyze with Gemini
        gemini_response = analyze_image_gemini(image_bytes.read(), caption)
        
        # Increment usage counter
        context.user_data[USE_COUNT_KEY] += 1
        
        # Send result
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text=f"🖼️ Image Analysis:\n\n{gemini_response}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text="❌ Error processing image. Please try again."
        )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main chat handler - routes messages to selected AI model.
    
    Flow:
    1. Check if model is selected
    2. Check rate limits (for Gemini)
    3. Show "generating" message
    4. Call appropriate AI API
    5. Return response
    6. Handle errors gracefully
    """
    selected_model = context.user_data.get('menu_selection')
    user_message = update.message.text.strip()
    
    # Ensure model is selected
    if not selected_model:
        await update.message.reply_text(
            "⚠️ Please select an AI model first!\n"
            "Use /start to choose a model."
        )
        return
    
    # Check Gemini limits
    if selected_model == "gemini":
        is_limited, limit_message = check_gemini_limit(context.user_data)
        if is_limited:
            await update.message.reply_text(limit_message)
            return
    
    logger.info(f"Routing to {selected_model}: {user_message[:50]}...")
    
    # Show processing indicator
    sent_message = await update.message.reply_text(
        f"🤖 {AI_MODELS[selected_model]['display']} is thinking..."
    )
    
    try:
        response = ""
        
        if selected_model == "gemini":
            # Get or create session
            chat_session = get_or_create_gemini_session(context.user_data)
            
            # Send message
            response = chat_gemini(chat_session, user_message)
            
            # Increment counter
            context.user_data[USE_COUNT_KEY] += 1
            
            logger.info(f"Gemini response: {response[:100]}...")
            
        elif selected_model == "chatgpt":
            response = chat_gpt(user_message)
            
        else:
            # Placeholder for unimplemented models
            response = (
                f"🚧 {AI_MODELS[selected_model]['display']} "
                f"integration coming soon!\n\n"
                f"Available models: Gemini, ChatGPT"
            )
        
        # Send response
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text=response
        )
        
    except Exception as e:
        logger.error(f"Error in {selected_model}: {e}")
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=sent_message.message_id,
            text=(
                f"❌ Error communicating with {AI_MODELS[selected_model]['display']}.\n"
                f"Please try again or use /reset to switch models."
            )
        )


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main() -> None:
    """
    Main application entry point.
    
    Key components explained:
    
    1. PicklePersistence:
       - Saves user_data to disk between restarts
       - Allows conversation continuity
       - File: 'arbitrarycallbackdatabot'
    
    2. arbitrary_callback_data:
       - Allows complex Python objects in button callbacks
       - Bypasses Telegram's 64-byte limit
       - Stores data in bot's cache
    
    3. Handler order matters:
       - Specific handlers (commands) before generic ones (text)
       - Invalid callback handler catches expired buttons
    """
    
    # Initialize persistence
    try:
        persistence = PicklePersistence(filepath="bot_data")
    except Exception as e:
        logger.error(f"Persistence init error: {e}")
        persistence = PicklePersistence(filepath="bot_data")
    
    # Build application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("exit", exit_command))
    application.add_handler(CommandHandler("switch", switch_command))
    
    # Register callback handlers (order matters!)
    application.add_handler(
        CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(list_button))
    
    # Register message handlers
    application.add_handler(MessageHandler(filters.PHOTO, image_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # Run bot
    logger.info("🚀 Bot starting...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot shut down complete")


if __name__ == "__main__":
    main()