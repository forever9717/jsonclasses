"""module for positive validator."""
from ..exceptions import ValidationException
from .validator import Validator
from ..ctx import Ctx


class PositiveValidator(Validator):
    """Positive validator marks value valid for large than zero."""

    def validate(self, ctx: Ctx) -> None:
        if ctx.value is None:
            return ctx.value
        if ctx.value <= 0:
            kp = ctx.keypath_root
            v = ctx.value
            raise ValidationException(
                {kp: f'Value \'{v}\' at \'{kp}\' should be positive.'},
                ctx.root
            )
