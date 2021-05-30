import ipaddress
import itertools
from typing import Any, Optional, Tuple, Type

import pytest

from aiosnmp import asn1
from aiosnmp.asn1_rust import Decoder, Encoder, Error


class TestEncoder:
    @pytest.mark.parametrize(
        ("value", "number", "expected"),
        [
            # boolean
            (True, None, b"\x01\x01\xff"),
            (True, asn1.Number.Boolean, b"\x01\x01\xff"),
            (False, None, b"\x01\x01\x00"),
            (False, asn1.Number.Boolean, b"\x01\x01\x00"),
            # integer
            (0, None, b"\x02\x01\x00"),
            (1, None, b"\x02\x01\x01"),
            (-0, None, b"\x02\x01\x00"),
            (-1, None, b"\x02\x01\xff"),
            (127, None, b"\x02\x01\x7f"),
            (128, None, b"\x02\x02\x00\x80"),
            (-127, None, b"\x02\x01\x81"),
            (-128, None, b"\x02\x01\x80"),
            (-129, None, b"\x02\x02\xff\x7f"),
            (32767, None, b"\x02\x02\x7f\xff"),
            (32768, None, b"\x02\x03\x00\x80\x00"),
            (32769, None, b"\x02\x03\x00\x80\x01"),
            (-32767, None, b"\x02\x02\x80\x01"),
            (-32768, None, b"\x02\x02\x80\x00"),
            (-32769, None, b"\x02\x03\xff\x7f\xff"),
            (
                5233100606242806050955395731361295,
                None,
                b"\x02\x0f\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f",
            ),
            (
                -5233100606242806050955395731361295,
                None,
                b"\x02\x0f\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6\xf5\xf4\xf3\xf2\xf1\xf1",
            ),
            # bytes
            (b"foo", None, b"\x04\x03foo"),
            (b"x" * 60, None, b"\x04<" + b"x" * 60),
            (b"x" * 255, None, b"\x04\x81\xff" + b"x" * 255),
            (b"x" * 256, None, b"\x04\x82\x01\x00" + b"x" * 256),
            (b"x" * 257, None, b"\x04\x82\x01\x01" + b"x" * 257),
            (b"x" * 0xFFFF, None, b"\x04\x82\xff\xff" + b"x" * 0xFFFF),
            # string
            ("foo", asn1.Number.PrintableString, b"\x13\x03foo"),
            ("fooé", None, b"\x04\x05\x66\x6f\x6f\xc3\xa9"),
            ("fooé", asn1.Number.PrintableString, b"\x13\x05\x66\x6f\x6f\xc3\xa9"),
            # null
            (None, asn1.Number.Null, b"\x05\x00"),
            (None, None, b"\x05\x00"),
            # object identifier
            ("1.2.3", asn1.Number.ObjectIdentifier, b"\x06\x02\x2a\x03"),
            ("39.2.3", asn1.Number.ObjectIdentifier, b"\x06\x03\x8c\x1a\x03"),
            ("1.39.3", asn1.Number.ObjectIdentifier, b"\x06\x02\x4f\x03"),
            ("1.2.300000", asn1.Number.ObjectIdentifier, b"\x06\x04\x2a\x92\xa7\x60"),
            (
                "1.2.840.113554.1.2.1.1",
                asn1.Number.ObjectIdentifier,
                b"\x06\x0a\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x01",
            ),
            # ip address
            (ipaddress.IPv4Address("127.0.0.1"), asn1.Number.IPAddress, b"\x40\x04\x7f\x00\x00\x01"),
            (ipaddress.IPv4Address("1.1.1.1"), asn1.Number.IPAddress, b"\x40\x04\x01\x01\x01\x01"),
            (ipaddress.IPv4Address("255.255.255.255"), asn1.Number.IPAddress, b"\x40\x04\xff\xff\xff\xff"),
            (ipaddress.IPv4Address("0.0.0.0"), asn1.Number.IPAddress, b"\x40\x04\x00\x00\x00\x00"),
            # enumerated
            (1, asn1.Number.Enumerated, b"\x0a\x01\x01"),
        ],
        ids=itertools.count(),  # fix for windows ValueError: the environment variable is longer than 32767 characters
    )
    def test_simple_encode(self, value: Any, number: Optional[asn1.TNumber], expected: bytes) -> None:
        encoder = Encoder()
        encoder.write(value, number)
        result = encoder.output()
        assert result == expected

    @pytest.mark.parametrize(
        ("number", "typ", "values", "expected"),
        [
            (asn1.Number.Sequence, None, (1, b"foo"), b"\x30\x08\x02\x01\x01\x04\x03foo"),
            (asn1.Number.Sequence, None, (1, 2), b"\x30\x06\x02\x01\x01\x02\x01\x02"),
            (asn1.Number.Set, None, (1, b"foo"), b"\x31\x08\x02\x01\x01\x04\x03foo"),
            (asn1.Number.Set, None, (1, 2), b"\x31\x06\x02\x01\x01\x02\x01\x02"),
            (1, asn1.Class.Context, (1,), b"\xa1\x03\x02\x01\x01"),
            (1, asn1.Class.Application, (1,), b"\x61\x03\x02\x01\x01"),
            (1, asn1.Class.Private, (1,), b"\xe1\x03\x02\x01\x01"),
        ],
    )
    def test_one_enter(self, number: asn1.TNumber, typ: asn1.TType, values: Tuple, expected: bytes) -> None:
        encoder = Encoder()
        encoder.enter(number, typ)
        for value in values:
            encoder.write(value)
        encoder.exit()
        res = encoder.output()
        assert res == expected

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                ((asn1.Number.Sequence, None, (1, b"foo")),) * 3,
                b"\x30\x08\x02\x01\x01\x04\x03foo" * 3,
            ),
            (
                (
                    (asn1.Number.Sequence, None, (1, 2)),
                    (asn1.Number.Sequence, None, (10, 20)),
                ),
                b"\x30\x06\x02\x01\x01\x02\x01\x02\x30\x06\x02\x01\n\x02\x01\x14",
            ),
            (
                (
                    (asn1.Number.Set, None, (b"value", b"foo", ipaddress.IPv4Address("5.6.7.8"))),
                    (asn1.Number.Sequence, None, (1, True, False)),
                ),
                b"1\x12\x04\x05value\x04\x03foo@\x04\x05\x06\x07\x080\t\x02\x01\x01\x01\x01\xff\x01\x01\x00",
            ),
        ],
    )
    def test_multiple_enter(
        self, values: Tuple[Tuple[asn1.TNumber, Optional[asn1.TClass], Tuple]], expected: bytes
    ) -> None:
        encoder = Encoder()
        for number, typ, values_ in values:
            encoder.enter(number, typ)
            for value in values_:
                encoder.write(value)
            encoder.exit()

        res = encoder.output()
        assert res == expected

    def test_error_stack(self) -> None:
        encoder = Encoder()
        encoder.enter(asn1.Number.Sequence)
        with pytest.raises(Error, match="Stack is not empty."):
            encoder.output()

    @pytest.mark.parametrize(
        "value",
        ["1", "40.2.3", "1.40.3", "1.2.3.", ".1.2.3", "foo", "foo.bar"],
    )
    def test_error_object_identifier(self, value: str) -> None:
        encoder = Encoder()
        with pytest.raises(Error, match="Illegal object identifier"):
            encoder.write(value, asn1.Number.ObjectIdentifier)

    def test_exit_errors(self) -> None:
        encoder = Encoder()
        with pytest.raises(Error, match="Tag stack is empty."):
            encoder.exit()

    def test_cannot_determine_number(self) -> None:
        encoder = Encoder()
        with pytest.raises(Error, match="Cannot determine Number for value type"):
            encoder.write(1.21)

    def test_invalid_number(self) -> None:
        encoder = Encoder()
        with pytest.raises(Error, match="Unhandled Number 155 value 1"):
            encoder.write(1, 155)


class TestDecoder:
    @pytest.mark.parametrize(
        ("buffer", "instance", "number", "typ", "cls", "expected"),
        [
            (b"\x01\x01\xff", bool, asn1.Number.Boolean, asn1.Type.Primitive, asn1.Class.Universal, True),
            (b"\x01\x01\x01", bool, asn1.Number.Boolean, asn1.Type.Primitive, asn1.Class.Universal, True),
            (b"\x01\x01\x00", bool, asn1.Number.Boolean, asn1.Type.Primitive, asn1.Class.Universal, False),
            (b"\x02\x01\x01", int, asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal, 1),
            (b"\x02\x04\xff\xff\xff\xff", int, asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal, -1),
            (b"\x02\x01\xff", int, asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal, -1),
            (
                b"\x02\x0f\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f",
                int,
                asn1.Number.Integer,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                5233100606242806050955395731361295,
            ),
            (
                b"\x02\x0f\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6\xf5\xf4\xf3\xf2\xf1\xf1",
                int,
                asn1.Number.Integer,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                -5233100606242806050955395731361295,
            ),
            (b"\x02\x01\x7f", int, asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal, 127),
            (b"\x02\x02\x00\x80", int, asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal, 128),
            (b"\x02\x01\x80", int, asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal, -128),
            (b"\x02\x02\xff\x7f", int, asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal, -129),
            (
                b"\x02\x10\xff\x7f\x2b\x3a\x4d\xea\x48\x1e\x1f\x37\x7b\xa8\xbd\x7f\xb0\x16",
                int,
                asn1.Number.Integer,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                -668929531791034950848739021124816874,
            ),
            (b"\x04\x03foo", bytes, asn1.Number.OctetString, asn1.Type.Primitive, asn1.Class.Universal, b"foo"),
            (
                b"\x04\x82\xff\xff" + b"x" * 0xFFFF,
                bytes,
                asn1.Number.OctetString,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                b"x" * 0xFFFF,
            ),
            (b"\x13\x03foo", str, asn1.Number.PrintableString, asn1.Type.Primitive, asn1.Class.Universal, "foo"),
            (
                b"\x13\x05\x66\x6f\x6f\xc3\xa9",
                str,
                asn1.Number.PrintableString,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                "fooé",
            ),
            (b"\x05\x00", type(None), asn1.Number.Null, asn1.Type.Primitive, asn1.Class.Universal, None),
            (
                b"\x06\x02\x2a\x03",
                str,
                asn1.Number.ObjectIdentifier,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                ".1.2.3",
            ),
            (
                b"\x06\x03\x8c\x1a\x03",
                str,
                asn1.Number.ObjectIdentifier,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                ".39.2.3",
            ),
            (
                b"\x06\x02\x4f\x03",
                str,
                asn1.Number.ObjectIdentifier,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                ".1.39.3",
            ),
            (
                b"\x06\x04\x2a\x92\xa7\x60",
                str,
                asn1.Number.ObjectIdentifier,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                ".1.2.300000",
            ),
            (
                b"\x06\x0a\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x01",
                str,
                asn1.Number.ObjectIdentifier,
                asn1.Type.Primitive,
                asn1.Class.Universal,
                ".1.2.840.113554.1.2.1.1",
            ),
            (b"\x0a\x01\x01", int, asn1.Number.Enumerated, asn1.Type.Primitive, asn1.Class.Universal, 1),
            (b"\x80\x00", type(None), 0, asn1.Type.Primitive, asn1.Class.Context, None),
            (b"\x81\x00", type(None), 1, asn1.Type.Primitive, asn1.Class.Context, None),
            (b"\x82\x00", type(None), 2, asn1.Type.Primitive, asn1.Class.Context, None),
            (b"\x43\x03\x54\xa5\xb0", int, 3, asn1.Type.Primitive, asn1.Class.Application, 5547440),
            (b"\x42\x01\x02", int, 2, asn1.Type.Primitive, asn1.Class.Application, 2),
            (b"\x41\x01\x2a", int, 1, asn1.Type.Primitive, asn1.Class.Application, 42),
            (
                b"\x40\x04\x7f\x00\x00\x01",
                ipaddress.IPv4Address,
                0,
                asn1.Type.Primitive,
                asn1.Class.Application,
                ipaddress.IPv4Address("127.0.0.1"),
            ),
        ],
        ids=itertools.count(),  # fix for windows ValueError: the environment variable is longer than 32767 characters
    )
    def test_simple_decode(
        self, buffer: bytes, instance: Type, number: asn1.TNumber, typ: asn1.TType, cls: asn1.TClass, expected: Any
    ) -> None:
        decoder = Decoder(buffer)
        tag = decoder.peek()
        assert tag.number == number
        assert tag.typ == typ
        assert tag.cls == cls

        tag, value = decoder.read()
        assert tag.number == number
        assert tag.typ == typ
        assert tag.cls == cls

        assert isinstance(value, instance)
        assert value == expected
        assert decoder.eof()

    @pytest.mark.parametrize(
        ("buffer", "number", "typ", "cls", "expected_values"),
        [
            (
                b"\x30\x08\x02\x01\x01\x04\x03foo",
                asn1.Number.Sequence,
                asn1.Type.Constructed,
                asn1.Class.Universal,
                (1, b"foo"),
            ),
            (
                b"\x30\x06\x02\x01\x01\x02\x01\x02",
                asn1.Number.Sequence,
                asn1.Type.Constructed,
                asn1.Class.Universal,
                (1, 2),
            ),
            (
                b"\x31\x08\x02\x01\x01\x04\x03foo",
                asn1.Number.Set,
                asn1.Type.Constructed,
                asn1.Class.Universal,
                (1, b"foo"),
            ),
            (
                b"\x31\x06\x02\x01\x01\x02\x01\x02",
                asn1.Number.Set,
                asn1.Type.Constructed,
                asn1.Class.Universal,
                (1, 2),
            ),
            (
                b"\xa1\x03\x02\x01\x01",
                1,
                asn1.Type.Constructed,
                asn1.Class.Context,
                (1,),
            ),
            (
                b"\x61\x03\x02\x01\x01",
                1,
                asn1.Type.Constructed,
                asn1.Class.Application,
                (1,),
            ),
            (
                b"\xe1\x03\x02\x01\x01",
                1,
                asn1.Type.Constructed,
                asn1.Class.Private,
                (1,),
            ),
        ],
    )
    def test_one_enter(
        self, buffer: bytes, number: asn1.TNumber, typ: asn1.TType, cls: asn1.TClass, expected_values: Tuple
    ) -> None:
        decoder = Decoder(buffer)
        tag = decoder.peek()
        assert tag.number == number
        assert tag.typ == typ
        assert tag.cls == cls

        decoder.enter()
        for expected in expected_values:
            _, value = decoder.read()
            assert value == expected

        decoder.exit()

        assert decoder.eof()

    @pytest.mark.parametrize(
        ("buffer", "expected_values"),
        [
            (
                b"\x30\x08\x02\x01\x01\x04\x03foo" * 3,
                ((1, b"foo"),) * 3,
            ),
            (
                b"\x30\x06\x02\x01\x01\x02\x01\x02\x30\x06\x02\x01\n\x02\x01\x14",
                (
                    (1, 2),
                    (10, 20),
                ),
            ),
            (
                b"1\x12\x04\x05value\x04\x03foo@\x04\x05\x06\x07\x080\t\x02\x01\x01\x01\x01\xff\x01\x01\x00",
                (
                    (b"value", b"foo", ipaddress.IPv4Address("5.6.7.8")),
                    (1, True, False),
                ),
            ),
        ],
    )
    def test_multiple_enter(self, buffer: bytes, expected_values: Tuple[Tuple]) -> None:
        decoder = Decoder(buffer)

        for expected in expected_values:
            decoder.enter()
            for value_ in expected:
                _, value = decoder.read()
                assert value == value_

            decoder.exit()

        assert decoder.eof()

    @pytest.mark.parametrize(
        ("buffer", "expected_values"),
        [
            (b"\x02\x01\x01\x02\x01\x02", (1, 2)),
            (b"\x30\x06\x02\x01\x01\x02\x01\x02\x02\x01\x03", (b"\x02\x01\x01\x02\x01\x02", 3)),
        ],
    )
    def test_read_multiple(self, buffer: bytes, expected_values: Tuple[Any]) -> None:
        decoder = Decoder(buffer)
        for expected in expected_values:
            _, value = decoder.read()
            assert value == expected

        assert decoder.eof()

    @pytest.mark.parametrize(
        ("buffer", "error"),
        [
            (b"", "Input is empty."),
            (b"\x3f", "Premature end of input."),
            (b"\x3f\x83", "Premature end of input."),
        ],
    )
    def test_peek_errors(self, buffer: bytes, error: str) -> None:
        decoder = Decoder(buffer)
        with pytest.raises(Error, match=error):
            decoder.peek()

    @pytest.mark.parametrize(
        ("buffer", "error"),
        [
            (b"", "Input is empty."),
            (b"\x02", "Premature end of input."),
            (b"\x04\x82\xff", "Premature end of input."),
            (b"\x04\xff" + b"\xff" * 0x7F, "ASN1 syntax error"),
            (b"\x02\x01", "Premature end of input."),
            (b"\x02\x02\x01", "Premature end of input."),
            (b"\x06\x02\x80\x01", "ASN1 syntax error"),
            (b"\x06\x02\x8c\x40", "ASN1 syntax error"),
        ],
    )
    def test_read_errors(self, buffer: bytes, error: str) -> None:
        decoder = Decoder(buffer)
        with pytest.raises(Error, match=error):
            decoder.read()

    def test_cannot_enter(self) -> None:
        decoder = Decoder(b"\x01\x01\xff")
        with pytest.raises(Error, match="Cannot enter a non-constructed tag."):
            decoder.enter()

    def test_premature_exit(self) -> None:
        decoder = Decoder(b"\x01\x01\xff")
        with pytest.raises(Error, match="Tag stack is empty."):
            decoder.exit()

    def test_big_boolean(self) -> None:
        decoder = Decoder(b"\x01\x02\xff\x00")
        with pytest.raises(Error, match="ASN1 syntax error"):
            decoder.read()

    def test_not_null_null(self) -> None:
        decoder = Decoder(b"\x05\x01\x01")
        with pytest.raises(Error, match="ASN1 syntax error"):
            decoder.read()


class TestEncoderDecoder:
    @pytest.mark.parametrize(
        ("value", "number"),
        [
            (None, None),
            (True, None),
            (False, None),
            (0, None),
            (1, None),
            (-1, None),
            (127, None),
            (128, None),
            (129, None),
            (-126, None),
            (-127, None),
            (-128, None),
            (-129, None),
            (668929531791034950848739021124816874, None),
            (-668929531791034950848739021124816874, None),
            ("abc", asn1.Number.PrintableString),
            ("abc" * 10, asn1.Number.PrintableString),
            ("abc" * 100, asn1.Number.PrintableString),
            (b"abc", None),
            (b"abc" * 10, None),
            (b"abc" * 100, None),
            (ipaddress.IPv4Address("0.0.0.0"), None),
            (ipaddress.IPv4Address("255.255.255.255"), None),
            (ipaddress.IPv4Address("192.168.0.1"), None),
            (ipaddress.IPv4Address("8.8.8.8"), None),
        ],
    )
    def test_simple(self, value: Any, number: Optional[asn1.TNumber]) -> None:
        encoder = Encoder()
        encoder.write(value, number)
        data = encoder.output()
        decoder = Decoder(data)
        _, decoded = decoder.read()
        assert decoded == value
        assert decoder.eof()
