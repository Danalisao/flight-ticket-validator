# Flight Ticket Validator

## 🎯 Overview
An AI-powered service for extracting and validating airline ticket information using OCR and machine learning technologies.

## 🚀 Features
- Automatic ticket information extraction using Claude AI
- Flight route validation via Amadeus API
- Support for multiple file formats (JPEG, PNG, PDF)
- Intelligent caching system for OCR results
- Comprehensive validation of ticket data
- RESTful API with Swagger documentation

## 🛠️ Technical Stack
- **Language**: Python 3.12.7
- **Web Framework**: Flask with Flask-RESTX
- **OCR Engine**: Claude AI (Anthropic)
- **Flight Data**: Amadeus API
- **Image Processing**: Pillow, pdf2image
- **Documentation**: Swagger UI

## 📋 Prerequisites
- Python 3.12.7
- Anthropic API Key (for Claude AI)
- Amadeus API Credentials

## ⚙️ Environment Variables
```bash
# Claude AI Configuration
ANTHROPIC_API_KEY=your_claude_api_key

# Amadeus API Configuration
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
```

## 🚀 Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/flight-ticket-validator.git
cd flight-ticket-validator
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## 🏃‍♂️ Running the Application
```bash
python run.py
```
The API will be available at http://localhost:5000
Swagger documentation at http://localhost:5000/api/docs

## 🧪 Running Tests
```bash
pytest
```

## 📁 Project Structure
```
flight-ticket-validator/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── services/
│   │   ├── amadeus_service.py
│   │   └── ocr_service.py
│   └── validators/
│       └── ticket_validator.py
├── tests/
│   └── ...
├── cache/
├── .env
├── config.py
├── requirements.txt
└── run.py
```

## 📝 API Documentation
### POST /api/tickets/validate
Validates a flight ticket image and returns extracted information.

**Parameters**:
- `ticket_image`: Image file (JPEG, PNG, PDF)
- `verify_flight`: Boolean (optional) - Verify flight with Amadeus

**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "extracted_info": {
    "passenger_name": "LASTNAME/FIRSTNAME",
    "flight_number": "AF123",
    "departure": {
      "iata_code": "CDG",
      "city": "Paris",
      "country": "France",
      "terminal": "2E"
    },
    "arrival": {
      "iata_code": "JFK",
      "city": "New York",
      "country": "United States",
      "terminal": "1"
    },
    "departure_date": "2024-03-15",
    "ticket_number": "1234567890",
    "connections": []
  },
  "flight_verified": true,
  "verification_details": { ... }
}
```

## 🔒 Security Considerations
- API keys are managed via environment variables
- Input validation for all file uploads
- Rate limiting for external API calls
- Secure error handling
- Cache management for sensitive data

## 📈 Future Improvements
1. Multi-language ticket support
2. Machine learning model for improved accuracy
3. Batch processing capabilities
4. Advanced error recovery
5. Performance optimization
