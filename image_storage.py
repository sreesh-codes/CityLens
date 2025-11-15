from __future__ import annotations

import base64
import io
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException, UploadFile, status
from PIL import Image


class SupabaseImageStorage:
    """Handle image uploads to Supabase Storage."""

    def __init__(self, bucket_name: str = 'citylens-images') -> None:
        self.bucket_name = bucket_name
        self._supabase = None
        self._use_local_fallback = False
        self._local_dir: Optional[Path] = None
        supabase_url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_KEY')

        if not supabase_url or not service_key:
            print('Supabase credentials missing. Using local base64 storage.')
            self._use_local_fallback = True
            uploads_dir = Path(__file__).resolve().parents[2] / 'uploads'
            uploads_dir.mkdir(parents=True, exist_ok=True)
            self._local_dir = uploads_dir
            return

        try:
            from supabase import create_client  # type: ignore import-time optional

            self._supabase = create_client(supabase_url, service_key)
            self._ensure_bucket_exists()
        except Exception as exc:  # pragma: no cover - defensive
            print(f'Failed to initialize Supabase storage: {exc}')
            self._supabase = None
            self._use_local_fallback = True

    @property
    def client(self):
        if not self._supabase:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Supabase storage is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.',
            )
        return self._supabase

    def _ensure_bucket_exists(self) -> None:
        try:
            buckets = self.client.storage.list_buckets()
            if not any(bucket.name == self.bucket_name for bucket in buckets):
                self.client.storage.create_bucket(self.bucket_name, options={'public': True})
                print(f'Created Supabase bucket: {self.bucket_name}')
        except Exception as exc:  # pragma: no cover - defensive
            print(f'Bucket setup failed: {exc}')

    async def upload_image(self, file: UploadFile) -> dict[str, Any]:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Empty image file.')

        optimized = self._optimize_image(contents)
        extension = (file.filename.split('.')[-1] if file.filename else 'jpg').lower()
        filename = f'{uuid.uuid4()}.{extension}'
        now = datetime.utcnow()
        file_path = f'reports/{now.year}/{now.month}/{filename}'

        if self._use_local_fallback:
            if not self._local_dir:
                raise HTTPException(status_code=500, detail='Local storage directory unavailable')
            local_file = self._local_dir / filename
            local_file.write_bytes(optimized)
            data_url = f"data:{file.content_type or 'image/jpeg'};base64,{base64.b64encode(optimized).decode()}"
            return {
                'url': data_url,
                'path': str(local_file),
                'bucket': 'local',
                'size': len(optimized),
                'content_type': file.content_type or 'image/jpeg',
            }

        try:
            self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=optimized,
                file_options={
                    'content-type': file.content_type or 'image/jpeg',
                    'cache-control': '3600',
                    'upsert': 'false',
                },
            )
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Image upload failed: {exc}')

        public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
        return {
            'url': public_url,
            'path': file_path,
            'bucket': self.bucket_name,
            'size': len(optimized),
            'content_type': file.content_type or 'image/jpeg',
        }

    async def delete_image(self, file_path: str) -> bool:
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as exc:  # pragma: no cover - defensive
            print(f'Failed to delete image: {exc}')
            return False

    def _optimize_image(self, image_bytes: bytes, max_size: tuple[int, int] = (1920, 1920), quality: int = 85) -> bytes:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background

            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            return output.read()
        except Exception as exc:  # pragma: no cover - defensive
            print(f'Image optimization failed: {exc}')
            return image_bytes


image_storage = SupabaseImageStorage()


async def upload_report_image(file: UploadFile) -> str:
    result = await image_storage.upload_image(file)
    return result['url']

