"""module for instanceof validator."""
from __future__ import annotations
from typing import Any, Sequence, Type, Union, cast, TYPE_CHECKING
from ..fields import (Field, FieldDescription, FieldStorage, FieldType,
                      Nullability, WriteRule, ReadRule, Strictness, fields,
                      is_reference_field)
from ..exceptions import ValidationException
from .validator import Validator
from ..keypath import concat_keypath
from ..types_resolver import resolve_types
from ..contexts import ValidatingContext, TransformingContext, ToJSONContext
if TYPE_CHECKING:
    from ..json_object import JSONObject
    from ..types import Types
    InstanceOfType = Union[Types, str, Type[JSONObject]]


class InstanceOfValidator(Validator):
    """InstanceOf validator validates and transforms JSON Class instance."""

    def __init__(self, raw_type: InstanceOfType) -> None:
        self.raw_type = raw_type

    def define(self, fdesc: FieldDescription) -> None:
        fdesc.field_type = FieldType.INSTANCE
        fdesc.instance_types = self.raw_type

    def validate(self, context: ValidatingContext) -> None:
        from ..json_object import JSONObject
        from ..orm_object import ORMObject
        if context.value is None:
            return
        types = resolve_types(self.raw_type, context.config_owner.linked_class)
        cls = cast(Type[JSONObject], types.fdesc.instance_types)
        all_fields = context.all_fields
        if all_fields is None:
            all_fields = cls.config.validate_all_fields
        if not isinstance(context.value, cls):
            raise ValidationException({
                context.keypath_root: (f"Value at '{context.keypath_root}' "
                                       f"should be instance of "
                                       f"'{cls.__name__}'.")
            }, context.root)
        primary_key = cast(str, cls.config.primary_key)
        try:
            id = cast(Union[str, int], getattr(context.value, primary_key))
            if id is not None:
                if context.lookup_map.fetch(cls.__name__, id):
                    return
                context.lookup_map.put(cls.__name__, id, context.value)
        except AttributeError:
            pass
        only_validate_modified = False
        modified_fields = []
        if isinstance(context.value, ORMObject) and not context.value.is_new:
            only_validate_modified = True
            modified_fields = list(context.value.modified_fields)
        keypath_messages = {}
        for field in fields(context.value):
            fname = field.field_name
            fd = field.fdesc
            bypass = False
            if fd.field_storage == FieldStorage.EMBEDDED:
                if only_validate_modified and fname not in modified_fields:
                    bypass = True
            if bypass:
                continue
            try:
                field.field_types.validator.validate(context.new(
                    value=getattr(context.value, fname),
                    keypath_root=concat_keypath(context.keypath_root, fname),
                    keypath_owner=fname,
                    owner=context.value,
                    config_owner=context.value.__class__.config,
                    keypath_parent=fname,
                    parent=context.value,
                    fdesc=field.fdesc))
            except ValidationException as exception:
                if all_fields:
                    keypath_messages.update(exception.keypath_messages)
                else:
                    raise exception
        if len(keypath_messages) > 0:
            raise ValidationException(
                keypath_messages=keypath_messages,
                root=context.root)

    def _strictness_check(self,
                          context: TransformingContext,
                          dest: JSONObject) -> None:
        if context.config_owner.camelize_json_keys:
            available_name_pairs = [(field.field_name, field.json_field_name)
                                    for field in fields(dest)]
            available_names = [e for pair in available_name_pairs for e in pair]
        else:
            available_names = [field.field_name for field in fields(dest)]
        for k in context.value.keys():
            if k not in available_names:
                raise ValidationException(
                    {context.keypath_root: f'Key \'{k}\' at \'{context.keypath_root}\' is not allowed.'},
                    context.root)

    def _fill_default_value(self,
                            field: Field,
                            dest: JSONObject,
                            context: TransformingContext,
                            cls: Type[JSONObject]):
        if field.assigned_default_value is not None:
            setattr(dest, field.field_name, field.assigned_default_value)
        else:
            tsfmd = field.field_types.validator.transform(context.new(
                value=None,
                keypath_root=concat_keypath(context.keypath_root, field.field_name),
                keypath_owner=field.field_name,
                owner=context.value,
                config_owner=cls.config,
                keypath_parent=field.field_name,
                parent=context.value,
                fdesc=field.fdesc))
            setattr(dest, field.field_name, tsfmd)

    def _has_field_value(self, field: Field, keys: Sequence[str]) -> bool:
        return field.json_field_name in keys or field.field_name in keys

    def _get_field_value(self,
                         field: Field,
                         context: TransformingContext) -> Any:
        field_value = context.value.get(field.json_field_name)
        if field_value is None and context.config_owner.camelize_json_keys:
            field_value = context.value.get(field.field_name)
        return field_value

    # pylint: disable=arguments-differ, too-many-locals, too-many-branches
    def transform(self, context: TransformingContext) -> Any:
        from ..types import Types
        from ..json_object import JSONObject
        # handle non normal value
        if context.value is None:
            return context.dest
        if not isinstance(context.value, dict):
            return context.dest if context.dest is not None else context.value
        # figure out types, cls and dest
        types = resolve_types(self.raw_type, context.config_owner.linked_class)
        cls = cast(Type[JSONObject], types.fdesc.instance_types)
        primary_key = cls.config.primary_key
        id = cast(Union[str, int], context.value.get(primary_key))
        soft_apply_mode = False
        if context.dest is not None:
            dest = context.dest
            if id is not None:
                context.lookup_map.put(cls.__name__, id, dest)
        elif id is not None:
            exist_item = context.lookup_map.fetch(cls.__name__, id)
            if exist_item is not None:
                dest = exist_item
                soft_apply_mode = True
            else:
                dest = cls()
                context.lookup_map.put(cls.__name__, id, dest)
        else:
            dest = cls()
        # strictness check
        strictness = cast(bool, cls.config.strict_input)
        if context.fdesc is not None:
            if context.fdesc.strictness == Strictness.STRICT:
                strictness = True
            elif context.fdesc.strictness == Strictness.UNSTRICT:
                strictness = False
        if strictness:
            self._strictness_check(context, dest)
        # fill values
        dict_keys = list(context.value.keys())
        nonnull_ref_lists: list[str] = []
        for field in fields(dest):
            if not self._has_field_value(field, dict_keys):
                if is_reference_field(field):
                    fdesc = field.fdesc
                    if fdesc.field_type == FieldType.LIST:
                        if fdesc.collection_nullability == Nullability.NONNULL:
                            nonnull_ref_lists.append(field.field_name)
                    pass
                elif context.fill_dest_blanks and not soft_apply_mode:
                    self._fill_default_value(field, dest, context, cls)
                continue
            field_value = self._get_field_value(field, context)
            allow_write_field = True
            if field.fdesc.write_rule == WriteRule.NO_WRITE:
                allow_write_field = False
            if field.fdesc.write_rule == WriteRule.WRITE_ONCE:
                cfv = getattr(dest, field.field_name)
                if (cfv is not None) and (not isinstance(cfv, Types)):
                    allow_write_field = False
            if field.fdesc.write_rule == WriteRule.WRITE_NONNULL:
                if field_value is None:
                    allow_write_field = False
            if not allow_write_field:
                if context.fill_dest_blanks:
                    self._fill_default_value(field, dest, context, cls)
                continue
            field_context = context.new(
                value=field_value,
                keypath_root=concat_keypath(context.keypath_root,
                                            field.field_name),
                keypath_owner=field.field_name,
                owner=context.value,
                config_owner=cls.config,
                keypath_parent=field.field_name,
                parent=context.value,
                fdesc=field.fdesc)
            tsfmd = field.field_types.validator.transform(field_context)
            setattr(dest, field.field_name, tsfmd)
        for cname in nonnull_ref_lists:
            if getattr(dest, cname) is None:
                setattr(dest, cname, [])
        return dest

    def tojson(self, context: ToJSONContext) -> Any:
        if context.value is None:
            return None
        retval = {}
        entity_chain = context.entity_chain
        cls_name = context.value.__class__.__name__
        no_key_refs = cls_name in entity_chain
        for field in fields(context.value):
            field_value = getattr(context.value, field.field_name)
            fd = field.field_types.fdesc
            jf_name = field.json_field_name
            ignore_writeonly = context.ignore_writeonly
            if fd.field_storage == FieldStorage.LOCAL_KEY and no_key_refs:
                continue
            if fd.field_storage == FieldStorage.FOREIGN_KEY and no_key_refs:
                continue
            if fd.read_rule == ReadRule.NO_READ and not ignore_writeonly:
                continue
            item_context = context.new(
                value=field_value,
                entity_chain=[*entity_chain, cls_name])
            retval[jf_name] = field.field_types.validator.tojson(item_context)
        return retval
