from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class Issue(BaseModel):
    id: str
    description: str
    category: str
    location: Optional[List[float]] = None
    image_url: Optional[HttpUrl] = None
    status: str = "pending"
