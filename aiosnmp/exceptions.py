__all__ = (
    "SnmpTimeoutError",
    "SnmpUnsupportedValueType",
    "SnmpErrorTooBig",
    "SnmpErrorNoSuchName",
    "SnmpErrorBadValue",
    "SnmpErrorReadOnly",
    "SnmpErrorGenErr",
    "SnmpErrorNoAccess",
    "SnmpErrorWrongType",
    "SnmpErrorWrongLength",
    "SnmpErrorWrongEncoding",
    "SnmpErrorWrongValue",
    "SnmpErrorNoCreation",
    "SnmpErrorInconsistentValue",
    "SnmpErrorResourceUnavailable",
    "SnmpErrorCommitFailed",
    "SnmpErrorUndoFailed",
    "SnmpErrorAuthorizationError",
    "SnmpErrorNotWritable",
    "SnmpErrorInconsistentName",
)

from asyncio import TimeoutError
from typing import Optional


class SnmpException(Exception):
    pass


class SnmpTimeoutError(SnmpException, TimeoutError):
    pass


class SnmpUnsupportedValueType(SnmpException):
    pass


class SnmpErrorStatus(SnmpException):
    message = ""

    def __init__(self, index: int, oid: Optional[str] = None) -> None:
        if oid is not None:
            msg = f"index: {index}, oid: {oid}, message: {self.message}"
        else:
            msg = f"index: {index}, message: {self.message}"
        super().__init__(msg)


class SnmpErrorTooBig(SnmpErrorStatus):
    message = (
        "The agent could not place the results "
        "of the requested SNMP operation in a single SNMP message."
    )


class SnmpErrorNoSuchName(SnmpErrorStatus):
    message = "The requested SNMP operation identified an unknown variable."


class SnmpErrorBadValue(SnmpErrorStatus):
    message = (
        "The requested SNMP operation tried to change a variable "
        "but it specified either a syntax or value error."
    )


class SnmpErrorReadOnly(SnmpErrorStatus):
    message = (
        "The requested SNMP operation tried to change a variable "
        "that was not allowed to change, "
        "according to the community profile of the variable."
    )


class SnmpErrorGenErr(SnmpErrorStatus):
    message = (
        "An error other than one of those listed here "
        "occurred during the requested SNMP operation."
    )


class SnmpErrorNoAccess(SnmpErrorStatus):
    message = "The specified SNMP variable is not accessible."


class SnmpErrorWrongType(SnmpErrorStatus):
    message = (
        "The value specifies a type that is inconsistent "
        "with the type required for the variable."
    )


class SnmpErrorWrongLength(SnmpErrorStatus):
    message = (
        "The value specifies a length that is inconsistent "
        "with the length required for the variable."
    )


class SnmpErrorWrongEncoding(SnmpErrorStatus):
    message = (
        "The value contains an Abstract Syntax Notation One (ASN.1) encoding "
        "that is inconsistent with the ASN.1 tag of the field."
    )


class SnmpErrorWrongValue(SnmpErrorStatus):
    message = "The value cannot be assigned to the variable."


class SnmpErrorNoCreation(SnmpErrorStatus):
    message = "The variable does not exist, and the agent cannot create it."


class SnmpErrorInconsistentValue(SnmpErrorStatus):
    message = "The value is inconsistent with values of other managed objects."


class SnmpErrorResourceUnavailable(SnmpErrorStatus):
    message = (
        "Assigning the value to the variable requires allocation of resources "
        "that are currently unavailable."
    )


class SnmpErrorCommitFailed(SnmpErrorStatus):
    message = "No validation errors occurred, but no variables were updated."


class SnmpErrorUndoFailed(SnmpErrorStatus):
    message = (
        "No validation errors occurred. Some variables were updated "
        "because it was not possible to undo their assignment."
    )


class SnmpErrorAuthorizationError(SnmpErrorStatus):
    message = "An authorization error occurred."


class SnmpErrorNotWritable(SnmpErrorStatus):
    message = "The variable exists but the agent cannot modify it."


class SnmpErrorInconsistentName(SnmpErrorStatus):
    message = (
        "The variable does not exist; "
        "the agent cannot create it because the named object instance "
        "is inconsistent with the values of other managed objects."
    )
