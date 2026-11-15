"""Keep reviewable hosted fixtures tied to the current production source."""
import contextlib
import importlib.util
import io
import hashlib
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from test_review_regressions import Decisions

FOLDER = Path(__file__).resolve().parent / "hosted"


def load_builder():
    spec = importlib.util.spec_from_file_location("hosted_builder", FOLDER / "build_fixtures.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder


class HostedFixtureSync(unittest.TestCase):
    def test_native_message_probe_matches_production_helpers(self):
        source = (FOLDER.parent.parent / "futures_v7_5.pine").read_text(encoding="utf-8")
        probe = (FOLDER / "release_message_check.pine").read_text(encoding="utf-8")
        self.assertIn(hashlib.sha256(source.encode("utf-8")).hexdigest(), probe)
        for name in ("eventIdentity", "jsonIntOrNull", "jsonNumberOrNull", "jsonString", "alertPayload"):
            pattern = rf"^{name}\([^\n]*\) =>\n(?:    [^\n]*\n)+"
            original = re.search(pattern, source, re.MULTILINE)
            copied = re.search(pattern, probe, re.MULTILINE)
            self.assertIsNotNone(original, name)
            self.assertIsNotNone(copied, name)
            self.assertEqual(original.group(), copied.group(), name)

    def test_generated_fixtures_match_production(self):
        builder = load_builder()
        generated = {}
        def capture(path, text, **options):
            generated[path.name] = text
            return len(text)
        with patch.object(Path, "write_text", new=capture):
            with contextlib.redirect_stdout(io.StringIO()):
                builder.build()
        self.assertEqual(set(generated), {"indicator_lifecycle.pine", "accounting_reconciliation.pine"})
        for name, text in generated.items():
            self.assertEqual((FOLDER / name).read_text(encoding="utf-8"), text, name)

    def test_instrumentation_rejects_missing_or_ambiguous_anchor(self):
        builder = load_builder()
        self.assertEqual(builder.replace_once("before TARGET after", "TARGET", "audit"), "before audit after")
        for source in ("renamed", "TARGET TARGET"):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "exactly one source anchor"):
                builder.replace_once(source, "TARGET", "audit")

    def test_title_drift_fails_before_any_fixture_is_written(self):
        builder = load_builder()
        original_read = Path.read_text
        title = 'indicator("Liquidity + Structure Monitor v1.1.1", shorttitle = "LSM v1.1.1"'
        for replacement in ('indicator("Renamed', title + "\n" + title):
            def altered_read(path, **options):
                text = original_read(path, **options)
                if path.name == "liquidity_structure_v1.pine":
                    text = text.replace(title, replacement)
                return text
            with self.subTest(replacement=replacement), patch.object(Path, "read_text", new=altered_read), patch.object(Path, "write_text") as write:
                with self.assertRaisesRegex(ValueError, "exactly one source anchor"):
                    builder.build()
                write.assert_not_called()

    def test_accounting_fixture_rejects_unsupported_chart_context(self):
        source = (FOLDER / "accounting_reconciliation.pine").read_text(encoding="utf-8")
        engine = Decisions(source)
        symbol = dict(root="MNQ", currency="USD", pointvalue=2, mintick=0.25)
        def supported(standard=True, seconds=60, **changes):
            return engine.assignment("auditChartSupported", chart=SimpleNamespace(is_standard=standard),
                                     timeframe=SimpleNamespace(in_seconds=lambda: seconds),
                                     syminfo=SimpleNamespace(**(symbol | changes)))
        self.assertTrue(supported())
        for context in (dict(standard=False), dict(seconds=300), dict(root="NQ"),
                        dict(currency="EUR"), dict(pointvalue=20), dict(mintick=0.5)):
            with self.subTest(context=context):
                self.assertFalse(supported(**context))
        self.assertIn("if barstate.isfirst and not auditChartSupported", source)
