import re
from datetime import datetime

def validate_ticket_number(ticket_number):
    """
    Validate ticket number format.
    Can contain letters, numbers, and hyphens.
    """
    if not ticket_number:  # Optional field
        return None
        
    # Remove any whitespace and hyphens for validation
    cleaned_number = ticket_number.replace(" ", "").replace("-", "")
    
    if not cleaned_number:
        return "Ticket number cannot be empty"
    
    # Allow alphanumeric characters
    if not cleaned_number.isalnum():
        return "Ticket number can only contain letters, numbers, spaces and hyphens"
    
    return None

def validate_ticket_data(ticket_data):
    """
    Validate extracted ticket information
    Returns dict with is_valid flag and list of errors
    """
    errors = []
    
    # Validate passenger name format (LASTNAME/FIRSTNAME)
    if not ticket_data.get('passenger_name'):
        errors.append("Nom du passager manquant")
    elif not re.match(r'^[A-Z]+/[A-Z][a-z]+$', ticket_data['passenger_name']):
        errors.append("Format du nom incorrect (doit être LASTNAME/Firstname)")
    
    # Validate flight number format
    if not ticket_data.get('flight_number'):
        errors.append("Numéro de vol manquant")
    elif not re.match(r'^[A-Z]{2,3}\d{1,4}[A-Z]?$', ticket_data['flight_number']):
        errors.append("Format du numéro de vol incorrect")
    
    # Validate departure date format and logic
    if not ticket_data.get('departure_date'):
        errors.append("Date de départ manquante")
    else:
        try:
            departure_date = datetime.strptime(ticket_data['departure_date'], '%Y-%m-%d')
            if departure_date < datetime.now():
                errors.append("La date de départ est dans le passé")
        except ValueError:
            errors.append("Format de date incorrect (doit être YYYY-MM-DD)")
    
    # Validate ticket number
    if not ticket_data.get('ticket_number'):
        errors.append("Numéro de billet manquant")
    elif not re.match(r'^\d{3}-\d{10}$', ticket_data['ticket_number']):
        errors.append("Format du numéro de billet incorrect")
    
    # Validate departure location
    if not ticket_data.get('departure'):
        errors.append("Informations de départ manquantes")
    else:
        departure = ticket_data['departure']
        if not departure.get('iata_code'):
            errors.append("Code IATA de départ manquant")
        elif not re.match(r'^[A-Z]{3}$', departure['iata_code']):
            errors.append("Format du code IATA de départ incorrect")
        
        if not departure.get('city'):
            errors.append("Ville de départ manquante")
        if not departure.get('country'):
            errors.append("Pays de départ manquant")
        if not departure.get('terminal'):
            errors.append("Terminal de départ manquant")
    
    # Validate arrival location
    if not ticket_data.get('arrival'):
        errors.append("Informations d'arrivée manquantes")
    else:
        arrival = ticket_data['arrival']
        if not arrival.get('iata_code'):
            errors.append("Code IATA d'arrivée manquant")
        elif not re.match(r'^[A-Z]{3}$', arrival['iata_code']):
            errors.append("Format du code IATA d'arrivée incorrect")
        
        if not arrival.get('city'):
            errors.append("Ville d'arrivée manquante")
        if not arrival.get('country'):
            errors.append("Pays d'arrivée manquant")
        if not arrival.get('terminal'):
            errors.append("Terminal d'arrivée manquant")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }

def validate_date_format(date_str):
    """
    Validate that the date string is in YYYY-MM-DD format
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False
