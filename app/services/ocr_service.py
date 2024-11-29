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
import random
import traceback

# Create cache directory if it doesn't exist
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

def get_cache_key(image_bytes):
    """Generate a cache key from image bytes"""
    return hashlib.md5(image_bytes).hexdigest()

def get_from_cache(cache_key):
    """Get cached result if it exists and is not expired"""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                # Cache expires after 24 hours
                if time.time() - cached_data['timestamp'] < 24 * 60 * 60:
                    return cached_data['result']
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
    return None

def save_to_cache(cache_key, result):
    """Save result to cache"""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'timestamp': time.time(),
                'result': result
            }, f)
    except Exception as e:
        logger.warning(f"Cache save error: {e}")

def clear_cache():
    """Clear OCR results cache"""
    for cache_file in CACHE_DIR.glob("*.pkl"):
        try:
            cache_file.unlink()
        except Exception as e:
            logger.warning(f"Error deleting cache file {cache_file}: {e}")
    logger.info("OCR service cache cleared")

def encode_image_to_base64(image):
    """Convert PIL Image to base64"""
    image_bytes = BytesIO()
    image.save(image_bytes, format='JPEG', quality=85)
    return base64.b64encode(image_bytes.getvalue()).decode('utf-8')

def call_claude_api(messages, system_prompt, max_retries=3):
    """Call Claude API with retry mechanism and error handling"""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": messages
                    }
                ],
                system=system_prompt
            )
            return response
        except anthropic.APIError as e:
            if "overloaded_error" in str(e).lower():
                wait_time = (2 ** attempt) + random.random()
                logger.warning(f"Claude API overloaded. Retry {attempt + 1}/{max_retries} after {wait_time:.2f}s")
                time.sleep(wait_time)
            else:
                raise
    
    logger.error("Claude API consistently overloaded")
    raise Exception("Claude API service unavailable")

def parse_claude_response(response):
    """Parse Claude API response and extract JSON"""
    try:
        content = response.content[0].text
        # Clean up the response to ensure valid JSON
        json_str = content.strip()
        if json_str.startswith('```json'):
            json_str = json_str[7:]
        if json_str.endswith('```'):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # Parse JSON
        extracted_info = json.loads(json_str)
        
        # Ensure all required fields exist
        required_fields = ['passenger_name', 'flight_number', 'departure', 'arrival', 'departure_date']
        for field in required_fields:
            if field not in extracted_info:
                extracted_info[field] = None
        
        if 'departure' not in extracted_info or not extracted_info['departure']:
            extracted_info['departure'] = {}
        if 'arrival' not in extracted_info or not extracted_info['arrival']:
            extracted_info['arrival'] = {}
        if 'connections' not in extracted_info:
            extracted_info['connections'] = []
            
        return extracted_info
    except Exception as e:
        logger.error(f"Response parsing error: {e}")
        logger.error(f"Raw response: {response}")
        raise

def parse_flight_date(date_str):
    """
    Parse flight date from various formats to YYYY-MM-DD
    Rules:
    - If year not specified, use current year
    - Date must be current year and within next 2 weeks
    - If date is in the past for current year, return None
    
    Handles formats:
    - 29JUL
    - 29JUL24
    - 29/07
    - 29/07/24
    - 29/07/2024
    """
    from datetime import datetime, timedelta
    import re
    
    # Clean the input
    date_str = date_str.strip().upper()
    
    # Current date and max future date (2 weeks)
    current_date = datetime.now()
    max_future_date = current_date + timedelta(weeks=2)
    
    try:
        # Handle format "29JUL" or "29JUL24"
        if re.match(r'^\d{2}[A-Z]{3}\d{0,2}$', date_str):
            day = int(date_str[:2])
            month_str = date_str[2:5]
            year_str = date_str[5:] if len(date_str) > 5 else ''
            
            # Convert month name to number
            months = {
                'JAN': 1, 'FEV': 2, 'MAR': 3, 'AVR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AOU': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
                'FEB': 2, 'APR': 4, 'AUG': 8
            }
            month = months.get(month_str, None)
            if not month:
                raise ValueError(f"Invalid month: {month_str}")
            
            # Handle year
            if year_str:
                if len(year_str) == 2:
                    # For two-digit years, only accept current year
                    current_two_digit = current_date.year % 100
                    if int(year_str) != current_two_digit:
                        raise ValueError(f"Date must be in current year (20{current_two_digit})")
                    year = current_date.year
                else:
                    year = int(year_str)
                    if year != current_date.year:
                        raise ValueError(f"Date must be in current year ({current_date.year})")
            else:
                # If no year provided, use current year
                year = current_date.year
            
            # Create date object and validate
            parsed_date = datetime(year, month, day)
            
            # Check if date is valid (not in past and within 2 weeks)
            if parsed_date < current_date:
                raise ValueError("Date cannot be in the past")
            if parsed_date > max_future_date:
                raise ValueError("Date cannot be more than 2 weeks in the future")
            
            return parsed_date.strftime('%Y-%m-%d')
            
        # Handle format "29/07" or "29/07/24" or "29/07/2024"
        elif '/' in date_str:
            parts = date_str.split('/')
            if len(parts) >= 2:
                day = int(parts[0])
                month = int(parts[1])
                
                if len(parts) == 3:
                    year_str = parts[2]
                    if len(year_str) == 2:
                        # Only accept current year
                        current_two_digit = current_date.year % 100
                        if int(year_str) != current_two_digit:
                            raise ValueError(f"Date must be in current year (20{current_two_digit})")
                        year = current_date.year
                    else:
                        year = int(year_str)
                        if year != current_date.year:
                            raise ValueError(f"Date must be in current year ({current_date.year})")
                else:
                    # If no year provided, use current year
                    year = current_date.year
                
                # Create date object and validate
                parsed_date = datetime(year, month, day)
                
                # Check if date is valid (not in past and within 2 weeks)
                if parsed_date < current_date:
                    raise ValueError("Date cannot be in the past")
                if parsed_date > max_future_date:
                    raise ValueError("Date cannot be more than 2 weeks in the future")
                
                return parsed_date.strftime('%Y-%m-%d')
        
        raise ValueError(f"Unsupported date format: {date_str}")
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {str(e)}")
        return None

def get_country_for_city(city):
    """
    Returns the country for known French cities.
    """
    french_cities = {
        'MARSEILLE': 'France',
        'PARIS': 'France',
        'LYON': 'France',
        'TOULOUSE': 'France',
        'NICE': 'France',
        'NANTES': 'France',
        'STRASBOURG': 'France',
        'MONTPELLIER': 'France',
        'BORDEAUX': 'France',
        'LILLE': 'France',
        'RENNES': 'France',
        'REIMS': 'France',
        'TOULON': 'France',
        'SAINT-ETIENNE': 'France',
        'LE HAVRE': 'France',
        'GRENOBLE': 'France',
        'DIJON': 'France',
        'ANGERS': 'France',
        'VILLEURBANNE': 'France',
        'NIMES': 'France',
        'AIX-EN-PROVENCE': 'France',
        'BREST': 'France',
        'LIMOGES': 'France',
        'TOURS': 'France',
        'AMIENS': 'France',
        'PERPIGNAN': 'France',
        'METZ': 'France',
        'BESANCON': 'France',
        'ORLEANS': 'France',
        'ROUEN': 'France',
        'MULHOUSE': 'France',
        'CAEN': 'France',
        'NANCY': 'France',
        'AVIGNON': 'France'
    }
    
    city = city.upper() if city else ''
    return french_cities.get(city, None)

def extract_ticket_info(image):
    """
    Extract ticket information from image using Claude AI
    Includes fallback mechanism for service unavailability
    """
    try:
        # Convert image to base64
        image_base64 = encode_image_to_base64(image)
        
        # Check cache first
        cache_key = hashlib.md5(image_base64.encode()).hexdigest()
        cached_result = get_from_cache(cache_key)
        if cached_result:
            return cached_result

        # Prepare system prompt and message
        system_prompt = """You are an expert at extracting flight ticket information from images, with extensive knowledge of world geography. 
        Your task is to carefully analyze the provided flight ticket or boarding pass image and extract specific information.
        
        Focus on these key elements:
        1. Passenger name (in LASTNAME/FIRSTNAME format)
        2. Flight number (airline code + number)
        3. Departure information:
           - IATA code (e.g., MRS for Marseille)
           - City name exactly as shown
           - Country: Use your knowledge to determine the country based on the city
             Examples:
             - Marseille → France
             - London → United Kingdom
             - New York → United States
             - Tokyo → Japan
             - Dubai → United Arab Emirates
           - Terminal if shown
        4. Arrival information (same rules as departure)
        5. Date information - CRITICAL RULES:
           - Extract the exact date format shown (e.g., "29JUL" or "29/07")
           - Do not modify or assume the year
           - Keep the date exactly as shown on the ticket
        6. Ticket or boarding pass number
        7. Any connection information
        
        Important rules:
        - Extract information EXACTLY as shown on the ticket
        - For passenger names, maintain the exact format (e.g., LASTNAME/FIRSTNAME)
        - Use IATA codes exactly as shown (e.g., MRS for Marseille)
        - Include terminal information if present
        - Only include information you are certain about
        - Pay attention to both English and other languages on the ticket
        - For cities and countries:
          * Extract city names exactly as shown
          * ALWAYS include the country based on your knowledge of world geography
          * If a city could be in multiple countries, use the most likely one based on context
          * Use official country names in English
        
        Return the information in this JSON format:
        {
            "passenger_name": "LASTNAME/FIRSTNAME",
            "flight_number": "XX1234",
            "departure": {
                "iata_code": "XXX",
                "city": "City name",
                "country": "Deduced country name",
                "terminal": "Terminal info"
            },
            "arrival": {
                "iata_code": "XXX",
                "city": "City name",
                "country": "Deduced country name",
                "terminal": "Terminal info"
            },
            "departure_date": "As shown on ticket (e.g., 29JUL)",
            "ticket_number": "XXXXX",
            "connections": []
        }"""

        message_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_base64
                }
            },
            {
                "type": "text",
                "text": "Please extract the flight ticket information from this image. Use your knowledge of world geography to determine the country for each city. For dates, extract them EXACTLY as shown on the ticket without any modification. Return ONLY the JSON object with the extracted information."
            }
        ]

        try:
            # Call Claude API
            response = call_claude_api(message_content, system_prompt)
            
            # Parse the response and extract JSON
            extracted_info = parse_claude_response(response)
            
            # Process the date
            if extracted_info.get('departure_date'):
                parsed_date = parse_flight_date(extracted_info['departure_date'])
                if parsed_date:
                    extracted_info['departure_date'] = parsed_date
                else:
                    # Si la date n'est pas valide selon nos règles
                    extracted_info['validation_errors'] = extracted_info.get('validation_errors', [])
                    extracted_info['validation_errors'].append(
                        "La date du vol doit être dans l'année en cours et dans les 2 prochaines semaines"
                    )
            
            # Cache the result
            save_to_cache(cache_key, extracted_info)
            
            return extracted_info

        except Exception as api_error:
            logger.error(f"Claude API error: {api_error}")
            logger.error(traceback.format_exc())
            raise

    except Exception as e:
        logger.error(f"Unexpected error extracting ticket info: {str(e)}")
        logger.error(traceback.format_exc())
        raise