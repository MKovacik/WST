import pytest
import os
import tempfile
from app import app as flask_app
from rag_engine import RAGEngine

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF tokens in tests
        'UPLOAD_FOLDER': tempfile.mkdtemp()  # Use temporary directory for uploads
    })
    
    yield flask_app
    
    # Cleanup after tests
    if os.path.exists(flask_app.config['UPLOAD_FOLDER']):
        for file in os.listdir(flask_app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(flask_app.config['UPLOAD_FOLDER'], file))
        os.rmdir(flask_app.config['UPLOAD_FOLDER'])

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def rag():
    return RAGEngine()
