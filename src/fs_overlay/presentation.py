"""Presentation endpoints separated from application execution."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PresentationKind(StrEnum):
    DISPLAY = "display"
    STREAM = "stream"
    INPUT = "input"
    AUDIO = "audio"
    REMOTE_DESKTOP = "remote_desktop"


@dataclass(frozen=True, slots=True)
class PresentationEndpoint:
    endpoint_id: str
    kind: PresentationKind
    protocol: str
    platform: str
    interactive: bool = True
    admitted: bool = False

    def admit(self) -> "PresentationEndpoint":
        return PresentationEndpoint(
            endpoint_id=self.endpoint_id,
            kind=self.kind,
            protocol=self.protocol,
            platform=self.platform,
            interactive=self.interactive,
            admitted=True,
        )

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.endpoint_id:
            errors.append("missing endpoint id")
        if not self.protocol:
            errors.append("missing presentation protocol")
        if not self.platform:
            errors.append("missing presentation platform")
        if not self.admitted:
            errors.append("presentation endpoint is not admitted")
        return tuple(errors)
