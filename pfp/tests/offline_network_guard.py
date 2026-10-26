"""Opt-in pytest plugin forbidding socket connections. AuthorityEffect: None.

Load with -p omega_engine_pfp.tests.offline_network_guard.
"""

import socket


def _blocked(*args, **kwargs):
    raise RuntimeError("P0_OFFLINE_VALIDATION_NETWORK_FORBIDDEN")


socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
