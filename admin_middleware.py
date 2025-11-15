from __future__ import annotations

from functools import wraps
from typing import Awaitable, Callable, TypeVar

from fastapi import HTTPException, Request, status

Handler = TypeVar('Handler', bound=Callable[..., Awaitable])


def require_admin(handler: Handler) -> Handler:
  @wraps(handler)
  async def _wrapper(*args, **kwargs):
    request: Request | None = kwargs.get('request')
    if request is None:
      for arg in args:
        if isinstance(arg, Request):
          request = arg
          break
    if request is None:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Missing request context')

    user_role = request.headers.get('x-user-role')
    if user_role not in {'admin', 'municipality'}:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Admin role required')

    return await handler(*args, **kwargs)

  return _wrapper  # type: ignore[return-value]
