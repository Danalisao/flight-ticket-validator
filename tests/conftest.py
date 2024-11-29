import pytest
from app import create_app
import os
import tempfile

@pytest.fixture
def app():
    """Créer une instance de l'application pour les tests"""
    # Créer un répertoire temporaire pour les uploads
    test_upload_folder = tempfile.mkdtemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'UPLOAD_FOLDER': test_upload_folder
    })

    yield app

    # Nettoyer le répertoire temporaire
    for root, dirs, files in os.walk(test_upload_folder, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(test_upload_folder)

@pytest.fixture
def client(app):
    """Client de test pour faire des requêtes à l'application"""
    return app.test_client()

@pytest.fixture
def sample_ticket_data():
    """Données d'exemple d'un billet valide"""
    return {
        'passenger_name': 'John Doe',
        'flight_number': 'AF123',
        'departure_airport': 'CDG',
        'arrival_airport': 'JFK',
        'departure_time': '2024-12-25T10:00:00',
        'arrival_time': '2024-12-25T22:00:00'
    }

@pytest.fixture
def invalid_ticket_data():
    """Données d'exemple d'un billet invalide"""
    return {
        'passenger_name': 'John123',  # Invalide: contient des chiffres
        'flight_number': '12345',     # Invalide: pas de lettres au début
        'departure_airport': 'XX',    # Invalide: code IATA incorrect
        'arrival_airport': 'YY',      # Invalide: code IATA incorrect
        'departure_time': '2023-01-01T10:00:00',  # Invalide: date passée
        'arrival_time': '2023-01-01T09:00:00'     # Invalide: avant le départ
    }
