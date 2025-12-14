# 🤖 AiBot
AI telegram bot - which has 5 different Ai Models init incuding:
  - 1 Google \\ Gemini
  - 2 OpenAi \\ Chatgpt 
  - 3 Twitter \\ Grok 
  - 4 Anthropic \\ Cloude.ai
  - 5 DeepSeek \\ Deepseek 

 ## Usage

 - How it works? 
 * This Ai telegram bot is connected directly to these Models:
      - 1. Google \\ Gemini
      - 2. OpenAi \\ Chatgpt 
      - 3. Twitter \\ Grok 
      - 4. Anthropic \\ Cloude.ai
      - 5. DeepSeek \\ Deepseek 
* Easy to use just connected to Models by API


## ⚡ Features
 
- Start or Clear options
- Colorful UI for Talk with Ai.
- Easy-to-run Python scripts.

# 🚀 Complete Multi-AI Telegram Bot Guide

## 📑 Table of Contents
1. [Installation & Setup](#installation--setup)
2. [API Keys Configuration](#api-keys-configuration)
3. [Understanding Each AI Model](#understanding-each-ai-model)
4. [Code Architecture](#code-architecture)
5. [New Commands](#new-commands)
6. [Testing Guide](#testing-guide)
7. [Troubleshooting](#troubleshooting)

---

## 📦 Installation & Setup

### 1. System Requirements
```bash
# Python 3.10 or higher (Required for Grok)
python3 --version

# Should show: Python 3.10.x or higher
```

### 2. Install All Dependencies
```bash
# Create/update requirements.txt
cat > requirements.txt << EOF
python-telegram-bot==21.0
python-dotenv==1.0.0
google-genai==0.2.0
anthropic==0.40.0
openai==1.60.0
xai-sdk==0.1.0
Pillow==10.0.0
httpx==0.27.0
EOF

# Install
pip install -r requirements.txt
```

### 3. Project Structure
```
aibot/
├── app.py              # Main bot (UPDATED)
├── gemini.py           # Google Gemini API
├── gpt.py              # OpenAI ChatGPT API (UPDATED)
├── claude_api.py       # Anthropic Claude API (NEW)
├── grok.py             # xAI Grok API (NEW)
├── deepseek.py         # DeepSeek API (NEW)
├── .env                # API keys (NEVER commit!)
├── .gitignore          # Ignore sensitive files
├── requirements.txt    # Python dependencies
└── bot_data            # Persistent storage (auto-created)
```

---

## 🔑 API Keys Configuration

### Get Your API Keys

#### 1. **Telegram Bot Token**
```
1. Message @BotFather on Telegram
2. Send /newbot and follow instructions
3. Copy the token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
```

#### 2. **Google Gemini API**
```
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Get API Key"
3. Copy key (starts with: AIza...)
```

#### 3. **OpenAI ChatGPT API**
```
1. Visit: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy key (starts with: sk-proj-...)
Note: Requires paid account ($5+ credit)
```

#### 4. **Anthropic Claude API**
```
1. Visit: https://console.anthropic.com/
2. Go to "API Keys"
3. Click "Create Key"
4. Copy key (starts with: sk-ant-...)
Note: $5 free credit for new users
```

#### 5. **xAI Grok API**
```
1. Visit: https://console.x.ai/
2. Sign up/login with X account
3. Go to "API Keys"
4. Create new key
5. Copy key
Note: $25 free credit in December 2024
```

#### 6. **DeepSeek API**
```
1. Visit: https://platform.deepseek.com/
2. Register account
3. Top up balance (minimum $1)
4. Go to API Keys
5. Create new key (starts with: sk-...)
```

### Create .env File
```bash
# In your project root
cat > .env << 'EOF'
# Telegram
BOT_TOKEN=your_telegram_token_here

# Google Gemini
GEMINI_API_KEY=your_gemini_key_here

# OpenAI ChatGPT
OPENAI_API_KEY=your_openai_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_claude_key_here

# xAI Grok
XAI_API_KEY=your_grok_key_here

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_key_here
EOF
```

### Secure Your Keys
```bash
# Add to .gitignore
cat >> .gitignore << EOF
.env
*.pyc
__pycache__/
ai/
bot_data*
*.log
EOF
```

---

## 🤖 Understanding Each AI Model

### 1. **😎 Google Gemini**

**What it is:**
- Google's multimodal AI model
- Excels at understanding text and images together
- Fast and efficient

**Key Features:**
- ✅ Conversation memory (stateful sessions)
- ✅ Image analysis (vision)
- ✅ Fast responses
- ✅ Free tier available

**Best for:**
- General conversations
- Image understanding
- Quick questions
- Free usage

**Technical Details:**
```python
# Uses gRPC-based API
# Session-based (server manages context)
# Unpicklable (can't save to disk)

# Example flow:
chat = create_new_gemini_chat()  # Create session
response = chat_gemini(chat, "Hello")  # Send message
# Session remembers this message
response = chat_gemini(chat, "What did I say?")  # Contextual
```

**Cost:** Free tier generous, then pay-per-use

---

### 2. **👽 OpenAI ChatGPT**

**What it is:**
- OpenAI's flagship language model
- Most well-known AI assistant
- Multiple versions (GPT-4, GPT-3.5, GPT-4o)

**Key Features:**
- ✅ Highest quality responses (GPT-4)
- ✅ Vision capable (GPT-4o, GPT-4-turbo)
- ✅ Fast with GPT-3.5
- ✅ Industry standard

**Best for:**
- Complex reasoning
- Creative writing
- Code generation
- When quality matters most

**Technical Details:**
```python
# Uses REST API (standard HTTP)
# Stateless (we manage history)
# OpenAI-compatible format (standard)

# Example flow:
history = []
response, history = chat_gpt("Hello", history)
# We manually pass history
response, history = chat_gpt("What did I say?", history)
```

**Models:**
- `gpt-4o`: Best overall ($2.50/M input, $10/M output)
- `gpt-4-turbo`: Very capable ($10/M input, $30/M output)
- `gpt-3.5-turbo`: Fast & cheap ($0.50/M input, $1.50/M output)

**Cost:** Moderate to high (but excellent quality)

---

### 3. **👾 Anthropic Claude**

**What it is:**
- Anthropic's advanced AI assistant
- Known for safety and helpfulness
- Long context window (200k tokens)

**Key Features:**
- ✅ Very long conversations (200k context)
- ✅ Excellent at following instructions
- ✅ Vision capable
- ✅ Strong ethical guidelines

**Best for:**
- Long documents/conversations
- Detailed analysis
- Code review
- Following complex instructions

**Technical Details:**
```python
# Uses REST API
# Stateless (we manage history)
# Similar to OpenAI but different format

# Example flow:
history = []
response, history = chat_claude("Hello", history)
# History stored as list of messages
response, history = chat_claude("Continue", history)
```

**Models:**
- `claude-sonnet-4-5`: Best balance ($3/M input, $15/M output)
- `claude-opus-4-1`: Most capable ($15/M input, $75/M output)
- `claude-haiku-4-5`: Fastest ($0.25/M input, $1.25/M output)

**Cost:** Moderate (great value for long contexts)

---

### 4. **☠ xAI Grok**

**What it is:**
- Elon Musk's xAI company's model
- Witty, sometimes humorous
- Real-time web/X search integration

**Key Features:**
- ✅ Web search built-in
- ✅ X (Twitter) search
- ✅ Vision capable (Grok-4)
- ✅ Code execution
- ✅ Latest real-time data

**Best for:**
- Current events
- News/tweets
- When you need real-time info
- Technical queries with web context

**Technical Details:**
```python
# Uses gRPC (like Gemini, not REST)
# Session-based
# Can search web/X automatically
# Official Python SDK required

# Example flow:
chat = create_grok_chat()  # Session created
response = chat_grok(chat, "Latest AI news")
# Grok can search web automatically
```

**Models:**
- `grok-4`: Latest, vision support
- `grok-3`: Previous gen, reliable
- `grok-beta`: Experimental features

**Cost:** $5/M input, $15/M output

**Unique Features:**
- Autonomous web search
- X/Twitter integration
- Code execution on server

---

### 5. **🤖 DeepSeek**

**What it is:**
- Chinese AI company's open-weight model
- Extremely cost-effective
- Strong at coding and math

**Key Features:**
- ✅ 10-50x cheaper than GPT-4
- ✅ Reasoning mode (shows thinking)
- ✅ Context caching (90% discount on repeated content)
- ✅ OpenAI-compatible API

**Best for:**
- Cost-sensitive applications
- Coding tasks
- Math/logic problems
- High-volume usage

**Technical Details:**
```python
# Uses OpenAI-compatible API
# Just change base_url
# Stateless (we manage history)
# Two models: chat and reasoner

# Example flow:
history = []
# Fast mode
response, history = chat_deepseek("Hello", history)

# Reasoning mode (shows thinking process)
response, history = chat_deepseek(
    "Solve: x^2 + 5x + 6 = 0",
    history,
    enable_reasoning=True
)
# Shows: <think>...</think> then answer
```

**Models:**
- `deepseek-chat`: Fast general model (DeepSeek-V3.2)
- `deepseek-reasoner`: Shows chain-of-thought (DeepSeek-R1)

**Cost:** Ultra-low
- Cache hit: $0.014/M tokens (90% discount!)
- Cache miss: $0.14/M tokens
- 10-50x cheaper than GPT-4

**Unique Features:**
- Reasoning mode (chain-of-thought)
- Context caching (huge savings)
- OpenAI compatibility (easy migration)

---

## 🏗️ Code Architecture

### How the Bot Works

```
User sends message
       ↓
Check model selected?
       ↓
Route to appropriate AI API
       ↓
Manage conversation history
       ↓
Send to API
       ↓
Return response to user
```

### State Management

**Session-based (Gemini, Grok):**
```python
# Create once, reuse
session = create_session()
response = chat(session, "Hello")
response = chat(session, "Continue")
# Session remembers everything
```

**History-based (ChatGPT, Claude, DeepSeek):**
```python
# Pass history each time
history = []
response, history = chat("Hello", history)
response, history = chat("Continue", history)
# We track history manually
```

### Persistence Strategy

**What gets saved:**
- User's selected model
- Conversation histories (ChatGPT, Claude, DeepSeek)
- Usage counters (Gemini rate limiting)
- Cooldown timers

**What doesn't get saved:**
- Gemini chat sessions (unpicklable)
- Grok chat sessions (unpicklable)
- Temporary cache data

**Why:**
- Thread locks can't be pickled
- We recreate sessions on demand
- Conversation history sufficient for stateless APIs

---

## 🎮 New Commands

### `/start`
**What it does:** Initialize bot, show AI model selection

**Example:**
```
User: /start
Bot: 👋 Hi Alice! Welcome to Ai Models👾
     Choose your AI model: [Keyboard with 5 models]
```

### `/switch`
**What it does:** Switch to a different AI model

**Example:**
```
User: /switch
Bot: 🔄 Switching from 😎 Gemini
     Available models:
     • 😎 Gemini
     • 👽 ChatGPT
     • 👾 Claude
     • ☠ Grok
     • 🤖 DeepSeek
     [Keyboard appears]
```

**Use case:** Try different AIs for comparison

### `/exit`
**What it does:** Exit current model, return to selection

**Example:**
```
User: /exit
Bot: 👋 Exited from 👽 ChatGPT
     Your conversation history is preserved.
     Select a new model: [Keyboard]
```

**Difference from /reset:** Keeps conversation history

### `/reset`
**What it does:** Clear ALL conversation history

**Example:**
```
User: /reset
Bot: ✅ Reset complete!
     Conversation history cleared.
     Use /start to select a new model.
```

**Use case:** Start completely fresh

### `/status`
**What it does:** Show current usage statistics

**Example:**
```
User: /status
Bot: 📊 Your Status
     Selected Model: Gemini
     Gemini Uses: 5/10
     Cooldown: Not active
```

### `/help`
**What it does:** Show all commands and features

---

## 🧪 Testing Guide

### Test Each Model Independently

#### 1. Test Gemini
```bash
python gemini.py
```

Expected output:
```
🧪 Testing Gemini integration...
1️⃣ Testing connection...
✅ Connection successful!
2️⃣ Testing chat session...
Response: 4
```

#### 2. Test ChatGPT
```bash
python gpt.py
```

#### 3. Test Claude
```bash
python claude_api.py
```

#### 4. Test Grok
```bash
python grok.py
```

Note: Requires Python 3.10+

#### 5. Test DeepSeek
```bash
python deepseek.py
```

### Test Complete Bot

```bash
# Start bot
python app.py

# You should see:
# 2025-12-15 XX:XX:XX - INFO - 🚀 Bot starting...
# 2025-12-15 XX:XX:XX - INFO - Application started
```

### In Telegram

**Test 1: Model Selection**
```
You: /start
Bot: [Shows 5 models]
You: [Click Gemini]
Bot: ✅ Model selected: 😎 Gemini
```

**Test 2: Basic Chat**
```
You: Hello!
Bot: 🤖 😎 Gemini is thinking...
Bot: [Gemini's response]
```

**Test 3: Conversation Memory**
```
You: My name is Alice
Bot: Nice to meet you, Alice!
You: What's my name?
Bot: Your name is Alice
```

**Test 4: Model Switching**
```
You: /switch
Bot: [Shows keyboard]
You: [Select ChatGPT]
Bot: ✅ Selected: 👽 ChatGPT
You: Hello
Bot: [ChatGPT's response]
```

**Test 5: Image Analysis** (Gemini/Claude/GPT/Grok)
```
You: [Send photo with caption "What's in this?"]
Bot: 🖼️ Analyzing image...
Bot: [Detailed description]
```

### Common Test Scenarios

**Test Rate Limiting (Gemini):**
```
Send 11 messages quickly to Gemini
After 10: Should show cooldown message
```

**Test History Persistence:**
```
1. Start bot, send messages
2. Stop bot (Ctrl+C)
3. Start bot again
4. Send /status
Should remember usage count
```

**Test All Models:**
```
For each model:
1. Select model
2. Send "Hi"
3. Send "What did I say?"
4. Verify memory works
```

---

## 🔧 Troubleshooting

### Error: "Module not found: xai_sdk"
```bash
# Grok requires Python 3.10+
python3 --version

# Install Grok SDK
pip install xai-sdk

# If still fails, check Python version
python3.10 -m pip install xai-sdk
```

### Error: "API key not found"
```bash
# Check .env file exists
cat .env

# Verify keys are set
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('BOT_TOKEN'))"

# Should print your token, not None
```

### Error: "Pickle error"
```bash
# Clear old persistence file
rm bot_data*

# Restart bot
python app.py
```

### Error: "Rate limit exceeded"
**For OpenAI/Claude:**
- Wait a few minutes
- Check your API usage dashboard
- Upgrade plan if needed

**For Gemini:**
- Built-in cooldown system
- Wait 2 minutes
- Or use another model

### Error: "Insufficient quota/balance"
**OpenAI:**
```
1. Go to platform.openai.com/account/billing
2. Add payment method
3. Add credits
```

**DeepSeek:**
```
1. Go to platform.deepseek.com
2. Click "Recharge"
3. Minimum $1
```

**Anthropic:**
```
1. Go to console.anthropic.com
2. Add payment method
3. Note: $5 free credit for new users
```

### Bot Not Responding

**Check bot is running:**
```bash
# Should show "Application started"
python app.py
```

**Check bot token:**
```
Message @BotFather on Telegram
Send: /mybots
Select your bot
Check it exists and is active
```

**Check logs:**
```bash
# Run bot and look for errors
python app.py

# Check for:
# - "INFO - Application started" (good)
# - "ERROR" messages (problems)
```

### Model-Specific Issues

**Gemini:**
- Check API key from aistudio.google.com
- Verify free tier limits
- Try after cooldown period

**ChatGPT:**
- Requires paid account ($5+ credit)
- Check billing at platform.openai.com
- Verify API key is valid

**Claude:**
- Free $5 credit for new users
- Check console.anthropic.com
- Verify key starts with "sk-ant-"

**Grok:**
- Requires Python 3.10+
- Check API key from console.x.ai
- Verify xai-sdk installed

**DeepSeek:**
- Requires balance top-up
- Check platform.deepseek.com
- Minimum $1 deposit

---

## 📊 Cost Comparison

| Model | Input Cost | Output Cost | Best For | Free Tier |
|-------|-----------|------------|----------|-----------|
| **Gemini** | Free / $0.10/M | Free / $0.40/M | General use | ✅ Generous |
| **ChatGPT-3.5** | $0.50/M | $1.50/M | Fast & cheap | ❌ |
| **ChatGPT-4o** | $2.50/M | $10/M | Best quality | ❌ |
| **Claude Sonnet** | $3/M | $15/M | Long contexts | ✅ $5 credit |
| **Grok-4** | $5/M | $15/M | Real-time data | ✅ $25 credit |
| **DeepSeek** | $0.14/M | $0.28/M | Ultra-cheap | ❌ |

*M = Million tokens; Prices as of Dec 2024*

---

## 🎯 Best Practices

### 1. **Start with Gemini**
- Free tier
- Good quality
- Easy to test

### 2. **Use DeepSeek for Volume**
- 10-50x cheaper
- Great for coding
- High-volume applications

### 3. **Use ChatGPT for Quality**
- When accuracy matters
- Complex reasoning
- Creative writing

### 4. **Use Claude for Long Context**
- Long documents
- Detailed analysis
- Multi-step instructions

### 5. **Use Grok for Current Info**
- Latest news
- Real-time data
- Web research

### 6. **Rate Limiting**
- Implement for all APIs
- Prevent cost overruns
- Protect against abuse

### 7. **Error Handling**
- Always wrap API calls in try-except
- Provide helpful error messages
- Log errors for debugging

### 8. **History Management**
- Truncate long conversations
- Reset when switching topics
- Clear periodically

---

## 🚀 Next Steps

1. ✅ Test each model independently
2. ✅ Get all API keys
3. ✅ Update .env file
4. ✅ Run bot and test in Telegram
5. ⬜ Deploy to production
6. ⬜ Add custom features
7. ⬜ Monitor usage and costs

---

## 📚 Additional Resources

- **Gemini Docs**: https://ai.google.dev/docs
- **OpenAI Docs**: https://platform.openai.com/docs
- **Claude Docs**: https://docs.anthropic.com/
- **Grok Docs**: https://docs.x.ai/
- **DeepSeek Docs**: https://api-docs.deepseek.com/
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

## ✨ You're All Set!

You now have a complete multi-AI Telegram bot with:
- ✅ 5 different AI models
- ✅ Vision support (4 models)
- ✅ Conversation memory
- ✅ Rate limiting
- ✅ Model switching
- ✅ Comprehensive error handling

Start the bot and enjoy! 🎉
