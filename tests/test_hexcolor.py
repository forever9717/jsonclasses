from __future__ import annotations
from unittest import TestCase
from jsonclasses.excs import ValidationException
from tests.classes.hex_color import HexColor


class TestHexColor(TestCase):

    def test_hex_color_doesnt_raise(self):
        color = HexColor(hex_color='01FD6F')
        color.validate()

    def test_hex_color_raises_if_value_is_not_valid(self):
        color = HexColor(hex_color='ZZZZZZ')
        with self.assertRaises(ValidationException) as context:
            color.validate()
        self.assertEqual(len(context.exception.keypath_messages), 1)
        self.assertEqual(context.exception.keypath_messages['hexColor'],
                         "value is not hex color string")
    
    

