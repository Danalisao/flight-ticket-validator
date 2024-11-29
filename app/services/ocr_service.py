import os
import anthropic
import json
from PIL import Image
from io import BytesIO
import hashlib
import pickle
import time
import base64
from pathlib import Path
import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create cache directory if it doesn't exist
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def test_claude_api():
    """Test Claude API configuration and connectivity"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return False, "ANTHROPIC_API_KEY not configured"
        
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Test API with a simple request
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": "Test"}]
        )
        logger.info("Claude API test successful")
        return True, "API connection successful"
    except anthropic.APIError as e:
        logger.error(f"Claude API test failed: {e}")
        return False, f"API error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error testing Claude API: {e}")
        return False, f"Unexpected error: {str(e)}"

def get_cache_key(image):
    """Generate a cache key from PIL Image"""
    try:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or 'PNG')
        return hashlib.md5(img_byte_arr.getvalue()).hexdigest()
    except Exception as e:
        logger.error(f"Error generating cache key: {e}")
        return None

def get_from_cache(cache_key):
    """Get cached result if it exists and is not expired"""
    if not cache_key:
        return None
        
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                # Cache expires after 24 hours
                if time.time() - cached_data['timestamp'] < 24 * 60 * 60:
                    logger.debug("Cache hit")
                    return cached_data['result']
                logger.debug("Cache expired")
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
    return None

def save_to_cache(cache_key, result):
    """Save result to cache"""
    if not cache_key or not result:
        return
        
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'timestamp': time.time(),
                'result': result
            }, f)
        logger.debug("Saved to cache")
    except Exception as e:
        logger.warning(f"Cache save error: {e}")

def clear_cache():
    """Clear all cached OCR results"""
    try:
        for cache_file in CACHE_DIR.glob("*.pkl"):
            cache_file.unlink()
        logger.info("Cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False

def encode_image_to_base64(image):
    """Convert PIL Image to base64"""
    try:
        # Convert RGBA to RGB if needed
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # Ensure image is in RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Save as JPEG with good quality
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr = img_byte_arr.getvalue()
        b64_str = base64.b64encode(img_byte_arr).decode('utf-8')
        logger.debug(f"Image encoded successfully, size: {len(b64_str)} chars")
        return b64_str
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return None

def extract_ticket_info(image: Image.Image) -> dict:
    """
    Extract ticket information from image using Claude AI
    
    Args:
        image: PIL Image object
        
    Returns:
        Dictionary containing extracted ticket information
    """
    try:
        logger.info("Starting ticket information extraction")
        
        # Test API configuration
        api_success, api_message = test_claude_api()
        if not api_success:
            logger.error(f"Claude API test failed: {api_message}")
            return None
            
        # Generate cache key from image
        logger.debug("Generating cache key")
        cache_key = get_cache_key(image)
        
        # Check cache first
        cached_result = get_from_cache(cache_key)
        if cached_result:
            logger.info("Using cached OCR result")
            return cached_result
            
        # Convert image to base64
        logger.debug("Converting image to base64")
        image_b64 = encode_image_to_base64(image)
        if not image_b64:
            logger.error("Failed to encode image")
            return None
        
        # Prepare Claude API request
        logger.debug("Preparing Claude API request")
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        system_prompt = """You are an expert at extracting flight ticket information.
        Your task is to analyze the provided flight ticket or boarding pass image and extract specific information.
        
        Follow these rules:
        1. Extract information EXACTLY as shown on the ticket
        2. For passenger names, maintain the exact format (e.g., LASTNAME/FIRSTNAME)
        3. For flight numbers, include airline code (e.g., AF123)
        4. For dates, convert to YYYY-MM-DD format
        5. For locations, extract city, country, and IATA code
        6. If you're not certain about information, set it to null
        
        Return the information in this exact JSON format:
        {
            "passenger_name": "LASTNAME/FIRSTNAME",
            "flight_number": "XX1234",
            "departure_date": "YYYY-MM-DD",
            "departure": {
                "city": "City name",
                "country": "Country name",
                "iata_code": "XXX"
            },
            "arrival": {
                "city": "City name",
                "country": "Country name",
                "iata_code": "XXX"
            },
            "ticket_number": "12345678"
        }"""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract the flight ticket information from this image following the exact format specified. If you cannot find certain information, set those fields to null."
                    }
                ]
            }
        ]
        
        # Call Claude API
        logger.debug("Calling Claude API")
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=messages
        )
        
        logger.debug(f"Claude API response: {response.content[0].text}")
        
        # Parse response
        try:
            result = json.loads(response.content[0].text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude API response: {e}")
            logger.error(f"Raw response: {response.content[0].text}")
            return None
        
        # Validate result structure
        required_fields = ['passenger_name', 'flight_number', 'departure_date', 'departure', 'arrival']
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            logger.error(f"Missing required fields in API response: {missing_fields}")
            return None
            
        # Cache the result
        save_to_cache(cache_key, result)
        
        logger.info("Successfully extracted ticket information")
        return result
        
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return None
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}")
        logger.error(traceback.format_exc())
        return None