#!/usr/bin/env python3
"""Contract tests for inert episode input and deterministic metrics."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skill_compiler.episode import INPUT_SCHEMA, load_episode_input, make_episode
from skill_compiler.metrics import RUN_SCHEMA, load_run, summarize


class EpisodeInputTests(unittest.TestCase):
    def test_json_file_preserves_quotes_as_data(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "episode.json"
            payload = {
                "schema": INPUT_SCHEMA,
                "source": "autoskill",
                "signal_type": "user_correction",
                "signal": 'User said "Stop doing that!" and used $HOME literally.',
                "proposed_invariant": "Treat candidate prose as inert data.",
                "evidence": ["session:42"],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_episode_input(path)
            episode = make_episode(
                source=loaded["source"],
                signal_type=loaded["signal_type"],
                signal=loaded["signal"],
                proposed_invariant=loaded["proposed_invariant"],
                evidence=loaded["evidence"],
            )
            self.assertEqual(episode["signal"], payload["signal"])
            self.assertEqual(episode["evidence"], ["session:42"])

    def test_unknown_input_field_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "episode.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": INPUT_SCHEMA,
                        "source": "autoskill",
                        "signal": "x",
                        "proposed_invariant": "y",
                        "authority_effect": "Minted",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unknown episode input fields"):
                load_episode_input(path)


class MetricsTests(unittest.TestCase):
    def test_counts_are_derived_from_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "run.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": RUN_SCHEMA,
                        "session_id": "s1",
                        "signals": [
                            {
                                "signal_type": "correction",
                                "description": "first",
                                "durable": True,
                                "confidence": "HIGH",
                                "evidence": ["file:1"],
                            },
                            {
                                "signal_type": "correction",
                                "description": "second",
                                "durable": False,
                                "confidence": "LOW",
                                "evidence": [],
                            },
                        ],
                        "proposals": [{"id": "p1"}],
                    }
                ),
                encoding="utf-8",
            )
            result = summarize(load_run(path), root)
            self.assertEqual(result["signal_count"], 2)
            self.assertEqual(result["durable_signal_count"], 1)
            self.assertEqual(result["signals_by_type"], {"correction": 2})
            self.assertEqual(result["proposal_count"], 1)
            self.assertIsNone(result["capture_rate"])


if __name__ == "__main__":
    unittest.main()
