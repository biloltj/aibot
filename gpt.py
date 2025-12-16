import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI, APIError

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "❌ OPENAI_API_KEY not found!\n"
        "Get your API key from: https://platform.openai.com/api-keys\n"
        "Add it to your .env file:\n"
        "OPENAI_API_KEY=sk-your_key_here"
    )

client = OpenAI(api_key=API_KEY)

DEFAULT_MODEL = "gpt-4o"  
VISION_MODEL = "gpt-4o"   
CHEAP_MODEL = "gpt-3.5-turbo" 

SYSTEM_PROMPT = """You are a helpful, witty, and knowledgeable AI assistant.
You provide clear, accurate, and friendly responses to user questions.
You can engage in natural conversations and remember context."""



def create_conversation_history() -> List[Dict[str, str]]:
    """
    Creates a new empty conversation history.
    
    Returns:
        Empty list for storing messages
    
    OpenAI Message Format:
    [
        {"role": "system", "content": "You are..."},  # Optional
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    Roles explained:
    - system: Sets AI behavior (only at start)
    - user: Human messages
    - assistant: AI responses
    
    Why we manage history manually:
    - OpenAI API is stateless
    - Must send full conversation each time
    - Gives us control over context length
    - Can implement features like summary/truncation
    """
    return []


def add_message(
    history: List[Dict[str, str]], 
    role: str, 
    content: str
) -> List[Dict[str, str]]:

    if role not in ["system", "user", "assistant"]:
        raise ValueError(f"Invalid role: {role}")
    
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
    
    system_msg = None
    messages = history
    
    if history and history[0]["role"] == "system":
        system_msg = history[0]
        messages = history[1:]
    
    truncated = messages[-max_messages:]
    
    # Re-add system message
    if system_msg:
        truncated = [system_msg] + truncated
    
    return truncated

def chat_gpt(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    temperature: float = 1.0
) -> tuple[str, List[Dict[str, str]]]:
    
    if conversation_history is None:
        conversation_history = create_conversation_history()
        add_message(conversation_history, "system", system_prompt)
    
    add_message(conversation_history, "user", user_message)
    
    conversation_history = truncate_history(conversation_history)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversation_history,
            max_tokens=max_tokens,
            temperature=temperature
        )
   
        response_text = response.choices[0].message.content
        
        add_message(conversation_history, "assistant", response_text)
        
        return response_text, conversation_history
        
    except APIError as e:
        error_msg = str(e)
        
        if "insufficient_quota" in error_msg.lower():
            error_response = "⚠️ OpenAI API quota exceeded. Check your billing at platform.openai.com"
        elif "rate_limit" in error_msg.lower():
            error_response = "⚠️ Rate limit exceeded. Please slow down."
        elif "context_length" in error_msg.lower():
            error_response = "⚠️ Message too long. Try a shorter conversation or use /reset"
        elif "invalid_api_key" in error_msg.lower():
            error_response = "❌ Invalid API key. Check your OPENAI_API_KEY"
        else:
            error_response = f"❌ OpenAI API error: {error_msg}"
        
        return error_response, conversation_history
        
    except Exception as e:
        error_response = f"❌ Unexpected error: {str(e)}"
        return error_response, conversation_history

def chat_gpt_simple(
    user_message: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 512
) -> str:

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

def analyze_image_gpt(
    image_data: bytes,
    prompt: str,
    model: str = VISION_MODEL,
    max_tokens: int = 1024
) -> str:

    
    import base64
    
    try:
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
       
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
        
    except APIError as e:
        error_msg = str(e)
        if "unsupported" in error_msg.lower():
            return "❌ Model doesn't support vision. Use gpt-4o or gpt-4-turbo."
        elif "too large" in error_msg.lower():
            return "❌ Image too large. Maximum size is 20MB."
        else:
            return f"❌ API error: {error_msg}"
            
    except Exception as e:
        return f"❌ Error processing image: {str(e)}"

def test_gpt_connection() -> bool:

    try:
        response = chat_gpt_simple("Say OK", max_tokens=10)
        return "OK" in response.upper()
    except Exception as e:
        print(f"ChatGPT connection test failed: {e}")
        return False


def estimate_tokens(text: str) -> int:
 
    return len(text) // 4

if __name__ == "__main__":

    print("🧪 Testing ChatGPT integration...\n")
    
    # Test 1: Connection
    print("1️⃣ Testing connection...")
    if test_gpt_connection():
        print("✅ Connection successful!\n")
    else:
        print("❌ Connection failed!")
        print("Check your OPENAI_API_KEY in .env file\n")
        exit(1)
    
    # Test 2: Simple chat (no history)
    print("2️⃣ Testing simple chat...")
    response = chat_gpt_simple("What is 2+2? Answer in one sentence.")
    print(f"Response: {response}\n")
    
    # Test 3: Conversation with memory
    print("3️⃣ Testing conversation memory...")
    response, history = chat_gpt("My name is Alice")
    print(f"Response: {response}")
    
    response, history = chat_gpt("What's my name?", conversation_history=history)
    print(f"Response: {response}\n")
    
    # Test 4: Token estimation
    print("4️⃣ Testing token estimation...")
    sample_text = "This is a sample text for token estimation."
    tokens = estimate_tokens(sample_text)
    print(f"Text: '{sample_text}'")
    print(f"Estimated tokens: {tokens}\n")
    
    # Test 5: Different models
    print("5️⃣ Testing different models...")
    response = chat_gpt_simple(
        "Say 'cheap' if you're GPT-3.5", 
        model="gpt-3.5-turbo",
        max_tokens=20
    )
    print(f"GPT-3.5 response: {response}\n")
    
    print("✅ All tests complete!")
    print("\n📚 Integration Guide:")
    print("1. Install: pip install openai python-dotenv")
    print("2. Get API key: https://platform.openai.com/api-keys")
    print("3. Add to .env: OPENAI_API_KEY=sk-your_key_here")
    print("4. Import: from gpt import chat_gpt")
    print("5. Use: response, history = chat_gpt('Hello!')")