"""Small text/byte conversion helpers used by the Goose extractor."""

import datetime
from decimal import Decimal


class DjangoUnicodeDecodeError(UnicodeDecodeError):
    """Unicode decoding error that retains the original object."""

    def __init__(self, obj, *args):
        self.obj = obj
        super().__init__(*args)

    def __str__(self):
        original = super().__str__()
        return "%s. You passed in %r (%s)" % (original, self.obj, type(self.obj))


class StrAndUnicode:
    """Compatibility mixin whose string representation is Unicode text."""

    def __str__(self):
        return str(self.__unicode__())


def is_protected_type(obj):
    """Return whether ``obj`` is a scalar that should remain unchanged."""
    return isinstance(
        obj,
        (type(None), int, float, Decimal, datetime.datetime, datetime.date,
         datetime.time),
    )


def force_unicode(value, encoding="utf-8", strings_only=False, errors="strict"):
    """Return text for strings and bytes, preserving protected scalars if asked."""
    if isinstance(value, str):
        return value
    if strings_only and is_protected_type(value):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode(encoding, errors)
    return str(value)


def smart_unicode(value, encoding="utf-8", strings_only=False, errors="strict"):
    """Decode bytes as text and otherwise return a string representation."""
    return force_unicode(value, encoding, strings_only, errors)


def smart_str(value, encoding="utf-8", strings_only=False, errors="strict"):
    """Return bytes encoded with ``encoding`` (unless preserving a scalar)."""
    if strings_only and is_protected_type(value):
        return value
    if isinstance(value, bytes):
        if encoding == "utf-8":
            return value
        return value.decode("utf-8", errors).encode(encoding, errors)
    return force_unicode(value, encoding, strings_only, errors).encode(encoding, errors)
