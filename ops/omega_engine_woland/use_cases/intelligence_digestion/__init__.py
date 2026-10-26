"""Intelligence Digestion & Archiving Use Cases.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .corpora_scraper import CorporaScraper
    from .digestion_service import DigestionDependencies, DigestionReceipt, DigestionRecord, IntelligenceDigestionService, digest_and_archive_intelligence, read_run_findings_result
    from .omc_dag_miner import OMCDagMiner, devour_and_archive_omc_dags
    from .paper_review_miner import PaperReviewMiner

__all__ = ['CorporaScraper', 'DigestionDependencies', 'DigestionReceipt', 'DigestionRecord', 'IntelligenceDigestionService', 'OMCDagMiner', 'PaperReviewMiner', 'devour_and_archive_omc_dags', 'digest_and_archive_intelligence', 'read_run_findings_result']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CorporaScraper': ('.corpora_scraper', 'CorporaScraper'),
    'DigestionDependencies': ('.digestion_service', 'DigestionDependencies'),
    'DigestionReceipt': ('.digestion_service', 'DigestionReceipt'),
    'DigestionRecord': ('.digestion_service', 'DigestionRecord'),
    'IntelligenceDigestionService': ('.digestion_service', 'IntelligenceDigestionService'),
    'digest_and_archive_intelligence': ('.digestion_service', 'digest_and_archive_intelligence'),
    'read_run_findings_result': ('.digestion_service', 'read_run_findings_result'),
    'OMCDagMiner': ('.omc_dag_miner', 'OMCDagMiner'),
    'devour_and_archive_omc_dags': ('.omc_dag_miner', 'devour_and_archive_omc_dags'),
    'PaperReviewMiner': ('.paper_review_miner', 'PaperReviewMiner'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
