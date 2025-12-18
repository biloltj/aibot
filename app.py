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
from gpt import chat_gpt, estimate_tokens  
from grok import chat_grok, create_grok_chat, analyze_image_grok
from claude import chat_claude, analyze_image_claude
from deepseek import chat_deepseek


MAX_GEMINI_USES = 10
COOLDOWN_MINUTES = 2
COOLDOWN_KEY = 'gemini_cooldown'
USE_COUNT_KEY = 'gemini_use_count'


MAX_GROK_RPM = 5 
MAX_GROK_TPM = 10000  # 10,000 tokens per minute
GROK_COOLDOWN_MINUTES = 1  # 1-minute cooldown
GROK_RPM_KEY = 'grok_rpm_count'
GROK_TPM_KEY = 'grok_tpm_count'
GROK_COOLDOWN_KEY = 'grok_cooldown'

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Bot Token not found in .env file")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


AI_MODELS = {
    "gemini": {"display": "😎 Gemini", "enabled": True},
    "chatgpt": {"display": "👽 ChatGPT", "enabled": True},
    "grok": {"display": "☠ Grok", "enabled": True},
    "claude": {"display": "👾 Claude", "enabled": True},
    "deepseek": {"display": "🤖 DeepSeek", "enabled": True},
}


def build_keyboard(ai_models: dict) -> InlineKeyboardMarkup:
    buttons = []
    model_ids = list(ai_models.keys())
    for idx, (model_id, config) in enumerate(ai_models.items()):
        if config["enabled"]:
            callback_data = (idx, model_ids)
            button = InlineKeyboardButton(config["display"], callback_data=callback_data)
            buttons.append(button)
    return InlineKeyboardMarkup.from_column(buttons)

def check_gemini_limit(user_data: dict) -> tuple[bool, str]:
    now = datetime.now()
    cooldown_until = user_data.get(COOLDOWN_KEY)
    use_count = user_data.get(USE_COUNT_KEY, 0)

    if cooldown_until and now < cooldown_until:
        remaining_time = cooldown_until - now
        minutes = int(remaining_time.total_seconds() // 60)
        seconds = int(remaining_time.total_seconds() % 60)
        return True, f"⛔ Gemini Limit! Wait {minutes}m {seconds}s."

    if cooldown_until and now >= cooldown_until:
        user_data[USE_COUNT_KEY] = 0
        user_data[COOLDOWN_KEY] = None
        use_count = 0

    if use_count >= MAX_GEMINI_USES:
        user_data[COOLDOWN_KEY] = now + timedelta(minutes=COOLDOWN_MINUTES)
        return True, f"🛑 {MAX_GEMINI_USES} Gemini uses reached. Wait {COOLDOWN_MINUTES} min."

    return False, None

# NEW: Check Grok RPM and TPM limits
def check_grok_limit(user_data: dict, message: str) -> tuple[bool, str]:
    now = datetime.now()
    cooldown_until = user_data.get(GROK_COOLDOWN_KEY)
    rpm_count = user_data.get(GROK_RPM_KEY, 0)
    tpm_count = user_data.get(GROK_TPM_KEY, 0)

    # Check if in cooldown
    if cooldown_until and now < cooldown_until:
        remaining = cooldown_until - now
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        return True, f"⛔ Grok Limit! Wait {minutes}m {seconds}s."

    # Reset if cooldown expired
    if cooldown_until and now >= cooldown_until:
        user_data[GROK_RPM_KEY] = 0
        user_data[GROK_TPM_KEY] = 0
        user_data[GROK_COOLDOWN_KEY] = None
        rpm_count = 0
        tpm_count = 0

    # Estimate tokens for this message (input + expected output)
    tokens = estimate_tokens(message) + 500  # Assume 500 output tokens
    if rpm_count >= MAX_GROK_RPM or tpm_count + tokens >= MAX_GROK_TPM:
        user_data[GROK_COOLDOWN_KEY] = now + timedelta(minutes=GROK_COOLDOWN_MINUTES)
        return True, (
            f"🛑 Grok Limit! {MAX_GROK_RPM} requests or {MAX_GROK_TPM} tokens reached.\n"
            f"Wait {GROK_COOLDOWN_MINUTES} minute."
        )

    # Update counts
    user_data[GROK_RPM_KEY] = rpm_count + 1
    user_data[GROK_TPM_KEY] = tpm_count + tokens
    return False, None

def get_or_create_gemini_session(user_data: dict):
    if '_gemini_session_cache' not in user_data:
        user_data['_gemini_session_cache'] = create_new_gemini_chat()
    return user_data['_gemini_session_cache']

def get_or_create_grok_session(user_data: dict):
    if '_grok_session_cache' not in user_data:
        user_data['_grok_session_cache'] = create_grok_chat()
    return user_data['_grok_session_cache']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['menu_selection'] = None
    context.user_data.setdefault(USE_COUNT_KEY, 0)
    context.user_data.setdefault(COOLDOWN_KEY, None)
    context.user_data.setdefault(GROK_RPM_KEY, 0)  # NEW
    context.user_data.setdefault(GROK_TPM_KEY, 0)  # NEW
    context.user_data.setdefault(GROK_COOLDOWN_KEY, None)  # NEW

    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hi {user.mention_html()}!\n"
        f"Welcome to the Multi-AI Chat Bot! 🤖\n\n"
        f"Choose an AI model below:",
        reply_markup=ForceReply(selective=True),
    )
    await update.message.reply_text(
        "💬 Select your AI model:",
        reply_markup=build_keyboard(AI_MODELS)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 Multi-AI Chat Bot Help\n\n"
        "Commands:\n"
        "/start - Select model\n"
        "/switch - Change model\n"
        "/exit - Exit current model\n"
        "/reset - Clear history\n"
        "/status - Usage stats\n"
        "/help - This message\n\n"
        "Models:\n"
        "😎 Gemini • 👽 ChatGPT • ☠ Grok • 👾 Claude • 🤖 DeepSeek\n\n"
        "💡 Gemini: 10 uses/2 min\n💡 Grok: 5 reqs or 10k tokens/min",
        parse_mode='Markdown'
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if '_gemini_session_cache' in context.user_data:
        del context.user_data['_gemini_session_cache']
    if '_grok_session_cache' in context.user_data:
        del context.user_data['_grok_session_cache']
    context.user_data['menu_selection'] = None
    context.user_data[GROK_RPM_KEY] = 0  
    context.user_data[GROK_TPM_KEY] = 0
    context.user_data[GROK_COOLDOWN_KEY] = None
    await update.message.reply_text("✅ Reset complete! Use /start to choose a model.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    use_count = context.user_data.get(USE_COUNT_KEY, 0)
    grok_rpm = context.user_data.get(GROK_RPM_KEY, 0)
    grok_tpm = context.user_data.get(GROK_TPM_KEY, 0)
    selected = context.user_data.get('menu_selection', 'None').title()
    await update.message.reply_text(
        f"📊 Status\n\n"
        f"Model: {selected}\n"
        f"Gemini uses: {use_count}/{MAX_GEMINI_USES}\n"
        f"Grok requests: {grok_rpm}/{MAX_GROK_RPM}\n"
        f"Grok tokens: {grok_tpm}/{MAX_GROK_TPM}",
        parse_mode='Markdown'
    )

async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    selected = context.user_data.get('menu_selection')
    if selected:
        display = AI_MODELS.get(selected, {}).get('display', selected)
        context.user_data['menu_selection'] = None
        await update.message.reply_text(
            f"👋 Exited {display}\nSelect new model:",
            reply_markup=build_keyboard(AI_MODELS)
        )
    else:
        await update.message.reply_text("No model selected. Use /start.")

async def switch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['menu_selection'] = None
    await update.message.reply_text(
        "🔄 Choose a new model:",
        reply_markup=build_keyboard(AI_MODELS)
    )


async def list_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        button_index, model_ids = cast("tuple[int, list[str]]", query.data)
        selected_model_id = model_ids[button_index]
        context.user_data['menu_selection'] = selected_model_id
        display_name = AI_MODELS[selected_model_id]["display"]

        await query.edit_message_text(
            f"✅ Selected: {display_name}\n\n"
            f"Start chatting! Send messages or images.\n\n"
            f"Commands: /reset /switch /help /status",
            reply_markup=None
        )
        context.drop_callback_data(query)
    except Exception as e:
        logger.error(f"Button error: {e}")
        await query.edit_text("❌ Error. Use /start again.")

async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.effective_message.edit_text("⚠️ Button expired. Use /start.")


async def image_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = context.user_data.get('menu_selection')
    if selected not in ["gemini", "grok", "claude"]:
        await update.message.reply_text(
            f"❌ {AI_MODELS.get(selected,{}).get('display','This model')} does not support images.\n"
            "Switch to Gemini, Grok, or Claude."
        )
        return

    caption = update.message.caption or "Describe this image."
    sent = await update.message.reply_text(f"🖼️ Analyzing with {AI_MODELS[selected]['display']}...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = io.BytesIO()
        await file.download_to_memory(image_bytes)
        image_bytes.seek(0)
        image_data = image_bytes.read()

        if selected == "gemini":
            is_limited, msg = check_gemini_limit(context.user_data)
            if is_limited:
                await sent.edit_text(msg)
                return
            response = analyze_image_gemini(image_data, caption)
            context.user_data[USE_COUNT_KEY] += 1
        elif selected == "grok":
            is_limited, msg = check_grok_limit(context.user_data, caption)
            if is_limited:
                await sent.edit_text(msg)
                return
            response = analyze_image_grok(image_data, caption)
            context.user_data[GROK_RPM_KEY] += 1
            context.user_data[GROK_TPM_KEY] += estimate_tokens(caption) + 500
        elif selected == "claude":
            response = analyze_image_claude(image_data, caption)

        await sent.edit_text(f"🖼️ Analysis:\n\n{response}", parse_mode='Markdown')
    except Exception as e:
        await sent.edit_text("❌ Image analysis failed.")
        logger.error(f"Image error: {e}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    selected = context.user_data.get('menu_selection')
    text = update.message.text.strip()

    if not selected:
        await update.message.reply_text("Please select a model with /start")
        return

    if selected == "gemini":
        is_limited, msg = check_gemini_limit(context.user_data)
        if is_limited:
            await update.message.reply_text(msg)
            return
    elif selected == "grok":
        is_limited, msg = check_grok_limit(context.user_data, text)
        if is_limited:
            await update.message.reply_text(msg)
            return

    thinking = await update.message.reply_text(f"🤖 {AI_MODELS[selected]['display']} is thinking...")

    try:
        response = ""
        if selected == "gemini":
            session = get_or_create_gemini_session(context.user_data)
            response = chat_gemini(session, text)
            context.user_data[USE_COUNT_KEY] += 1
        elif selected == "chatgpt":
            response = chat_gpt(text)
        elif selected == "grok":
            session = get_or_create_grok_session(context.user_data)
            response = chat_grok(session, text)
            context.user_data[GROK_RPM_KEY] += 1
            context.user_data[GROK_TPM_KEY] += estimate_tokens(text) + 500
        elif selected == "claude":
            history = context.user_data.get('claude_history', [])
            response, history = chat_claude(text, history)
            context.user_data['claude_history'] = history
        elif selected == "deepseek":
            history = context.user_data.get('deepseek_history', [])
            response, history = chat_deepseek(text, history)
            context.user_data['deepseek_history'] = history

        await thinking.edit_text(response)
    except Exception as e:
        await thinking.edit_text("❌ Error. Try again or switch model.")
        logger.error(f"{selected} error: {e}")


def main() -> None:
    persistence = PicklePersistence(filepath="bot_data")
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("exit", exit_command))
    application.add_handler(CommandHandler("switch", switch_command))

    application.add_handler(CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData))
    application.add_handler(CallbackQueryHandler(list_button))

    application.add_handler(MessageHandler(filters.PHOTO, image_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("🚀 Multi-AI Bot starting with ALL 5 models!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()