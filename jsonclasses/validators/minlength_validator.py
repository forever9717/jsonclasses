"""module for minlength validator."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..exceptions import ValidationException
from .validator import Validator
if TYPE_CHECKING:
    from ..ctx import Ctx


class MinlengthValidator(Validator):
    """Minlength validator validates value against min length."""

    def __init__(self, minlength: int) -> None:
        self.minlength = minlength

    def validate(self, ctx: Ctx) -> None:
        if ctx.value is None:
            return
        if len(ctx.value) < self.minlength:
            raise ValidationException(
                {ctx.keypath_root: f'Length of value \'{ctx.value}\' at \'{ctx.keypath_root}\' should not be less than {self.minlength}.'},
                ctx.root
            )
