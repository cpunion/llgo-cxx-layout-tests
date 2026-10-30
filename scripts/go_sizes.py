#!/usr/bin/env python3
"""Run Go storage probes; record failures as data, never as passing assertions."""
import argparse
import json
import os
import pathlib
import re
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--llgo', default='llgo')
p.add_argument('--profile', choices=['native', 'gojs', 'emscripten', 'emscripten-memory64', 'wasi'], default='native')
p.add_argument('--out', default='results/go-sizes')
a = p.parse_args()
out = ROOT / a.out
out.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
llflags = []
goflags = []
if a.profile != 'native':
    env.update(GOOS='wasip1' if a.profile == 'wasi' else 'js', GOARCH='wasm', CGO_ENABLED='0')
    llflags = ['-emulator']
    if a.profile != 'gojs':
        llflags += ['-target', a.profile]
    if a.profile == 'wasi':
        goflags = ['-exec=wasmtime']
    else:
        goroot = subprocess.check_output(['go', 'env', 'GOROOT'], text=True).strip()
        goflags = ['-exec=' + str(pathlib.Path(goroot) / 'lib/wasm/go_js_wasm_exec')]

rows = []
def run(name, cmd, cwd, expected):
    start = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=900)
        log, code = r.stdout, r.returncode
    except subprocess.TimeoutExpired as e:
        log = e.stdout or b''
        if isinstance(log, bytes): log = log.decode(errors='replace')
        log += '\nAUDIT PROCESS TIMEOUT\n'
        code = 124
    (out / (name + '.log')).write_text(log)
    passed = re.findall(r'^\s*--- PASS: (\S+)', log, re.M)
    failed = re.findall(r'^\s*--- FAIL: (\S+)', log, re.M)
    started = re.findall(r'^=== RUN\s+(\S+)', log, re.M)
    complete = all(x in passed for x in expected)
    status = 'PASS' if code == 0 and complete else 'FAIL' if failed else 'ERROR'
    rows.append(dict(name=name, command=cmd, cwd=str(cwd), status=status, exit=code,
                     passed=passed, failed=failed, started=started,
                     seconds=round(time.time()-start, 2)))
    print(name, status, 'passed', len(passed), 'failed', len(failed), flush=True)
    (out / 'summary.json').write_text(json.dumps(rows, indent=2)+'\n')

source = (ROOT / 'experiments/go_sizes/sizes_test.go').read_text()
names = re.findall(r'\(t, "([a-z0-9_]+)", unsafe.Sizeof', source)
expected = ['TestGoTypeSizes'] + ['TestGoTypeSizes/'+x for x in names]
common = ['-count=1', '-v', '-timeout=3m']
goenv = subprocess.check_output(['go', 'env', 'GOOS', 'GOARCH', 'GOVERSION'], env=env, text=True)
provenance = dict(profile=a.profile, go_env=goenv.splitlines(), llgo_root=env.get('LLGO_ROOT'),
                  expected_cases=len(names), audit_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
if env.get('LLGO_ROOT'):
    provenance['llgo_commit'] = subprocess.check_output(['git','rev-parse','HEAD'],cwd=env['LLGO_ROOT'],text=True).strip()
(out / 'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
run('gc', ['go', 'test']+goflags+common+['./experiments/go_sizes'], ROOT, expected)
run('llgo', [a.llgo, 'test']+llflags+common+['./experiments/go_sizes'], ROOT, expected)
if env.get('LLGO_ROOT'):
    run('existing-unsafe', [a.llgo, 'test']+llflags+common+['./test/std/unsafe'],
        pathlib.Path(env['LLGO_ROOT']), ['TestSizeof', 'TestAlignof', 'TestOffsetof'])
