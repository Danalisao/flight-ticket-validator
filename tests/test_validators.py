import pytest
from app.validators.ticket_validator import (
    validate_ticket_data,
    validate_passenger_name,
    validate_flight_number,
    validate_iata_code,
    validate_flight_dates
)
from datetime import datetime, timedelta

def test_validate_passenger_name():
    """Test la validation du nom du passager"""
    assert validate_passenger_name("John Doe")
    assert validate_passenger_name("Jean-Pierre Dupont")
    assert validate_passenger_name("María José")
    
    assert not validate_passenger_name("John123")
    assert not validate_passenger_name("John@Doe")
    assert not validate_passenger_name("")
    assert not validate_passenger_name(None)

def test_validate_flight_number():
    """Test la validation du numéro de vol"""
    assert validate_flight_number("AF123")
    assert validate_flight_number("BA1")
    assert validate_flight_number("LH9999")
    
    assert not validate_flight_number("123AF")
    assert not validate_flight_number("A123")
    assert not validate_flight_number("AF12345")
    assert not validate_flight_number("")
    assert not validate_flight_number(None)

def test_validate_iata_code():
    """Test la validation des codes IATA avec vérification Amadeus"""
    # Codes IATA valides connus
    assert validate_iata_code("CDG")  # Paris Charles de Gaulle
    assert validate_iata_code("JFK")  # New York JFK
    assert validate_iata_code("LAX")  # Los Angeles
    
    # Codes IATA invalides
    assert not validate_iata_code("CD")
    assert not validate_iata_code("CDGX")
    assert not validate_iata_code("123")
    assert not validate_iata_code("")
    assert not validate_iata_code(None)
    assert not validate_iata_code("ZZZ")  # Code inexistant

def test_validate_flight_dates():
    """Test la validation des dates de vol"""
    now = datetime.now()
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    
    # Dates valides
    valid_departure = future.isoformat()
    valid_arrival = (future + timedelta(hours=2)).isoformat()
    assert not validate_flight_dates(valid_departure, valid_arrival)
    
    # Date de départ dans le passé
    assert validate_flight_dates(past.isoformat(), valid_arrival)
    
    # Arrivée avant le départ
    invalid_arrival = (future - timedelta(hours=1)).isoformat()
    assert validate_flight_dates(valid_departure, invalid_arrival)
    
    # Vol trop long
    long_flight = (future + timedelta(hours=25)).isoformat()
    assert validate_flight_dates(valid_departure, long_flight)

def test_validate_ticket_data():
    """Test la validation complète des données du billet avec Amadeus"""
    # Données de vol valides (utiliser des vols réels)
    valid_ticket_data = {
        'passenger_name': 'John Doe',
        'flight_number': 'AF123',  # Un vol Air France réel
        'departure_airport': 'CDG',  # Paris
        'arrival_airport': 'JFK',    # New York
        'departure_time': (datetime.now() + timedelta(days=30)).isoformat(),
        'arrival_time': (datetime.now() + timedelta(days=30, hours=8)).isoformat()
    }
    
    # Valider le billet
    result = validate_ticket_data(valid_ticket_data)
    assert result['is_valid'], f"Validation failed with errors: {result['errors']}"
    
    # Données de vol invalides
    invalid_ticket_data = {
        'passenger_name': 'John123',  # Nom invalide
        'flight_number': 'XX999',     # Numéro de vol invalide
        'departure_airport': 'ZZZ',   # Code IATA invalide
        'arrival_airport': 'YYY',     # Code IATA invalide
        'departure_time': datetime.now().isoformat(),  # Date dans le passé
        'arrival_time': (datetime.now() + timedelta(hours=1)).isoformat()
    }
    
    # Valider le billet invalide
    result = validate_ticket_data(invalid_ticket_data)
    assert not result['is_valid']
    assert len(result['errors']) > 0
