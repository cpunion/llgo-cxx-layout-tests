#!/usr/bin/env python3
"""Install a temporary in-package audit in a clean LLGo checkout and remove it."""
import argparse, json, os, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--llgo-root', required=True)
p.add_argument('--out', default='results/go-ir')
a=p.parse_args()
src=pathlib.Path(a.llgo_root).resolve()
out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
fixture=src/'ssa/zz_external_basic_size_audit_test.go'
env=os.environ.copy();env['AUDIT_IR_OUT']=str(out)
cmd=['go','test','-count=1','-v','./ssa','-run','^TestAuditGoBasicLLVMTypes$']
with fixture.open('x') as f:
    f.write((ROOT/'experiments/go_ir/size_ir_test.go.txt').read_text())
try:
    r=subprocess.run(cmd,cwd=src,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
    (out/'test.log').write_text(r.stdout)
    (out/'provenance.json').write_text(json.dumps(dict(command=cmd,exit=r.returncode,
        llgo_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=src,text=True).strip(),
        go=subprocess.check_output(['go','version'],text=True).strip(),
        llvm=subprocess.check_output(['llvm-config','--version'],text=True).strip()),indent=2)+'\n')
    print(r.stdout[-3000:])
finally:
    fixture.unlink()
raise SystemExit(r.returncode)
