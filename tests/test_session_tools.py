"""Offline regression tests: no game launch, process stop, or live mailbox access."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'tools/run-session.ps1'
DRIVER = ROOT / 'tools/test-driver/DCTestDriver.lua'

class SessionCliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([shutil.which('pwsh'), '-NoProfile', '-File', str(RUNNER), '-ValidateOnly', *args], capture_output=True, text=True)

    def test_json_and_defaults(self):
        for args in [(), ('-StepsJson', '["cmd=ping","cmd=snapshot"]')]:
            result = self.invoke(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), ['cmd=ping', 'cmd=snapshot'])

    def test_file_and_single_step(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'steps with spaces.json'
            path.write_text('["cmd=ping","cmd=snapshot"]', encoding='utf-8')
            result = self.invoke('-StepsFile', str(path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)), 2)
        self.assertEqual(json.loads(self.invoke('-StepsJson', '["cmd=ping"]').stdout), ['cmd=ping'])

    def test_reject_ambiguous_invalid_and_shutdown(self):
        for args in [('-Steps', 'cmd=ping,cmd=snapshot'), ('-StepsJson', '"cmd=ping"'), ('-StepsJson','[]'), ('-StepsJson','[1]'), ('-StepsJson','["cmd=quit"]'), ('-StepsJson','["cmd=ping;seq=3"]'), ('-StepsJson','["cmd=ping;cmd=save"]'), ('-Steps','cmd=ping','-StepsJson','["cmd=ping"]')]:
            with self.subTest(args=args):
                self.assertNotEqual(self.invoke(*args).returncode, 0)

    def test_parsers(self):
        script = "$e=$null;$t=$null;foreach($p in @('tools/run-session.ps1','tools/sync-test-driver.ps1')){[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PWD $p),[ref]$t,[ref]$e)|Out-Null;if($e.Count){throw ($e|Out-String)}}"
        result = subprocess.run([shutil.which('pwsh'), '-NoProfile', '-Command', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

class DriverTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
files={}; saved=0; quit=0
Events={OnTick={Add=function(f) tick=f end},OnGameStart={Add=function(f) start=f end}}
function getFileReader(path)
 local s=files[path];if not s then return nil end;local i=0
 return {read=function() i=i+1;if i>#s then return -1 end;return string.byte(s,i) end,close=function() end}
end
function getFileWriter(path) return {write=function(_,s) files[path]=s end,close=function() end} end
function getSpecificPlayer() return nil end
function saveGame() saved=saved+1 end
function dcTestQuit() quit=quit+1 end
function send(s) files['dctest_in.txt']=s;for i=1,10 do tick() end;return files['dctest_out.txt'] end
''')
        self.lua.execute(DRIVER.read_text(encoding='utf-8'))

    def test_readonly_and_quit_disabled(self):
        g = self.lua.globals()
        self.assertIn('session=abc;seq=1;ok=1;pong=1', g.send('session=abc;seq=1;cmd=ping'))
        self.assertIn('ok=1', g.send('session=abc;seq=2;cmd=snapshot'))
        self.assertIn('err=quit_disabled', g.send('session=abc;seq=3;cmd=quit'))
        self.assertEqual((g.saved,g.quit), (0,0))

    def test_identity_and_duplicate(self):
        send=self.lua.globals().send
        self.assertIn('bad_identity',send('seq=1;cmd=ping'))
        self.assertIn('pong=1',send('session=abc;seq=1;cmd=ping'))
        self.assertIn('session=xyz;seq=2;ok=0;err=session_mismatch',send('session=xyz;seq=2;cmd=save'))
        self.assertIn('duplicate_field',send('session=abc;seq=2;cmd=ping;cmd=save'))
        self.assertIn('stale_seq',send('session=abc;seq=1;cmd=snapshot'))
        self.assertEqual(self.lua.globals().saved,0)

    def test_execution_error_keeps_identity(self):
        self.lua.execute("getSpecificPlayer=function() return 1 end")
        result=self.lua.globals().send('session=abc;seq=1;cmd=snapshot')
        self.assertIn('session=abc;seq=1;ok=0;err=execution_error;', result)

if __name__ == '__main__': unittest.main()
