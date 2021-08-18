"""module for deny validator."""
from ..field_definition import FieldDefinition, DeleteRule
from .validator import Validator


class DenyValidator(Validator):
    """Deny validator marks a relationship's delete rule as deny."""

    def define(self, fdef: FieldDefinition) -> None:
        fdef.delete_rule = DeleteRule.DENY
