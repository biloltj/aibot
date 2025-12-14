"""
Gemini API Integration Module

This module handles all interactions with Google's Gemini AI API.

Key concepts:
1. Client initialization - Creates connection to Gemini API
2. Chat sessions - Stateful conversations with memory
3. Vision capabilities - Image analysis and understanding
"""

import os
import io
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from PIL import Image

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY not found!\n"
        "Add it to your .env file:\n"
        "GEMINI_API_KEY=your_key_here"
    )

# Initialize Gemini client
# This client is reused for all API calls (efficient connection pooling)
client = genai.Client(api_key=API_KEY)

# ============================================================================
# CHAT SESSION FUNCTIONS
# ============================================================================

def create_new_gemini_chat():
    """
    Creates a new stateful Gemini chat session.
    
    What is a chat session?
    - Maintains conversation history automatically
    - Remembers context from previous messages
    - More natural, coherent conversations
    
    System instruction:
    - Sets the AI's personality and behavior
    - Applied to every message in the session
    - Helps maintain consistent tone
    
    Model selection:
    - gemini-2.5-flash: Fast, cost-effective, great quality
    - Alternatives: gemini-2.5-pro (more powerful but slower/costlier)
    
    Returns:
        Chat session object (contains thread locks - not picklable!)
    """
    
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
    """
    Sends a message to an existing Gemini chat session.
    
    Args:
        chat_session: Active chat session from create_new_gemini_chat()
        txt: User's message text
    
    Returns:
        String response from Gemini
    
    How it works:
    1. Validates chat session exists
    2. Sends message through the session (maintains history)
    3. Extracts text from response
    4. Handles errors gracefully
    
    Why we use chat sessions instead of single messages:
    - Maintains conversation context
    - More natural follow-up questions
    - Gemini can refer to previous messages
    - Better user experience
    """
    
    if chat_session is None:
        return "❌ Error: Gemini chat session not initialized. Use /reset to restart."
    
    try:
        # Send message (automatically includes conversation history)
        response = chat_session.send_message(txt)
        
        # Extract text from response
        # response.text handles multiple content parts automatically
        return response.text
        
    except APIError as e:
        # API-specific errors (rate limits, auth issues, etc.)
        error_msg = str(e)
        if "quota" in error_msg.lower():
            return "⚠️ Gemini API quota exceeded. Please try again later."
        elif "rate" in error_msg.lower():
            return "⚠️ Too many requests. Please slow down."
        else:
            return f"❌ Gemini API error: {error_msg}"
            
    except Exception as e:
        # Catch-all for unexpected errors
        return f"❌ Unexpected error: {str(e)}"


# ============================================================================
# VISION FUNCTIONS (IMAGE ANALYSIS)
# ============================================================================

def analyze_image_gemini(image_data: bytes, prompt: str) -> str:
    """
    Analyzes an image using Gemini's vision capabilities.
    
    Args:
        image_data: Raw image bytes (from Telegram download)
        prompt: User's question about the image
    
    Returns:
        Gemini's description/analysis of the image
    
    How Gemini Vision works:
    1. Gemini can understand image content (multimodal AI)
    2. Combines visual understanding with language generation
    3. Can answer questions, describe scenes, read text, identify objects
    
    Why we use Pillow (PIL):
    - Validates image format before sending to API
    - Ensures image is properly formatted
    - Handles various image formats (JPEG, PNG, WebP, etc.)
    
    Multimodal request:
    - Pass both image and text together
    - Gemini processes them as a single input
    - More accurate than separate processing
    """
    
    try:
        # Load and validate image
        # io.BytesIO wraps bytes in a file-like object for PIL
        img = Image.open(io.BytesIO(image_data))
        
        # Optional: Log image info for debugging
        # print(f"Image format: {img.format}, Size: {img.size}, Mode: {img.mode}")
        
        # Make API call with multimodal content
        # Note: This uses generate_content, not a chat session
        # Each image analysis is independent (no conversation history)
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # Same model, but non-chat mode
            contents=[img, prompt]  # Pass image object and text together
        )
        
        return response.text
        
    except APIError as e:
        # API-specific errors
        error_msg = str(e)
        if "unsupported" in error_msg.lower():
            return "❌ Unsupported image format. Try JPEG or PNG."
        elif "too large" in error_msg.lower():
            return "❌ Image too large. Please send a smaller image."
        else:
            return f"❌ API error during image analysis: {error_msg}"
            
    except Exception as e:
        # Catch image loading errors, format issues, etc.
        return f"❌ Error processing image: {str(e)}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def test_gemini_connection() -> bool:
    """
    Tests if Gemini API is accessible and working.
    
    Returns:
        True if connection successful, False otherwise
    
    Use this during bot startup to verify API key is valid.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Hello"
        )
        return response.text is not None
    except Exception as e:
        print(f"Gemini connection test failed: {e}")
        return False


# ============================================================================
# EXAMPLE USAGE (for testing this module independently)
# ============================================================================

if __name__ == "__main__":
    """
    Test the Gemini integration independently.
    Run: python gemini.py
    """
    
    print("🧪 Testing Gemini integration...")
    
    # Test 1: Connection
    print("\n1️⃣ Testing connection...")
    if test_gemini_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        exit(1)
    
    # Test 2: Chat session
    print("\n2️⃣ Testing chat session...")
    chat = create_new_gemini_chat()
    if chat:
        print("✅ Chat session created!")
        
        # Send a test message
        response = chat_gemini(chat, "What is 2+2? Answer in one sentence.")
        print(f"Response: {response}")
    else:
        print("❌ Failed to create chat session!")
    
    # Test 3: Vision (requires an image file)
    print("\n3️⃣ Testing vision...")
    print("Skipping vision test (requires image file)")
    
    print("\n✅ All tests complete!")