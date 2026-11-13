"""Finite BQNF-FSIGN gate with typed, independently replayed witnesses.

The host pins the packet and signed path rows before seeing a model proposal.
These methods check exact finite equations and path pairings. They cannot admit
named functional claims until a Rust core_functional adapter is connected.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Any
from paper011_recovered_demo2.bqnf_zero import PacketError, check_alpha_witness, check_cochain_packet
from paper011_recovered_demo2.meron_witness import WitnessError, verify_meron_witness

@dataclass(frozen=True)
class HostPacket:
    d0: tuple[tuple[Any, ...], ...]
    d1: tuple[tuple[Any, ...], ...]
    c1: tuple[Any, ...]
    source_ref: str

@dataclass(frozen=True)
class GateResult:
    status: str
    admitted: bool
    detail: str
    phi1_zero: bool | None = None
    gamma2: Fraction | None = None
    witness: Any = None
    authority_effect: str = 'None'

class BqnfCertificateGate:

    def __init__(self, packet: HostPacket | None, sectors: tuple[Any, ...] | None=None):
        self.packet = packet
        self.sectors = sectors

    def _packet_result(self):
        if self.packet is None or not self.packet.source_ref:
            raise PacketError('host-pinned packet and source_ref required')
        return check_cochain_packet(self.packet.d0, self.packet.d1, self.packet.c1)

    def verify_repair(self, proposed_alpha: Any) -> GateResult:
        try:
            packet = self._packet_result()
        except PacketError as exc:
            return GateResult('RefusedBadPacket', False, str(exc))
        if not isinstance(proposed_alpha, (list, tuple)):
            return GateResult('RefusedMissingAlpha', False, 'explicit alpha vector required')
        try:
            alpha = check_alpha_witness(packet, proposed_alpha)
        except PacketError as exc:
            return GateResult('RefusedBadAlpha', False, str(exc))
        return GateResult('RefusedFunctionalAdapterUnavailable', False, 'd0*alpha=c1 replayed exactly; Phi1 and Gamma2 require the Rust core_functional adapter', witness=alpha)

    def verify_cancellation(self, cancellation_ids: Any, xi: Any) -> GateResult:
        try:
            self._packet_result()
        except PacketError as exc:
            return GateResult('RefusedBadPacket', False, str(exc))
        if self.sectors is None:
            return GateResult('RefusedMissingPaths', False, 'host-pinned signed path rows required')
        try:
            witness = verify_meron_witness(self.sectors, cancellation_ids, xi)
        except WitnessError as exc:
            return GateResult('RefusedInvalidXi', False, str(exc))
        return GateResult('RefusedFunctionalAdapterUnavailable', False, 'finite path pairing replayed exactly; Phi1, Gamma2, and scalar Xi require the Rust core_functional adapter', witness=witness)
__all__ = ['HostPacket', 'GateResult', 'BqnfCertificateGate']
