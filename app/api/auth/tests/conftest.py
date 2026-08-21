from datetime import datetime
from uuid import UUID

import pytest

from app.db import User


@pytest.fixture
def user() -> User:
    return User(
        id=UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5"),
        email="some@example.com",
        name="name",
        surname="surname",
        hashed_password="hashed_password",
        created_at=datetime(2020, 1, 20),
    )
