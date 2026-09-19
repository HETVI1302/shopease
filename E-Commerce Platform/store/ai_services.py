from google import genai
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

# Using gemini-1.5-flash as default fast model, you can switch to gemini-1.5-pro for more complex tasks
MODEL_NAME = "gemini-1.5-flash"

def get_ai_search_intent(query):
    """
    Parses an unstructured search query into categories and keywords.
    E.g., "cheap gifts for kids" -> {"categories": ["Kids", "Toys"], "tags": ["cheap", "gift"]}
    """
    if not settings.GEMINI_API_KEY:
        return {"categories": [], "tags": []}
    
    prompt = f"""
    Analyze the following e-commerce search query: "{query}"
    Extract the intent and return ONLY a raw JSON object with two keys:
    - "categories": A list of relevant product categories (e.g., Men, Women, Kids, Electronics, Toys, Grocery, Clothes, Jewellery, Footwear, Yoga).
    - "tags": A list of descriptive tags or keywords (e.g., cheap, winter, gift, running).
    Do not include markdown blocks, just the JSON string.
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini AI Search Error: {e}")
        return {"categories": [], "tags": [query]}

def generate_review_summary(reviews_text):
    """
    Generates a concise 'Pros & Cons' summary from a list of reviews.
    """
    if not settings.GEMINI_API_KEY or not reviews_text:
        return "Not enough data for AI summary."

    prompt = f"""
    Based on the following customer reviews, generate a very concise summary (max 3-4 sentences) highlighting the main Pros and Cons.
    Format as plain text or basic HTML lists.
    Reviews:
    {reviews_text}
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini AI Summary Error: {e}")
        return "Failed to generate summary."

def auto_generate_product_description(title, tags):
    """
    Generates a catchy product description for the admin panel.
    """
    if not settings.GEMINI_API_KEY:
        return "Please configure GEMINI_API_KEY to generate descriptions."

    prompt = f"""
    Write a catchy, conversion-optimized e-commerce product description for a product named "{title}".
    Keywords/Tags to include: {tags}.
    The description should be professional, highlighting benefits, and formatted with short paragraphs. Max 150 words.
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini AI Copywriter Error: {e}")
        return "Failed to generate description."

def get_chatbot_response(user_message, context=""):
    """
    Chatbot assistant logic.
    """
    if not settings.GEMINI_API_KEY:
        return "Sorry, the AI assistant is currently offline (Missing API Key)."

    system_prompt = f"""
    You are ShopEase Assistant, a helpful and polite e-commerce customer support bot.
    Use the provided context about the store's products or user's order to answer the user's question.
    Keep answers brief (1-3 sentences) and friendly.
    Context: {context}
    User: {user_message}
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=system_prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini AI Chat Error: {e}")
        return "I'm having trouble connecting to my brain right now. Please try again later."
