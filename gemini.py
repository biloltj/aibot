import os
import io
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from PIL import Image



load_dotenv()
API_KEY = os.getenv("GEMENI_API_KEY")

if not API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY not found!\n"
        "Add it to your .env file:\n"
        "GEMINI_API_KEY=your_key_here"
    )


client = genai.Client(api_key=API_KEY)



def create_new_gemini_chat():
   
    
    chat_config = {
        'system_instruction': (
            "You are a helpful, witty, and knowledgeable AI assistant. "
            "You can remember our conversation history and provide contextual responses. "
            "Keep your answers clear, concise, and friendly. "
            "When analyzing images, be descriptive and specific about what you observe."
        )
    }
    
    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=chat_config
        )
        return chat
    except APIError as e:
        print(f"Error creating Gemini chat: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def chat_gemini(chat_session, txt: str) -> str:
  
    
    if chat_session is None:
        return "❌ Error: Gemini chat session not initialized. Use /reset to restart."
    
    try:
        response = chat_session.send_message(txt)
        
       
        return response.text
        
    except APIError as e:
        error_msg = str(e)
        if "quota" in error_msg.lower():
            return "⚠️ Gemini API quota exceeded. Please try again later."
        elif "rate" in error_msg.lower():
            return "⚠️ Too many requests. Please slow down."
        else:
            return f"❌ Gemini API error: {error_msg}"
            
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

def analyze_image_gemini(image_data: bytes, prompt: str) -> str:
    try:
       
        img = Image.open(io.BytesIO(image_data))
        
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',  
            contents=[img, prompt]  
        )
        
        return response.text
        
    except APIError as e:
        error_msg = str(e)
        if "unsupported" in error_msg.lower():
            return "❌ Unsupported image format. Try JPEG or PNG."
        elif "too large" in error_msg.lower():
            return "❌ Image too large. Please send a smaller image."
        else:
            return f"❌ API error during image analysis: {error_msg}"
            
    except Exception as e:
        return f"❌ Error processing image: {str(e)}"

def test_gemini_connection() -> bool:
   
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Hello"
        )
        return response.text is not None
    except Exception as e:
        print(f"Gemini connection test failed: {e}")
        return False


if __name__ == "__main__":
   
    
    print("🧪 Testing Gemini integration...")
    
    print("\n1️⃣ Testing connection...")
    if test_gemini_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        exit(1)
    
    print("\n2️⃣ Testing chat session...")
    chat = create_new_gemini_chat()
    if chat:
        print("✅ Chat session created!")
        
        response = chat_gemini(chat, "What is 2+2? Answer in one sentence.")
        print(f"Response: {response}")
    else:
        print("❌ Failed to create chat session!")
    
    print("\n3️⃣ Testing vision...")
    print("Skipping vision test (requires image file)")
    
    print("\n✅ All tests complete!")