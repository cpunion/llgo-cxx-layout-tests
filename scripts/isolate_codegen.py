#!/usr/bin/env python3
"""Manual diagnostic lane: serialized compilation and smaller packed/generic programs."""
import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];out=ROOT/'results/codegen-isolation';out.mkdir(parents=True,exist_ok=True);rows=[]
items=[('full-serial',['llgo','test','-p=1','-count=1','-v','./proposals/layout_runtime'])]
for name in ['packed_arg','pack2_arg','promoted','native_func']:items.append((name,['llgo','run','-p=1','./experiments/packed_codegen/'+name]))
for name,cmd in items:
 r=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(name+'.log')).write_text(r.stdout);rows.append({'case':name,'command':cmd,'exit':r.returncode,'status':'PASS' if r.returncode==0 else 'COMPILER_CRASH' if 'SIGSEGV' in r.stdout else 'ERROR'});print(name,rows[-1]['status'],flush=True)
(out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
# Diagnostic lane records compiler failures as data; it does not mark them passing.
