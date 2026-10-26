"""Run directly: python -B ai-mod/tests/test_teammate_protocol.py"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
import teammate_protocol as p


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.request = p.WireMessage("a" * 32, 1, "9007199254740993", "none", "hello")
        self.wire = p.encode_wire(self.request).decode("utf-8")

    def test_valid_follow_wait_noop(self):
        for action in ("follow", "wait", "none"):
            with self.subTest(action=action):
                decision = p.parse_model_json(json.dumps({"text": "你好 = yes", "action": action}))
                reply = p.make_reply(self.request, decision)
                self.assertEqual(p.parse_reply(p.encode_wire(reply), self.request), reply)
                self.assertEqual(reply.npc_id, "9007199254740993")
                self.assertEqual(reply.action, action)
        self.assertEqual(p.parse_request(self.wire), self.request)

    def test_stale_session(self):
        with self.assertRaisesRegex(p.ProtocolError, "session"):
            p.parse_reply(self.wire.replace("a" * 32, "b" * 32), self.request)

    def test_seq_mismatch(self):
        with self.assertRaisesRegex(p.ProtocolError, "seq"):
            p.parse_reply(self.wire.replace("seq=1", "seq=2"), self.request)

    def test_exact_npc_mismatch(self):
        with self.assertRaisesRegex(p.ProtocolError, "npc_id"):
            p.parse_reply(self.wire.replace("9007199254740993", "9007199254740992"), self.request)

    def test_malformed_json_and_no_eval(self):
        cases = ["", "{", "[]", "null", "true", "42", "{}",
                 "{'text':'x','action':'none'}", '```json\n{}\n```',
                 '__import__("os").system("echo forbidden")',
                 '{"text":"x","action":"none"} trailing',
                 '{"text":"x","text":"y","action":"none"}',
                 '{"text":NaN,"action":"none"}',
                 '{"text":Infinity,"action":"none"}',
                 '{"text":"x","action":"none","extra":0}',
                 '{"text":"x"}', b'\xff', '\ufeff{}', '[' * 2000]
        for source in cases:
            with self.subTest(source=repr(source[:80])), self.assertRaises(p.ProtocolError):
                p.parse_model_json(source)

    def test_model_type_errors_and_commands(self):
        for text in (None, 0, True, [], {}):
            with self.subTest(text=text), self.assertRaises(p.ProtocolError):
                p.parse_model_json(json.dumps({"text": text, "action": "none"}))
        for action in (None, True, 1, [], {}, "", "noop", "attack", "FOLLOW", "wait "):
            with self.subTest(action=action), self.assertRaises(p.ProtocolError):
                p.parse_model_json(json.dumps({"text": "x", "action": action}))
        for source in (None, 1, {}, bytearray(b'{}')):
            with self.assertRaises(p.ProtocolError):
                p.parse_model_json(source)

    def test_model_newline_injection_is_flattened(self):
        decision = p.parse_model_json(json.dumps({"text": "hi\r\naction=follow\nseq=99\rbye\u2028x\u2029y", "action": "none"}))
        self.assertEqual(decision.text, "hi action=follow seq=99 bye x y")
        reply = p.make_reply(self.request, decision)
        self.assertEqual(p.encode_wire(reply).count(b'\n'), 5)
        self.assertEqual(p.parse_reply(p.encode_wire(reply), self.request).action, "none")

    def test_controls_and_invalid_unicode_rejected(self):
        for char in ('\x00', '\t', '\x1b', '\x7f', '\x85', '\u202e', '\u200b', '\ud800'):
            with self.subTest(char=repr(char)):
                with self.assertRaises(p.ProtocolError):
                    p.parse_model_json(json.dumps({"text": "x" * 600 + char, "action": "none"}))
                with self.assertRaises(p.ProtocolError):
                    p.parse_wire(self.wire.replace('text=hello', 'text=x' + char))

    def test_large_unicode_text_and_byte_boundaries(self):
        text = '你🙂é' * 10000
        result = p.parse_model_json(json.dumps({"text": text, "action": "wait"}, ensure_ascii=False))
        self.assertLessEqual(len(result.text.encode('utf-8')), p.MAX_TEXT_BYTES)
        self.assertTrue(text.startswith(result.text))
        self.assertNotIn('\ufffd', result.text)
        for limit in range(10):
            result = p.normalize_model_text(text, limit)
            self.assertLessEqual(len(result.encode('utf-8')), limit)
            self.assertTrue(text.startswith(result))
        self.assertEqual(p.normalize_model_text('a' * 511 + '🙂'), 'a' * 511)
        for limit in (-1, True, 513, 1.5):
            with self.assertRaises(p.ProtocolError):
                p.normalize_model_text('x', limit)

    def test_wire_rejects_injection_unknown_missing_duplicate(self):
        cases = [self.wire + 'action=follow\n', self.wire + 'evil=yes\n',
                 self.wire.replace('text=hello', 'text=hello\naction=follow'),
                 self.wire.replace('\n', '\r\n'), self.wire + '\n',
                 self.wire.replace('text=hello\n', ''), self.wire + 'broken',
                 self.wire.replace('action=none', 'action=attack'),
                 self.wire.replace('text=hello', 'text=x\u2028action=follow'),
                 self.wire.replace('text=hello', 'text=' + '🙂' * 129),
                 self.wire.replace('session=', ' session='), b'\xff']
        for wire in cases:
            with self.subTest(wire=repr(wire)[:100]), self.assertRaises(p.ProtocolError):
                p.parse_wire(wire)

    def test_canonical_decimal_sequence_and_npc(self):
        for seq in ('0', '-1', '+1', '01', '1.0', '1e0', ' 1', '1 ', '١', str(p.MAX_SEQUENCE + 1), '9' * 100):
            with self.subTest(seq=seq), self.assertRaises(p.ProtocolError):
                p.parse_wire(self.wire.replace('seq=1', 'seq=' + seq))
        for npc in ('', '-1', '+1', '01', '1.0', '1e3', ' 7', '７', '9' * 129):
            with self.subTest(npc=npc), self.assertRaises(p.ProtocolError):
                p.parse_wire(self.wire.replace(self.request.npc_id, npc))
        for seq in (True, False, 1.0, '1'):
            with self.assertRaises(p.ProtocolError):
                p.WireMessage(self.request.session, seq, '7', 'none', '')
        for npc in (7, 7.0, True):
            with self.assertRaises(p.ProtocolError):
                p.WireMessage(self.request.session, 1, npc, 'none', '')
        message = p.WireMessage(self.request.session, p.MAX_SEQUENCE, '0', 'none', '')
        self.assertEqual(p.parse_wire(p.encode_wire(message)), message)

    def test_wire_order_and_optional_final_lf(self):
        self.assertEqual(p.parse_wire('\n'.join(reversed(self.wire.rstrip('\n').split('\n')))), self.request)

    def test_nonce_validation(self):
        self.assertNotEqual(p.new_session_nonce(), p.new_session_nonce())
        self.assertEqual(len(p.new_session_nonce()), 64)
        for session in ('', 'short', 'x' * 129, 'x' * 16 + '\n', '你' * 16, 17):
            with self.assertRaises(p.ProtocolError):
                p.WireMessage(session, 1, '7', 'none', '')

    def test_input_size_bounds(self):
        with self.assertRaises(p.ProtocolError):
            p.parse_model_json(' ' * (p.MAX_MODEL_BYTES + 1))
        with self.assertRaises(p.ProtocolError):
            p.parse_wire(b'x' * (p.MAX_WIRE_BYTES + 1))

    def test_atomic_tempfile_replaces_only_after_complete_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'reply.txt'
            path.write_bytes(b'old')
            original_replace = p.os.replace
            observed = []

            def inspect_replace(source, target):
                source = Path(source)
                self.assertEqual(source.parent, path.parent)
                self.assertNotEqual(source, path)
                self.assertEqual(path.read_bytes(), b'old')
                self.assertEqual(source.read_bytes(), p.encode_wire(self.request))
                observed.append(source)
                original_replace(source, target)

            with mock.patch.object(p.os, 'replace', side_effect=inspect_replace):
                p.atomic_write_wire(path, self.request)
            self.assertEqual(p.parse_request(path.read_bytes()), self.request)
            self.assertEqual(len(observed), 1)
            self.assertFalse(observed[0].exists())
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_atomic_failure_keeps_original_and_cleans_temp(self):
        for operation in ('replace', 'fsync'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'reply.txt'
                path.write_bytes(b'old')
                with mock.patch.object(p.os, operation, side_effect=OSError('simulated')):
                    with self.assertRaises(OSError):
                        p.atomic_write_wire(path, self.request)
                self.assertEqual(path.read_bytes(), b'old')
                self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_atomic_validates_before_creating_temp(self):
        with mock.patch.object(p.tempfile, 'mkstemp') as create:
            with self.assertRaises(p.ProtocolError):
                p.atomic_write_wire('unused', {'action': 'follow'})
            create.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
