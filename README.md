# Euporie: Intelligent Test Data Generator for Mobile Applications

## Overview

Euporie is a robust FastAPI-based application designed to intelligently generate test data for mobile application fields. By analyzing screenshots and XML structures, it determines the necessity of data generation and provides structured data when required.

**Current Status**: Beta version supporting Android XML only. iOS support coming soon.

## Key Features

- Automated analysis of mobile screens for data generation needs
- Dual input support: Screenshots and XML hierarchy files
- Intelligent data generation powered by OpenAI's GPT-4
- RESTful API for seamless integration
- Detailed field metadata extraction from XML
- Comprehensive API documentation

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- FastAPI
- uvicorn
- requests (for URL handling)
- python-dotenv (for environment variable management)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/qapilotio/Euporie.git
   cd Euporie
   ```

````

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

Analyzes mobile screens to determine if test data generation is required and provides generated data if needed.

#### Request Body

```json
{
  "image": "string", // Optional: File path or URL
  "xml": "string", // Optional: File path or URL
  "config_data": {} // Optional: Configuration data for field generation
}
```

**Note**: Either `image` or `xml` must be provided. When both are present, XML analysis takes precedence.

#### Response Format

```json
{
  "status": "success",
  "agent_response": {
    "data_generation_required": "yes/no",
    "fields": [
      {
        "field_name": "string",
        "input_type": "string",
        "value": "string",
        "source": "generated/config file"
      }
    ]
  }
}
```

### GET /health

Health check endpoint returning application status.

## Project Structure

```
euporie/
├── main.py          # FastAPI application and endpoints
├── utils.py         # Helper functions and utilities
├── prompts.py       # GPT-4 prompt templates
├── llm.py           # OpenAI integration
├── requirements.txt # Project dependencies
└── .env             # Environment variables
```

## Error Handling

The API implements comprehensive error handling for:

- Invalid input formats
- Missing required fields
- Failed API calls
- Image processing errors
- XML parsing failures

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
````
