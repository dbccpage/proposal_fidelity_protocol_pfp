"""Exact algebraic certificate checker for C020."""

from __future__ import annotations

from typing import Any

from ...reference_solver.solver import solve as ref_solve


def check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    status = cert.get("status")
    expected = ref_solve(case)
    expected_status = expected.get("status")

    if status != expected_status:
        return {
            "verdict": "FAIL",
            "reason": f"Status mismatch: expected {expected_status}, got {status}",
        }

    if status == "OUT_OF_SCOPE":
        expected_witness = expected.get("witness", {})
        cert_witness = cert.get("witness", {})
        if not isinstance(cert_witness, dict):
            return {
                "verdict": "FAIL",
                "reason": "OUT_OF_SCOPE witness must be a mapping",
            }
        if cert_witness.get("reason") != expected_witness.get("reason"):
            return {
                "verdict": "FAIL",
                "reason": f"Witness reason mismatch: expected {expected_witness.get('reason')}, got {cert_witness.get('reason')}",
            }
        if cert_witness.get("generator") != expected_witness.get("generator"):
            return {
                "verdict": "FAIL",
                "reason": f"Witness generator mismatch: expected {expected_witness.get('generator')}, got {cert_witness.get('generator')}",
            }
        return {"verdict": "PASS", "details": "Out of scope witness confirmed"}

    if status != "SOLVED":
        return {"verdict": "FAIL", "reason": f"Unsupported status: {status}"}

    # Verify filtration
    req_filt = case.get("filtration", "columns")
    cert_filt = cert.get("filtration")
    if cert_filt != req_filt:
        return {
            "verdict": "FAIL",
            "reason": f"Filtration mismatch: expected {req_filt}, got {cert_filt}",
        }

    def verify_single_filtration(
        exp_data: dict[str, Any], act_data: dict[str, Any], filt_label: str
    ) -> dict[str, Any] | None:
        # Check E2
        exp_e2 = exp_data.get("E2", {})
        act_e2 = act_data.get("E2", {})
        if exp_e2 != act_e2:
            return {
                "verdict": "FAIL",
                "reason": f"[{filt_label}] E2 mismatch: expected {exp_e2}, got {act_e2}",
            }

        # Check differentials
        exp_diffs = sorted(
            exp_data.get("differentials", []), key=lambda d: (int(d["r"]), d["from"])
        )
        act_diffs = sorted(
            act_data.get("differentials", []), key=lambda d: (int(d.get("r", 0)), d.get("from", ""))
        )
        if exp_diffs != act_diffs:
            return {
                "verdict": "FAIL",
                "reason": f"[{filt_label}] Differentials mismatch: expected {exp_diffs}, got {act_diffs}",
            }

        # Check Einf
        exp_einf = exp_data.get("Einf", {})
        act_einf = act_data.get("Einf", {})
        if exp_einf != act_einf:
            return {
                "verdict": "FAIL",
                "reason": f"[{filt_label}] Einf mismatch: expected {exp_einf}, got {act_einf}",
            }

        # Verify page recursion on reported numbers
        # In columns: d_r: (p, q) -> (p - r, q + r - 1)
        # In rows:    d_r: (p, q) -> (p + r - 1, q - r)
        diff_by_r: dict[int, list[dict[str, str]]] = {}
        for d in act_diffs:
            r = int(d["r"])
            diff_by_r.setdefault(r, []).append(d)

        curr_page = {k: int(v) for k, v in act_e2.items()}
        for r in range(2, 6):
            next_page = dict(curr_page)
            for d in diff_by_r.get(r, []):
                p_str, q_str = d["from"].split(",")
                p, q = int(p_str), int(q_str)
                rank = int(d["rank"])
                # Source position
                next_page[f"{p},{q}"] = next_page.get(f"{p},{q}", 0) - rank
                # Target position
                if filt_label == "columns":
                    tgt_p = p - r
                    tgt_q = q + r - 1
                else:
                    tgt_p = p + r - 1
                    tgt_q = q - r

                if tgt_p >= 0 and tgt_q >= 0:
                    next_page[f"{tgt_p},{tgt_q}"] = next_page.get(f"{tgt_p},{tgt_q}", 0) - rank

            next_page = {k: v for k, v in next_page.items() if v != 0}
            for k, v in next_page.items():
                if v < 0:
                    return {
                        "verdict": "FAIL",
                        "reason": f"[{filt_label}] Page recursion defect: negative dimension {v} at {k} on page E^{r + 1}",
                    }
            curr_page = next_page

        calc_einf = {k: str(v) for k, v in curr_page.items() if v > 0}
        if calc_einf != act_einf:
            return {
                "verdict": "FAIL",
                "reason": f"[{filt_label}] Abutment recursion defect: page recursion yields {calc_einf}, but Einf is {act_einf}",
            }

        return None

    if req_filt == "both":
        err_c = verify_single_filtration(
            expected.get("columns", {}), cert.get("columns", {}), "columns"
        )
        if err_c:
            return err_c
        err_r = verify_single_filtration(expected.get("rows", {}), cert.get("rows", {}), "rows")
        if err_r:
            return err_r
        exp_tot = expected.get("tot_homology", {})
        act_tot = cert.get("tot_homology", {})
        if exp_tot != act_tot:
            return {
                "verdict": "FAIL",
                "reason": f"Total homology mismatch: expected {exp_tot}, got {act_tot}",
            }
        for filt_key in ["columns", "rows"]:
            einf = cert[filt_key].get("Einf", {})
            for n in range(11):
                sum_n = sum(int(v) for k, v in einf.items() if sum(map(int, k.split(","))) == n)
                exp_hn = int(act_tot.get(str(n), 0))
                if sum_n != exp_hn:
                    return {
                        "verdict": "FAIL",
                        "reason": f"[{filt_key}] Abutment theorem violated at degree {n}: sum Einf {sum_n} != dim H_n(Tot) {exp_hn}",
                    }
    else:
        err = verify_single_filtration(expected, cert, req_filt)
        if err:
            return err
        exp_tot = expected.get("tot_homology", {})
        act_tot = cert.get("tot_homology", {})
        if exp_tot != act_tot:
            return {
                "verdict": "FAIL",
                "reason": f"Total homology mismatch: expected {exp_tot}, got {act_tot}",
            }
        einf = cert.get("Einf", {})
        for n in range(11):
            sum_n = sum(int(v) for k, v in einf.items() if sum(map(int, k.split(","))) == n)
            exp_hn = int(act_tot.get(str(n), 0))
            if sum_n != exp_hn:
                return {
                    "verdict": "FAIL",
                    "reason": f"Abutment theorem violated at degree {n}: sum Einf {sum_n} != dim H_n(Tot) {exp_hn}",
                }

    return {
        "verdict": "PASS",
        "details": "All pages, differentials, page recursions, and abutments verified",
    }
