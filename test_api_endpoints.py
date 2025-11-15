from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_report(monkeypatch):
  with patch('app.api.routes.ai_classifier.classify_urban_issue', return_value={
    'severity': 5,
    'safety_risk': False,
    'estimated_affected_people': 10,
    'issue_type': 'pothole'
  }):
    response = client.post('/api/reports', json={
      'image_url': 'https://supabase.test/image.jpg',
      'location_lat': 25.2,
      'location_lng': 55.27,
      'user_id': 'user-1',
      'description': 'Test'
    })
    assert response.status_code == 201


def test_report_validation():
  response = client.post('/api/reports', json={})
  assert response.status_code in {400, 422}


def test_rate_limit(monkeypatch):
  for _ in range(3):
    client.get('/api/reports')
