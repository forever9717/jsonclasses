"""module for outputvalue validator."""
from ..field_definition import FieldDefinition, EnumOutput
from .validator import Validator


class OutputValueValidator(Validator):
    """Output value validator tweaks enum validator's behavior."""

    def define(self, fdef: FieldDefinition) -> None:
        fdef.enum_output = EnumOutput.VALUE
