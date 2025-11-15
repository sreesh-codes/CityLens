from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_full_report_flow():
  with patch('app.api.routes.upload_image_to_cloudinary', new=AsyncMock(return_value='https://cdn/test.jpg')):
    create = client.post(
      '/api/reports',
      files={'image': ('test.jpg', b'sample-bytes', 'image/jpeg')},
      data={'location_lat': 25.2, 'location_lng': 55.27, 'user_id': 'user-1'},
    )
    assert create.status_code == 201
    report_id = create.json()['id']
    detail = client.get(f'/api/reports/{report_id}')
    assert detail.status_code == 200
