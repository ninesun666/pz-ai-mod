import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('standalone_monitor', ROOT / 'standalone/runtime/monitor_run.py')
MONITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MONITOR)


class MonitorTests(unittest.TestCase):
    def test_terminal_report_stops_without_waiting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'stdout.log').write_text('[DCStandaloneTest] world started\n[DCStandalone] diag finder=found\n')
            (root / 'report.json').write_text(json.dumps({'passed': False, 'reason': 'follow timeout'}))
            output = io.StringIO()
            with patch.object(MONITOR, 'capture', return_value=True) as capture, \
                    patch.object(MONITOR.time, 'sleep') as sleep, contextlib.redirect_stdout(output):
                MONITOR.main([directory, '30'])
            sleep.assert_not_called()
            capture.assert_called_once()
            self.assertIn('finder=found', output.getvalue())
            self.assertIn('terminal report passed=False reason=follow timeout', output.getvalue())

    def test_diagnostics_are_not_one_time_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / 'stdout.log'
            log.write_text('[DCStandalone] diag finder=notrunning\n')
            def advance(_):
                log.write_text('[DCStandalone] diag finder=notrunning\n[DCStandalone] diag finder=found\n')
                (root / 'report.json').write_text('{"passed": false}')
            output = io.StringIO()
            with patch.object(MONITOR.time, 'sleep', side_effect=advance), contextlib.redirect_stdout(output):
                MONITOR.main([directory, '30'])
            self.assertIn('finder=notrunning', output.getvalue())
            self.assertIn('finder=found', output.getvalue())


if __name__ == '__main__':
    unittest.main()
