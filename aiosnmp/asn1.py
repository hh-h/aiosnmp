# This file is part of Python-ASN1. Python-ASN1 is free software that is
# made available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# Python-ASN1 is copyright (c) 2007-2016 by the Python-ASN1 authors.

import enum
import ipaddress
import re
from contextlib import contextmanager
from typing import Any, Iterator, List, NamedTuple, Optional, Tuple, Union, cast


class Number(enum.IntEnum):
    EndOfContents = 0x00
    Boolean = 0x01
    Integer = 0x02
    BitString = 0x03
    OctetString = 0x04
    Null = 0x05
    ObjectIdentifier = 0x06
    ObjectDescription = 0x07
    Enumerated = 0x0A
    UTF8String = 0x0C
    Sequence = 0x10
    Set = 0x11
    PrintableString = 0x13
    IA5String = 0x16
    UTCTime = 0x17
    UnicodeString = 0x1E

    IPAddress = 0x40
    Counter32 = 0x41
    Gauge32 = 0x42
    TimeTicks = 0x43
    Opaque = 0x44
    NsapAddress = 0x45
    Counter64 = 0x46
    Uinteger32 = 0x47
    OpaqueFloat = 0x78
    OpaqueDouble = 0x79
    NoSuchObject = 0x80
    NoSuchInstance = 0x81
    EndOfMibView = 0x82


class Type(enum.IntEnum):
    Constructed = 0x20
    Primitive = 0x00


class Class(enum.IntEnum):
    Universal = 0x00
    Application = 0x40
    Context = 0x80
    Private = 0xC0


TNumber = Union[Number, int]
TType = Union[Type, int]
TClass = Union[Class, int]


class Tag(NamedTuple):
    nr: TNumber
    typ: TType
    cls: TClass


class Error(Exception):
    pass


class Encoder:
    __slots__ = "m_stack"

    def __init__(self) -> None:
        self.m_stack: List[List[bytes]] = [[]]

    @contextmanager
    def enter(self, nr: TNumber, cls: Optional[TClass] = None) -> Iterator[None]:
        """This method starts the construction of a constructed type.

        Args:
            nr (int): The desired ASN.1 type. Use ``Number`` enumeration.

            cls (int): This optional parameter specifies the class
                of the constructed type. The default class to use is the
                universal class. Use ``Class`` enumeration.

        Returns:
            None

        Raises:
            `Error`
        """
        if cls is None:
            cls = Class.Universal
        self._emit_tag(nr, Type.Constructed, cls)
        self.m_stack.append([])

        yield

        if len(self.m_stack) == 1:
            raise Error("Tag stack is empty.")
        value = b"".join(self.m_stack[-1])
        del self.m_stack[-1]
        self._emit_length(len(value))
        self._emit(value)

    def write(
        self,
        value: Any,
        nr: Optional[TNumber] = None,
        typ: Optional[TType] = None,
        cls: Optional[TClass] = None,
    ) -> None:
        """This method encodes one ASN.1 tag and writes it to the output buffer.

        Note:
            Normally, ``value`` will be the only parameter to this method.
            In this case Python-ASN1 will autodetect the correct ASN.1 type from
            the type of ``value``, and will output the encoded value based on this
            type.

        Args:
            value (any): The value of the ASN.1 tag to write. Python-ASN1 will
                try to autodetect the correct ASN.1 type from the type of
                ``value``.

            nr (int): If the desired ASN.1 type cannot be autodetected or is
                autodetected wrongly, the ``nr`` parameter can be provided to
                specify the ASN.1 type to be used. Use ``Number`` enumeration.

            typ (int): This optional parameter can be used to write constructed
                types to the output by setting it to indicate the constructed
                encoding type. In this case, ``value`` must already be valid ASN.1
                encoded data as plain Python bytes. This is not normally how
                constructed types should be encoded though, see `Encoder.enter()`
                and `Encoder.leave()` for the recommended way of doing this.
                Use ``Type`` enumeration.

            cls (int): This parameter can be used to override the class of the
                ``value``. The default class is the universal class.
                Use ``Class`` enumeration.

        Returns:
            None

        Raises:
            `Error`
        """
        if nr is None:
            if isinstance(value, int):
                nr = Number.Integer
            elif isinstance(value, str) or isinstance(value, bytes):
                nr = Number.OctetString
            elif value is None:
                nr = Number.Null
            elif isinstance(value, ipaddress.IPv4Address):
                nr = Number.IPAddress
            else:
                raise Error(f"Cannot determine Number for value type {type(value)}")
        if typ is None:
            typ = Type.Primitive
        if cls is None:
            cls = Class.Universal
        value = self._encode_value(nr, value)
        self._emit_tag(nr, typ, cls)
        self._emit_length(len(value))
        self._emit(value)

    def output(self) -> bytes:
        """This method returns the encoded ASN.1 data as plain Python ``bytes``.
        This method can be called multiple times, also during encoding.
        In the latter case the data that has been encoded so far is
        returned.

        Note:
            It is an error to call this method if the encoder is still
            constructing a constructed type, i.e. if `Encoder.enter()` has been
            called more times that `Encoder.leave()`.

        Returns:
            bytes: The DER encoded ASN.1 data.

        Raises:
            `Error`
        """
        if len(self.m_stack) != 1:
            raise Error("Stack is not empty.")
        output = b"".join(self.m_stack[0])
        return output

    def _emit_tag(self, nr: TNumber, typ: TType, cls: TClass) -> None:
        """Emit a tag."""
        self._emit_tag_short(nr, typ, cls)

    def _emit_tag_short(self, nr: TNumber, typ: TType, cls: TClass) -> None:
        """Emit a short tag."""
        self._emit(bytes([nr | typ | cls]))

    def _emit_length(self, length: int) -> None:
        """Emit length octets."""
        if length < 128:
            self._emit_length_short(length)
        else:
            self._emit_length_long(length)

    def _emit_length_short(self, length: int) -> None:
        """Emit the short length form (< 128 octets)."""
        assert length < 128
        self._emit(bytes([length]))

    def _emit_length_long(self, length: int) -> None:
        """Emit the long length form (>= 128 octets)."""
        values = []
        while length:
            values.append(length & 0xFF)
            length >>= 8
        values.reverse()
        # really for correctness as this should not happen anytime soon
        assert len(values) < 127
        head = bytes([0x80 | len(values)])
        self._emit(head)
        for val in values:
            self._emit(bytes([val]))

    def _emit(self, s: bytes) -> None:
        """Emit raw bytes."""
        assert isinstance(s, bytes)
        self.m_stack[-1].append(s)

    def _encode_value(self, nr: TNumber, value: Any) -> bytes:
        """Encode a value."""
        if nr in (Number.Integer, Number.Enumerated):
            return self._encode_integer(value)
        elif nr in (Number.OctetString, Number.PrintableString):
            return self._encode_octet_string(value)
        elif nr == Number.Boolean:
            return self._encode_boolean(value)
        elif nr == Number.Null:
            return self._encode_null()
        elif nr == Number.ObjectIdentifier:
            return self._encode_object_identifier(value)
        elif nr == Number.IPAddress:
            return self._encode_ipaddress(value)
        raise Error(f"Unhandled Number {nr} value {value}")

    @staticmethod
    def _encode_boolean(value: bool) -> bytes:
        """Encode a boolean."""
        return value and bytes(b"\xff") or bytes(b"\x00")

    @staticmethod
    def _encode_integer(value: int) -> bytes:
        """Encode an integer."""
        if value < 0:
            value = -value
            negative = True
            limit = 0x80
        else:
            negative = False
            limit = 0x7F
        values = []
        while value > limit:
            values.append(value & 0xFF)
            value >>= 8
        values.append(value & 0xFF)
        if negative:
            # create two's complement
            for i in range(len(values)):  # Invert bits
                values[i] = 0xFF - values[i]
            for i in range(len(values)):  # Add 1
                values[i] += 1
                if values[i] <= 0xFF:
                    break
                assert i != len(values) - 1
                values[i] = 0x00
        if negative and values[len(values) - 1] == 0x7F:  # Two's complement corner case
            values.append(0xFF)
        values.reverse()
        return bytes(values)

    @staticmethod
    def _encode_octet_string(value: Union[str, bytes]) -> bytes:
        """Encode an octet string."""
        # Use the primitive encoding
        assert isinstance(value, str) or isinstance(value, bytes)
        if isinstance(value, str):
            value = value.encode("utf-8")
        return value

    @staticmethod
    def _encode_null() -> bytes:
        """Encode a Null value."""
        return bytes(b"")

    _re_oid = re.compile(r"^[0-9]+(\.[0-9]+)+$")

    def _encode_object_identifier(self, oid: str) -> bytes:
        """Encode an object identifier."""
        if not self._re_oid.match(oid):
            raise Error("Illegal object identifier")
        cmps = list(map(int, oid.split(".")))
        if cmps[0] > 39 or cmps[1] > 39:
            raise Error("Illegal object identifier")
        cmps = [40 * cmps[0] + cmps[1]] + cmps[2:]
        cmps.reverse()
        result = []
        for cmp_data in cmps:
            result.append(cmp_data & 0x7F)
            while cmp_data > 0x7F:
                cmp_data >>= 7
                result.append(0x80 | (cmp_data & 0x7F))
        result.reverse()
        return bytes(result)

    @staticmethod
    def _encode_ipaddress(value: ipaddress.IPv4Address) -> bytes:
        """Encode an ip address."""
        return int(value).to_bytes(4, byteorder="big")


class Decoder:
    __slots__ = ("m_stack", "m_tag")

    def __init__(self, data: bytes) -> None:
        self.m_stack: List[List] = [[0, data]]
        self.m_tag: Optional[Tag] = None

    def peek(self) -> Tag:
        """This method returns the current ASN.1 tag (i.e. the tag that a
        subsequent `Decoder.read()` call would return) without updating the
        decoding offset. In case no more data is available from the input,
        this method returns ``None`` to signal end-of-file.

        This method is useful if you don't know whether the next tag will be a
        primitive or a constructed tag. Depending on the return value of `peek`,
        you would decide to either issue a `Decoder.read()` in case of a primitive
        type, or an `Decoder.enter()` in case of a constructed type.

        Note:
            Because this method does not advance the current offset in the input,
            calling it multiple times in a row will return the same value for all
            calls.

        Returns:
            `Tag`: The current ASN.1 tag.

        Raises:
            `Error`
        """
        if self._end_of_input():
            raise Error("Input is empty.")
        if self.m_tag is None:
            self.m_tag = self._read_tag()
        return self.m_tag

    def read(self, nr: Optional[TNumber] = None) -> Tuple[Tag, Any]:
        """This method decodes one ASN.1 tag from the input and returns it as a
        ``(tag, value)`` tuple. ``tag`` is a 3-tuple ``(nr, typ, cls)``,
        while ``value`` is a Python object representing the ASN.1 value.
        The offset in the input is increased so that the next `Decoder.read()`
        call will return the next tag. In case no more data is available from
        the input, this method returns ``None`` to signal end-of-file.

        Returns:
            `Tag`, value: The current ASN.1 tag and its value.

        Raises:
            `Error`
        """
        if self._end_of_input():
            raise Error("Input is empty.")
        tag = self.peek()
        length = self._read_length()
        if nr is None:
            nr = tag.nr | tag.cls
        value = self._read_value(nr, length)
        self.m_tag = None
        return tag, value

    def eof(self) -> bool:
        """Return True if we are at the end of input.

        Returns:
            bool: True if all input has been decoded, and False otherwise.
        """
        return self._end_of_input()

    @contextmanager
    def enter(self) -> Iterator[None]:
        """This method enters the constructed type that is at the current
        decoding offset.

        Note:
            It is an error to call `Decoder.enter()` if the to be decoded ASN.1 tag
            is not of a constructed type.

        Returns:
            None
        """
        tag = self.peek()
        if tag.typ != Type.Constructed:
            raise Error("Cannot enter a non-constructed tag.")
        length = self._read_length()
        bytes_data = self._read_bytes(length)
        self.m_stack.append([0, bytes_data])
        self.m_tag = None

        yield

        if len(self.m_stack) == 1:
            raise Error("Tag stack is empty.")
        del self.m_stack[-1]
        self.m_tag = None

    def _read_tag(self) -> Tag:
        """Read a tag from the input."""
        byte = self._read_byte()
        cls = byte & 0xC0
        typ = byte & 0x20
        nr = byte & 0x1F
        if nr == 0x1F:  # Long form of tag encoding
            nr = 0
            while True:
                byte = self._read_byte()
                nr = (nr << 7) | (byte & 0x7F)
                if not byte & 0x80:
                    break
        return Tag(nr=nr, typ=typ, cls=cls)

    def _read_length(self) -> int:
        """Read a length from the input."""
        byte = self._read_byte()
        if byte & 0x80:
            count = byte & 0x7F
            if count == 0x7F:
                raise Error("ASN1 syntax error")
            bytes_data = self._read_bytes(count)
            length = 0
            for byte in bytes_data:
                length = (length << 8) | int(byte)
            try:
                length = int(length)
            except OverflowError:
                pass
        else:
            length = byte
        return length

    def _read_value(self, nr: TNumber, length: int) -> Any:
        """Read a value from the input."""
        bytes_data = self._read_bytes(length)
        if nr == Number.Boolean:
            return self._decode_boolean(bytes_data)
        elif nr in (
            Number.Integer,
            Number.Enumerated,
            Number.TimeTicks,
            Number.Gauge32,
            Number.Counter32,
            Number.Counter64,
            Number.Uinteger32,
        ):
            return self._decode_integer(bytes_data)
        elif nr == Number.OctetString:
            return self._decode_octet_string(bytes_data)
        elif nr == Number.Null:
            return self._decode_null(bytes_data)
        elif nr == Number.ObjectIdentifier:
            return self._decode_object_identifier(bytes_data)
        elif nr in (Number.PrintableString, Number.IA5String, Number.UTCTime):
            return self._decode_printable_string(bytes_data)
        elif nr in (Number.EndOfMibView, Number.NoSuchObject, Number.NoSuchInstance):
            return None
        elif nr == Number.IPAddress:
            return self._decode_ip_address(bytes_data)
        return bytes_data

    def _read_byte(self) -> int:
        """Return the next input byte, or raise an error on end-of-input."""
        index, input_data = self.m_stack[-1]
        try:
            byte: int = input_data[index]
        except IndexError:
            raise Error("Premature end of input.")
        self.m_stack[-1][0] += 1
        return byte

    def _read_bytes(self, count: int) -> bytes:
        """Return the next ``count`` bytes of input. Raise error on
        end-of-input."""
        index, input_data = self.m_stack[-1]
        bytes_data: bytes = input_data[index : index + count]
        if len(bytes_data) != count:
            raise Error("Premature end of input.")
        self.m_stack[-1][0] += count
        return bytes_data

    def _end_of_input(self) -> bool:
        """Return True if we are at the end of input."""
        index, input_data = self.m_stack[-1]
        assert not index > len(input_data)
        return cast(int, index) == len(input_data)

    @staticmethod
    def _decode_boolean(bytes_data: bytes) -> bool:
        if len(bytes_data) != 1:
            raise Error("ASN1 syntax error")
        return not bytes_data[0] == 0

    @staticmethod
    def _decode_integer(bytes_data: bytes) -> int:
        values = [int(b) for b in bytes_data]
        negative = values[0] & 0x80
        if negative:
            # make positive by taking two's complement
            for i in range(len(values)):
                values[i] = 0xFF - values[i]
            for i in range(len(values) - 1, -1, -1):
                values[i] += 1
                if values[i] <= 0xFF:
                    break
                assert i > 0
                values[i] = 0x00
        value = 0
        for val in values:
            value = (value << 8) | val
        if negative:
            value = -value
        try:
            value = int(value)
        except OverflowError:
            pass
        return value

    @staticmethod
    def _decode_octet_string(bytes_data: bytes) -> bytes:
        return bytes_data

    @staticmethod
    def _decode_null(bytes_data: bytes) -> None:
        if len(bytes_data) != 0:
            raise Error("ASN1 syntax error")

    @staticmethod
    def _decode_object_identifier(bytes_data: bytes) -> str:
        result: List[int] = []
        value: int = 0
        for i in range(len(bytes_data)):
            byte = int(bytes_data[i])
            if value == 0 and byte == 0x80:
                raise Error("ASN1 syntax error")
            value = (value << 7) | (byte & 0x7F)
            if not byte & 0x80:
                result.append(value)
                value = 0
        if len(result) == 0 or result[0] > 1599:
            raise Error("ASN1 syntax error")
        result = [result[0] // 40, result[0] % 40] + result[1:]
        return f".{'.'.join(str(x) for x in result)}"

    @staticmethod
    def _decode_printable_string(bytes_data: bytes) -> str:
        return bytes_data.decode("utf-8")

    @staticmethod
    def _decode_ip_address(bytes_data: bytes) -> ipaddress.IPv4Address:
        return ipaddress.IPv4Address(int.from_bytes(bytes_data, byteorder="big"))
