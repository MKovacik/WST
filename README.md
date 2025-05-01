# Chat with LM Studio

A web application that provides a chat interface for LM Studio with RAG (Retrieval-Augmented Generation) capabilities.

## Features

- Interactive chat interface with LM Studio
- PDF document upload and processing
- RAG-based context retrieval
- Configurable model parameters
- Real-time syntax highlighting for code
- CSRF protection and rate limiting
- Comprehensive logging system

## Tech Stack

- **Backend**:
  - Flask 2.0.1
  - PyPDF 5.4.0
  - Transformers 4.36+
  - scikit-learn 1.3+
  - NumPy 1.24+
  - PyTorch 2.6+

- **Frontend**:
  - TypeScript
  - highlight.js
  - Modern CSS with Flexbox

## Prerequisites

- Python 3.8+
- Node.js 14+
- LM Studio running locally

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd WST
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Node.js dependencies:
   ```bash
   npm install
   ```

5. Build TypeScript files:
   ```bash
   npm run build
   ```

## Configuration

1. Make sure LM Studio is running locally on port 1234 (default)
2. The application uses the following default settings:
   - Max file size: 16MB
   - Rate limits:
     - Chat: 30 requests per minute
     - File upload: 10 requests per hour
   - Default model parameters can be configured through the UI

## Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Access the application at `http://localhost:5000`

## Development

- TypeScript source files are in `static/js/src/`
- Run `npm run watch` for continuous TypeScript compilation
- Run tests with `pytest tests/`

## Project Structure

```
WST/
├── app.py              # Main Flask application
├── rag_engine.py       # RAG implementation
├── logging_config.py   # Logging configuration
├── requirements.txt    # Python dependencies
├── package.json       # Node.js dependencies
├── tsconfig.json      # TypeScript configuration
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── src/       # TypeScript source files
│       └── dist/      # Compiled JavaScript
├── templates/
│   └── index.html
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── logs/              # Application logs
└── uploads/           # Uploaded files (gitignored)
```

## Security Features

- CSRF protection for all forms and API endpoints
- Rate limiting to prevent abuse
- Secure file upload handling
- Input validation and sanitization
- Proper error handling and logging

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Logging

Logs are stored in the `logs` directory:
- `app.log`: General application logs
- `error.log`: Error logs
- `api.log`: API request logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here]
