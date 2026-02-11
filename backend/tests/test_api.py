
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure import of server works
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import app

client = TestClient(app)

def test_read_root():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "message": "TahalilAI Backend is running"}

@patch("server.analyze_image")
def test_analyze_flow(mock_analyze_image):
    """
    Test the full flow:
    1. Upload file
    2. Receive job_id
    3. Poll status until complete
    """
    # Mock the AI return value
    expected_analysis = "Mocked AI Analysis Result"
    mock_analyze_image.return_value = expected_analysis

    # Create dummy file
    file_content = b"fake image content"
    files = {"file": ("test.png", file_content, "image/png")}
    data = {"age": "25", "gender": "male"}

    # 1. Start Analysis
    response = client.post("/analyze", files=files, data=data)
    assert response.status_code == 200
    json_resp = response.json()
    
    assert json_resp["status"] == "queued"
    assert "job_id" in json_resp
    job_id = json_resp["job_id"]

    # 2. Check Status (It might be processing or completed instantly depending on thread speed)
    # Since TestClient runs in the same process, BackgroundTasks might run synchronously or very fast.
    # In TestClient, BackgroundTasks are executed after the response is sent.
    
    # We poll status
    status_resp = client.get(f"/status/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    
    # It should be completed because TestClient executes background tasks
    assert status_data["status"] == "completed"
    assert status_data["result"]["analysis"] == expected_analysis
    
    # Verify mock was called with correct args
    args, kwargs = mock_analyze_image.call_args
    # args[0] is file path
    assert "test.png" in args[0] 
    assert kwargs.get("age") == "25" or args[1] == "25" # depending on how it was called
    assert kwargs.get("gender") == "male" or args[2] == "male"

def test_get_nonexistent_job():
    response = client.get("/status/fake-job-id")
    assert response.status_code == 200
    assert response.json() == {"status": "not_found"}
