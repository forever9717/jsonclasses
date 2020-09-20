"""module for index validator."""
from typing import Any
from ..config import Config
from .validator import Validator


class IndexValidator(Validator):

    def validate(self, value: Any, key_path: str, root: Any, all_fields: bool, config: Config) -> None:
        pass
