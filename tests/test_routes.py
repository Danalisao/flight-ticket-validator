import pytest
import os
import io
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_test_image(text="PASSENGER: John Doe\nFLIGHT: AF123\nDEPARTURE: CDG\nARRIVAL: JFK"):
    """Crée une image de test avec du texte"""
    # Créer une image blanche
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Ajouter du texte en noir
    draw.text((10, 10), text, fill='black')
    
    # Convertir en bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_validate_ticket_no_file(client):
    """Test l'envoi d'une requête sans fichier"""
    response = client.post('/api/v1/validate-ticket')
    assert response.status_code == 400
    assert b'Aucun fichier' in response.data

def test_validate_ticket_empty_file(client):
    """Test l'envoi d'une requête avec un fichier vide"""
    data = {'file': (io.BytesIO(), '')}
    response = client.post('/api/v1/validate-ticket', data=data)
    assert response.status_code == 400
    assert b'Aucun fichier' in response.data

def test_validate_ticket_invalid_extension(client):
    """Test l'envoi d'un fichier avec une extension non autorisée"""
    data = {'file': (io.BytesIO(b'test data'), 'test.txt')}
    response = client.post('/api/v1/validate-ticket', data=data)
    assert response.status_code == 400
    assert b'Type de fichier non autoris' in response.data

@pytest.mark.skip(reason="Nécessite Tesseract OCR installé")
def test_validate_ticket_valid_image(client):
    """Test l'envoi d'une image valide"""
    img_data = create_test_image()
    data = {'file': (img_data, 'test.png')}
    response = client.post('/api/v1/validate-ticket', data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] in ['valid', 'invalid']

def test_validate_ticket_large_file(client):
    """Test l'envoi d'un fichier trop volumineux"""
    # Créer un fichier de plus de 5 Mo
    large_data = b'x' * (6 * 1024 * 1024)
    data = {'file': (io.BytesIO(large_data), 'large.png')}
    response = client.post('/api/v1/validate-ticket', data=data)
    assert response.status_code == 413  # Request Entity Too Large

def test_validate_ticket_rate_limit(client):
    """Test la limite de requêtes"""
    # Faire 101 requêtes
    for _ in range(101):
        response = client.post('/api/v1/validate-ticket')
    
    # La 101ème requête devrait être limitée
    assert response.status_code == 429  # Too Many Requests
