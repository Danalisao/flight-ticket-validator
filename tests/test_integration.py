import unittest
from unittest.mock import patch, MagicMock
import os
import json
from datetime import datetime, timedelta

from app.services.ocr_service import OCRService
from app.services.amadeus_service import AmadeusService
from app.validators.ticket_validator import TicketValidator
from app.services.cache_service import CacheService

class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Configuration initiale pour les tests d'intégration"""
        self.ocr_service = OCRService()
        self.amadeus_service = AmadeusService()
        self.validator = TicketValidator()
        self.cache_service = CacheService()

    def test_full_ticket_processing_flow(self):
        """Test le flux complet de traitement d'un billet"""
        # Créer un billet de test
        test_image_path = self._create_test_ticket()

        # Mock les appels API externes
        with patch('app.services.amadeus_service.Client') as mock_amadeus:
            # Configurer le mock Amadeus
            mock_amadeus.return_value.schedule.flights.get.return_value = MagicMock(
                data=[{
                    'flightDesignator': {
                        'departure': 'CDG',
                        'arrival': 'JFK'
                    }
                }]
            )

            # Extraire et valider les informations du billet
            ticket_info = self.ocr_service.extract_ticket_info(test_image_path)

            # Vérifier les résultats
            self.assertIsNotNone(ticket_info)
            self.assertTrue('validation' in ticket_info)
            self.assertTrue(isinstance(ticket_info['validation'], dict))

        # Nettoyer
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

    def test_cache_integration(self):
        """Test l'intégration du cache"""
        # Préparer les données de test
        test_data = {
            'passenger_name': 'John Smith',
            'flight_number': 'AF123',
            'departure_airport': 'CDG',
            'arrival_airport': 'JFK',
            'departure_time': '2024-03-15 10:30',
            'arrival_time': '2024-03-15 12:45'
        }

        # Tester la mise en cache
        cache_key = self.cache_service.cache_key('test', 'flight_info')
        self.cache_service.set(cache_key, test_data)

        # Récupérer du cache
        cached_data = self.cache_service.get(cache_key)
        self.assertEqual(cached_data, test_data)

    @patch('app.services.amadeus_service.Client')
    def test_validator_integration(self, mock_amadeus):
        """Test l'intégration du validateur"""
        # Configurer le mock Amadeus
        mock_amadeus.return_value.reference_data.locations.get.return_value = MagicMock(
            data=[{'iataCode': 'CDG'}]
        )

        # Données de test
        test_data = {
            'passenger_name': 'John Smith',
            'flight_number': 'AF123',
            'departure_airport': 'CDG',
            'arrival_airport': 'JFK',
            'departure_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
            'arrival_time': (datetime.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%d %H:%M')
        }

        # Valider les données
        is_valid, errors = self.validator.validate_ticket_data(test_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_error_handling_integration(self):
        """Test la gestion des erreurs intégrée"""
        # Test avec des données invalides
        invalid_data = {
            'passenger_name': '123',  # Nom invalide
            'flight_number': 'INVALID',  # Numéro de vol invalide
            'departure_airport': 'INVALID',  # Code IATA invalide
            'arrival_airport': 'INVALID',  # Code IATA invalide
            'departure_time': 'invalid_date',  # Date invalide
            'arrival_time': 'invalid_date'  # Date invalide
        }

        # Valider les données invalides
        is_valid, errors = self.validator.validate_ticket_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)

    def _create_test_ticket(self):
        """Crée une image de test d'un billet d'avion"""
        from PIL import Image, ImageDraw
        import tempfile

        # Créer une image
        image = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(image)

        # Ajouter du texte
        text_content = [
            "BOARDING PASS",
            "Passenger Name: John Smith",
            "Flight Number: AF123",
            "From: CDG",
            "To: JFK",
            "Departure: 2024-03-15 10:30",
            "Arrival: 2024-03-15 12:45"
        ]

        y_position = 50
        for text in text_content:
            draw.text((50, y_position), text, fill='black')
            y_position += 40

        # Sauvegarder l'image
        temp_path = os.path.join(tempfile.gettempdir(), 'test_ticket.png')
        image.save(temp_path)
        return temp_path

if __name__ == '__main__':
    unittest.main()
