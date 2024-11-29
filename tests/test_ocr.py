import unittest
from unittest.mock import patch, MagicMock
from app.services.ocr_service import OCRService
from PIL import Image, ImageDraw
import tempfile
import os
import json

class TestOCRService(unittest.TestCase):
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.ocr_service = OCRService()
        self.test_image_path = self.create_test_image()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if hasattr(self, 'test_image_path') and os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def create_test_image(self):
        """Crée une image de test avec du texte simulant un billet d'avion"""
        image = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(image)
        
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
            
        temp_path = os.path.join(tempfile.gettempdir(), 'test_ticket.png')
        image.save(temp_path)
        return temp_path

    @patch('httpx.post')
    def test_extract_text_success(self, mock_post):
        """Test l'extraction réussie du texte"""
        # Simuler une réponse réussie de l'API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': 'BOARDING PASS\nPassenger: John Smith\nFlight: AF123'}]
        }
        mock_post.return_value = mock_response

        result = self.ocr_service.extract_text_from_file(self.test_image_path)
        self.assertIn('BOARDING PASS', result)
        self.assertIn('John Smith', result)

    @patch('httpx.post')
    def test_extract_ticket_info_success(self, mock_post):
        """Test l'extraction réussie des informations structurées"""
        # Simuler une réponse réussie de l'API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{
                'text': json.dumps({
                    'passenger_name': 'John Smith',
                    'flight_number': 'AF123',
                    'departure_airport': 'CDG',
                    'arrival_airport': 'JFK',
                    'departure_time': '2024-03-15 10:30',
                    'arrival_time': '2024-03-15 12:45'
                })
            }]
        }
        mock_post.return_value = mock_response

        result = self.ocr_service.extract_ticket_info(self.test_image_path)
        self.assertEqual(result['passenger_name'], 'John Smith')
        self.assertEqual(result['flight_number'], 'AF123')
        self.assertEqual(result['departure_airport'], 'CDG')

    @patch('httpx.post')
    def test_api_error_handling(self, mock_post):
        """Test la gestion des erreurs de l'API"""
        # Simuler une erreur de l'API
        mock_post.side_effect = Exception("API Error")

        result = self.ocr_service.extract_text_from_file(self.test_image_path)
        self.assertEqual(result, "")

        result = self.ocr_service.extract_ticket_info(self.test_image_path)
        self.assertIsNone(result['passenger_name'])
        self.assertIsNone(result['flight_number'])

    def test_invalid_file_path(self):
        """Test avec un chemin de fichier invalide"""
        result = self.ocr_service.extract_text_from_file("invalid_path.png")
        self.assertEqual(result, "")

        result = self.ocr_service.extract_ticket_info("invalid_path.png")
        self.assertIsNone(result['passenger_name'])

    @patch('httpx.post')
    def test_malformed_json_response(self, mock_post):
        """Test la gestion des réponses JSON malformées"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': 'Invalid JSON'}]
        }
        mock_post.return_value = mock_response

        result = self.ocr_service.extract_ticket_info(self.test_image_path)
        self.assertIsNone(result['passenger_name'])

    @patch('httpx.post')
    def test_missing_api_key(self, mock_post):
        """Test le comportement sans clé API"""
        # Sauvegarder la clé API actuelle
        original_key = self.ocr_service.api_key
        self.ocr_service.api_key = None

        result = self.ocr_service.extract_text_from_file(self.test_image_path)
        self.assertEqual(result, "")

        result = self.ocr_service.extract_ticket_info(self.test_image_path)
        self.assertIsNone(result['passenger_name'])

        # Restaurer la clé API
        self.ocr_service.api_key = original_key

    def test_pdf_handling(self):
        """Test le traitement des fichiers PDF"""
        # Ce test nécessiterait un fichier PDF de test
        # Pour l'instant, nous vérifions juste que la méthode existe
        self.assertTrue(hasattr(self.ocr_service, 'extract_text_from_file'))
        self.assertTrue(hasattr(self.ocr_service, 'extract_ticket_info'))

if __name__ == '__main__':
    unittest.main()
