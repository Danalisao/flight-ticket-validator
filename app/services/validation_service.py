import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from .amadeus_service import AmadeusService
from .ocr_service import extract_ticket_info, clear_cache as clear_ocr_cache
from PIL import Image
import io
from werkzeug.datastructures import FileStorage

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ValidationService:
    def __init__(self):
        self.amadeus_service = AmadeusService()

    def validate_ticket(self, file: FileStorage) -> Dict:
        """
        Validate a flight ticket by extracting information and verifying with Amadeus
        
        Args:
            file: FileStorage object containing the ticket image
            
        Returns:
            Dict containing validation results and extracted information
        """
        try:
            logger.info(f"Starting validation for file: {file.filename}")
            
            # Check file content type
            if not file.content_type:
                logger.error("No content type provided")
                return {
                    "is_valid": False,
                    "errors": ["Invalid file type"],
                    "extracted_info": None
                }
                
            if not file.content_type.startswith(('image/', 'application/pdf')):
                logger.error(f"Invalid content type: {file.content_type}")
                return {
                    "is_valid": False,
                    "errors": ["Only images and PDF files are supported"],
                    "extracted_info": None
                }

            # Convert FileStorage to PIL Image
            try:
                image_bytes = file.read()
                image = Image.open(io.BytesIO(image_bytes))
                logger.debug(f"Image opened successfully: {image.format} {image.size}")
            except Exception as e:
                logger.error(f"Error opening image: {e}")
                return {
                    "is_valid": False,
                    "errors": ["Could not open the image file"],
                    "extracted_info": None
                }

            # Validate image
            image_validation_result = validate_image(image)
            if not image_validation_result[0]:
                return {
                    "is_valid": False,
                    "errors": [image_validation_result[2]],
                    "extracted_info": None
                }

            # Extracted ticket information is valid, proceed with validation
            ticket_info = image_validation_result[1]

            # Validate extracted information
            ticket_validation_result = validate_ticket_info(ticket_info)
            if not ticket_validation_result[0]:
                return {
                    "is_valid": False,
                    "errors": [ticket_validation_result[2]],
                    "extracted_info": ticket_info
                }

            logger.info("Ticket validation successful")
            return {
                "is_valid": True,
                "errors": [],
                "extracted_info": ticket_info
            }

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                "is_valid": False,
                "errors": ["Error validating ticket: " + str(e)],
                "extracted_info": None
            }

    def clear_cache(self):
        """Clear the OCR cache"""
        try:
            clear_ocr_cache()
            return {"status": "success", "message": "Cache cleared successfully"}
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return {"status": "error", "message": str(e)}

def validate_image(image: Image.Image) -> Tuple[bool, Dict, Optional[str]]:
    """
    Validate the uploaded image and extract ticket information
    
    Args:
        image: PIL Image object
        
    Returns:
        Tuple of (success, result_dict, error_message)
    """
    try:
        # Basic image validation
        if not isinstance(image, Image.Image):
            return False, {}, "Invalid image format"
            
        # Check image dimensions
        if image.size[0] < 100 or image.size[1] < 100:
            return False, {}, "Image too small - minimum size is 100x100 pixels"
            
        if image.size[0] > 4000 or image.size[1] > 4000:
            return False, {}, "Image too large - maximum size is 4000x4000 pixels"
            
        # Extract ticket information
        logger.info("Extracting ticket information")
        ticket_info = extract_ticket_info(image)
        
        if not ticket_info:
            return False, {}, "Could not extract information from ticket. Please ensure the image is clear and contains visible ticket information."
            
        # Validate extracted information
        validation_result = validate_ticket_info(ticket_info)
        if not validation_result[0]:
            return validation_result
            
        return True, ticket_info, None
        
    except Exception as e:
        logger.error(f"Image validation error: {str(e)}")
        return False, {}, f"Error processing image: {str(e)}"

def validate_ticket_info(ticket_info: Dict) -> Tuple[bool, Dict, Optional[str]]:
    """
    Validate extracted ticket information
    
    Args:
        ticket_info: Dictionary containing ticket information
        
    Returns:
        Tuple of (success, ticket_info, error_message)
    """
    try:
        # Check required fields
        required_fields = ['passenger_name', 'flight_number', 'departure_date', 'departure', 'arrival']
        missing_fields = [field for field in required_fields if not ticket_info.get(field)]
        
        if missing_fields:
            return False, ticket_info, f"Missing required information: {', '.join(missing_fields)}"
            
        # Validate passenger name format (LASTNAME/FIRSTNAME)
        if not re.match(r'^[A-Z]+/[A-Z]+$', ticket_info['passenger_name']):
            return False, ticket_info, "Invalid passenger name format. Expected LASTNAME/FIRSTNAME"
            
        # Validate flight number format (2 letters followed by 1-4 digits)
        if not re.match(r'^[A-Z]{2}\d{1,4}$', ticket_info['flight_number']):
            return False, ticket_info, "Invalid flight number format. Expected airline code (2 letters) followed by 1-4 digits"
            
        # Validate date format and value
        try:
            departure_date = datetime.strptime(ticket_info['departure_date'], '%Y-%m-%d')
            if departure_date < datetime(2000, 1, 1):  # Basic sanity check
                return False, ticket_info, "Invalid departure date - too old"
        except ValueError:
            return False, ticket_info, "Invalid date format. Expected YYYY-MM-DD"
            
        # Validate location information
        for location_type in ['departure', 'arrival']:
            location = ticket_info[location_type]
            if not isinstance(location, dict):
                return False, ticket_info, f"Invalid {location_type} location format"
                
            # Check required location fields
            required_location_fields = ['city', 'country', 'iata_code']
            missing_location_fields = [field for field in required_location_fields if not location.get(field)]
            
            if missing_location_fields:
                return False, ticket_info, f"Missing {location_type} location information: {', '.join(missing_location_fields)}"
                
            # Validate IATA code format (3 uppercase letters)
            if not re.match(r'^[A-Z]{3}$', location['iata_code']):
                return False, ticket_info, f"Invalid {location_type} IATA code format. Expected 3 uppercase letters"
        
        # All validations passed
        return True, ticket_info, None
        
    except Exception as e:
        logger.error(f"Ticket validation error: {str(e)}")
        return False, ticket_info, f"Error validating ticket information: {str(e)}"
