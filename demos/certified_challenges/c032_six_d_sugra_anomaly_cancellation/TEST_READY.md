# TEST_READY: Challenge C032 (6D Supergravity Anomaly Cancellation)

**AuthorityEffect:** None.  
**Status:** READY FOR VERIFICATION.  
**Date:** 2026-09-27  

## Test Commands (Local Sequential Execution)
```bash
# 1. Participant Packet & Reference Solver
python -m pytest demos/certified_challenges/c032_six_d_sugra_anomaly_cancellation/tests/test_c032_participant_packet.py demos/certified_challenges/c032_six_d_sugra_anomaly_cancellation/tests/test_c032_reference_solver.py -v

# 2. Dual Checkers & Mutation Suite
python -m pytest demos/certified_challenges/c032_six_d_sugra_anomaly_cancellation/tests/test_c032_dual_checkers.py demos/certified_challenges/c032_six_d_sugra_anomaly_cancellation/judge_packet/mutation_suite/test_c032_checker_mutations.py -v

# 3. Governance & E2E Integration
python -m pytest demos/certified_challenges/c032_six_d_sugra_anomaly_cancellation/tests/test_governance_and_commit_reveal.py demos/certified_challenges/c032_six_d_sugra_anomaly_cancellation/tests/test_e2e_challenge.py -v
```
