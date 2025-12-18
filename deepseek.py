import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI, APIError


load_dotenv()
API_KEY = "sk-a69e3a6f11fb43bfb476228183b8795c"

if not API_KEY:
    raise ValueError(
        "❌ DEEPSEEK_API_KEY not found!\n"
        "Get your API key from: https://platform.deepseek.com/\n"
        "Add it to your .env file:\n"
        "DEEPSEEK_API_KEY=sk-your_key_here"
    )

# Initialize DeepSeek client using OpenAI SDK
# DeepSeek API is compatible with OpenAI's format
# We just change the base_url to point to DeepSeek's servers
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"  # This is the key difference!
)

# Model configuration
DEFAULT_MODEL = "deepseek-chat"  # Fast, general purpose
REASONING_MODEL = "deepseek-reasoner"  # Advanced reasoning with CoT

SYSTEM_PROMPT = """You are a helpful, intelligent AI assistant.
You provide clear, accurate, and well-reasoned responses.
You excel at coding, mathematics, and logical reasoning."""


def create_conversation_history() -> List[Dict[str, str]]:
    
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
    
    # Keep system message if present
    system_msg = None
    messages = history
    
    if history and history[0]["role"] == "system":
        system_msg = history[0]
        messages = history[1:]
    
    # Keep most recent messages
    truncated = messages[-max_messages:]
    
    # Re-add system message
    if system_msg:
        truncated = [system_msg] + truncated
    
    return truncated


def chat_deepseek(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    temperature: float = 1.0,
    enable_reasoning: bool = False
) -> tuple[str, List[Dict[str, str]]]:
   
    if enable_reasoning:
        model = REASONING_MODEL
    
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
        
        # For reasoning model, also show thinking process if available
        if model == REASONING_MODEL:
           
            if "<think>" in response_text:
                parts = response_text.split("</think>")
                if len(parts) == 2:
                    thinking = parts[0].replace("<think>", "").strip()
                    answer = parts[1].strip()
                    response_text = f"💭 Thinking:\n{thinking}\n\n📝 Answer:\n{answer}"
   
        add_message(conversation_history, "assistant", response_text)
        
        return response_text, conversation_history
        
    except APIError as e:
        error_msg = str(e)
        
        if "insufficient" in error_msg.lower():
            error_response = "⚠️ Insufficient balance. Top up at platform.deepseek.com"
        elif "rate" in error_msg.lower():
            error_response = "⚠️ Rate limit exceeded. Please slow down."
        elif "context_length" in error_msg.lower():
            error_response = "⚠️ Message too long. Try /reset to clear history."
        else:
            error_response = f"❌ DeepSeek API error: {error_msg}"
        
        return error_response, conversation_history
        
    except Exception as e:
        error_response = f"❌ Unexpected error: {str(e)}"
        return error_response, conversation_history

def chat_deepseek_simple(
    user_message: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 512,
    enable_reasoning: bool = False
) -> str:
   
    
    if enable_reasoning:
        model = REASONING_MODEL
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=max_tokens
        )
        
        response_text = response.choices[0].message.content
        
        # Format reasoning output if present
        if enable_reasoning and "<think>" in response_text:
            parts = response_text.split("</think>")
            if len(parts) == 2:
                thinking = parts[0].replace("<think>", "").strip()
                answer = parts[1].strip()
                response_text = f"💭 Thinking:\n{thinking}\n\n📝 Answer:\n{answer}"
        
        return response_text
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


def test_deepseek_connection() -> bool:
 
    try:
        response = chat_deepseek_simple("Say OK", max_tokens=10)
        return "OK" in response.upper()
    except Exception as e:
        print(f"DeepSeek connection test failed: {e}")
        return False


def get_model_info() -> Dict[str, str]:
   
    return {
        "deepseek-chat": {
            "name": "DeepSeek-V3.2",
            "type": "Fast general-purpose model",
            "context": "64k tokens",
            "use_for": "General chat, coding, quick answers",
            "cost": "Very low (cache hits: $0.014/M tokens)"
        },
        "deepseek-reasoner": {
            "name": "DeepSeek-R1",
            "type": "Advanced reasoning model",
            "context": "64k tokens",
            "use_for": "Complex problems, math, logic, planning",
            "cost": "Low (shows chain-of-thought)",
            "note": "Uses more tokens due to thinking process"
        }
    }




if __name__ == "__main__":
  
    
    print("🧪 Testing DeepSeek integration...\n")
    
    # Test 1: Connection
    print("1️⃣ Testing connection...")
    if test_deepseek_connection():
        print("✅ Connection successful!\n")
    else:
        print("❌ Connection failed!")
        print("Check your DEEPSEEK_API_KEY in .env file\n")
        exit(1)
    
    # Test 2: Simple chat (deepseek-chat)
    print("2️⃣ Testing deepseek-chat...")
    response = chat_deepseek_simple("What is 2+2? Answer in one sentence.")
    print(f"Response: {response}\n")
    
    # Test 3: Reasoning mode (deepseek-reasoner)
    print("3️⃣ Testing deepseek-reasoner (with thinking)...")
    response = chat_deepseek_simple(
        "If I have 5 apples and give away 2, how many do I have?",
        enable_reasoning=True,
        max_tokens=500
    )
    print(f"Response:\n{response}\n")
    
    # Test 4: Conversation with memory
    print("4️⃣ Testing conversation memory...")
    response, history = chat_deepseek("My favorite color is blue")
    print(f"Response: {response}")
    
    response, history = chat_deepseek(
        "What's my favorite color?", 
        conversation_history=history
    )
    print(f"Response: {response}\n")
    
    # Test 5: Model information
    print("5️⃣ Available models:")
    models = get_model_info()
    for model_id, info in models.items():
        print(f"\n{model_id}:")
        print(f"  Name: {info['name']}")
        print(f"  Type: {info['type']}")
        print(f"  Context: {info['context']}")
        print(f"  Best for: {info['use_for']}")
        print(f"  Cost: {info['cost']}")
        if 'note' in info:
            print(f"  Note: {info['note']}")
    
    print("\n✅ All tests complete!")
    print("\n📚 Integration Guide:")
    print("1. Install: pip install openai python-dotenv")
    print("2. Get API key: https://platform.deepseek.com/")
    print("3. Add to .env: DEEPSEEK_API_KEY=sk-your_key_here")
    print("4. Import: from deepseek import chat_deepseek")
    print("5. Use: response, history = chat_deepseek('Hello!')")
    print("\n💡 Pro Tips:")
    print("- Use deepseek-chat for fast general answers")
    print("- Use deepseek-reasoner for complex problems")
    print("- DeepSeek is 10-50x cheaper than GPT-4!")
    print("- Context caching saves even more money")