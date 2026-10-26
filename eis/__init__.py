"""Omega Engine Epistemic Immune System (OEEIS).

The one owner of the package's immune logic. Other bounded contexts (OEWAS,
the Woland swarm) consume it through application-layer ports.

What is implemented:

- a two-signal danger gate that suppresses only when a detector match
  (Signal 1) and host-observed damage (Signal 2) co-occur, and a screening use
  case that refuses a Signal 2 derived from Signal 1 (`TWO_SIGNAL_COLLAPSE`);
- thymic negative selection: a rule is screened against a panel of clean
  fixtures with the matcher that will run it;
- an exact allosteric gate, which is a threshold on summed sensor signals with
  a per-sensor cap that yields a minimum number of sensors;
- idle-run counters for detector rules (linear, not an exponential half-life);
- learned-guard activation (`EPIC-OE-IMMUNE-002`) and external antibody
  admission (`EPIC-OE-PHARMACY-001`);
- matchers for the pharmacy failure classes (native `pharmacy_detect`), the
  farm classifier and the Demo 3 protocol codes.

Regulatory T-cell supervision lives in OEWAS (`domain/operad/treg.py`), not
here. Nothing in this package learns, selects rules by affinity, or admits
anything by itself.
"""

from __future__ import annotations

__version__ = "0.1.0"
