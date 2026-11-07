"""Unit tests for local runner, sample generation, and reporting scripts."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import URLError

from scripts import generate_sample_documents, run_coverage, run_local, run_tests

TEST_DATA = Path(__file__).resolve().parents[2] / "data"


class SuccessfulResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


class FakeProcess:
    def __init__(self, exit_code=None):
        self.exit_code = exit_code
        self.terminated = False

    def poll(self):
        return self.exit_code

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        self.exit_code = 0
        return 0


class ProjectScriptTests(unittest.TestCase):
    def test_local_environment_parser_handles_comments_quotes_spaces_and_missing_file(self):
        with tempfile.TemporaryDirectory(dir=TEST_DATA) as temp:
            path = Path(temp) / "local.env"
            path.write_text("# comment\n\n HOST = 127.0.0.1 \nKEY='quoted value'\nIGNORED\n", encoding="utf-8")
            self.assertEqual(run_local.load_env(path), {"HOST": "127.0.0.1", "KEY": "quoted value"})
            self.assertEqual(run_local.load_env(path.with_name("missing.env")), {})

    def test_local_runner_can_start_one_service_and_stops_after_keyboard_interrupt(self):
        with tempfile.TemporaryDirectory(dir=TEST_DATA) as temp:
            root = Path(temp)
            (root / "config").mkdir()
            (root / "frontend").mkdir()
            (root / "config/local.env").write_text(
                "FRONTEND_PORT=5173\nCONTRACT_API_URL=http://127.0.0.1:8001\n"
                "PRICING_API_URL=http://127.0.0.1:8002\nBILLING_API_URL=http://127.0.0.1:8003\n",
                encoding="utf-8",
            )
            process = FakeProcess()
            with patch.object(run_local, "ROOT", root), patch.object(run_local.subprocess, "Popen", return_value=process) as popen, \
                    patch.object(run_local, "urlopen", return_value=SuccessfulResponse()), \
                    patch.object(run_local.time, "sleep", side_effect=KeyboardInterrupt), \
                    patch("sys.argv", ["run_local.py", "--only", "frontend"]):
                self.assertEqual(run_local.main(), 0)
            self.assertTrue(process.terminated)
            self.assertEqual(len(popen.call_args_list), 1)
            command = popen.call_args.args[0]
            self.assertEqual(command[2], "http.server")
            self.assertEqual(Path(command[command.index("--directory") + 1]), root / "frontend")
            self.assertTrue((root / "frontend/runtime-config.js").is_file())

    def test_local_runner_reports_process_that_exits_during_startup(self):
        with tempfile.TemporaryDirectory(dir=TEST_DATA) as temp:
            root = Path(temp)
            (root / "config").mkdir()
            (root / "frontend").mkdir()
            (root / "config/local.env").write_text("HOST=127.0.0.1\n", encoding="utf-8")
            with patch.object(run_local, "ROOT", root), patch.object(run_local.subprocess, "Popen", return_value=FakeProcess(1)), \
                    patch.object(run_local, "urlopen", return_value=SuccessfulResponse()), \
                    patch("sys.argv", ["run_local.py", "--only", "frontend"]):
                self.assertEqual(run_local.main(), 1)

    def test_local_runner_reports_service_that_never_becomes_ready(self):
        with tempfile.TemporaryDirectory(dir=TEST_DATA) as temp:
            root = Path(temp)
            (root / "config").mkdir()
            (root / "frontend").mkdir()
            (root / "config/local.env").write_text("HOST=127.0.0.1\n", encoding="utf-8")
            with patch.object(run_local, "ROOT", root), patch.object(run_local.subprocess, "Popen", return_value=FakeProcess()), \
                    patch.object(run_local, "urlopen", side_effect=URLError("offline")), \
                    patch.object(run_local.time, "sleep", return_value=None), \
                    patch("sys.argv", ["run_local.py", "--only", "frontend"]):
                self.assertEqual(run_local.main(), 1)

    def test_sample_generator_creates_demo_and_test_upload_pdfs(self):
        with tempfile.TemporaryDirectory(dir=TEST_DATA) as temp, patch.object(generate_sample_documents, "SAMPLE_ROOT", Path(temp)):
            generate_sample_documents.main()
            files = list(Path(temp).rglob("*.pdf"))
            self.assertEqual(len(files), 18)
            self.assertEqual(len(list((Path(temp) / "contracts").rglob("*.pdf"))), 4)
            self.assertEqual(len(list((Path(temp) / "billing").rglob("*.pdf"))), 12)
            self.assertEqual(len(list((Path(temp) / "test_uploads").rglob("*.pdf"))), 2)

    def test_one_command_test_runner_discovers_every_owned_suite(self):
        self.assertTrue(run_tests.TEST_FOLDERS)
        self.assertTrue(all(path.is_dir() for path in run_tests.TEST_FOLDERS))
        self.assertEqual(run_coverage.percent(3, 4), "75.0%")
        self.assertEqual(run_coverage.percent(0, 0), "n/a")
        report = {"a.py": {"summary": {"num_statements": 5, "covered_lines": 3, "missing_lines": 2}}}
        self.assertEqual(run_coverage.sum_files(report, "a.py"), (5, 3, 2))
        ui_spec = Path(generate_sample_documents.__file__).with_name("not_a_test.js")
        self.assertEqual(run_coverage.count_playwright_cases(ui_spec), 0)


if __name__ == "__main__":
    unittest.main()
