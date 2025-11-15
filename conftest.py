import asyncio
from collections import defaultdict
from datetime import datetime
from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import reports_store, comments_store


@pytest.fixture(autouse=True)
def clear_stores():
  reports_store.clear()
  comments_store.clear()


@pytest.fixture
async def sample_report_payload(tmp_path):
  class DummyFile:
    def __init__(self, content):
      self.content = content
      self.filename = 'sample.jpg'

    async def read(self):
      return self.content
  return {
    'image': DummyFile(b'sample-bytes'),
    'location_lat': 25.2,
    'location_lng': 55.27,
    'description': 'Test issue',
    'user_id': 'user-test',
  }


@pytest.fixture
async def client() -> AsyncIterator[TestClient]:
  with TestClient(app) as c:
    yield c
