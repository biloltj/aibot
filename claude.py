import os
from typing import List, Dict
from dotenv import load_dotenv
from anthropic import Anthropic, APIError

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    raise ValueError(
        "❌ ANTHROPIC_API_KEY not found!\n"
        "Get your API key from: https://console.anthropic.com/\n"
        "Add it to your .env file:\n"
        "ANTHROPIC_API_KEY=sk-ant-your_key_here"
    )

client = Anthropic(api_key=API_KEY)
# Model selection
# claude-sonnet-4-5-20250929: Balanced speed/quality (recommended)
# claude-opus-4-1: Most capable, slower, more expensive
# claude-haiku-4-5-20251001: Fastest, most economical
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
# System prompt - Sets Claude's behavior and personality
SYSTEM_PROMPT = """You are a helpful, witty, and knowledgeable AI assistant. 
You provide clear, concise, and accurate answers. 
You can engage in natural conversations and remember context from earlier in the conversation.
You're friendly and professional."""

def create_conversation_history() -> List[Dict[str, str]]:
    """
    Creates a new empty conversation history.
    
    Returns:
        Empty list to store message dictionaries
    
    Why we need this:
    - Claude's API doesn't maintain state between requests
    - We must send full conversation history with each API call
    - This ensures Claude remembers previous messages
    
    Message format:
    [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"},
        {"role": "user", "content": "What's the weather?"}
    ]
    
    Rules:
    - Must alternate between "user" and "assistant"
    - First message must be from "user"
    - Last message should be from "user" (the current question)
    """
    return []


def add_message(
    history: List[Dict[str, str]], 
    role: str, 
    content: str
) -> List[Dict[str, str]]:
    """
    Adds a message to the conversation history.
    
    Args:
        history: Current conversation history
        role: Either "user" or "assistant"
        content: Message text
    
    Returns:
        Updated history with new message
    
    Why this function:
    - Ensures consistent message format
    - Validates role values
    - Makes history management cleaner
    """
    if role not in ["user", "assistant"]:
        raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
    
    history.append({
        "role": role,
        "content": content
    })
    return history


def truncate_history(
    history: List[Dict[str, str]], 
    max_messages: int = 20
) -> List[Dict[str, str]]:
    """
    Truncates conversation history to prevent token limit issues.
    
    Args:
        history: Full conversation history
        max_messages: Maximum number of messages to keep
    
    Returns:
        Truncated history (most recent messages)
    
    Why truncate:
    - Claude has context limits (200k tokens for Sonnet)
    - Long histories = higher costs
    - Recent messages are usually more relevant
    - Prevents "context window exceeded" errors
    
    Strategy:
    - Keep the most recent N messages
    - Always maintain user-assistant alternation
    - If odd number after truncation, remove one more
    """
    if len(history) <= max_messages:
        return history
    
    # Keep most recent messages
    truncated = history[-max_messages:]
    
    # Ensure we start with a user message
    if truncated and truncated[0]["role"] == "assistant":
        truncated = truncated[1:]
    
    return truncated


# ============================================================================
# MAIN CHAT FUNCTION
# ============================================================================

def chat_claude(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024
) -> tuple[str, List[Dict[str, str]]]:
    """
    Sends a message to Claude and returns the response with updated history.
    
    Args:
        user_message: The user's message text
        conversation_history: Previous messages (or None for new conversation)
        system_prompt: Instructions for Claude's behavior
        model: Which Claude model to use
        max_tokens: Maximum length of response (not input!)
    
    Returns:
        Tuple of (response_text, updated_history)
    
    How it works:
    1. Initialize history if needed
    2. Add user's message to history
    3. Truncate if history is too long
    4. Send request to Claude API
    5. Extract response text
    6. Add response to history
    7. Return both response and updated history
    
    Key API Parameters Explained:
    
    - model: Which Claude version to use
      * Sonnet: Best balance of speed/quality
      * Opus: Most capable, but slower/pricier
      * Haiku: Fastest and cheapest
    
    - max_tokens: Max OUTPUT tokens (not input!)
      * Controls response length
      * 1 token ≈ 4 characters
      * Higher = longer responses but more cost
      * Common values: 1024 (short), 4096 (long)
    
    - system: Shapes Claude's behavior
      * Sets personality, tone, expertise
      * Applied to entire conversation
      * Can include instructions, constraints
    
    - messages: The conversation history
      * Must alternate user/assistant
      * Claude reads all previous context
      * Affects response quality and relevance
    
    - temperature: Randomness (not used here, defaults to 1.0)
      * 0.0 = deterministic, focused
      * 1.0 = creative, varied
      * Higher = more random
    """
    
    # Initialize history if this is a new conversation
    if conversation_history is None:
        conversation_history = create_conversation_history()
    
    # Add user's message to history
    add_message(conversation_history, "user", user_message)
    
    # Truncate history to stay within limits
    conversation_history = truncate_history(conversation_history)
    
    try:
        # Make API call to Claude
        # This is the main interaction with Anthropic's API
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,  # Sets Claude's personality
            messages=conversation_history  # Full conversation context
        )
        
        # Extract the text content from response
        # Response structure: response.content[0].text
        # Claude always returns a list of content blocks
        response_text = response.content[0].text
        
        # Add Claude's response to history
        add_message(conversation_history, "assistant", response_text)
        
        # Return both the response and updated history
        # The caller needs the history for the next message
        return response_text, conversation_history
        
    except APIError as e:
        # Handle API-specific errors
        error_msg = str(e)
        
        if "overloaded" in error_msg.lower():
            error_response = "⚠️ Claude is experiencing high demand. Please try again in a moment."
        elif "rate" in error_msg.lower():
            error_response = "⚠️ Too many requests. Please slow down."
        elif "quota" in error_msg.lower():
            error_response = "⚠️ API quota exceeded. Check your usage at console.anthropic.com"
        elif "authentication" in error_msg.lower():
            error_response = "❌ Authentication failed. Check your API key."
        else:
            error_response = f"❌ Claude API error: {error_msg}"
        
        # Don't add error to history - it's not part of conversation
        return error_response, conversation_history
        
    except Exception as e:
        # Catch-all for unexpected errors
        error_response = f"❌ Unexpected error: {str(e)}"
        return error_response, conversation_history


# ============================================================================
# VISION FUNCTION (IMAGE ANALYSIS)
# ============================================================================

def analyze_image_claude(
    image_data: bytes,
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024
) -> str:
    """
    Analyzes an image using Claude's vision capabilities.
    
    Args:
        image_data: Raw image bytes
        prompt: Question about the image
        model: Claude model (must support vision)
        max_tokens: Max response length
    
    Returns:
        Claude's analysis of the image
    
    How Claude Vision Works:
    1. Image is base64 encoded automatically
    2. Sent as part of message content (multimodal)
    3. Claude analyzes visual content
    4. Returns text description/analysis
    
    Supported formats:
    - JPEG, PNG, WebP, GIF
    - Max size: 5MB for Sonnet, 10MB for Opus
    
    Vision-capable models:
    - Claude Sonnet 3.5+
    - Claude Opus 3+
    - NOT Haiku (no vision support)
    
    Content structure for vision:
    [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": "<base64_encoded_image>"
            }
        },
        {
            "type": "text",
            "text": "What's in this image?"
        }
    ]
    """
    
    import base64
    from PIL import Image
    import io
    
    try:
        # Validate and get image format
        img = Image.open(io.BytesIO(image_data))
        image_format = img.format.lower()
        
        # Map PIL formats to MIME types
        mime_types = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif"
        }
        
        media_type = mime_types.get(image_format, "image/jpeg")
        
        # Encode image to base64
        # Claude requires base64 encoding for images
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create multimodal message
        # Combines image and text in single message
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        
        return response.content[0].text
        
    except APIError as e:
        error_msg = str(e)
        if "unsupported" in error_msg.lower():
            return "❌ Unsupported image format. Use JPEG, PNG, WebP, or GIF."
        elif "too large" in error_msg.lower():
            return "❌ Image too large. Maximum size is 5MB."
        else:
            return f"❌ API error: {error_msg}"
            
    except Exception as e:
        return f"❌ Error processing image: {str(e)}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def test_claude_connection() -> bool:
    """
    Tests Claude API connection and authentication.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        response, _ = chat_claude("Hello, respond with just 'OK'")
        return "OK" in response.upper()
    except Exception as e:
        print(f"Claude connection test failed: {e}")
        return False


def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count.
    
    Args:
        text: Input text
    
    Returns:
        Approximate token count
    
    Note: This is a rough estimate. For exact counts, use:
    client.count_tokens(text)
    
    Estimation rule:
    - 1 token ≈ 4 characters
    - 1 token ≈ 0.75 words
    """
    return len(text) // 4


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test the Claude integration independently.
    Run: python claude_api.py
    """
    
    print("🧪 Testing Claude integration...\n")
    
    # Test 1: Connection
    print("1️⃣ Testing connection...")
    if test_claude_connection():
        print("✅ Connection successful!\n")
    else:
        print("❌ Connection failed!\n")
        exit(1)
    
    # Test 2: Simple chat
    print("2️⃣ Testing simple chat...")
    response, history = chat_claude("What is 2+2? Answer in one sentence.")
    print(f"Response: {response}\n")
    
    # Test 3: Follow-up message (conversation memory)
    print("3️⃣ Testing conversation memory...")
    response, history = chat_claude(
        "What was my previous question?",
        conversation_history=history
    )
    print(f"Response: {response}\n")
    
    # Test 4: Token estimation
    print("4️⃣ Testing token estimation...")
    sample_text = "This is a sample text for token estimation."
    tokens = estimate_tokens(sample_text)
    print(f"Text: '{sample_text}'")
    print(f"Estimated tokens: {tokens}\n")
    
    print("✅ All tests complete!")
    print("\n📚 Integration Guide:")
    print("1. Install: pip install anthropic python-dotenv Pillow")
    print("2. Get API key: https://console.anthropic.com/")
    print("3. Add to .env: ANTHROPIC_API_KEY=your_key_here")
    print("4. Import: from claude_api import chat_claude")
    print("5. Use: response, history = chat_claude('Hello!')")