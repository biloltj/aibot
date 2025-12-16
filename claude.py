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

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
SYSTEM_PROMPT = """You are a helpful, witty, and knowledgeable AI assistant. 
You provide clear, concise, and accurate answers. 
You can engage in natural conversations and remember context from earlier in the conversation.
You're friendly and professional."""

def create_conversation_history() -> List[Dict[str, str]]:
  
    return []


def add_message(
    history: List[Dict[str, str]], 
    role: str, 
    content: str
) -> List[Dict[str, str]]:
  
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
   
    if len(history) <= max_messages:
        return history
    
    truncated = history[-max_messages:]
    
    if truncated and truncated[0]["role"] == "assistant":
        truncated = truncated[1:]
    
    return truncated

def chat_claude(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024
) -> tuple[str, List[Dict[str, str]]]:
   
    # Initialize history if this is a new conversation
    if conversation_history is None:
        conversation_history = create_conversation_history()
    
    # Add user's message to history
    add_message(conversation_history, "user", user_message)
    
    # Truncate history to stay within limits
    conversation_history = truncate_history(conversation_history)
    
    try:
     
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,  # Sets Claude's personality
            messages=conversation_history  # Full conversation context
        )
        
       
        response_text = response.content[0].text
        
        # Add Claude's response to history
        add_message(conversation_history, "assistant", response_text)
        
       
        return response_text, conversation_history
        
    except APIError as e:
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
        
        return error_response, conversation_history
        
    except Exception as e:
        error_response = f"❌ Unexpected error: {str(e)}"
        return error_response, conversation_history

def analyze_image_claude(
    image_data: bytes,
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024
) -> str:
    
    
    import base64
    from PIL import Image
    import io
    
    try:
        img = Image.open(io.BytesIO(image_data))
        image_format = img.format.lower()
        
        mime_types = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif"
        }
        
        media_type = mime_types.get(image_format, "image/jpeg")
        
      
        base64_image = base64.b64encode(image_data).decode('utf-8')
     
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


def test_claude_connection() -> bool:
    
    try:
        response, _ = chat_claude("Hello, respond with just 'OK'")
        return "OK" in response.upper()
    except Exception as e:
        print(f"Claude connection test failed: {e}")
        return False


def estimate_tokens(text: str) -> int:
     return len(text) // 4


if __name__ == "__main__":
   
    
    print("🧪 Testing Claude integration...\n")
    
    print("1️⃣ Testing connection...")
    if test_claude_connection():
        print("✅ Connection successful!\n")
    else:
        print("❌ Connection failed!\n")
        exit(1)
    
    print("2️⃣ Testing simple chat...")
    response, history = chat_claude("What is 2+2? Answer in one sentence.")
    print(f"Response: {response}\n")
    
    print("3️⃣ Testing conversation memory...")
    response, history = chat_claude(
        "What was my previous question?",
        conversation_history=history
    )
    print(f"Response: {response}\n")
    
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