import enum
from typing import Union


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
