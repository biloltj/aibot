import os
import io 
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from PIL import Image

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not found in environment variables")

client = genai.Client(api_key=API_KEY)

def create_new_gemini_chat():
    """Initializes a new, stateful chat session with a system instruction."""
    
    # 💥 FIX: Wrap the system_instruction inside the 'config' dictionary 💥
    chat_config = {
        'system_instruction': (
            "You are a friendly, witty, and highly capable Gemini Bot assistant. "
            "You can remember past messages and analyze images. Keep answers concise."
        )
    }
    
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=chat_config 
    )
    return chat

def chat_gemini(chat_session, txt: str) -> str:
    """Sends a message to an existing chat session and gets the response."""
    if chat_session is None:
        return "Error: Gemini chat session is not initialized."
    
    try:
        response = chat_session.send_message(txt)
        # We implicitly enable thinking by using a capable model and good prompt.
        return response.text
    except APIError as e:
        return f"An API error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# --- New Vision Function ---

def analyze_image_gemini(image_data: bytes, prompt: str) -> str:
    """
    Analyzes an image and a prompt using the Gemini API.
    
    Args:
        image_data (bytes): The raw image file data from Telegram.
        prompt (str): The user's question about the image (caption).

    Returns:
        str: The Gemini model's descriptive response.
    """
    try:
        # Load the image from raw bytes using Pillow
        img = Image.open(io.BytesIO(image_data))
        
        # Multimodal request: Pass both the image object and the text prompt
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, prompt]
        )
        return response.text
        
    except APIError as e:
        return f"An API error occurred during image analysis: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"