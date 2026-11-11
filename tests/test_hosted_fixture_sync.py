"""Keep reviewable hosted fixtures tied to the current production source."""
import contextlib
import importlib.util
import io
from pathlib import Path
from unittest.mock import patch
import unittest


class HostedFixtureSync(unittest.TestCase):
    def test_generated_fixtures_match_production(self):
        folder = Path(__file__).resolve().parent / "hosted"
        spec = importlib.util.spec_from_file_location("hosted_builder", folder / "build_fixtures.py")
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        generated = {}
        def capture(path, text, **options):
            generated[path.name] = text
            return len(text)
        with patch.object(Path, "write_text", new=capture):
            with contextlib.redirect_stdout(io.StringIO()):
                builder.build()
        self.assertEqual(set(generated), {"indicator_lifecycle.pine", "accounting_reconciliation.pine"})
        for name, text in generated.items():
            self.assertEqual((folder / name).read_text(encoding="utf-8"), text, name)
