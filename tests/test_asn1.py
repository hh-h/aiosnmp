# This file is part of Python-ASN1. Python-ASN1 is free software that is
# made available under the MIT license. Consult the file "LICENSE" that
# is distributed together with this file for the exact licensing terms.
#
# Python-ASN1 is copyright (c) 2007-2016 by the Python-ASN1 authors. See the
# file "AUTHORS" for a complete overview.

import ipaddress

import pytest

import aiosnmp.asn1 as asn1


class TestEncoder:
    def test_boolean(self) -> None:
        enc = asn1.Encoder()
        enc.write(True, asn1.Number.Boolean)
        res = enc.output()
        assert res == b"\x01\x01\xff"

    def test_integer(self) -> None:
        enc = asn1.Encoder()
        enc.write(1)
        res = enc.output()
        assert res == b"\x02\x01\x01"

    def test_long_integer(self) -> None:
        enc = asn1.Encoder()
        enc.write(0x0102030405060708090A0B0C0D0E0F)
        res = enc.output()
        assert (
            res
            == b"\x02\x0f\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        )

    def test_negative_integer(self) -> None:
        enc = asn1.Encoder()
        enc.write(-1)
        res = enc.output()
        assert res == b"\x02\x01\xff"

    def test_long_negative_integer(self) -> None:
        enc = asn1.Encoder()
        enc.write(-0x0102030405060708090A0B0C0D0E0F)
        res = enc.output()
        assert (
            res
            == b"\x02\x0f\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6\xf5\xf4\xf3\xf2\xf1\xf1"
        )

    @pytest.mark.parametrize(
        ("number", "result"),
        (
            (0, b"\x02\x01\x00"),
            (1, b"\x02\x01\x01"),
            (-0, b"\x02\x01\x00"),
            (-1, b"\x02\x01\xff"),
            (127, b"\x02\x01\x7f"),
            (128, b"\x02\x02\x00\x80"),
            (-127, b"\x02\x01\x81"),
            (-128, b"\x02\x01\x80"),
            (-129, b"\x02\x02\xff\x7f"),
            (32767, b"\x02\x02\x7f\xff"),
            (32768, b"\x02\x03\x00\x80\x00"),
            (32769, b"\x02\x03\x00\x80\x01"),
            (-32767, b"\x02\x02\x80\x01"),
            (-32768, b"\x02\x02\x80\x00"),
            (-32769, b"\x02\x03\xff\x7f\xff"),
        ),
    )
    def test_twos_complement_boundaries(self, number: int, result: bytes) -> None:
        enc = asn1.Encoder()
        enc.write(number)
        assert enc.output() == result

    def test_octet_string(self) -> None:
        enc = asn1.Encoder()
        enc.write(b"foo")
        res = enc.output()
        assert res == b"\x04\x03foo"

    def test_printable_string(self) -> None:
        enc = asn1.Encoder()
        enc.write("foo", nr=asn1.Number.PrintableString)
        res = enc.output()
        assert res == b"\x13\x03foo"

    def test_unicode_octet_string(self) -> None:
        enc = asn1.Encoder()
        enc.write("fooé")
        res = enc.output()
        assert res == b"\x04\x05\x66\x6f\x6f\xc3\xa9"

    def test_unicode_printable_string(self) -> None:
        enc = asn1.Encoder()
        enc.write("fooé", nr=asn1.Number.PrintableString)
        res = enc.output()
        assert res == b"\x13\x05\x66\x6f\x6f\xc3\xa9"

    def test_null(self) -> None:
        enc = asn1.Encoder()
        enc.write(None)
        res = enc.output()
        assert res == b"\x05\x00"

    def test_object_identifier(self) -> None:
        enc = asn1.Encoder()
        enc.write("1.2.3", asn1.Number.ObjectIdentifier)
        res = enc.output()
        assert res == b"\x06\x02\x2a\x03"

    def test_long_object_identifier(self) -> None:
        enc = asn1.Encoder()
        enc.write("39.2.3", asn1.Number.ObjectIdentifier)
        res = enc.output()
        assert res == b"\x06\x03\x8c\x1a\x03"

        enc = asn1.Encoder()
        enc.write("1.39.3", asn1.Number.ObjectIdentifier)
        res = enc.output()
        assert res == b"\x06\x02\x4f\x03"

        enc = asn1.Encoder()
        enc.write("1.2.300000", asn1.Number.ObjectIdentifier)
        res = enc.output()
        assert res == b"\x06\x04\x2a\x92\xa7\x60"

    def test_real_object_identifier(self) -> None:
        enc = asn1.Encoder()
        enc.write("1.2.840.113554.1.2.1.1", asn1.Number.ObjectIdentifier)
        res = enc.output()
        assert res == b"\x06\x0a\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x01"

    def test_ipaddress(self) -> None:
        enc = asn1.Encoder()
        enc.write(ipaddress.IPv4Address("127.0.0.1"), asn1.Number.IPAddress)
        res = enc.output()
        assert res == b"\x40\x04\x7f\x00\x00\x01"

    def test_enumerated(self) -> None:
        enc = asn1.Encoder()
        enc.write(1, asn1.Number.Enumerated)
        res = enc.output()
        assert res == b"\x0a\x01\x01"

    def test_sequence(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(asn1.Number.Sequence):
            enc.write(1)
            enc.write(b"foo")
        res = enc.output()
        assert res == b"\x30\x08\x02\x01\x01\x04\x03foo"

    def test_sequence_of(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(asn1.Number.Sequence):
            enc.write(1)
            enc.write(2)
        res = enc.output()
        assert res == b"\x30\x06\x02\x01\x01\x02\x01\x02"

    def test_set(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(asn1.Number.Set):
            enc.write(1)
            enc.write(b"foo")
        res = enc.output()
        assert res == b"\x31\x08\x02\x01\x01\x04\x03foo"

    def test_set_of(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(asn1.Number.Set):
            enc.write(1)
            enc.write(2)
        res = enc.output()
        assert res == b"\x31\x06\x02\x01\x01\x02\x01\x02"

    def test_context(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(1, asn1.Class.Context):
            enc.write(1)
        res = enc.output()
        assert res == b"\xa1\x03\x02\x01\x01"

    def test_application(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(1, asn1.Class.Application):
            enc.write(1)
        res = enc.output()
        assert res == b"\x61\x03\x02\x01\x01"

    def test_private(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(1, asn1.Class.Private):
            enc.write(1)
        res = enc.output()
        assert res == b"\xe1\x03\x02\x01\x01"

    def test_long_tag_length(self) -> None:
        enc = asn1.Encoder()
        enc.write(b"x" * 0xFFFF)
        res = enc.output()
        assert res == b"\x04\x82\xff\xff" + b"x" * 0xFFFF

    def test_error_stack(self) -> None:
        enc = asn1.Encoder()
        with enc.enter(asn1.Number.Sequence):
            with pytest.raises(asn1.Error):
                enc.output()

    @pytest.mark.parametrize(
        "value", ["1", "40.2.3", "1.40.3", "1.2.3.", ".1.2.3", "foo", "foo.bar"]
    )
    def test_error_object_identifier(self, value) -> None:
        enc = asn1.Encoder()
        with pytest.raises(asn1.Error):
            enc.write(value, asn1.Number.ObjectIdentifier)


class TestDecoder:
    @pytest.mark.parametrize(
        ("buf", "result"),
        ((b"\x01\x01\xff", 1), (b"\x01\x01\x01", 1), (b"\x01\x01\x00", 0)),
    )
    def test_boolean(self, buf: bytes, result: int) -> None:
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (asn1.Number.Boolean, asn1.Type.Primitive, asn1.Class.Universal)
        tag, val = dec.read()
        assert isinstance(val, int)
        assert val == result

    @pytest.mark.parametrize(
        ("buf", "result"), ((b"\x02\x01\x01", 1), (b"\x02\x04\xff\xff\xff\xff", -1))
    )
    def test_integer(self, buf: bytes, result: int) -> None:
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (asn1.Number.Integer, asn1.Type.Primitive, asn1.Class.Universal)
        tag, val = dec.read()
        assert isinstance(val, int)
        assert val == result

    def test_long_integer(self) -> None:
        buf = b"\x02\x0f\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == 0x0102030405060708090A0B0C0D0E0F

    def test_negative_integer(self) -> None:
        buf = b"\x02\x01\xff"
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == -1

    def test_long_negative_integer(self) -> None:
        buf = b"\x02\x0f\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6\xf5\xf4\xf3\xf2\xf1\xf1"
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == -0x0102030405060708090A0B0C0D0E0F

    @pytest.mark.parametrize(
        ("buf", "result"),
        (
            (b"\x02\x01\x7f", 127),
            (b"\x02\x02\x00\x80", 128),
            (b"\x02\x01\x80", -128),
            (b"\x02\x02\xff\x7f", -129),
        ),
    )
    def test_twos_complement_boundaries(self, buf: bytes, result: int) -> None:
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == result

    def test_octet_string(self) -> None:
        buf = b"\x04\x03foo"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (
            asn1.Number.OctetString,
            asn1.Type.Primitive,
            asn1.Class.Universal,
        )
        tag, val = dec.read()
        assert val == b"foo"

    def test_printable_string(self) -> None:
        buf = b"\x13\x03foo"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (
            asn1.Number.PrintableString,
            asn1.Type.Primitive,
            asn1.Class.Universal,
        )
        tag, val = dec.read()
        assert val == "foo"

    def test_unicode_printable_string(self) -> None:
        buf = b"\x13\x05\x66\x6f\x6f\xc3\xa9"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (
            asn1.Number.PrintableString,
            asn1.Type.Primitive,
            asn1.Class.Universal,
        )
        tag, val = dec.read()
        assert val == "fooé"

    def test_null(self) -> None:
        buf = b"\x05\x00"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (asn1.Number.Null, asn1.Type.Primitive, asn1.Class.Universal)
        tag, val = dec.read()
        assert val is None

    def test_object_identifier(self) -> None:
        buf = b"\x06\x02\x2a\x03"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (
            asn1.Number.ObjectIdentifier,
            asn1.Type.Primitive,
            asn1.Class.Universal,
        )
        tag, val = dec.read()
        assert val == ".1.2.3"

    @pytest.mark.parametrize(
        ("buf", "result"),
        (
            (b"\x06\x03\x8c\x1a\x03", ".39.2.3"),
            (b"\x06\x02\x4f\x03", ".1.39.3"),
            (b"\x06\x04\x2a\x92\xa7\x60", ".1.2.300000"),
        ),
    )
    def test_long_object_identifier(self, buf: bytes, result: str) -> None:
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == result

    def test_real_object_identifier(self) -> None:
        buf = b"\x06\x0a\x2a\x86\x48\x86\xf7\x12\x01\x02\x01\x01"
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == ".1.2.840.113554.1.2.1.1"

    def test_enumerated(self) -> None:
        buf = b"\x0a\x01\x01"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (
            asn1.Number.Enumerated,
            asn1.Type.Primitive,
            asn1.Class.Universal,
        )
        tag, val = dec.read()
        assert isinstance(val, int)
        assert val == 1

    def test_sequence(self) -> None:
        buf = b"\x30\x08\x02\x01\x01\x04\x03foo"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (
            asn1.Number.Sequence,
            asn1.Type.Constructed,
            asn1.Class.Universal,
        )
        with dec.enter():
            tag, val = dec.read()
            assert val == 1
            tag, val = dec.read()
            assert val == b"foo"

    def test_sequence_of(self) -> None:
        buf = b"\x30\x06\x02\x01\x01\x02\x01\x02"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (
            asn1.Number.Sequence,
            asn1.Type.Constructed,
            asn1.Class.Universal,
        )
        with dec.enter():
            tag, val = dec.read()
            assert val == 1
            tag, val = dec.read()
            assert val == 2

    def test_set(self) -> None:
        buf = b"\x31\x08\x02\x01\x01\x04\x03foo"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (asn1.Number.Set, asn1.Type.Constructed, asn1.Class.Universal)
        with dec.enter():
            tag, val = dec.read()
            assert val == 1
            tag, val = dec.read()
            assert val == b"foo"

    def test_set_of(self) -> None:
        buf = b"\x31\x06\x02\x01\x01\x02\x01\x02"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (asn1.Number.Set, asn1.Type.Constructed, asn1.Class.Universal)
        with dec.enter():
            tag, val = dec.read()
            assert val == 1
            tag, val = dec.read()
            assert val == 2

    def test_no_such_object(self) -> None:
        buf = b"\x80\x00"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (0, asn1.Type.Primitive, asn1.Class.Context)
        tag, val = dec.read()
        assert val is None

    def test_no_such_instance(self) -> None:
        buf = b"\x81\x00"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (1, asn1.Type.Primitive, asn1.Class.Context)
        tag, val = dec.read()
        assert val is None

    def test_end_of_mib_view(self) -> None:
        buf = b"\x82\x00"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (2, asn1.Type.Primitive, asn1.Class.Context)
        tag, val = dec.read()
        assert val is None

    def test_time_ticks(self) -> None:
        buf = b"\x43\x03\x54\xa5\xb0"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (3, asn1.Type.Primitive, asn1.Class.Application)
        tag, val = dec.read()
        assert val == 5547440

    def test_gauge32(self) -> None:
        buf = b"\x42\x01\x02"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (2, asn1.Type.Primitive, asn1.Class.Application)
        tag, val = dec.read()
        assert val == 2

    def test_counter32(self) -> None:
        buf = b"\x41\x01\x2a"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (1, asn1.Type.Primitive, asn1.Class.Application)
        tag, val = dec.read()
        assert val == 42

    def test_ipaddress(self) -> None:
        buf = b"\x40\x04\x7f\x00\x00\x01"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (0, asn1.Type.Primitive, asn1.Class.Application)
        tag, val = dec.read()
        assert val == ipaddress.IPv4Address("127.0.0.1")

    def test_context(self) -> None:
        buf = b"\xa1\x03\x02\x01\x01"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (1, asn1.Type.Constructed, asn1.Class.Context)
        with dec.enter():
            tag, val = dec.read()
            assert val == 1

    def test_application(self) -> None:
        buf = b"\x61\x03\x02\x01\x01"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (1, asn1.Type.Constructed, asn1.Class.Application)
        with dec.enter():
            tag, val = dec.read()
            assert val == 1

    def test_private(self) -> None:
        buf = b"\xe1\x03\x02\x01\x01"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (1, asn1.Type.Constructed, asn1.Class.Private)
        with dec.enter():
            tag, val = dec.read()
            assert val == 1

    def test_long_tag_id(self) -> None:
        buf = b"\x3f\x83\xff\x7f\x03\x02\x01\x01"
        dec = asn1.Decoder(buf)
        tag = dec.peek()
        assert tag == (0xFFFF, asn1.Type.Constructed, asn1.Class.Universal)
        with dec.enter():
            tag, val = dec.read()
            assert val == 1

    def test_long_tag_length(self) -> None:
        buf = b"\x04\x82\xff\xff" + b"x" * 0xFFFF
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == b"x" * 0xFFFF

    def test_read_multiple(self) -> None:
        buf = b"\x02\x01\x01\x02\x01\x02"
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == 1
        tag, val = dec.read()
        assert val == 2
        assert dec.eof()

    def test_skip_primitive(self) -> None:
        buf = b"\x02\x01\x01\x02\x01\x02"
        dec = asn1.Decoder(buf)
        dec.read()
        tag, val = dec.read()
        assert val == 2
        assert dec.eof()

    def test_skip_constructed(self) -> None:
        buf = b"\x30\x06\x02\x01\x01\x02\x01\x02\x02\x01\x03"
        dec = asn1.Decoder(buf)
        dec.read()
        tag, val = dec.read()
        assert val == 3
        assert dec.eof()

    def test_no_input(self) -> None:
        dec = asn1.Decoder(b"")
        with pytest.raises(asn1.Error):
            dec.peek()

    @pytest.mark.parametrize("buf", (b"\x3f", b"\x3f\x83"))
    def test_error_missing_tag_bytes(self, buf: bytes) -> None:
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.peek()

    def test_error_no_length_bytes(self) -> None:
        buf = b"\x02"
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.read()

    def test_error_missing_length_bytes(self) -> None:
        buf = b"\x04\x82\xff"
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.read()

    def test_error_too_many_length_bytes(self) -> None:
        buf = b"\x04\xff" + b"\xff" * 0x7F
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.read()

    def test_error_no_value_bytes(self) -> None:
        buf = b"\x02\x01"
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.read()

    def test_error_missing_value_bytes(self) -> None:
        buf = b"\x02\x02\x01"
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.read()

    def test_error_non_normalised_object_identifier(self) -> None:
        buf = b"\x06\x02\x80\x01"
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.read()

    def test_error_object_identifier_with_too_large_first_component(self) -> None:
        buf = b"\x06\x02\x8c\x40"
        dec = asn1.Decoder(buf)
        with pytest.raises(asn1.Error):
            dec.read()

    def test_big_negative_integer(self) -> None:
        buf = (
            b"\x02\x10\xff\x7f\x2b\x3a\x4d\xea\x48\x1e\x1f\x37\x7b\xa8\xbd\x7f\xb0\x16"
        )
        dec = asn1.Decoder(buf)
        tag, val = dec.read()
        assert val == -668929531791034950848739021124816874
        assert dec.eof()


class TestEncoderDecoder:
    @pytest.mark.parametrize(
        "value",
        (
            668929531791034950848739021124816874,
            667441897913742713771034596334288035,
            664674827807729028941298133900846368,
            666811959353093594446621165172641478,
        ),
    )
    def test_big_numbers(self, value: int) -> None:
        encoder = asn1.Encoder()
        encoder.write(value, asn1.Number.Integer)
        encoded_bytes = encoder.output()
        decoder = asn1.Decoder(encoded_bytes)
        tag, val = decoder.read()
        assert val == value

    @pytest.mark.parametrize(
        "value",
        (
            -668929531791034950848739021124816874,
            -667441897913742713771034596334288035,
            -664674827807729028941298133900846368,
            -666811959353093594446621165172641478,
        ),
    )
    def test_big_negative_numbers(self, value: int) -> None:
        encoder = asn1.Encoder()
        encoder.write(value, asn1.Number.Integer)
        encoded_bytes = encoder.output()
        decoder = asn1.Decoder(encoded_bytes)
        tag, val = decoder.read()
        assert val == value
