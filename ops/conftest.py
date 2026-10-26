"""Repository-wide test isolation.

AuthorityEffect: None. Credential discovery reads a developer's real `.env`, so it is off for
every test. A test of discovery turns it on for itself and supplies its own directories.
"""

import importlib
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import Sequence

import pytest


class _AliasLoader(Loader):
    """Return the loaded canonical module without executing its source again."""

    def __init__(self, module: ModuleType) -> None:
        self.module = module

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        return self.module

    def exec_module(self, module: ModuleType) -> None:
        pass


class _MssnSnSymgamAliasFinder(MetaPathFinder):
    """Transparently redirects imports from legacy omega_engine_projects paths to canonical packages."""

    _PREFIX_OLD = "omega_engine_projects.mssn_sn_symgam"
    _PREFIX_NEW = "omega_engine_woland.tests.pilots"

    def __init__(self) -> None:
        self._repo_root = Path(__file__).resolve().parent
        mub6_code = (
            self._repo_root
            / "omega_engine_atlas"
            / "coda_atlas"
            / "F004_papers"
            / "010_mub6"
            / "code"
        )
        if mub6_code.exists() and str(mub6_code) not in sys.path:
            sys.path.insert(0, str(mub6_code))
        fqm_python = (
            self._repo_root
            / "omega_engine_atlas"
            / "coda_atlas"
            / "F004_papers"
            / "006_finite_qm"
            / "python"
        )
        if fqm_python.exists() and str(fqm_python) not in sys.path:
            sys.path.insert(0, str(fqm_python))

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if fullname == "omega_engine_projects":
            mod = ModuleType("omega_engine_projects")
            mod.__path__ = []
            return ModuleSpec(fullname, _AliasLoader(mod), is_package=True)

        if fullname == self._PREFIX_OLD or fullname.startswith(f"{self._PREFIX_OLD}."):
            sub = fullname[len(self._PREFIX_OLD):]
            if sub.startswith(".upgrades"):
                target_name = f"omega_engine_education.curriculum.the_symbol_game{sub}"
            elif sub == ".challenges.f_program_synthesis.c059_sql_null_total_query_synthesis" or sub.startswith(".challenges.f_program_synthesis.c059_sql_null_total_query_synthesis."):
                target_name = f"omega_engine_pfp.tests.pilots.c059_sql_null_total_query_synthesis{sub[len('.challenges.f_program_synthesis.c059_sql_null_total_query_synthesis'):]}"
            elif sub == ".challenges.f_program_synthesis.c051_exact_lp_solver_with_duals" or sub.startswith(".challenges.f_program_synthesis.c051_exact_lp_solver_with_duals."):
                target_name = f"omega_engine_pfp.tests.pilots.c051_exact_lp_solver_with_duals{sub[len('.challenges.f_program_synthesis.c051_exact_lp_solver_with_duals'):]}"
            elif sub == ".challenges.f_program_synthesis.c052_maxflow_mincut_certificates" or sub.startswith(".challenges.f_program_synthesis.c052_maxflow_mincut_certificates."):
                target_name = f"omega_engine_pfp.tests.pilots.c052_maxflow_mincut_certificates{sub[len('.challenges.f_program_synthesis.c052_maxflow_mincut_certificates'):]}"
            elif sub == ".challenges.f_program_synthesis.c053_bareiss_fraction_free_matrix_inversion" or sub.startswith(".challenges.f_program_synthesis.c053_bareiss_fraction_free_matrix_inversion."):
                target_name = f"omega_engine_pfp.tests.pilots.c053_bareiss_fraction_free_matrix_inversion{sub[len('.challenges.f_program_synthesis.c053_bareiss_fraction_free_matrix_inversion'):]}"
            elif sub == ".challenges.f_program_synthesis.c054_exact_linear_systems" or sub.startswith(".challenges.f_program_synthesis.c054_exact_linear_systems."):
                target_name = f"omega_engine_pfp.tests.pilots.c054_exact_linear_systems{sub[len('.challenges.f_program_synthesis.c054_exact_linear_systems'):]}"
            elif sub == ".challenges.f_program_synthesis.c055_assignment_with_potentials" or sub.startswith(".challenges.f_program_synthesis.c055_assignment_with_potentials."):
                target_name = f"omega_engine_pfp.tests.pilots.c055_assignment_with_potentials{sub[len('.challenges.f_program_synthesis.c055_assignment_with_potentials'):]}"
            elif sub == ".challenges" or sub.startswith(".challenges."):
                target_name = f"omega_engine_pfp.tests.demo_004{sub[len('.challenges'):]}"
            elif sub == ".demos":
                target_name = f"{self._PREFIX_NEW}"
            elif sub.startswith(".demos."):
                target_name = f"{self._PREFIX_NEW}{sub[len('.demos'):]}"
            elif sub == ".judge_audit.tests" or sub.startswith(".judge_audit.tests."):
                target_name = f"omega_engine_pfp.tests.judge_audit{sub[len('.judge_audit.tests'):]}"
            elif sub == ".judge_audit" or sub.startswith(".judge_audit."):
                target_name = f"omega_engine_woland.tests.pilots.judge_packet_audit{sub[len('.judge_audit'):]}"
            else:
                target_name = f"{self._PREFIX_NEW}{sub}"
            target_mod = importlib.import_module(target_name)
            return ModuleSpec(
                fullname,
                _AliasLoader(target_mod),
                is_package=hasattr(target_mod, "__path__"),
            )

        if fullname == "omega_engine_projects.mub6" or fullname.startswith("omega_engine_projects.mub6."):
            sub = fullname[len("omega_engine_projects.mub6"):]
            if sub in ("", ".code"):
                mod = ModuleType(fullname)
                mod.__path__ = []
                return ModuleSpec(fullname, _AliasLoader(mod), is_package=True)
            if sub.startswith(".code.mub_verify"):
                target_name = f"mub_verify{sub[len('.code.mub_verify'):]}"
                target_mod = importlib.import_module(target_name)
                return ModuleSpec(
                    fullname,
                    _AliasLoader(target_mod),
                    is_package=hasattr(target_mod, "__path__"),
                )

        if fullname == "omega_engine_projects.finite_qm" or fullname.startswith("omega_engine_projects.finite_qm."):
            sub = fullname[len("omega_engine_projects.finite_qm"):]
            if sub in ("", ".python"):
                mod = ModuleType(fullname)
                mod.__path__ = []
                return ModuleSpec(fullname, _AliasLoader(mod), is_package=True)
            if sub.startswith(".python.finite_qm"):
                target_name = f"finite_qm{sub[len('.python.finite_qm'):]}"
                target_mod = importlib.import_module(target_name)
                return ModuleSpec(
                    fullname,
                    _AliasLoader(target_mod),
                    is_package=hasattr(target_mod, "__path__"),
                )
            if sub.startswith(".finite_qm"):
                target_name = f"finite_qm{sub[len('.finite_qm'):]}"
                target_mod = importlib.import_module(target_name)
                return ModuleSpec(
                    fullname,
                    _AliasLoader(target_mod),
                    is_package=hasattr(target_mod, "__path__"),
                )

        return None


if not any(isinstance(finder, _MssnSnSymgamAliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _MssnSnSymgamAliasFinder())


@pytest.fixture(autouse=True)
def _credential_discovery_off(monkeypatch):
    monkeypatch.setenv("OMEGA_CREDENTIAL_DISCOVERY", "off")


def _bind_stage_ddc_alphabet() -> None:
    from omega_engine_woland.stage.ddc_alphabet_source import install_ddc_alphabet

    install_ddc_alphabet()


_bind_stage_ddc_alphabet()
