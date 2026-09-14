from unittest.mock import patch

@patch('app.ai.generate_response', create=True) 
def test_mock_ai_chat(mock_ai):
    mock_ai.return_value = "أهلاً بيك! أنا الذكاء الاصطناعي المزيف الخاص بالاختبارات."
    
    result = mock_ai("اشرح لي درس الرياضيات؟")
    
    assert result == "أهلاً بيك! أنا الذكاء الاصطناعي المزيف الخاص بالاختبارات."