"""module for assigning operator validator."""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from inspect import signature
from ..exceptions import ValidationException
from ..fdef import Fdef
from .validator import Validator
if TYPE_CHECKING:
    from ..ctx import Ctx


class AsopValidator(Validator):
    """Assigning operator validator assigns the transfromed operator to the
    current field.
    """

    def __init__(self, transformer: Callable) -> None:
        if not callable(transformer):
            raise ValueError('asop transformer is not callable')
        params_len = len(signature(transformer).parameters)
        if params_len > 3 or params_len < 1:
            raise ValueError('not a valid asop transformer')
        self.transformer = transformer

    def define(self, fdef: Fdef) -> None:
        fdef._requires_operator_assign = True
        fdef._operator_assign_transformer = self.transformer

    def validate(self, ctx: Ctx) -> None:
        if ctx.owner.is_new or ctx.keypath_owner in ctx.owner.modified_fields:
            if ctx.value is None:
                raise ValidationException(
                    keypath_messages={
                        ctx.keypath_root: "no operator being assigned"},
                    root=ctx.root)
