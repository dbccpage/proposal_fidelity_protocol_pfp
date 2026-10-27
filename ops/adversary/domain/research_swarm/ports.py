"""Pure ports for Adversary research and repository audit orchestration."""

from typing import Protocol

from .models import FindingV1


class AuditSquadPort(Protocol):
    files_scanned_count: int

    def audit_squad_alpha_rust(self) -> list[FindingV1]: ...
    def audit_squad_beta_python(self) -> list[FindingV1]: ...
    def audit_squad_gamma_lean(self) -> list[FindingV1]: ...
    def audit_squad_delta_atlas(self) -> list[FindingV1]: ...
