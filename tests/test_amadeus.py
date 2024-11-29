import pytest
from app.services.amadeus_service import AmadeusFlightService

def test_amadeus_airport_details():
    """Test la récupération des détails d'un aéroport"""
    service = AmadeusFlightService()
    
    # Test avec un aéroport valide
    airport_details = service.get_airport_details('CDG')
    assert airport_details is not None
    assert 'name' in airport_details
    
    # Test avec un code IATA invalide
    airport_details = service.get_airport_details('XXX')
    assert airport_details is None

def test_amadeus_flight_validation():
    """Test la validation d'un vol"""
    service = AmadeusFlightService()
    
    # Test avec un vol valide (à ajuster selon les disponibilités actuelles)
    validation_result = service.validate_flight(
        flight_number='AF123', 
        departure_airport='CDG', 
        arrival_airport='JFK', 
        departure_time='2024-12-25T10:00:00'
    )
    
    # Vérifier la structure de la réponse
    assert 'is_valid' in validation_result
    assert 'details' in validation_result or 'error' in validation_result

def test_amadeus_flight_invalid():
    """Test la validation d'un vol invalide"""
    service = AmadeusFlightService()
    
    # Test avec des paramètres manifestement invalides
    validation_result = service.validate_flight(
        flight_number='XX999', 
        departure_airport='ZZZ', 
        arrival_airport='YYY', 
        departure_time='2024-12-25T10:00:00'
    )
    
    # Le vol devrait être considéré comme invalide
    assert validation_result['is_valid'] is False
