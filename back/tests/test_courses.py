from unittest.mock import Mock

def test_mock_get_courses():
    mock_course_service = Mock()
    
    mock_course_service.get_all_courses.return_value = [{"id": 1, "title": "مقدمة في البرمجة"}]
    
    courses = mock_course_service.get_all_courses()
    
    assert len(courses) == 1
    assert courses[0]["title"] == "مقدمة في البرمجة"