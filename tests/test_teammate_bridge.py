"""Offline-only tests: every model transport is mocked; no remote calls."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
import teammate_bridge as bridge
import teammate_protocol as protocol


class FakeResponse(io.BytesIO):
    status = 200


def envelope(content='{"text":"On my way","action":"follow"}', **choice):
    return json.dumps({"choices": [{"finish_reason": "stop", "message": {
        "content": content}, **choice}]}).encode()


class TeammateBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.request_path, self.reply_path = root / "request", root / "reply"
        self.config_path = root / "config.json"
        self.request = protocol.WireMessage("session_1234567890", 2,
                                           "90071992547409931234", "none", "Follow me")
        protocol.atomic_write_wire(self.request_path, self.request)
        self.config = bridge.ModelConfig("https://example.invalid/v1/chat/completions",
                                         "fake-model", "test-secret", 4.5)
        self.transport = Mock(return_value=FakeResponse(envelope()))
        self.worker = bridge.TeammateBridge(config=self.config, opener=self.transport)
        # Test isolation: accidental default HTTP attempts fail locally.
        self.network = patch.object(bridge.urllib_request, "build_opener",
                                    side_effect=AssertionError("unexpected network"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def config_file(self, **updates):
        data = {"base_url": "https://example.invalid/v1", "model": "fake-model",
                "api_key": "test-secret"}
        data.update(updates)
        self.config_path.write_text(json.dumps(data), encoding="utf-8")
        return self.config_path

    def process(self):
        return self.worker.process_once(self.request_path, self.reply_path)

    def cli_args(self):
        return ["--request", str(self.request_path), "--reply", str(self.reply_path), "--once"]

    def test_full_correlation_prompt_timeout_and_bound(self):
        response = FakeResponse(envelope())
        response.read = Mock(wraps=response.read)
        self.transport.return_value = response
        result = self.process()
        self.assertEqual(protocol.parse_reply(self.reply_path.read_bytes(), self.request), result)
        self.assertEqual(result.action, "follow")
        self.assertEqual(result.text, "On my way")
        self.assertEqual(result.npc_id, "90071992547409931234")
        req = self.transport.call_args.args[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.get_header("Authorization"), "Bearer test-secret")
        payload = json.loads(req.data)
        self.assertIn("实体 NPC 队友", payload["messages"][0]["content"])
        self.assertIn("text 默认使用简体中文", payload["messages"][0]["content"])
        self.assertIn("512 字节", payload["messages"][0]["content"])
        self.assertIn('"none"、"follow" 或 "wait"', payload["messages"][0]["content"])
        self.assertEqual(json.loads(payload["messages"][1]["content"])["npc_id"], self.request.npc_id)
        self.assertEqual(self.transport.call_args.kwargs, {"timeout": 4.5})
        response.read.assert_called_once_with(protocol.MAX_MODEL_BYTES + 1)
        self.assertTrue(response.closed)
        self.assertEqual(list(Path(self.tmp.name).glob("*.tmp")), [])

    def test_json_mode_explicit_and_fail_closed(self):
        self.assertFalse(bridge.load_config(self.config_file()).json_mode)
        for bad in (1, 0, 'true', None, []):
            with self.assertRaises(bridge.BridgeError):
                bridge.load_config(self.config_file(json_mode=bad))
        config = bridge.load_config(self.config_file(json_mode=True))
        self.worker = bridge.TeammateBridge(config=config, opener=self.transport)
        self.process()
        self.assertEqual(json.loads(self.transport.call_args.args[0].data)['response_format'], {'type': 'json_object'})
        self.transport.return_value = FakeResponse(envelope('{"text":"x","action":"attack"}'))
        with self.assertRaises(bridge.BridgeError):
            bridge.call_model(self.request, config, opener=self.transport)

    def test_unknown_action_rejected_without_retry_or_replacing_reply(self):
        self.reply_path.write_bytes(b"previous reply")
        self.transport.return_value = FakeResponse(envelope('{"text":"x","action":"attack"}'))
        with self.assertRaises(bridge.BridgeError):
            self.process()
        with self.assertRaises(bridge.StaleRequest):
            self.process()
        self.transport.assert_called_once()
        self.assertEqual(self.reply_path.read_bytes(), b"previous reply")

    def test_missing_credential_config_and_explicit_real_mode(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.load_config(self.config_file(api_key=""))
        with self.assertRaises(bridge.BridgeError):
            bridge.TeammateBridge()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(bridge.main(self.cli_args()), 2)
            self.assertEqual(bridge.main(self.cli_args() + ["--config", str(self.config_path)]), 2)
        self.assertFalse(self.reply_path.exists())

    def test_stale_repeat_and_lower_sequence_and_session_switch(self):
        self.process()
        for seq in (2, 1):
            protocol.atomic_write_wire(self.request_path, protocol.WireMessage(
                self.request.session, seq, self.request.npc_id, "none", "Changed"))
            with self.assertRaises(bridge.StaleRequest):
                self.process()
        self.transport.assert_called_once()
        self.transport.return_value = FakeResponse(envelope())
        other = protocol.WireMessage("other_session_12345", 1, "12", "none", "Hello")
        protocol.atomic_write_wire(self.request_path, other)
        self.process()
        protocol.atomic_write_wire(self.request_path, self.request)
        with self.assertRaises(bridge.StaleRequest):
            self.process()
        self.assertEqual(self.transport.call_count, 2)

    def test_offline_cli_is_noop_labelled_and_no_http(self):
        self.assertEqual(bridge.main(self.cli_args() + ["--offline"]), 0)
        result = protocol.parse_reply(self.reply_path.read_bytes(), self.request)
        self.assertEqual(result.action, "none")
        self.assertIn("offline", result.text.lower())
        self.assertIn("离线模式：未执行动作", result.text)

    def test_chinese_help_and_safe_argument_errors(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exit_info:
            bridge.main(["--help"])
        self.assertEqual(exit_info.exception.code, 0)
        self.assertIn("用法：", output.getvalue())
        self.assertIn("显示帮助并退出", output.getvalue())
        self.assertNotIn("show this help", output.getvalue())
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as exit_info:
            bridge.main(["--bad-option", "sensitive-token"])
        self.assertEqual(exit_info.exception.code, 2)
        self.assertIn("参数无效", errors.getvalue())
        self.assertNotIn("sensitive-token", errors.getvalue())

    def test_real_cli_round_trip_with_mock_transport(self):
        self.config_file()
        self.network.stop()
        with patch.object(bridge.urllib_request, "build_opener") as factory:
            factory.return_value.open = self.transport
            self.assertEqual(bridge.main(self.cli_args() + ["--config", str(self.config_path)]), 0)
        self.assertEqual(protocol.parse_reply(self.reply_path.read_bytes(), self.request).action, "follow")

    def test_strict_wire_rejected_before_transport(self):
        for raw in (b"invalid", protocol.encode_wire(self.request).replace(b"\n", b"\r\n"),
                    b"a" * (protocol.MAX_WIRE_BYTES + 1)):
            self.request_path.write_bytes(raw)
            with self.assertRaises(protocol.ProtocolError):
                self.process()
        self.transport.assert_not_called()

    def test_bad_model_responses_fail_closed(self):
        responses = [b"not JSON", b"{}", envelope("```python\nprint('no')\n```"),
                     envelope('{"text":"x","action":"none","code":"x"}'),
                     envelope('{"text":"x","action":"none","action":"wait"}'),
                     envelope(finish_reason="length"), envelope(content=None),
                     b"x" * (protocol.MAX_MODEL_BYTES + 1)]
        for raw in responses:
            with self.subTest(raw=raw[:50]):
                transport = Mock(return_value=FakeResponse(raw))
                worker = bridge.TeammateBridge(config=self.config, opener=transport)
                with self.assertRaises(bridge.BridgeError):
                    worker.process_once(self.request_path, self.reply_path)
                transport.assert_called_once()
                self.assertFalse(self.reply_path.exists())

    def test_null_choices_cli_reports_safe_chinese_category(self):
        self.config_file()
        self.network.stop()
        self.transport.return_value = FakeResponse(b'{"choices":null,"debug":"test-secret remote-private"}')
        stderr = io.StringIO()
        with patch.object(bridge.urllib_request, 'build_opener') as factory:
            factory.return_value.open = self.transport
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(bridge.main(self.cli_args() + ['--config', str(self.config_path)]), 2)
        self.assertIn('模型接口未返回唯一有效候选', stderr.getvalue())
        self.assertNotIn('test-secret', stderr.getvalue())
        self.assertNotIn('remote-private', stderr.getvalue())
        self.assertFalse(self.reply_path.exists())
        self.transport.assert_called_once()

    def test_null_choices_preserves_previous_reply_and_claims_sequence(self):
        self.reply_path.write_bytes(b'previous session reply')
        self.transport.return_value = FakeResponse(b'{"choices":null,"object":"chat.completion"}')
        with self.assertRaises(bridge.BridgeError):
            self.process()
        self.assertEqual(self.reply_path.read_bytes(), b'previous session reply')
        with self.assertRaises(bridge.StaleRequest):
            self.process()
        self.transport.assert_called_once()

    def test_transport_failure_never_falls_back_or_leaks_credentials(self):
        self.config_file()
        self.network.stop()
        self.transport.side_effect = OSError("secret remote text test-secret")
        with patch.object(bridge.urllib_request, "build_opener") as factory:
            factory.return_value.open = self.transport
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(bridge.main(self.cli_args() + ["--config", str(self.config_path)]), 2)
        self.assertNotIn("test-secret", stderr.getvalue())
        self.assertNotIn("remote text", stderr.getvalue())
        self.assertFalse(self.reply_path.exists())
        self.transport.assert_called_once()
        self.assertNotIn("test-secret", repr(self.config))

    def test_watch_mode_duplicate_does_not_call_again(self):
        self.config_file()
        self.network.stop()
        with patch.object(bridge.urllib_request, "build_opener") as factory:
            factory.return_value.open = self.transport
            with patch.object(bridge.time, "sleep", side_effect=[None, KeyboardInterrupt]):
                self.assertEqual(bridge.main(self.cli_args()[:-1] + ["--config", str(self.config_path)]), 0)
        self.transport.assert_called_once()

    def test_request_snapshot_is_not_read_again_during_transport(self):
        def replace_request(*args, **kwargs):
            protocol.atomic_write_wire(self.request_path, protocol.WireMessage(
                self.request.session, 3, "4", "none", "different"))
            return FakeResponse(envelope())
        self.transport.side_effect = replace_request
        self.process()
        protocol.parse_reply(self.reply_path.read_bytes(), self.request)

    def test_config_validation_and_mailbox_aliases(self):
        for updates in ({"timeout_sec": float("inf")}, {"timeout_sec": True},
                        {"timeout_sec": -1}, {"api_key": "bad\r\nkey"},
                        {"base_url": "file:///tmp/model"},
                        {"base_url": "https://user:secret@example.invalid"}):
            with self.subTest(updates=updates), self.assertRaises(bridge.BridgeError):
                bridge.load_config(self.config_file(**updates))
        with self.assertRaises(bridge.BridgeError):
            self.worker.process_once(self.request_path, self.request_path)
        with self.assertRaises(bridge.BridgeError):
            bridge.validate_paths(self.request_path, self.reply_path, self.reply_path)

    def test_redirect_is_refused(self):
        with self.assertRaises(bridge.BridgeError):
            bridge._NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid")


if __name__ == "__main__":
    unittest.main()
