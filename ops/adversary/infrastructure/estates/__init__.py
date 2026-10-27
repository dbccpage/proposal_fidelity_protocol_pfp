"""Estate adapters: the Adversary base swarm's connections to its sister estates.

Each adapter implements one port from ``adversary.domain.estate_ports`` and a
``probe`` that performs one real round trip inside a scratch root. These modules are the
only places in Adversary that import the estates they connect to.

AuthorityEffect: None.
"""
