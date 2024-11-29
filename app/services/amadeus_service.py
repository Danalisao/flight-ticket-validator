from amadeus import Client, ResponseError
import os
import logging
from datetime import datetime
import json
from typing import Dict, Optional, List
import time

logger = logging.getLogger(__name__)

class AmadeusService:
    def __init__(self):
        self.client = Client(
            client_id=os.getenv('AMADEUS_CLIENT_ID'),
            client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
        )
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache

    def _get_cache_key(self, flight_number: str, departure_date: str) -> str:
        """Generate cache key for flight validation"""
        return f"{flight_number}_{departure_date}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get cached flight validation result if not expired"""
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return result
            del self.cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, result: Dict):
        """Save flight validation result to cache"""
        self.cache[cache_key] = (result, time.time())

    def clear_cache(self):
        """Clear all cached flight validation results"""
        self.cache = {}
        logger.info("Amadeus service cache cleared")

    def validate_flight(self, flight_info: Dict) -> Dict:
        """
        Validate flight information using Amadeus API
        
        Args:
            flight_info: Dictionary containing flight details:
                - flight_number: str (e.g., "VY1511")
                - departure_date: str (YYYY-MM-DD)
                - departure: Dict with iata_code
                - arrival: Dict with iata_code
        
        Returns:
            Dict containing validation results and additional flight information
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(flight_info['flight_number'], flight_info['departure_date'])
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached validation for flight {flight_info['flight_number']}")
                return cached_result

            # Extract carrier code and flight number
            carrier_code = flight_info['flight_number'][:2]
            flight_number = flight_info['flight_number'][2:]
            departure_date = flight_info['departure_date']

            try:
                response = self.client.schedule.flights.get(
                    carrierCode=carrier_code,
                    flightNumber=flight_number,
                    scheduledDepartureDate=departure_date
                )
                
                flight_schedules = response.data
                
                if not flight_schedules:
                    return {
                        "is_valid": False,
                        "errors": ["Vol non trouvé dans la base Amadeus"],
                        "details": None
                    }
                
                # Find matching flight
                matching_flight = None
                for schedule in flight_schedules:
                    if (schedule['flightDesignator']['carrierCode'] == carrier_code and
                        schedule['flightDesignator']['flightNumber'] == flight_number and
                        schedule['flightPoints'][0]['iataCode'] == flight_info['departure']['iata_code'] and
                        schedule['flightPoints'][-1]['iataCode'] == flight_info['arrival']['iata_code']):
                        matching_flight = schedule
                        break
                
                if not matching_flight:
                    return {
                        "is_valid": False,
                        "errors": ["Les informations de vol ne correspondent pas aux données Amadeus"],
                        "details": None
                    }
                
                # Extract only the information provided by Amadeus
                flight_details = {
                    "carrier": {
                        "code": matching_flight['flightDesignator']['carrierCode']
                    },
                    "flight_number": matching_flight['flightDesignator']['flightNumber'],
                    "departure": {
                        "iata_code": matching_flight['flightPoints'][0]['iataCode']
                    },
                    "arrival": {
                        "iata_code": matching_flight['flightPoints'][-1]['iataCode']
                    }
                }

                # Add optional fields only if they exist in the Amadeus response
                if 'carrierName' in matching_flight:
                    flight_details['carrier']['name'] = matching_flight['carrierName']
                
                if 'terminal' in matching_flight['flightPoints'][0]:
                    flight_details['departure']['terminal'] = matching_flight['flightPoints'][0]['terminal'].get('code')
                
                if 'scheduledTime' in matching_flight['flightPoints'][0]:
                    flight_details['departure']['scheduled_time'] = matching_flight['flightPoints'][0]['scheduledTime']
                
                if 'terminal' in matching_flight['flightPoints'][-1]:
                    flight_details['arrival']['terminal'] = matching_flight['flightPoints'][-1]['terminal'].get('code')
                
                if 'scheduledTime' in matching_flight['flightPoints'][-1]:
                    flight_details['arrival']['scheduled_time'] = matching_flight['flightPoints'][-1]['scheduledTime']
                
                if 'aircraftEquipment' in matching_flight and 'aircraftType' in matching_flight['aircraftEquipment']:
                    flight_details['aircraft'] = matching_flight['aircraftEquipment']['aircraftType']
                
                if 'status' in matching_flight:
                    flight_details['status'] = matching_flight['status']
                
                validation_result = {
                    "is_valid": True,
                    "errors": [],
                    "details": flight_details
                }
                
                # Cache the result
                self._save_to_cache(cache_key, validation_result)
                
                return validation_result

            except ResponseError as error:
                logger.error(f"Amadeus API error: {error}")
                return {
                    "is_valid": False,
                    "errors": ["Erreur lors de la vérification du vol"],
                    "details": None
                }
                
        except Exception as e:
            logger.error(f"Flight validation error: {str(e)}")
            return {
                "is_valid": False,
                "errors": ["Erreur interne lors de la validation du vol"],
                "details": None
            }

    def get_airport_info(self, iata_code: str) -> Optional[Dict]:
        """
        Get detailed airport information using Amadeus API
        
        Args:
            iata_code: str (e.g., "MRS")
            
        Returns:
            Dict containing airport details or None if not found
        """
        try:
            response = self.client.reference_data.locations.get(
                keyword=iata_code,
                subType=["AIRPORT"]
            )
            
            if response.data:
                airport = response.data[0]
                # Only include fields that exist in the Amadeus response
                result = {
                    "iata_code": airport["iataCode"]
                }
                
                if "name" in airport:
                    result["name"] = airport["name"]
                
                if "address" in airport:
                    if "cityName" in airport["address"]:
                        result["city"] = airport["address"]["cityName"]
                    if "countryName" in airport["address"]:
                        result["country"] = airport["address"]["countryName"]
                
                if "timeZone" in airport and "name" in airport["timeZone"]:
                    result["timezone"] = airport["timeZone"]["name"]
                
                return result
                
            return None
            
        except ResponseError as error:
            logger.error(f"Error getting airport info: {error}")
            return None
