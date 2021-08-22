"""module for enum validator."""
from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING
from enum import Enum
from ..fdef import (FieldType, Fdef, EnumInput,
                                EnumOutput)
from ..exceptions import ValidationException
from .validator import Validator
if TYPE_CHECKING:
    from ..ctx import Ctx


class EnumValidator(Validator):
    """Enum validator validates value against provided enum type."""

    def __init__(self, enum_or_name: Union[type[Enum], str]):
        super().__init__()
        self.enum_or_name = enum_or_name

    def define(self, fdef: Fdef) -> None:
        fdef._field_type = FieldType.ENUM
        fdef._raw_enum_class = self.enum_or_name
        if fdef.enum_input is None:
            fdef._enum_input = EnumInput.NAME
        if fdef.enum_output is None:
            fdef._enum_output = EnumOutput.NAME
        return

    def transform(self, ctx: Ctx) -> Any:
        if ctx.value is None:
            return None
        if isinstance(self.enum_or_name, str):
            jconf = ctx.cdefowner.jconf
            enum_class = jconf.cgraph.fetch_enum(self.enum_or_name)
        else:
            enum_class = self.enum_or_name
        if isinstance(ctx.value, enum_class):
            return ctx.value
        enum_input = ctx.fdef.enum_input
        if enum_input.__contains__(EnumInput.VALUE):
            try:
                return enum_class(ctx.value)
            except ValueError:
                pass
        elif isinstance(ctx.value, str):
            if enum_input.__contains__(EnumInput.NAME):
                try:
                    return enum_class[ctx.value]
                except KeyError:
                    pass
            if enum_input.__contains__(EnumInput.LOWERCASE_NAME):
                try:
                    return enum_class[ctx.value.upper()]
                except KeyError:
                    pass

            raise ValidationException({
                '.'.join([str(k) for k in ctx.keypathr]): 'unknown enum value'
            }, ctx.root)
        else:
            raise ValidationException({
                '.'.join([str(k) for k in ctx.keypathr]): 'unknown enum value'
            }, ctx.root)

    def validate(self, ctx: Ctx) -> None:
        if ctx.value is None:
            return None
        if isinstance(self.enum_or_name, str):
            jconf = ctx.cdefowner.jconf
            enum_class = jconf.cgraph.fetch_enum(self.enum_or_name)
        else:
            enum_class = self.enum_or_name
        if not isinstance(ctx.value, enum_class):
            raise ValidationException({
                '.'.join([str(k) for k in ctx.keypathr]): 'invalid enum value'
            }, ctx.root)

    def tojson(self, ctx: Ctx) -> Any:
        if ctx.value is None:
            return None
        if ctx.fdef.enum_output == EnumOutput.VALUE:
            return ctx.value.value
        elif ctx.fdef.enum_output == EnumOutput.NAME:
            return ctx.value.name
        elif ctx.fdef.enum_output == EnumOutput.LOWERCASE_NAME:
            return ctx.value.name.lower()
