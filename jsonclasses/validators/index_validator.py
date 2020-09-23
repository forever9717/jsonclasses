"""module for index validator."""
from .validator import Validator
from ..fields import FieldDescription


class IndexValidator(Validator):
    """Index validator implies this column should be indexed in database."""

    def define(self, field_description: FieldDescription) -> None:
        field_description.index = True
