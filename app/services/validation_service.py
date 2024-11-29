import logging
from datetime import datetime
from typing import Dict, List, Optional
from .amadeus_service import AmadeusService
from .ocr_service import extract_ticket_info, clear_cache as clear_ocr_cache

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self):
        self.amadeus_service = AmadeusService()

    def validate_ticket(self, image) -> Dict:
        """
        Validate a flight ticket by extracting information and verifying with Amadeus
        
        Args:
            image: PIL Image object of the ticket
            
        Returns:
            Dict containing validation results and extracted information
        """
        try:
            # Step 1: Extract ticket information using OCR
            extracted_info = extract_ticket_info(image)
            if not extracted_info:
                return {
                    "is_valid": False,
                    "errors": ["Impossible d'extraire les informations du billet"],
                    "extracted_info": None,
                    "flight_info": None
                }

            # Step 2: Validate extracted information format
            validation_errors = self._validate_extracted_info(extracted_info)
            if validation_errors:
                return {
                    "is_valid": False,
                    "errors": validation_errors,
                    "extracted_info": extracted_info,
                    "flight_info": None
                }

            # Step 3: Validate flight with Amadeus
            flight_validation = self.amadeus_service.validate_flight(extracted_info)
            
            # Step 4: Get additional airport information
            if flight_validation["is_valid"]:
                departure_info = self.amadeus_service.get_airport_info(
                    extracted_info["departure"]["iata_code"]
                )
                arrival_info = self.amadeus_service.get_airport_info(
                    extracted_info["arrival"]["iata_code"]
                )
                
                if departure_info:
                    extracted_info["departure"].update(departure_info)
                if arrival_info:
                    extracted_info["arrival"].update(arrival_info)

            return {
                "is_valid": flight_validation["is_valid"],
                "errors": flight_validation.get("errors", []),
                "extracted_info": extracted_info,
                "flight_info": flight_validation.get("details")
            }

        except Exception as e:
            logger.error(f"Ticket validation error: {str(e)}")
            return {
                "is_valid": False,
                "errors": ["Erreur lors de la validation du billet"],
                "extracted_info": None,
                "flight_info": None
            }

    def _validate_extracted_info(self, extracted_info: Dict) -> List[str]:
        """
        Validate the format and presence of required fields in extracted information
        
        Args:
            extracted_info: Dictionary containing extracted ticket information
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not extracted_info.get("passenger_name"):
            errors.append("Nom du passager manquant")
            
        if not extracted_info.get("flight_number"):
            errors.append("Numéro de vol manquant")
            
        if not extracted_info.get("departure_date"):
            errors.append("Date de départ manquante")
        else:
            try:
                # Validate date format
                datetime.strptime(extracted_info["departure_date"], "%Y-%m-%d")
            except ValueError:
                errors.append("Format de date invalide")
        
        # Check departure information
        departure = extracted_info.get("departure", {})
        if not departure or not departure.get("iata_code"):
            errors.append("Informations de départ manquantes")
            
        # Check arrival information
        arrival = extracted_info.get("arrival", {})
        if not arrival or not arrival.get("iata_code"):
            errors.append("Informations d'arrivée manquantes")
            
        return errors

    def clear_cache(self):
        """Clear all service caches"""
        self.amadeus_service.clear_cache()
        clear_ocr_cache()
        logger.info("All service caches cleared")
