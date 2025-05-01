from flask import Flask, render_template, request, jsonify, url_for, session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
import re
from rag_engine import RAGEngine
from markdown2 import Markdown
import json
from werkzeug.utils import secure_filename
import time
from logging_config import setup_logging

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)  # for session management
csrf = CSRFProtect(app)  # Initialize CSRF protection

# Set up logging
api_logger = setup_logging(app)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

markdown = Markdown(extras=['fenced-code-blocks', 'tables', 'break-on-newline'])

# LM Studio API endpoints
API_BASE = "http://127.0.0.1:1234/v1"
API_URL = f"{API_BASE}/chat/completions"
MODEL_INFO_URL = f"{API_BASE}/models"

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant with access to specific document knowledge. 
Format your responses using Markdown for better readability:
- Use **bold** for emphasis
- Use `code` for technical terms
- Use bullet points for lists
- Use numbered lists for steps
- Use headings when organizing information
- Use tables when comparing data
- Use code blocks with language specification for code
- Use > for quotes from the documents

When referencing information from documents, be clear but natural. Focus on accuracy and clarity."""

# Default LLM settings
DEFAULT_CONFIG = {
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 0.95,
    "context_chunks": 3
}

# Initialize RAG engine
rag = RAGEngine()

# File upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def before_request():
    """Log API request details"""
    if request.path.startswith('/api/'):
        api_logger.info(
            f"Request: {request.method} {request.path} - "
            f"Client: {request.remote_addr} - "
            f"User Agent: {request.user_agent}"
        )

@app.after_request
def after_request(response):
    """Log API response details"""
    if request.path.startswith('/api/'):
        api_logger.info(
            f"Response: {request.method} {request.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {time.time() - request.start_time:.2f}s"
        )
    return response

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    app.logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.path}")
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429

@app.errorhandler(Exception)
def handle_exception(e):
    """Log unhandled exceptions"""
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify(error="Internal server error"), 500

@app.route('/')
def home():
    # Initialize session variables if they don't exist
    for key, value in DEFAULT_CONFIG.items():
        if key not in session:
            session[key] = value
    
    return render_template('index.html', config=session)

@app.route('/model-info', methods=['GET'])
@limiter.limit("10 per minute")
def get_model_info():
    """Get information about the currently loaded model"""
    try:
        # Get model info from LM Studio
        print("\n=== Fetching Model Info ===")
        response = requests.get(MODEL_INFO_URL)
        response.raise_for_status()
        data = response.json()
        
        print("\nAPI Response from /models:")
        print(json.dumps(data, indent=2))
        
        # Extract model info from response
        models = data.get('data', [])
        if not models:
            raise ValueError("No models found in response")
            
        model = models[0]  # Get the first (active) model
        model_id = model.get('id')
        
        if not model_id:
            raise ValueError("Model ID not found in response")
            
        # Try to get more detailed model info
        detail_url = f"{MODEL_INFO_URL}/{model_id}"
        print(f"\nFetching detailed model info from: {detail_url}")
        
        detail_response = requests.get(detail_url)
        if detail_response.ok:
            model_details = detail_response.json()
            print("\nModel details response:")
            print(json.dumps(model_details, indent=2))
            
            # Try to get context length from model details
            context_length = None
            
            # First try to get it from model details
            if model_details:
                context_length = (
                    model_details.get('context_length') or
                    model_details.get('max_context_length') or
                    model_details.get('max_tokens') or
                    model_details.get('context_window')
                )
            
            # If not found in details, try the original model info
            if not context_length:
                context_length = (
                    model.get('context_length') or
                    model.get('max_context_length') or
                    model.get('max_tokens') or
                    model.get('context_window')
                )
            
            # If still not found, try to detect from model capabilities
            if not context_length:
                print("\nTesting model capabilities...")
                test_response = requests.post(API_URL, json={
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 32000
                })
                
                if test_response.ok:
                    print("\nTest response:")
                    print(json.dumps(test_response.json(), indent=2))
                else:
                    print("\nTest response error:")
                    print(test_response.text)
                    
                    # Try to extract context length from error message
                    error_msg = test_response.json().get('error', {}).get('message', '')
                    print(f"\nError message: {error_msg}")
                    
                    import re
                    limit_match = re.search(r'maximum context length is (\d+)', error_msg)
                    if limit_match:
                        context_length = int(limit_match.group(1))
                        print(f"\nExtracted context length from error: {context_length}")
            
            # If we still don't have a context length, use model-specific defaults
            if not context_length:
                model_id_lower = model_id.lower()
                if 'phi-2' in model_id_lower:
                    context_length = 2048
                elif 'phi-4' in model_id_lower:
                    context_length = 16384
                elif 'llama' in model_id_lower:
                    context_length = 4096
                elif 'mistral' in model_id_lower:
                    context_length = 8192
                elif 'mixtral' in model_id_lower:
                    context_length = 32768
                else:
                    # Try one more test with a common limit
                    test_response = requests.post(API_URL, json={
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 16384
                    })
                    if test_response.ok:
                        context_length = 16384
                    else:
                        context_length = 2048  # Conservative fallback
            
            model_params = {
                'model_name': model_id,
                'context_window': context_length,
                'max_tokens': context_length,
                'raw_api_response': {
                    'model_list': data,
                    'model_details': model_details
                }
            }
            
            print("\nFinal model parameters:")
            print(json.dumps(model_params, indent=2))
            return jsonify(model_params)
            
        else:
            raise ValueError(f"Failed to get model details: {detail_response.text}")
            
    except Exception as e:
        error_response = {
            'error': str(e),
            'model_name': 'Unknown Model',
            'context_window': 2048,  # Default fallback
            'max_tokens': 2048  # Default fallback
        }
        print("\nError response:")
        print(json.dumps(error_response, indent=2))
        return jsonify(error_response)

@app.route('/processed-files', methods=['GET'])
@limiter.limit("10 per minute")
def get_processed_files():
    """Get list of processed files"""
    return jsonify(rag.get_processed_files())

@app.route('/save-config', methods=['POST'])
@limiter.limit("10 per minute")
def save_config():
    """Save configuration"""
    data = request.json
    valid_keys = DEFAULT_CONFIG.keys()
    
    # Update only valid configuration keys
    updated = False
    for key in valid_keys:
        if key in data:
            # Convert numeric values to their proper type
            if key in ['temperature', 'top_p']:
                session[key] = float(data[key])
            elif key in ['max_tokens', 'context_chunks']:
                session[key] = int(data[key])
            else:
                session[key] = data[key]
            updated = True
    
    if updated:
        return jsonify({"status": "success", "message": "Configuration saved successfully"})
    else:
        return jsonify({"status": "error", "message": "No valid configuration data provided"}), 400

@app.route('/reset-config', methods=['POST'])
@limiter.limit("10 per minute")
def reset_config():
    """Reset configuration to defaults"""
    for key, value in DEFAULT_CONFIG.items():
        session[key] = value
    
    return jsonify({
        "status": "success", 
        "message": "Configuration reset to defaults",
        "config": DEFAULT_CONFIG
    })

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per hour")  # Strict limit for file uploads
def upload_file():
    start_time = time.time()
    try:
        app.logger.info(f"Processing file upload from {request.remote_addr}")
        
        if 'file' not in request.files:
            app.logger.warning("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            app.logger.warning("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            app.logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'File type not allowed'}), 400
        
        filename = secure_filename(file.filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file with RAG engine
        rag.add_pdf(filepath)
        
        app.logger.info(
            f"File upload processed successfully. "
            f"Filename: {filename}, "
            f"Duration: {time.time() - start_time:.2f}s"
        )
        
        return jsonify({'message': 'File uploaded successfully'})
        
    except Exception as e:
        app.logger.error(
            f"Error processing file upload: {str(e)}", 
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
@limiter.limit("30 per minute")  # Stricter limit for chat endpoint
def chat():
    start_time = time.time()
    user_message = request.json.get('message', '')
    
    try:
        app.logger.info(f"Processing chat request from {request.remote_addr}")
        
        if not user_message:
            app.logger.warning("Empty message received")
            return jsonify({"error": "Message is required"}), 400
        
        # Get relevant context using RAG
        context_chunks = session.get('context_chunks', DEFAULT_CONFIG['context_chunks'])
        context = rag.get_context_for_query(user_message, k=context_chunks)
        
        # Get the system prompt from session or use default
        system_prompt = session.get('system_prompt', DEFAULT_CONFIG['system_prompt'])
        
        # Add context to the system prompt
        full_system_prompt = system_prompt + "\n\nContext:\n" + context
        
        # Get LLM settings from session or use defaults
        temperature = session.get('temperature', DEFAULT_CONFIG['temperature'])
        max_tokens = session.get('max_tokens', DEFAULT_CONFIG['max_tokens'])
        top_p = session.get('top_p', DEFAULT_CONFIG['top_p'])
        
        # Prepare the request to LM Studio API with context
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        ai_message = response.json()['choices'][0]['message']['content']
        # Convert markdown to HTML
        html_response = markdown.convert(ai_message)
        app.logger.info(
            f"Chat request processed successfully. "
            f"Duration: {time.time() - start_time:.2f}s"
        )
        return jsonify({"response": html_response})
        
    except requests.RequestException as e:
        app.logger.error(f"API request error: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to communicate with LLM API"}), 503
    except Exception as e:
        app.logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
