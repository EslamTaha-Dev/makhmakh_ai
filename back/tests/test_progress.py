from unittest.mock import Mock

def test_mock_update_progress():
    mock_progress_service = Mock()
    
    mock_progress_service.update_status.return_value = {"status": "completed", "progress": 100}
    
    result = mock_progress_service.update_status(user_id=1, course_id=101)
    
    assert result["status"] == "completed"
    assert result["progress"] == 100