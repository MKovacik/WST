import pytest
import json
import os
from werkzeug.datastructures import FileStorage
from io import BytesIO

def test_home_page(client):
    """Test that the home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Chat with LM Studio' in response.data

def test_model_info(client, requests_mock):
    """Test the model info endpoint"""
    # Mock the LM Studio API response
    mock_response = {
        'data': [{
            'id': 'test-model',
            'context_length': 4096
        }]
    }
    requests_mock.get('http://127.0.0.1:1234/v1/models', json=mock_response)
    
    response = client.get('/model-info')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'model_name' in data
    assert 'context_window' in data

def test_upload_no_file(client):
    """Test file upload with no file"""
    response = client.post('/upload')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'No file part'

def test_upload_empty_file(client):
    """Test file upload with empty filename"""
    response = client.post('/upload', data={
        'file': (BytesIO(), '')
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'No selected file'

def test_upload_invalid_file_type(client):
    """Test file upload with invalid file type"""
    response = client.post('/upload', data={
        'file': (BytesIO(b'test content'), 'test.txt')
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'File type not allowed'

def test_upload_valid_pdf(client, tmp_path):
    """Test successful PDF upload"""
    # Create a minimal valid PDF file
    pdf_content = b'''%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
167
%%EOF'''
    
    response = client.post('/upload', data={
        'file': (BytesIO(pdf_content), 'test.pdf')
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'File uploaded successfully'

def test_chat_empty_message(client):
    """Test chat endpoint with empty message"""
    response = client.post('/chat', json={
        'message': ''
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_chat_valid_message(client, requests_mock):
    """Test chat endpoint with valid message"""
    # Mock the LM Studio API response
    mock_response = {
        'choices': [{
            'message': {
                'content': 'Test response'
            }
        }]
    }
    requests_mock.post('http://127.0.0.1:1234/v1/chat/completions', json=mock_response)
    
    response = client.post('/chat', json={
        'message': 'Hello'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'response' in data

def test_rate_limiting(client):
    """Test rate limiting"""
    # Make requests until we hit the rate limit
    for _ in range(31):  # Our limit is 30 per minute for chat
        client.post('/chat', json={'message': 'test'})
    
    # The next request should fail
    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 429
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Rate limit exceeded'
