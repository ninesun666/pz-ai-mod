"""Offline cross-language roundtrip. Fake model transport, not native/model proof."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bridge'))
import teammate_bridge as bridge
import teammate_protocol as protocol
from test_teammate_mailbox import boot, Reader


class ChineseRoundtripTests(unittest.TestCase):
    def test_chinese_request_bridge_reply_lua_action_and_speech(self):
        for action, answer in [('none', '我在这里，有什么打算？'),
                               ('follow', '好，我跟着你。'),
                               ('wait', '好，我在这里等你。')]:
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temp:
                lua, sink, _, ticks, now, npc = boot()
                mailbox = lua.globals().DC_AI_TeammateMailbox
                commands = []
                def command(value):
                    commands.append(value)
                    return True
                lua.globals().DC_AI_Teammate.follow = lambda: command('follow')
                lua.globals().DC_AI_Teammate.wait = lambda: command('wait')
                text = '请在这里等待，我去看看前面。'
                self.assertTrue(mailbox.request(text))
                root = Path(temp)
                request, reply = root/'request.txt', root/'reply.txt'
                request.write_bytes(sink[0].encode('utf-8'))
                original = protocol.parse_request(request.read_bytes())
                self.assertEqual(original.text, text)
                envelope = {'choices': [{'finish_reason': 'stop', 'message': {
                    'content': json.dumps({'text': answer, 'action': action}, ensure_ascii=False)
                }}]}
                response = io.BytesIO(json.dumps(envelope, ensure_ascii=False).encode('utf-8'))
                response.status = 200
                transport = Mock(return_value=response)
                config = bridge.ModelConfig('https://example.invalid/v1/chat/completions', 'fake-model', 'test-only')
                with patch.object(bridge.urllib_request, 'build_opener', side_effect=AssertionError('network forbidden')):
                    worker = bridge.TeammateBridge(config=config, opener=transport)
                    worker.process_once(request, reply)
                sent = json.loads(transport.call_args.args[0].data)
                self.assertEqual(json.loads(sent['messages'][1]['content'])['text'], text)
                self.assertIn('text 默认使用简体中文', sent['messages'][0]['content'])
                result = protocol.parse_reply(reply.read_bytes(), original)
                self.assertEqual(result.text, answer)
                self.assertEqual(result.npc_id, '9007199254740993')
                wire = reply.read_text(encoding='utf-8')
                lua.globals().getFileReader = lambda *args: Reader(wire)
                now[0] += 300
                ticks[0]()
                self.assertEqual(mailbox.status()['phase'], 'complete')
                self.assertIsNone(mailbox.status()['error'])
                self.assertEqual(npc.say, [answer])
                self.assertEqual(commands, [] if action == 'none' else [action])
                now[0] += 300
                ticks[0]()
                self.assertEqual(npc.say, [answer])
                self.assertEqual(commands, [] if action == 'none' else [action])
                transport.assert_called_once()


if __name__ == '__main__':
    unittest.main()
