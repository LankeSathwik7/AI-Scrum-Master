import pytest
from unittest.mock import Mock
from ui.dashboard import process_blockers

def test_blocker_fetch():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "Blocker: API Issue", "desc": "Critical problem"},
        {"name": "Regular Task", "desc": "Normal work"}
    ]
    
    result = process_blockers(mock_response)
    assert result == 1  # Only 1 blocker

def test_empty_response():
    mock_response = Mock()
    mock_response.status_code = 204
    result = process_blockers(mock_response)
    assert result == 0