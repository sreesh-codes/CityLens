from __future__ import annotations

import io
from typing import Dict

import cloudinary
import cloudinary.uploader
import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status
from loguru import logger
from PIL import Image

MAX_WIDTH = 1920
TARGET_SIZE_BYTES = 500 * 1024
CLOUDINARY_FOLDER = 'citylens/uploads'


async def optimize_image(file: UploadFile) -> bytes:
  try:
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
  except Exception as exc:  # noqa: BLE001
    logger.error('Failed to read image: {}', exc)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid image file') from exc

  image = image.convert('RGB')
  width, height = image.size
  if width > MAX_WIDTH:
    ratio = MAX_WIDTH / float(width)
    new_height = int(height * ratio)
    image = image.resize((MAX_WIDTH, new_height), Image.LANCZOS)

  buffer = io.BytesIO()
  quality = 95
  while True:
    buffer.seek(0)
    image.save(buffer, format='WEBP', quality=quality, method=6)
    size = buffer.tell()
    if size <= TARGET_SIZE_BYTES or quality <= 40:
      break
    quality -= 5

  return buffer.getvalue()


async def extract_metadata(file: UploadFile) -> Dict[str, str | float | bool]:
  contents = await file.read()
  np_image = np.frombuffer(contents, dtype=np.uint8)
  image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
  if image is None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unable to decode image')

  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  mean_brightness = float(np.mean(gray))
  laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
  too_dark = mean_brightness < 50
  blurry = laplacian_var < 20

  return {
    'capture_timestamp': file.headers.get('x-photo-timestamp', ''),
    'mean_brightness': mean_brightness,
    'sharpness_score': laplacian_var,
    'too_dark': too_dark,
    'blurry': blurry,
    'quality_score': max(0.0, min(1.0, (mean_brightness / 255) * (laplacian_var / 100))),
  }


async def upload_to_cloudinary(image_bytes: bytes) -> str:
  try:
    response = cloudinary.uploader.upload(
      image_bytes,
      folder=CLOUDINARY_FOLDER,
      resource_type='image',
      format='webp',
      transformation=[{'width': 1200, 'crop': 'limit'}],
      eager=[{'width': 200, 'crop': 'fill'}, {'width': 500, 'crop': 'fill'}],
    )
  except Exception as exc:  # noqa: BLE001
    logger.error('Cloudinary upload failed: {}', exc)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Failed to upload image') from exc

  return response['secure_url']


async def blur_faces(image_url: str) -> str:
  try:
    data = cloudinary.CloudinaryImage(image_url).download()
    np_image = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    for (x, y, w, h) in faces:
      roi = image[y:y + h, x:x + w]
      blurred = cv2.GaussianBlur(roi, (51, 51), 0)
      image[y:y + h, x:x + w] = blurred
    _, buffer = cv2.imencode('.webp', image)
    return await upload_to_cloudinary(buffer.tobytes())
  except Exception as exc:  # noqa: BLE001
    logger.error('Face blurring failed: {}', exc)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Face blurring failed') from exc
