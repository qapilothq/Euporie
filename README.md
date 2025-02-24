# Euporie: Intelligent Test Data Generator for Mobile Applications

## Overview

Euporie is a robust FastAPI-based application designed to intelligently generate test data for mobile application fields. By analyzing screenshots and XML structures, it determines the necessity of data generation and provides structured data following a strict priority-based generation system.

**Current Status**: Beta version supporting Android XML only. iOS support coming soon.

## Key Features

- Automated analysis of mobile screens for data generation needs
- Dual input support: Screenshots and XML hierarchy files
- Intelligent data generation with priority-based system:
  1. Configuration data (highest priority)
  2. Faker library integration (second priority)
  3. LLM-based generation (fallback option)
- RESTful API for seamless integration
- Detailed field metadata extraction from XML
- Comprehensive API documentation
- Support for base64 encoded images and XML as strings
- Extensive Faker library integration for realistic data generation

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- FastAPI
- uvicorn
- requests (for URL handling)
- python-dotenv (for environment variable management)
- Faker library for data generation
- Custom logging configuration

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/qapilotio/Euporie.git
   cd Euporie
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_openai_api_key
     ```

## Quick Start

1. Start the server:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Access the interactive API documentation:
   - OpenAPI UI: `http://localhost:8000/docs`
   - ReDoc UI: `http://localhost:8000/redoc`

## API Reference

### POST /invoke

Analyzes mobile screens and generates test data following a strict priority system.

#### Request Body

```json
{
  "image": "string", // Optional: Base64 encoded image string
  "xml": "string", // Optional: XML as string
  "image_url": "string", // Optional: Image URL
  "xml_url": "string", // Optional: XML URL
  "config_data": {} // Optional: Configuration data for field generation
}
```

**Note**: Either `image` or `xml` must be provided. When both are present, XML analysis takes precedence.

#### Response Format

```json
{
  "status": "success",
  "agent_response": {
    "data_generation_required": true/false,
    "fields": [
      {
        "id": "unique_identifier", // Only included with XML data
        "field_name": "string",
        "input_type": "string",
        "value": "string",
        "faker_function": "string", // null if source is 'config' or 'llm'
        "source": "config/faker/llm"
      }
    ]
  }
}
```

### Supported Faker Functions

The system supports numerous Faker functions for data generation, including:

- email
- address
- basic_phone_number
- city
- state
- zipcode
- country
- credit_card_number
- credit_card_expire
- credit_card_security_code
- date_of_birth
- name
- first_name
- last_name
- gender
- password
- username
- profile
- company
- company_email
- website (url)
- image (profile picture)
- language_name
- locale
- postalcode
- user_agent
- uuid4
- random_int
- ip address (ipv4, ipv6)
- date_time

### GET /health

Health check endpoint returning application status.

## Project Structure

```
euporie/
├── main.py          # FastAPI application and endpoints
├── utils.py         # Helper functions and utilities
├── prompts.py       # System prompt and templates
├── llm.py          # OpenAI integration
├── logger_config.py # Logging configuration
├── requirements.txt # Project dependencies
└── .env            # Environment variables
```

## Error Handling

The API implements comprehensive error handling for:

- Invalid input formats
- Missing required fields
- Failed API calls
- Image processing errors
- XML parsing failures
- Faker function failures
- JSON parsing errors

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Contact

For questions or support, please contact **[contactus@qapilot.com](mailto:contactus@qapilot.com)**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
