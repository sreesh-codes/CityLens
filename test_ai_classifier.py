from unittest.mock import patch

from app.services import ai_classifier


@patch('app.services.ai_classifier.OpenAI')
def test_classify_success(mock_client):
  instance = mock_client.return_value
  instance.responses.create.return_value.output = [type('obj', (), {'content': [{'text': '{"issue_type": "pothole", "severity": 8, "confidence": 0.9, "description": "Test", "safety_risk": true, "estimated_affected_people": 100, "recommended_action": "Fix"}'}]})]
  result = ai_classifier.classify_urban_issue('https://example.com/image')
  assert result['issue_type'] == 'pothole'

@patch('app.services.ai_classifier.OpenAI')
def test_low_confidence(mock_client):
  instance = mock_client.return_value
  instance.responses.create.return_value.output = [type('obj', (), {'content': [{'text': '{"issue_type": "pothole", "severity": 8, "confidence": 0.1, "description": "Test", "safety_risk": false, "estimated_affected_people": 10, "recommended_action": "Fix"}'}]})]
  result = ai_classifier.classify_urban_issue('https://example.com/image')
  assert result['issue_type'] == 'unclear_issue'
