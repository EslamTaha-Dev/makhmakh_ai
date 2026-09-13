from unittest.mock import Mock

def test_mock_login():
    mock_auth_service = Mock()
    
    mock_auth_service.verify_password.return_value = True
    
    is_valid = mock_auth_service.verify_password("my_secret_password")
    
    assert is_valid is True