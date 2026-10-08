"""Base class and shared field types for all model objects."""

import unicodedata
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints


class Entity(BaseModel):
    """Immutable, strictly validated model object. Change it with `evolve`, never in place."""

    model_config = ConfigDict(
        frozen=True, extra="forbid", strict=True, allow_inf_nan=False, validate_default=True
    )


def evolve[E: Entity](obj: E, **changes: Any) -> E:
    """Return a re-validated copy of `obj` with some fields replaced."""
    data = obj.model_dump()
    unknown = set(changes) - set(data)
    if unknown:
        raise TypeError(f"{type(obj).__name__} has no field(s) {sorted(unknown)}")
    data.update(changes)
    return type(obj).model_validate(data)


def _no_control_chars(value: str) -> str:
    for ch in value:
        if (unicodedata.category(ch) in ("Cc", "Cs") and ch not in "\n\t") or ch in "\ufffe\uffff":
            raise ValueError(
                "must not contain control characters"
            )  # (U+FFFE/FFFF are not valid XML)
    return value


Name = Annotated[
    str, StringConstraints(min_length=1, max_length=200), AfterValidator(_no_control_chars)
]
Text = Annotated[str, StringConstraints(max_length=5000), AfterValidator(_no_control_chars)]
