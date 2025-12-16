import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
API_KEY = "GROK_API_KEY"

if not API_KEY:
    raise ValueError(
        "❌ XAI_API_KEY not found!\n"
        "Get your API key from: https://console.x.ai/\n"
        "Add it to your .env file:\n"
        "XAI_API_KEY=your_key_here"
    )


try:
    import xai_sdk
    client = xai_sdk.Client(api_key=API_KEY)
except ImportError:
    raise ImportError(
        "❌ xai_sdk not installed!\n"
        "Install it with: pip install xai-sdk\n"
        "Note: Requires Python 3.10+"
    )

# Model configuration
DEFAULT_MODEL = "grok-4"  # Latest model with reasoning and vision
SYSTEM_PROMPT = """You are Grok, a witty and intelligent AI assistant created by xAI. 
You provide helpful, accurate, and sometimes humorous responses. 
You can search the web and X (Twitter) for real-time information when needed."""



def create_grok_chat(
    model: str = DEFAULT_MODEL,
    system_instruction: str = SYSTEM_PROMPT
):
    
    try:
        # Import chat utilities from SDK
        from xai_sdk.chat import system
        
        # Create chat session with system instruction
        # This is similar to Gemini's chat sessions
        chat = client.chat.create(
            model=model,
            messages=[system(system_instruction)]
        )
        return chat
        
    except Exception as e:
        print(f"Error creating Grok chat: {e}")
        return None


def chat_grok(
    chat_session,
    user_message: str,
    max_tokens: int = 1024,
    temperature: float = 1.0
) -> str:
  
    if chat_session is None:
        return "❌ Error: Grok chat session not initialized."
    
    try:
        # Import message utilities
        from xai_sdk.chat import user
        
        # Append user's message to chat
        chat_session.append(user(user_message))
        
        # Generate response
        # sample() is xAI's term for "generate completion"
        response = chat_session.sample()
        
        # Append response to session for context
        chat_session.append(response)
        
        # Return the text content
        return response.content
        
    except Exception as e:
        return f"❌ Error communicating with Grok: {str(e)}"




def analyze_image_grok(
    image_data: bytes,
    prompt: str,
    model: str = DEFAULT_MODEL
) -> str:
  
    try:
        import base64
        from xai_sdk.chat import user, image
        
        
        chat = client.chat.create(model=model)
        
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        image_url = f"data:image/jpeg;base64,{base64_image}"
        
        # Append message with image and text
        chat.append(
            user(
                prompt,
                image(image_url)
            )
        )
        
        # Get response
        response = chat.sample()
        
        return response.content
        
    except Exception as e:
        return f"❌ Error analyzing image with Grok: {str(e)}"


def chat_grok_openai_style(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024
) -> tuple[str, List[Dict[str, str]]]:
 
    try:
        from openai import OpenAI
        
        xai_client = OpenAI(
            api_key=API_KEY,
            base_url="https://api.x.ai/v1"
        )
        
        # Initialize history if needed
        if conversation_history is None:
            conversation_history = []
        
        # Add user message
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Make API call using OpenAI format
        response = xai_client.chat.completions.create(
            model=model,
            messages=conversation_history,
            max_tokens=max_tokens
        )
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        # Add response to history
        conversation_history.append({
            "role": "assistant",
            "content": response_text
        })
        
        return response_text, conversation_history
        
    except Exception as e:
        error_msg = f"❌ Error with Grok (OpenAI-compatible): {str(e)}"
        return error_msg, conversation_history

def test_grok_connection() -> bool:
  
    try:
        chat = create_grok_chat()
        if chat is None:
            return False
        
        response = chat_grok(chat, "Say OK")
        return "OK" in response.upper()
        
    except Exception as e:
        print(f"Grok connection test failed: {e}")
        return False


if __name__ == "__main__":
    """
    Test the Grok integration independently.
    Run: python grok.py
    """
    
    print("🧪 Testing Grok integration...\n")
    
    # Test 1: Connection
    print("1️⃣ Testing connection...")
    if test_grok_connection():
        print("✅ Connection successful!\n")
    else:
        print("❌ Connection failed!")
        print("Make sure you have:")
        print("1. Installed xai_sdk: pip install xai-sdk")
        print("2. Set XAI_API_KEY in .env file")
        print("3. Python 3.10+ installed\n")
        exit(1)
    
    # Test 2: Native SDK chat
    print("2️⃣ Testing native SDK chat...")
    chat = create_grok_chat()
    if chat:
        response = chat_grok(chat, "What is 2+2? Answer briefly.")
        print(f"Response: {response}\n")
        
        # Test conversation memory
        print("3️⃣ Testing conversation memory...")
        response = chat_grok(chat, "What was my previous question?")
        print(f"Response: {response}\n")
    else:
        print("❌ Failed to create chat session\n")
    
    # Test 4: OpenAI-compatible API
    print("4️⃣ Testing OpenAI-compatible API...")
    try:
        response, history = chat_grok_openai_style("Hello!")
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Note: OpenAI-compatible API requires openai package")
        print(f"Install with: pip install openai\n")
    
    print("✅ All tests complete!")
    print("\n📚 Integration Guide:")
    print("1. Install: pip install xai-sdk python-dotenv")
    print("2. Get API key: https://console.x.ai/")
    print("3. Add to .env: XAI_API_KEY=your_key_here")
    print("4. Import: from grok import create_grok_chat, chat_grok")
    print("5. Use: chat = create_grok_chat(); response = chat_grok(chat, 'Hello!')")