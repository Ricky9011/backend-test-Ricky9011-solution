import re
from uuid import UUID

from ulid import ULID


def to_snake_case(string: str) -> str:
    result = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", result).lower()


def generate_ulid() -> UUID:
    return ULID().to_uuid4()
