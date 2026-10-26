"""Integration tests for LegacyCatalogReaderAdapter."""

import unittest

from omega_engine_operads.domain.value_objects import EstateRef
from omega_engine_operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
)
from omega_engine_operads.infrastructure.fs.legacy_catalog_reader_adapter import (
    LegacyCatalogReaderAdapter,
)


class LegacyCatalogReaderAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = LegacyCatalogReaderAdapter()

    def test_read_legacy_estate_reads_skills_and_agents_from_disk(self) -> None:
        res = self.adapter.read_legacy_estate(EstateRef("canonical"))
        self.assertTrue(res.is_ok)
        docs = res.unwrap()
        self.assertGreater(len(docs), 0)
        self.assertGreater(len(docs[0].operations), 0)
        self.assertEqual(docs[0].operations[0].lifecycle.admission, AdmissionFacet.UNADMITTED)
